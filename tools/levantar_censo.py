#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Compara a nota do motor com a oficial de todos os participantes válidos.

Por prova (idiomas somados): participantes, diferença média, quantos ficaram a
mais de 2 pontos da nota oficial e a maior diferença. Registros inconsistentes ficam fora.

    python tools/levantar_censo.py --microdados-dir DIR --saida censo.json --processos 3

Cada processo trata um ano inteiro (cerca de 1 GB de RAM).
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

from tri_enem import CalculadorTRI  # noqa: E402
from tools.avaliar_catalogo import REGISTROS_INCONSISTENTES, chave_registro  # noqa: E402
from tools.recalibrar_validacao import MODELO, _linhas_validas, localizar_microdados  # noqa: E402

AREAS = ("CN", "CH", "LC", "MT")


def _inconsistentes() -> set:
    registros = json.loads(REGISTROS_INCONSISTENTES.read_text(encoding="utf-8"))
    return {chave_registro(r) for r in registros}


def levantar_ano(caminho: Path, ano: int, calc: CalculadorTRI, inconsistentes: set) -> dict:
    cabecalho = pd.read_csv(caminho, sep=";", nrows=0, encoding="latin1").columns
    colunas = [c for c in cabecalho if c == "TP_LINGUA" or any(
        c == f"{p}_{a}" for a in AREAS
        for p in ("TP_PRESENCA", "CO_PROVA", "NU_NOTA", "TX_RESPOSTAS"))]
    acumulado = defaultdict(lambda: {"n": 0, "soma": 0.0, "acima_2": 0, "maior_diferenca": 0.0})
    for bloco in pd.read_csv(caminho, sep=";", usecols=colunas, encoding="latin1",
                             dtype=str, chunksize=500_000):
        for area in AREAS:
            linhas = _linhas_validas(bloco, ano, area, None)
            for (prova, lingua), grupo in linhas.groupby(["prova", linhas["lingua"].fillna(-1)]):
                lingua = None if area != "LC" or ano == 2009 else int(lingua)
                try:
                    notas = calc.calcular_notas_batch(ano, area, int(prova), grupo["respostas"], lingua)
                except (ValueError, FileNotFoundError):
                    continue
                oficiais = grupo["nota"].to_numpy(dtype=float)
                erros = np.abs(notas - oficiais)
                excluir = np.asarray([
                    (ano, area, int(prova), o, r.upper()) in inconsistentes
                    for o, r in zip(oficiais, grupo["respostas"])
                ], dtype=bool)
                erros = erros[~excluir]
                if not erros.size:
                    continue
                r = acumulado[f"{ano},{area},{int(prova)}"]
                r["n"] += int(erros.size)
                r["soma"] += float(erros.sum())
                r["acima_2"] += int((erros > 2.0 + 1e-12).sum())
                r["maior_diferenca"] = max(r["maior_diferenca"], round(float(erros.max()), 2))
    return {k: {"n": r["n"], "mae": r["soma"] / r["n"], "acima_2": r["acima_2"],
                "maior_diferenca": r["maior_diferenca"]} for k, r in acumulado.items()}


def _levantar(args: tuple) -> tuple:
    microdados_dir, ano = args
    resultado = levantar_ano(localizar_microdados(microdados_dir, ano), ano, CalculadorTRI(), _inconsistentes())
    return ano, resultado


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--microdados-dir", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--anos", type=int, nargs="*", default=list(range(2009, 2026)))
    parser.add_argument("--processos", type=int, default=1)
    args = parser.parse_args()
    por_prova = {}
    tarefas = [(args.microdados_dir, ano) for ano in args.anos]
    with ProcessPoolExecutor(max_workers=args.processos) as executor:
        for ano, resultado in executor.map(_levantar, tarefas):
            por_prova.update(resultado)
            print(ano, flush=True)
    saida = {
        "modelo": MODELO,
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "por_prova": dict(sorted(por_prova.items())),
    }
    args.saida.write_text(json.dumps(saida, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
