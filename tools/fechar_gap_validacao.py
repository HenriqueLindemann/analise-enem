#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Reconstrói associações de itens e seleciona EAP sem ajustar ao holdout.

Uso: OPENBLAS_NUM_THREADS=1 python tools/fechar_gap_validacao.py
       --microdados-dir /caminho/MICRODADOS_ENEM --workers 3

O cache contém somente respostas, notas e hashes de casos; nunca inscrições.
As fontes originais continuam preservadas. Modelos e métricas são publicados
atomicamente pelo mesmo fluxo da recalibração canônica.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import platform
from collections import defaultdict
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tri_enem import CalculadorTRI, MapeadorProvas
from tools.recalibrar_validacao import (
    AmostraEstratificada, Caso, IDENTITY_ALGORITHM, _disponibilidade_itens, _provas_mapeadas,
    amostrar_microdados_paralelo, calibrar_catalogo, criar_manifesto,
    dividir_amostra, localizar_microdados, publicar_atomico, validar_artefatos,
)
from tools.reconstruir_associacao_itens import (
    ajustar_curvas, ajustar_um_item, associar_curvas,
    refinar_associacao, refinar_trocas, refinar_gabaritos, theta_parametros,
)

VERSION = "item-association-v1"
FAMILIAS = (
    (2011, "CN", [121, 122, 123, 124]),
    (2013, "MT", [179, 180, 181, 182]),
    (2016, "CN", [351, 352, 353, 354]),
    (2017, "CN", [391, 392, 393, 394]),
    (2017, "CH", [395, 396, 397, 398]),
    (2017, "MT", [403, 404, 405, 406]),
    (2018, "CN", [447, 448, 449, 450]),
    (2019, "MT", [515, 516, 517, 518]),
)
# A coleção adaptada usa a ordem do primeiro caderno regular no arquivo de
# itens; as respostas e gabaritos dos participantes usam o caderno indicado
# em codigo_base. Esses pares foram conferidos no arquivo inteiro de 2013.
ADAPTADAS_2013 = (
    ("CH", 187, 167, 169, 184), ("CN", 188, 171, 173, 183),
    ("LC", 189, 175, 176, 185), ("MT", 190, 179, 180, 186),
)


def proveniencia_algoritmo():
    arquivos = [ROOT / p for p in ("tools/fechar_gap_validacao.py",
        "tools/reconstruir_associacao_itens.py", "tools/recalibrar_validacao.py",
        "src/tri_enem/calculador.py", "src/tri_enem/calibracao_modelos.py",
        "src/tri_enem/precisao.py")]
    return {"runtime": {"python": platform.python_version(), "numpy": np.__version__,
                        "pandas": pd.__version__, "scipy": scipy.__version__},
            "code_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in arquivos}}


def salvar_amostra(cache, amostra, splits, diagnostico, fontes):
    dados = {
        "version": 2, "identity_algorithm": IDENTITY_ALGORITHM, "cap": amostra.cap,
        "sources": [{"path": str(p), "size": p.stat().st_size,
                     "mtime_ns": p.stat().st_mtime_ns} for p in fontes],
        "counts": [[*k, n] for k, n in amostra.contagens.items()],
        "splits": {k: {s: [asdict(c) for c in cs] for s, cs in v.items()}
                   for k, v in splits.items()},
        "diagnostics": diagnostico,
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache, "wt", encoding="utf-8") as f:
        json.dump(dados, f)


def carregar_amostra(cache, base):
    with gzip.open(cache, "rt", encoding="utf-8") as f:
        dados = json.load(f)
    if dados["version"] != 2 or dados.get("identity_algorithm") != IDENTITY_ALGORITHM:
        raise ValueError("Versão do cache de amostra inválida")
    fontes = [localizar_microdados(base, y) for y in range(2009, 2026)]
    atuais = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in fontes}
    salvas = {r["path"]: (r["size"], r["mtime_ns"]) for r in dados["sources"]}
    if atuais != salvas:
        raise ValueError("Fontes alteradas: remova o cache e amostre novamente")
    amostra = AmostraEstratificada(dados["cap"])
    for prova, lingua, faixa, n in dados["counts"]:
        amostra.registrar_contagem((prova, lingua, faixa), n)
    splits = {k: {s: [Caso(**c) for c in cs] for s, cs in v.items()}
              for k, v in dados["splits"].items()}
    return amostra, splits, dados["diagnostics"], fontes


