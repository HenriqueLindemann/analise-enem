#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Distribuição da nota oficial por número de acertos, por ano, aplicação e área.

Acertos contam só itens válidos (sem anuladas), como na interface. Cores e
idiomas da mesma aplicação são somados; cadernos de atendimento especializado
ficam fora. ``geral`` junta os participantes de todas as edições de cada
aplicação; ``geral_por_edicao`` dá o mesmo peso a cada edição. Grupos com menos
de 50 participantes não entram.

    python tools/levantar_notas_por_acertos.py --microdados-dir DIR --saida notas.json \\
        --app streamlit_app/assets/notas_por_acertos.json --processos 4

``--saida`` guarda tudo, com os histogramas da 1ª aplicação em ``.npz``.
``--app`` grava o recorte da interface; sem ``--microdados-dir``, refaz só o
recorte a partir da saída existente. No recorte, cada ano tem valor para 0 a
45 acertos: acima das questões válidas vale o gabarito, e grupos
pequenos vêm do modelo TRI da própria prova.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tri_enem import CalculadorTRI, MapeadorProvas  # noqa: E402
from tri_enem.calculador import ItemTRI  # noqa: E402
from tools.levantar_censo import AREAS, _inconsistentes  # noqa: E402
from tools.recalibrar_validacao import _linhas_validas, localizar_microdados  # noqa: E402

PERCENTIS = (5, 10, 25, 50, 75, 90, 95)
COLUNAS = ["n", "media", "min", *(f"p{p}" for p in PERCENTIS), "max"]
COLUNAS_GERAL = ["n", *(f"p{p}" for p in PERCENTIS)]
COLUNAS_GERAL_POR_EDICAO = ["edicoes", *(f"p{p}" for p in PERCENTIS)]
# Interface: mediana e faixa de 80% (p10 a p90), só da 1ª aplicação.
TIPO_APP = "1a_aplicacao"
AMOSTRAS_MODELO = 5000
MINIMO_PARTICIPANTES = 50
RESOLUCAO = 10  # bins de 0,1 ponto
LARGURA = 1000 * RESOLUCAO + 1
NOTAS = np.arange(LARGURA) / RESOLUCAO


def _percentis(contagem: np.ndarray) -> list[float]:
    acumulado = np.cumsum(contagem)
    return [round(float(NOTAS[np.searchsorted(acumulado, acumulado[-1] * p / 100)]), 1)
            for p in PERCENTIS]


def _estatisticas(contagem: np.ndarray) -> list:
    n = int(contagem.sum())
    ocupados = np.flatnonzero(contagem)
    media = float((contagem * NOTAS).sum() / n)
    return [n, round(media, 1), float(NOTAS[ocupados[0]]), *_percentis(contagem),
            float(NOTAS[ocupados[-1]])]


def levantar_ano(caminho: Path, ano: int) -> tuple[dict, dict]:
    calc, mapeador, inconsistentes = CalculadorTRI(), MapeadorProvas(), _inconsistentes()
    tipos = {(p.area, p.codigo): p.tipo_aplicacao for p in mapeador.listar_todas_provas(ano)}
    cabecalho = pd.read_csv(caminho, sep=";", nrows=0, encoding="latin1").columns
    colunas = [c for c in cabecalho if c == "TP_LINGUA" or any(
        c == f"{p}_{a}" for a in AREAS
        for p in ("TP_PRESENCA", "CO_PROVA", "NU_NOTA", "TX_RESPOSTAS"))]
    histogramas = defaultdict(lambda: np.zeros(46 * LARGURA, dtype=np.int64))
    itens_validos = defaultdict(set)
    for bloco in pd.read_csv(caminho, sep=";", usecols=colunas, encoding="latin1",
                             dtype=str, chunksize=500_000):
        for area in AREAS:
            linhas = _linhas_validas(bloco, ano, area, None)
            for (prova, lingua), grupo in linhas.groupby(["prova", linhas["lingua"].fillna(-1)]):
                tipo = tipos.get((area, int(prova)))
                if tipo is None or tipo == "especiais":
                    continue
                lingua = None if area != "LC" or ano == 2009 else int(lingua)
                try:
                    itens, binarias = calc.preparar_respostas_batch(
                        ano, area, int(prova), grupo["respostas"], lingua)
                except (ValueError, FileNotFoundError):
                    continue
                validos = np.asarray([not i.abandonado for i in itens])
                acertos = binarias[:, validos].sum(axis=1)
                oficiais = grupo["nota"].to_numpy(dtype=float)
                manter = ~np.asarray([
                    (ano, area, int(prova), o, r.upper()) in inconsistentes
                    for o, r in zip(oficiais, grupo["respostas"])
                ], dtype=bool)
                bins = np.clip(np.rint(oficiais * RESOLUCAO), 0, LARGURA - 1).astype(np.int64)
                chave = (tipo, area)
                indices = acertos[manter].astype(np.int64) * LARGURA + bins[manter]
                histogramas[chave] += np.bincount(indices, minlength=46 * LARGURA)
                itens_validos[chave].add(int(validos.sum()))
    provas, brutos = {}, {}
    for (tipo, area), plano in histogramas.items():
        hist = plano.reshape(46, LARGURA)
        n = hist.sum(axis=1)
        provas[f"{ano},{tipo},{area}"] = {
            "itens_validos": sorted(itens_validos[(tipo, area)]),
            "participantes": int(n.sum()),
            "acertos": {str(k): _estatisticas(hist[k])
                        for k in np.flatnonzero(n >= MINIMO_PARTICIPANTES)},
        }
        brutos[(tipo, area)] = hist
    return provas, brutos


