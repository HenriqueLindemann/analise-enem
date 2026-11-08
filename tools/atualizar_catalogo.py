#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Aplica o modelo atual ao catálogo e às fixtures, sem reamostrar.

- ``--cache-dir``: reajusta a escala por área no treino.
- ``--notas-gabarito``: substitui as notas de gabarito pelas levantadas com
  ``levantar_notas_gabarito.py``.
- ``--censo``: grava por prova as contagens de ``levantar_censo.py``.

Recalcula as métricas de cada amostra e o ``teste`` (holdout e confirmações
somados), que define o status; atualiza manifestos e
``docs/VALIDATION_REPORT.md``. Registros inconsistentes ficam fora das métricas.

    python tools/atualizar_catalogo.py --cache-dir resultados/investigacao \\
        --notas-gabarito notas.json --censo censo.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tri_enem.calibracao_modelos import classificar_validacao  # noqa: E402
from tools.recalibrar_validacao import MODELO, SCHEMA_VERSION, gerar_relatorio  # noqa: E402
from tools.avaliar_catalogo import (  # noqa: E402
    FIXTURES, ajustar_escala, avaliar, calculador, carregar_inconsistentes, ler_fixture,
    metricas_ponderadas, notas_casos, pesos_estrato, reconstrucao_efetiva, sha256,
    verificar_inconsistentes,
)

CATALOGO = ROOT / "src" / "tri_enem" / "coeficientes_data.json"
RELATORIO = ROOT / "docs" / "VALIDATION_REPORT.md"
CAMPOS_OBSOLETOS = ("slope", "intercept", "transformacao", "calibracao")
CAMPOS_REMOVIDOS = ("diagnostico_calibracao", "desempenho_tipico")


def migrar(catalogo: Dict[str, Any]) -> None:
    """Schema 4: escala única por área e grade fixa; sem modelo por prova."""
    catalogo["schema_version"] = SCHEMA_VERSION
    catalogo.pop("por_area", None)
    metadata = catalogo.setdefault("metadata", {})
    for area in ("CN", "CH", "LC", "MT"):
        metadata.pop(area, None)
    metadata.pop("objetivo_selecao", None)
    metadata["versao"] = "4.0"
    metadata["modelo"] = MODELO
    metadata["quadratura"] = {"tipo": "grade", "pontos": 40, "limite": 4.0}
    for info in catalogo["por_prova"].values():
        for campo in CAMPOS_OBSOLETOS:
            info.pop(campo, None)
        reconstrucao = reconstrucao_efetiva(info.pop("reconstrucao_itens", None))
        if reconstrucao:
            info["reconstrucao_itens"] = reconstrucao
        (info.get("qualidade") or {}).pop("fallback", None)


def _treino(cache_dir: Path) -> List[Dict[str, Any]]:
    import pandas as pd
    from tools.recalibrar_validacao import dividir_amostra

    casos = []
    for ano in range(2009, 2026):
        amostra = pd.read_pickle(cache_dir / f"amostra_{ano}.pkl")[0]
        for partes in dividir_amostra(amostra).values():
            casos.extend(c.publico("treino") for c in partes["treino"])
    return casos


def _chave(caso) -> str:
    return f"{caso['ano']},{caso['area']},{caso['co_prova']}"