def banco_parametros(calc, ano, area, codigos=None):
    df = calc._carregar_df_itens(ano)
    df = df[df.SG_AREA.eq(area)]
    if codigos is not None:
        df = df[df.CO_PROVA.isin(codigos)]
    return df[["NU_PARAM_A", "NU_PARAM_B", "NU_PARAM_C"]].dropna().drop_duplicates().to_numpy()


def matriz_original(calc, casos, itens_referencia):
    """Inclui posições publicadas como abandonadas na investigação."""
    ids = [t.co_item for t in itens_referencia]
    u = []
    for caso in casos:
        itens = calc.carregar_itens(caso.ano, caso.area, caso.co_prova, caso.tp_lingua)
        resposta = calc.normalizar_respostas(caso.respostas, caso.area, caso.ano, caso.tp_lingua)
        valores = {t.co_item: int(r == t.gabarito) for t, r in zip(itens, resposta)}
        u.append([valores[i] for i in ids])
    return np.asarray(u, dtype=float), np.asarray([c.nota_oficial for c in casos])


def resolver(u, y, inicial, banco, area):
    curvas, diagnostico = ajustar_curvas(u, y, inicial, area, max_nfev=600)
    par, _ = associar_curvas(curvas, banco)
    par, custo = refinar_associacao(u, y, par, banco, max_passes=25)
    if custo > 0.002:
        par, _ = refinar_trocas(u, y, par)
        par, custo = refinar_associacao(u, y, par, banco, max_passes=10)
    return par, {**diagnostico, "mse_discreto_treino": custo}


def assinatura_casos(casos):
    return hashlib.sha256("\n".join(sorted(c.case_id for c in casos)).encode()).hexdigest()


def payload(itens, parametros, origem, inferencia=None, codigo_base=None):
    resultado = {
        "quadratura": "grade_41", "origem": origem,
        "itens": [
            {"a": float(p[0]), "b": float(p[1]), "c": float(p[2]),
             "abandonado": bool(p[0] == 0), "gabarito": item.gabarito,
             "co_item": item.co_item}
            for item, p in zip(itens, parametros)
        ],
    }
    if inferencia is not None:
        resultado["inferencia"] = inferencia
    if codigo_base is not None:
        resultado["codigo_base"] = codigo_base
    return resultado