def _levantar(args: tuple) -> tuple[dict, dict]:
    microdados_dir, ano = args
    return levantar_ano(localizar_microdados(microdados_dir, ano), ano)


def _amostrar_padroes(calc: CalculadorTRI, itens: list[ItemTRI], k: int,
                      rng: np.random.Generator) -> np.ndarray:
    """Padrões com exatamente ``k`` acertos nos itens válidos, sob o 3PL e θ ~ N(0, 1).

    Sorteia θ com peso P(k | θ) e, dado θ, quais itens foram acertados.
    Itens anulados entram como acerto: não pesam no θ, só na regra do gabarito.
    """
    validos = [i for i in itens if not i.abandonado]
    n = len(validos)
    pontos = np.linspace(-6, 6, 241)
    a, b, c = (np.array([getattr(i, f"param_{x}") for i in validos]) for x in "abc")
    p = c + (1 - c) / (1 + np.exp(-calc.D * a * (pontos[:, None] - b)))
    # f[q, i, j]: P(itens i..n-1 somam j | θ_q)
    f = np.zeros((len(pontos), n + 1, n + 2))
    f[:, n, 0] = 1.0
    for i in range(n - 1, -1, -1):
        f[:, i] = f[:, i + 1] * (1 - p[:, i, None])
        f[:, i, 1:] += f[:, i + 1, :-1] * p[:, i, None]
    peso = np.exp(-pontos ** 2 / 2) * f[:, 0, k]
    q = rng.choice(len(pontos), size=AMOSTRAS_MODELO, p=peso / peso.sum())
    restante = np.full(AMOSTRAS_MODELO, k)
    padroes = np.zeros((AMOSTRAS_MODELO, n), dtype=np.int8)
    for i in range(n):
        chance = p[q, i] * np.where(restante > 0, f[q, i + 1, np.maximum(restante - 1, 0)], 0)
        acerto = rng.random(AMOSTRAS_MODELO) < chance / f[q, i, restante]
        padroes[:, i] = acerto
        restante -= acerto
    completos = np.ones((AMOSTRAS_MODELO, len(itens)), dtype=np.int8)
    completos[:, [j for j, i in enumerate(itens) if not i.abandonado]] = padroes
    return completos


def notas_pelo_modelo(calc: CalculadorTRI, mapeador: MapeadorProvas, ano: int,
                      area: str, k: int, rng: np.random.Generator) -> list[float]:
    """Percentis 10, 50 e 90 da nota com ``k`` acertos; em LC, os dois idiomas."""
    codigo = mapeador.obter_codigo(ano, area, TIPO_APP, "azul")
    linguas = (0, 1) if area == "LC" and ano != 2009 else (None,)
    notas = []
    for lingua in linguas:
        itens = calc.carregar_itens(ano, area, codigo, lingua)
        padroes = _amostrar_padroes(calc, itens, k, rng)
        resultado = calc.transformar_escala_batch(calc.estimar_theta_eap_batch(padroes, itens), area)
        gabarito = calc.nota_gabarito(ano, area, codigo, lingua)
        if gabarito is not None:
            resultado = np.where(padroes.all(axis=1), gabarito, resultado)
        notas.append(resultado)
    return [round(float(v), 1) for v in np.percentile(np.concatenate(notas), [10, 50, 90])]


