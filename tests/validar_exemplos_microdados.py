#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida exemplos auxiliares: compara nota calculada vs nota oficial.

O script é somente leitura. O catálogo e seus status são publicados
atomicamente por ``tools/recalibrar_validacao.py``.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import _utils

_utils.add_src_to_path()

from tri_enem.simulador import SimuladorNota

def validar(
    exemplos_path: Path,
    itens_path: Path | None = None,
) -> bool:
    exemplos: List[dict] = json.loads(exemplos_path.read_text(encoding="utf-8"))
    sim = SimuladorNota(
        itens_path=str(itens_path) if itens_path is not None else None
    )

    total = len(exemplos)
    print(f"Total de exemplos: {total}", flush=True)

    # Acumular erros por prova e globalmente
    diffs_global: List[float] = []
    por_prova: Dict[tuple, List[float]] = defaultdict(list)  # (ano,area,co_prova) -> [|dif|]
    provas_nao_encontradas: Dict[tuple, int] = {}
    casos_invalidos: List[str] = []

    for i, item in enumerate(exemplos, start=1):
        ano      = int(item["ano"])
        area     = item["area"]
        co_prova = int(item["co_prova"])
        tp_lingua = item.get("tp_lingua")
        lingua = (
            _utils.lingua_por_tp(tp_lingua) if area == "LC" else None
        )
        nota_oficial = _utils.to_float(item["nota_oficial"])
        respostas    = item["respostas"]
        if not math.isfinite(nota_oficial) or nota_oficial <= 0:
            casos_invalidos.append(
                f"{ano}/{area}/{co_prova}: nota oficial {nota_oficial!r}"
            )
            continue

        try:
            resultado = sim.calcular(
                area=area,
                ano=ano,
                respostas=respostas,
                lingua=lingua,
                co_prova=co_prova,
            )
        except (KeyError, ValueError) as e:
            chave = (ano, area, co_prova)
            provas_nao_encontradas[chave] = provas_nao_encontradas.get(chave, 0) + 1
            continue

        dif = abs(resultado.nota - nota_oficial)
        diffs_global.append(dif)
        por_prova[(ano, area, co_prova)].append(dif)

        if i % 200 == 0 or i == total:
            print(f"Progresso: {i}/{total}", flush=True)

    # Relatório global
    print("\n" + "=" * 72)
    if diffs_global:
        mae_global = sum(diffs_global) / len(diffs_global)
        max_dif    = max(diffs_global)
        print(f"MAE global          : {mae_global:.2f} pontos")
        print(f"Erro máximo         : {max_dif:.2f} pontos")
        print(f"Exemplos validados  : {len(diffs_global)}")
    print(f"Provas sem dados    : {len(provas_nao_encontradas)}")

    # Relatório por prova
    print("\n--- MAE por CO_PROVA ---")
    print(f"{'ANO':<5} {'AREA':<4} {'PROVA':<6} {'N':>3} {'MAE':>6}")
    print("-" * 40)

    for (ano, area, co_prova), erros in sorted(por_prova.items()):
        mae    = sum(erros) / len(erros)
        print(f"{ano:<5} {area:<4} {co_prova:<6} {len(erros):>3} {mae:>6.2f}")

    if provas_nao_encontradas:
        print("\n--- Provas não encontradas ---")
        for (ano, area, co_prova), count in sorted(provas_nao_encontradas.items()):
            print(f"  {ano} {area} CO_PROVA {co_prova}: {count} caso(s)")

    from tri_enem import verificar_precisao_prova

    faltas_inesperadas = []
    for ano, area, co_prova in provas_nao_encontradas:
        status = verificar_precisao_prova(ano, area, co_prova)["status"]
        if status != "sem_itens":
            faltas_inesperadas.append((ano, area, co_prova))

    violacoes_ok = []
    for (ano, area, co_prova), erros in por_prova.items():
        precisao = verificar_precisao_prova(ano, area, co_prova)
        if precisao["status"] == "ok" and max(erros) > 2.0 + 1e-12:
            violacoes_ok.append((ano, area, co_prova, max(erros)))

    if casos_invalidos:
        print("\n[falha] Casos com nota oficial inválida:")
        for caso in casos_invalidos[:20]:
            print(f"  {caso}")
    if faltas_inesperadas:
        print("\n[falha] Provas puladas sem status sem_itens:")
        for chave in faltas_inesperadas[:20]:
            print(f"  {chave}")
    if violacoes_ok:
        print("\n[falha] Provas ok com erro individual acima de 2 pontos:")
        for caso in violacoes_ok[:20]:
            print(f"  {caso[0]}/{caso[1]}/{caso[2]}: {caso[3]:.2f}")
    return not (casos_invalidos or faltas_inesperadas or violacoes_ok)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Comparar notas calculadas contra exemplos oficiais."
    )
    parser.add_argument(
        "--exemplos",
        default=str(_utils.EXEMPLOS_PATH),
        help="Arquivo JSON de exemplos gerado por gerar_exemplos_microdados.py",
    )
    parser.add_argument(
        "--itens-path",
        type=Path,
        help=(
            "Diretório externo opcional com ITENS_PROVA_<ano>.csv; quando "
            "omitido, usa os itens incluídos no pacote"
        ),
    )
    args = parser.parse_args()

    exemplos_path    = Path(args.exemplos)
    if not exemplos_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {exemplos_path}")
    if args.itens_path is not None and not args.itens_path.is_dir():
        raise SystemExit(
            f"Diretório de itens não encontrado: {args.itens_path}"
        )

    if not validar(exemplos_path, args.itens_path):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