def candidatos_familias(calc, provas, splits, candidatos):
    mapas = {}
    for ano, area, codigos in FAMILIAS:
        itens = [replace(t) for t in calc.carregar_itens(ano, area, codigos[0])]
        casos = [c for p in codigos for c in splits[f"{ano},{area},{p}"]["treino"]]
        u, y = matriz_original(calc, casos, itens)
        inicial = np.asarray([(t.param_a, t.param_b, t.param_c) if not t.abandonado
                              else (0, 0, 0.2) for t in itens])
        banco = banco_parametros(calc, ano, area, codigos)
        par, diag = resolver(u, y, inicial, banco, area)
        if ano == 2016 and area == "CN":
            raw = []
            for caso in casos:
                atuais = calc.carregar_itens(ano, area, caso.co_prova)
                s = calc.normalizar_respostas(caso.respostas, area, ano, None)
                letras = {t.co_item: r for t, r in zip(atuais, s)}
                raw.append([letras[t.co_item] for t in itens])
            par, keys, custo = refinar_gabaritos(
                raw, y, par, [t.gabarito for t in itens], banco)
            for item, key in zip(itens, keys):
                item.gabarito = str(key)
            u = (np.asarray(raw) == keys).astype(float)
            diag["mse_discreto_treino"] = custo
        print(f"{ano}/{area}: associação discreta; {diag}", flush=True)
        ids = [t.co_item for t in itens]
        mapa = dict(zip(ids, par))
        mapas[(ano, area)] = mapa
        # Um parâmetro ausente pode não existir no banco publicado. Testamos
        # ajuste de um único item, como candidato distinto e identificado.
        parcial, custo, j = ajustar_um_item(u, y, par) if diag["mse_discreto_treino"] > .002 else (par, 0, None)
        alternativas = [(mapa, "associacao_parametros_publicados", [])]
        if j is not None:
            alternativas.append((dict(zip(ids, parcial)), "associacao_com_parametro_estimado", [ids[j]]))
        for (a, ar, code), _ in provas.items():
            if (a, ar) != (ano, area):
                continue
            try:
                atuais = calc.carregar_itens(ano, area, code)
            except ValueError:
                continue
            if sum(t.co_item in mapa for t in atuais) < 30:
                continue
            key = f"{ano},{area},{code}"
            for mp, origem, estimados in alternativas:
                params = np.asarray([mp.get(t.co_item, (t.param_a, t.param_b, t.param_c))
                                     if not t.abandonado or t.co_item in mp else (0, 0, .2)
                                     for t in atuais])
                keys = {t.co_item: t.gabarito for t in itens}
                atuais = [replace(t, gabarito=keys.get(t.co_item, t.gabarito)) for t in atuais]
                meta = {"algorithm": VERSION, "n_treino": len(casos),
                        "training_case_ids_sha256": assinatura_casos(casos),
                        "itens_com_parametros_estimados": estimados,
                        "diagnostico": diag}
                candidatos.setdefault(key, []).append(payload(atuais, params, origem, meta))
    return mapas


def candidatos_adaptadas(calc, splits, candidatos, mapas):
    df = calc._carregar_df_itens(2013)
    for area, code, template, base, ppl in ADAPTADAS_2013:
        por_lingua = {}
        por_lingua_parcial = {}
        for lingua in ((0, 1) if area == "LC" else (None,)):
            raw = df[df.SG_AREA.eq(area) & df.CO_PROVA.eq(code)]
            if area == "LC":
                raw = raw[raw.TP_LINGUA.isna() | raw.TP_LINGUA.eq(lingua)]
            normais = calc.carregar_itens(2013, area, template, lingua)
            norm_ids = {t.co_item for t in normais}
            ppl_ids = set(df[df.SG_AREA.eq(area) & df.CO_PROVA.eq(ppl)].CO_ITEM)
            escolhidos = {}
            for pos, grupo in raw.groupby("CO_POSICAO"):
                regular = grupo[grupo.CO_ITEM.isin(norm_ids)]
                escolha = regular if len(regular) == 1 else grupo[~grupo.CO_ITEM.isin(ppl_ids)]
                if len(escolha) != 1:
                    raise ValueError(f"2013/{area}/{code}/{pos}: coleção ambígua")
                escolhidos[int(pos)] = escolha.iloc[0]
            pos_template = {t.co_item: t.posicao for t in normais}
            atuais = calc.carregar_itens(2013, area, base, lingua)
            ordenados = [escolhidos[pos_template[t.co_item]] for t in atuais]
            atuais = [replace(t, co_item=int(r.CO_ITEM)) for t, r in zip(atuais, ordenados)]
            mapa = mapas.get((2013, area), {})
            inicial = np.asarray([mapa.get(int(r.CO_ITEM), (r.NU_PARAM_A, r.NU_PARAM_B, r.NU_PARAM_C)) for r in ordenados])
            casos = [c for c in splits[f"2013,{area},{code}"]["treino"] if c.tp_lingua == lingua]
            u = np.asarray([calc.converter_respostas(calc.normalizar_respostas(c.respostas, area, 2013, lingua), atuais) for c in casos])
            y = np.asarray([c.nota_oficial for c in casos])
            banco = banco_parametros(calc, 2013, area)
            par, custo = refinar_associacao(u, y, inicial, banco, max_passes=25)
            if custo > .002:
                novo, diag = resolver(u, y, par, banco, area)
                if diag["mse_discreto_treino"] < custo:
                    par, custo = novo, diag["mse_discreto_treino"]
            meta = {"algorithm": VERSION, "n_treino": len(casos),
                    "training_case_ids_sha256": assinatura_casos(casos),
                    "colecao": "1a_aplicacao", "codigo_template": template,
                    "mse_discreto_treino": float(custo)}
            por_lingua[str(lingua)] = payload(atuais, par, "adaptada_2013_parametros_publicados", meta, base)
            parcial, _, j = ajustar_um_item(u, y, par) if custo > .002 else (par, 0, None)
            estimados = [atuais[j].co_item] if j is not None else []
            if area == "MT" and j is not None:
                for _ in range(4):
                    parcial, _, j = ajustar_um_item(u, y, parcial, max_nfev=200)
                    if j is None:
                        break
                    estimados.append(atuais[j].co_item)
            por_lingua_parcial[str(lingua)] = payload(atuais, parcial,
                "adaptada_2013_parametro_estimado", {**meta, "itens_com_parametros_estimados": sorted(set(estimados))}, base)
            print(f"2013/{area}/{code}/{lingua}: MSE discreto={custo:.5f}", flush=True)
        key = f"2013,{area},{code}"
        candidatos.setdefault(key, []).extend([
            {"por_idioma": por_lingua, "origem": "adaptada_2013_parametros_publicados"},
            {"por_idioma": por_lingua_parcial, "origem": "adaptada_2013_parametro_estimado"},
        ])