def recorte_app(saida: dict, histogramas: dict) -> dict:
    """1ª aplicação, de 0 a 45 acertos em todos os anos.

    Acima das questões válidas, usa todas as válidas (o gabarito). Com menos de
    50 participantes, os percentis vêm do modelo. ``geral`` junta só
    participantes reais, com a mesma regra.
    """
    calc, mapeador, rng = CalculadorTRI(), MapeadorProvas(), np.random.default_rng(0)
    indices = [COLUNAS.index(c) for c in ("p10", "p50", "p90")]
    edicoes, soma = defaultdict(dict), defaultdict(lambda: np.zeros((46, LARGURA), dtype=np.int64))
    for chave, prova in saida["provas"].items():
        ano, tipo, area = chave.split(",")
        if tipo != TIPO_APP:
            continue
        validos = max(prova["itens_validos"])
        hist = histogramas[f"{ano},{area}"]
        linhas = {}
        for k in range(46):
            efetivo = min(k, validos)
            soma[area][k] += hist[efetivo]
            real = prova["acertos"].get(str(efetivo))
            if real is not None:
                linhas[str(k)] = [*(real[i] for i in indices), 0]
            else:
                linhas[str(k)] = [*notas_pelo_modelo(calc, mapeador, int(ano), area, efetivo, rng), 1]
        edicoes[area][ano] = {"itens_validos": validos, "acertos": linhas}
    geral = {}
    for area, hist in sorted(soma.items()):
        n = hist.sum(axis=1)
        geral[area] = {str(k): [int(n[k]), *(_percentis(hist[k])[PERCENTIS.index(p)] for p in (10, 50, 90))]
                       for k in np.flatnonzero(n >= MINIMO_PARTICIPANTES)}
    return {
        "gerado_em": saida["gerado_em"],
        "colunas_geral": ["n", "p10", "p50", "p90"],
        "colunas_edicoes": ["p10", "p50", "p90", "modelo"],
        "geral": geral,
        "edicoes": {area: dict(sorted(anos.items())) for area, anos in sorted(edicoes.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--microdados-dir", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--app", type=Path)
    parser.add_argument("--anos", type=int, nargs="*", default=list(range(2009, 2026)))
    parser.add_argument("--processos", type=int, default=1)
    args = parser.parse_args()
    cache = args.saida.with_suffix(".npz")
    if args.microdados_dir is None:
        if not args.app:
            parser.error("sem --microdados-dir, informe --app")
        saida = json.loads(args.saida.read_text(encoding="utf-8"))
        with np.load(cache) as dados:
            _gravar_app(args.app, saida, dict(dados))
        return 0
    provas, primeira = {}, {}
    soma = defaultdict(lambda: np.zeros((46, LARGURA), dtype=np.int64))
    soma_edicoes = defaultdict(lambda: np.zeros((46, LARGURA)))
    edicoes = defaultdict(lambda: np.zeros(46, dtype=int))
    with ProcessPoolExecutor(max_workers=args.processos) as executor:
        tarefas = [(args.microdados_dir, a) for a in args.anos]
        for ano, (resultado, brutos) in zip(args.anos, executor.map(_levantar, tarefas)):
            provas.update(resultado)
            for chave, hist in brutos.items():
                if chave[0] == TIPO_APP:
                    primeira[f"{ano},{chave[1]}"] = hist
                n = hist.sum(axis=1)
                suficiente = n >= MINIMO_PARTICIPANTES
                soma[chave] += hist
                soma_edicoes[chave][suficiente] += hist[suficiente] / n[suficiente, None]
                edicoes[chave] += suficiente
            print(ano, flush=True)
    geral, geral_por_edicao = defaultdict(dict), defaultdict(dict)
    for (tipo, area), hist in sorted(soma.items()):
        n = hist.sum(axis=1)
        geral[tipo][area] = {str(k): [int(n[k]), *_percentis(hist[k])]
                             for k in np.flatnonzero(n >= MINIMO_PARTICIPANTES)}
        contagem = edicoes[(tipo, area)]
        geral_por_edicao[tipo][area] = {
            str(k): [int(contagem[k]), *_percentis(soma_edicoes[(tipo, area)][k])]
            for k in np.flatnonzero(contagem)
        }
    saida = {
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "minimo_participantes": MINIMO_PARTICIPANTES,
        "colunas": COLUNAS,
        "colunas_geral": COLUNAS_GERAL,
        "colunas_geral_por_edicao": COLUNAS_GERAL_POR_EDICAO,
        "geral": geral,
        "geral_por_edicao": geral_por_edicao,
        "provas": dict(sorted(provas.items())),
    }
    args.saida.write_text(json.dumps(saida, separators=(",", ":")) + "\n", encoding="utf-8")
    np.savez_compressed(cache, **primeira)
    if args.app:
        _gravar_app(args.app, saida, primeira)
    return 0


def _gravar_app(caminho: Path, saida: dict, histogramas: dict) -> None:
    caminho.write_text(json.dumps(recorte_app(saida, histogramas), separators=(",", ":")) + "\n",
                       encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