def aplicar_metricas(catalogo, amostras, inconsistentes, manifesto_media, timestamp) -> Dict[str, Any]:
    """Métricas por amostra (auditoria) e ``teste``, a soma delas, que define o status."""
    independentes = {k for k, v in manifesto_media["por_prova"].items() if v["independente"]}
    amostras = {**amostras, "media": [c for c in amostras["media"] if _chave(c) in independentes]}
    resultados = {nome: avaliar(catalogo, casos, inconsistentes) for nome, casos in amostras.items()}
    vistos, teste = set(), []
    for casos in amostras.values():
        for caso in casos:
            if caso["case_id"] in vistos:
                raise ValueError(f"{caso['case_id']}: caso repetido entre amostras de teste")
            vistos.add(caso["case_id"])
            teste.append(caso)
    resultados["teste"] = avaliar(catalogo, teste, inconsistentes)
    campos = {
        "holdout": ("validacao", None),
        "confirmacao": ("validacao_confirmacao", None),
        "residual": ("validacao_residual", "confirmacao_residual"),
        "media": ("validacao_media", "confirmacao_erro_medio"),
        "teste": ("teste", None),
    }
    for info in catalogo["por_prova"].values():
        faixas = (info.get("validacao") or {}).get("faixas_existentes") or []
        for campo, _ in campos.values():
            info.pop(campo, None)
        for campo in CAMPOS_REMOVIDOS:
            info.pop(campo, None)
        info["_faixas_existentes"] = faixas
    for nome, (campo, origem) in campos.items():
        for chave, m in resultados[nome]["por_prova"].items():
            catalogo["por_prova"][chave][campo] = {**m, **({"origem": origem} if origem else {})}
    for info in catalogo["por_prova"].values():
        faixas = info.pop("_faixas_existentes")
        for campo, _ in campos.values():
            if campo in info:
                info[campo]["faixas_existentes"] = faixas
        if info["qualidade"]["status"] in ("sem_itens", "sem_participantes"):
            info["qualidade"]["validado_em"] = timestamp
            continue
        status, motivo = classificar_validacao(info.get("teste"), faixas, info.get("censo"))
        info["qualidade"] = {"status": status, "motivo": motivo, "validado_em": timestamp}
    return resultados


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--notas-gabarito", type=Path)
    parser.add_argument("--censo", type=Path)
    parser.add_argument("--nao-publicar", action="store_true")
    args = parser.parse_args()

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    migrar(catalogo)
    if args.notas_gabarito:
        notas = json.loads(args.notas_gabarito.read_text(encoding="utf-8"))
        for chave, info in catalogo["por_prova"].items():
            info.pop("nota_gabarito", None)
            if chave in notas:
                info["nota_gabarito"] = notas[chave]
    if args.censo:
        censo = json.loads(args.censo.read_text(encoding="utf-8"))
        if censo.get("modelo") != MODELO:
            parser.error(f"censo gerado com {censo.get('modelo')!r}, esperado {MODELO!r}")
        for chave, info in catalogo["por_prova"].items():
            info.pop("censo", None)
            if chave in censo["por_prova"]:
                info["censo"] = censo["por_prova"][chave]
        catalogo["metadata"]["censo_gerado_em"] = censo["gerado_em"]
    inconsistentes = carregar_inconsistentes()
    nomes = {
        "holdout": "validation_holdout", "confirmacao": "reconstruction_confirmation",
        "residual": "residual_confirmation", "media": "mean_error_confirmation",
    }
    amostras = {k: ler_fixture(FIXTURES / f"{v}.jsonl.gz") for k, v in nomes.items()}
    if args.cache_dir:
        escala = ajustar_escala(calculador(catalogo), _treino(args.cache_dir), inconsistentes)
        catalogo["metadata"]["escala"] = escala
        print("escala:", json.dumps(escala), flush=True)
    elif "escala" not in catalogo["metadata"]:
        parser.error("--cache-dir é necessário para ajustar a escala")
    falhas = verificar_inconsistentes(
        catalogo, [c for casos in amostras.values() for c in casos], inconsistentes)
    if falhas:
        print("\n".join(falhas))
        return 1

    manifesto_media_path = FIXTURES / "mean_error_confirmation_manifest.json"
    manifesto_media = json.loads(manifesto_media_path.read_text())
    resultados = aplicar_metricas(catalogo, amostras, inconsistentes, manifesto_media, timestamp)
    catalogo["metadata"]["ultima_calibracao"] = timestamp
    for nome, r in resultados.items():
        print(f"{nome}: {json.dumps(r['total'])} excluídos={len(r['excluidos'])}")
    if args.nao_publicar:
        return 0

    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    hash_catalogo = sha256(CATALOGO)

    primario_path = FIXTURES / "validation_manifest.json"
    primario = json.loads(primario_path.read_text())
    status = defaultdict(int)
    for info in catalogo["por_prova"].values():
        status[info["qualidade"]["status"]] += 1
    primario["coverage"]["status"] = dict(sorted(status.items()))
    primario["generated_at"] = timestamp
    primario["model"] = {
        "name": MODELO, "scale": catalogo["metadata"]["escala"],
        "quadrature": catalogo["metadata"]["quadratura"],
        "inconsistent_records_sha256": sha256(FIXTURES / "registros_inconsistentes.json"),
        "excluded_from_holdout": resultados["holdout"]["excluidos"],
    }
    primario_path.write_text(json.dumps(primario, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    hash_primario = sha256(primario_path)

    def atualizar(nome, resultado, **hashes):
        path = FIXTURES / f"{nome}_manifest.json"
        manifesto = json.loads(path.read_text())
        manifesto["after"] = {k: resultado[k] for k in ("total", "por_prova", "case_ids_sha256")}
        manifesto["after"]["excluded_inconsistent"] = resultado["excluidos"]
        manifesto["after"]["model"] = MODELO
        manifesto.update(hashes)
        path.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        return manifesto

    atualizar("reconstruction_confirmation", resultados["confirmacao"],
              catalogo_sha256=hash_catalogo, source_manifest_sha256=hash_primario)
    atualizar("residual_confirmation", resultados["residual"],
              current_catalogo_sha256=hash_catalogo, primary_manifest_sha256=hash_primario)
    media = json.loads(manifesto_media_path.read_text())
    contagens = {(k, li, b): n for k, li, b, n in media["counts"]}
    por_prova_media = avaliar(catalogo, amostras["media"], inconsistentes)["por_prova"]
    calc = calculador(catalogo)
    grupos = defaultdict(list)
    for caso in amostras["media"]:
        if caso["case_id"] not in inconsistentes:
            grupos[_chave(caso)].append(caso)
    for chave, casos in grupos.items():
        erros = notas_casos(calc, casos) - np.asarray([c["nota_oficial"] for c in casos])
        media["por_prova"][chave]["after"] = por_prova_media[chave]
        media["por_prova"][chave]["after_weighted"] = metricas_ponderadas(
            erros, pesos_estrato(casos, contagens))
        media["por_prova"][chave].pop("mean_improvement_ci95", None)
    media.update(catalogo_sha256=hash_catalogo, primary_manifest_sha256=hash_primario, after_model=MODELO)
    manifesto_media_path.write_text(json.dumps(media, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    RELATORIO.write_text(gerar_relatorio(catalogo, primario), encoding="utf-8")
    print("catálogo, manifestos e relatório publicados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