def candidatos_isolados(calc, splits, candidatos):
    """Provas com associação própria; idiomas são tratados separadamente."""
    fontes = {}
    for ano, area, code in [(2015, "CN", 252), (2017, "CH", 412),
                            (2017, "LC", 413), (2021, "LC", 896), (2021, "LC", 897)]:
        key = f"{ano},{area},{code}"
        por_lingua, estimada = {}, {}
        for lingua in ((0, 1) if area == "LC" else (None,)):
            itens = calc.carregar_itens(ano, area, code, lingua)
            casos = [c for c in splits[key]["treino"] if c.tp_lingua == lingua]
            raw = np.asarray([list(calc.normalizar_respostas(c.respostas, area, ano, lingua)) for c in casos])
            y = np.asarray([c.nota_oficial for c in casos])
            par = np.asarray([(t.param_a, t.param_b, t.param_c) if not t.abandonado
                              else (0, 0, .2) for t in itens])
            banco = banco_parametros(calc, ano, area)
            par, keys, custo = refinar_gabaritos(raw, y, par, [t.gabarito for t in itens], banco)
            u = (raw == keys).astype(float)
            if custo > .002:
                novo, diag = resolver(u, y, par, banco, area)
                if diag["mse_discreto_treino"] < custo:
                    par, custo = novo, diag["mse_discreto_treino"]
            itens = [replace(t, gabarito=str(k)) for t, k in zip(itens, keys)]
            meta = {"algorithm": VERSION, "n_treino": len(casos),
                    "training_case_ids_sha256": assinatura_casos(casos),
                    "mse_discreto_treino": float(custo)}
            por_lingua[str(lingua)] = payload(itens, par, "parametros_publicados_gabaritos_inferidos", meta)
            parcial, _, j = ajustar_um_item(u, y, par) if custo > .002 else (par, 0, None)
            estimada[str(lingua)] = payload(itens, parcial, "associacao_com_parametro_estimado",
                {**meta, "itens_com_parametros_estimados": [itens[j].co_item] if j is not None else []})
            print(f"{key}/{lingua}: MSE discreto={custo:.6f}", flush=True)
        candidatos[key].extend([
            {"por_idioma": por_lingua, "origem": "parametros_publicados_gabaritos_inferidos"},
            {"por_idioma": estimada, "origem": "associacao_com_parametro_estimado"},
        ])
        fontes[key] = por_lingua
    # As curvas comuns recuperadas no espanhol da adaptação de 2021 são
    # identificadas com mais casos. Transferir por CO_ITEM dá um candidato
    # separado para o inglês e os cadernos 895/896, sujeito à mesma seleção.
    fonte = fontes["2021,LC,897"]["1"]
    mapa = {t["co_item"]: t for t in fonte["itens"][5:]}
    for code in (895, 896, 897):
        key, por_lingua = f"2021,LC,{code}", {}
        for lingua in (0, 1):
            itens = calc.carregar_itens(2021, "LC", code, lingua)
            itens = [replace(t, gabarito=mapa.get(t.co_item, {}).get("gabarito", t.gabarito)) for t in itens]
            par = np.asarray([[mapa[t.co_item][k] for k in ("a", "b", "c")] if t.co_item in mapa
                              else (t.param_a, t.param_b, t.param_c) if not t.abandonado
                              else (0, 0, .2) for t in itens])
            casos = [c for c in splits.get(key, {}).get("treino", []) if c.tp_lingua == lingua]
            if not casos:
                por_lingua[str(lingua)] = payload(itens, par, "transferencia_parametros_publicados")
                continue
            u = np.asarray([calc.converter_respostas(calc.normalizar_respostas(c.respostas, "LC", 2021, lingua), itens) for c in casos])
            y = np.asarray([c.nota_oficial for c in casos])
            par, custo = refinar_associacao(u, y, par, banco_parametros(calc, 2021, "LC"), 20)
            meta = {"algorithm": VERSION, "n_treino": len(casos),
                    "training_case_ids_sha256": assinatura_casos(casos),
                    "fonte_itens_comuns": fonte["inferencia"], "mse_discreto_treino": float(custo)}
            por_lingua[str(lingua)] = payload(itens, par, "transferencia_parametros_publicados", meta)
        candidatos.setdefault(key, []).append({"por_idioma": por_lingua,
                                               "origem": "transferencia_parametros_publicados"})


def extremos_de_treino(calc, splits, candidatos):
    """Âncoras identificáveis em treino, compartilhadas por curvas equivalentes."""
    grupos, configuracoes = defaultdict(dict), {}
    for key, split in splits.items():
        ano, area, code = key.split(",")
        ano, code = int(ano), int(code)
        for config in [None, *candidatos.get(key, [])]:
            origem = "vigente" if config is None else config["origem"]
            c = calc if config is None else CalculadorTRI(reconstrucoes={key: config})
            c._cache_df_itens = calc._cache_df_itens
            identidades, internos = [], []
            for lingua in sorted({r.tp_lingua for r in split["treino"]}, key=str):
                itens = c.carregar_itens(ano, area, code, lingua)
                ativos = [j for j, t in enumerate(itens) if not t.abandonado]
                if len(ativos) < 2:
                    continue
                identidade = (ano, area, itens[0].metodo_quadratura,
                    tuple(sorted((t.param_a, t.param_b, t.param_c) for t in itens if not t.abandonado)))
                padroes = np.zeros((2 + 2 * len(ativos), len(itens)))
                padroes[1] = 1
                for j, idx in enumerate(ativos):
                    padroes[2+j, idx] = 1
                    padroes[2+len(ativos)+j] = 1
                    padroes[2+len(ativos)+j, idx] = 0
                theta = c.estimar_theta_eap_batch(padroes, itens)
                internos.append((float(theta[2:2+len(ativos)].min()),
                                 float(theta[2+len(ativos):].max())))
                identidades.append((identidade, float(theta[0]), float(theta[1])))
                for r in split["treino"]:
                    if r.tp_lingua != lingua:
                        continue
                    texto = c.normalizar_respostas(r.respostas, area, ano, lingua)
                    u = np.asarray(c.converter_respostas(texto, itens))[ativos]
                    if u.sum() in (0, len(ativos)):
                        extremo = int(u.sum() > 0)
                        grupos[(identidade, extremo)][r.case_id] = r.nota_oficial
            if internos:
                configuracoes[(key, origem)] = (identidades,
                    [min(t[0] for t in internos), max(t[1] for t in internos)])
    resultado = {}
    for key, (identidades, limites) in configuracoes.items():
        pontos, contagem, ids = {}, 0, set()
        for identidade, t0, t1 in identidades:
            for extremo, t in enumerate((t0, t1)):
                casos = grupos[(identidade, extremo)]
                notas = list(casos.values())
                # Respostas equivalentes com notas diferentes não são âncoras.
                if notas and max(notas) - min(notas) <= .10000001:
                    tt = round(t, 10)
                    pontos[tt] = float(np.median(notas))
                    contagem += len(notas)
                    ids.update(casos)
        if pontos:
            resultado[key] = {"pontos": sorted(map(list, pontos.items())),
                "limites_internos": limites, "n_treino_extremos": contagem,
                "training_case_ids_sha256": hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()}
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microdados-dir", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--cache-amostra", type=Path, default=ROOT / "resultados/investigacao/amostra.json.gz")
    parser.add_argument("--nao-publicar", action="store_true")
    args = parser.parse_args()
    calc = CalculadorTRI(reconstrucoes={})
    provas = _provas_mapeadas(MapeadorProvas(), list(range(2009, 2026)))
    disponiveis, problemas = _disponibilidade_itens(calc, provas)
    if args.cache_amostra.exists():
        amostra, splits, diagnostico, fontes = carregar_amostra(args.cache_amostra, args.microdados_dir)
    else:
        amostra, diagnostico, fontes = amostrar_microdados_paralelo(
            args.microdados_dir, list(range(2009, 2026)), provas, disponiveis, 250_000, 160, args.workers)
        splits = dividir_amostra(amostra)
        salvar_amostra(args.cache_amostra, amostra, splits, diagnostico, fontes)
    candidatos = {f"{a},{ar},{p}": [{"quadratura": "grade_41", "origem": "grade_41"}]
                  for a, ar, p in provas}
    arquivos_algoritmo = [Path(__file__), ROOT / "tools/reconstruir_associacao_itens.py",
        ROOT / "tools/recalibrar_validacao.py", ROOT / "src/tri_enem/calibracao_modelos.py",
        ROOT / "src/tri_enem/calculador.py", ROOT / "src/tri_enem/data/itens/manifest.json", args.cache_amostra,
        *sorted((ROOT / "src/tri_enem/data/itens").glob("*/*.csv"))]
    proveniencia = proveniencia_algoritmo()
    assinatura = hashlib.sha256(b"".join(p.read_bytes() for p in arquivos_algoritmo)
        + json.dumps(proveniencia["runtime"], sort_keys=True).encode()).hexdigest()
    cache_candidatos = args.cache_amostra.parent / "candidatos_reconstrucao.json"
    salvos = json.loads(cache_candidatos.read_text()) if cache_candidatos.exists() else {}
    if salvos.get("assinatura") == assinatura:
        candidatos = salvos["candidatos"]
        extremos = {(k, o): v for k, o, v in salvos["extremos"]}
        print("Reutilizando candidatos conferidos pelo hash do algoritmo e das fontes", flush=True)
    else:
        mapas = candidatos_familias(calc, provas, splits, candidatos)
        candidatos_adaptadas(calc, splits, candidatos, mapas)
        candidatos_isolados(calc, splits, candidatos)
        extremos = extremos_de_treino(calc, splits, candidatos)
        cache_candidatos.write_text(json.dumps({"assinatura": assinatura, "candidatos": candidatos,
            "extremos": [[k, o, v] for (k, o), v in extremos.items()]}, ensure_ascii=False))
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    catalogo, holdout = calibrar_catalogo(calc, provas, problemas, amostra, splits,
        timestamp, candidatos_reconstrucao=candidatos, extremos_estimadores=extremos)
    validar_artefatos(catalogo, holdout, provas)
    manifesto = criar_manifesto(catalogo, holdout, fontes, amostra, splits,
                               diagnostico, timestamp, not args.nao_publicar)
    manifesto["algorithm_version"] = VERSION
    manifesto["research"] = {"estimator_selection": "treino_e_selecao",
                             "holdout_used_for_fitting": False, **proveniencia}
    if not args.nao_publicar:
        publicar_atomico(catalogo, holdout, manifesto)
    else:
        destino = args.cache_amostra.parent / "catalogo_candidato.json"
        destino.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Concluído: {len(holdout)} casos; {manifesto['coverage']['status']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
