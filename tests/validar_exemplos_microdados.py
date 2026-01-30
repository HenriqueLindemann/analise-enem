#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida exemplos de microdados usando as abstracoes da biblioteca.

Comparacao simples entre nota oficial (microdados) e nota calculada.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import _utils

_utils.add_src_to_path()

from tri_enem.simulador import SimuladorNota


def validar(exemplos_path: Path, microdados_limpos: Path) -> None:
    exemplos = json.loads(exemplos_path.read_text(encoding="utf-8"))
    sim = SimuladorNota(microdados_path=str(microdados_limpos))

    total = len(exemplos)
    progress_interval = 100
    print(f"Total de exemplos: {total}", flush=True)
    print("ANO | AREA | CO_PROVA | NOTA_OFICIAL | NOTA_CALC | DIF")
    print("-" * 72)

    diffs = []
    alertas = {}
    provas_nao_encontradas = {}

    for i, item in enumerate(exemplos, start=1):
        ano = int(item["ano"])
        area = item["area"]
        co_prova = int(item["co_prova"])
        tp_lingua = item.get("tp_lingua")
        lingua = _utils.lingua_por_tp(tp_lingua)

        nota_oficial = _utils.to_float(item["nota_oficial"])
        respostas = item["respostas"]

        try:
            resultado = sim.calcular(
                area=area,
                ano=ano,
                respostas=respostas,
                lingua=lingua if area == "LC" else "ingles",
                co_prova=co_prova,
            )
        except KeyError as e:
            # Prova nao encontrada nos coeficientes calibrados
            chave = (ano, area, co_prova)
            provas_nao_encontradas[chave] = provas_nao_encontradas.get(chave, 0) + 1
            continue
        except ValueError as e:
            # Erro de dados invalidos (respostas, formato, etc)
            print(f"  [WARN] ValueError {ano}/{area}/{co_prova}: {e}", flush=True)
            chave = (ano, area, co_prova)
            provas_nao_encontradas[chave] = provas_nao_encontradas.get(chave, 0) + 1
            continue

        nota_calc = resultado.nota
        dif = nota_calc - nota_oficial
        diffs.append(abs(dif))
        print(f"{ano} | {area} | {co_prova:>7} | {nota_oficial:>11.1f} | {nota_calc:>9.1f} | {dif:>7.1f}")

        if abs(dif) > _utils.LIMITE_DIF_PADRAO:
            chave = (ano, area, co_prova)
            stats = alertas.get(chave, {"count": 0, "max_abs": 0.0})
            stats["count"] += 1
            stats["max_abs"] = max(stats["max_abs"], abs(dif))
            alertas[chave] = stats

        if i % progress_interval == 0 or i == total:
            print(f"Progresso: {i}/{total}", flush=True)

    if diffs:
        mae = sum(diffs) / len(diffs)
        print("-" * 72)
        print(f"MAE (diferenca media absoluta): {mae:.2f}")

    if alertas:
        print(f"\nPONTOS DE ATENCAO (dif > {_utils.LIMITE_DIF_PADRAO}):")
        for (ano, area, co_prova), stats in sorted(alertas.items()):
            print(f"- {ano} {area} CO_PROVA {co_prova}: {stats['count']} casos, max {stats['max_abs']:.2f}")

    if provas_nao_encontradas:
        print("\nPROVAS NAO ENCONTRADAS NO microdados_limpos:")
        for (ano, area, co_prova), count in sorted(provas_nao_encontradas.items()):
            print(f"- {ano} {area} CO_PROVA {co_prova}: {count} casos")


def main() -> None:
    parser = argparse.ArgumentParser(description="Comparar notas calculadas vs microdados.")
    parser.add_argument("--exemplos", default="tests/fixtures/exemplos_microdados.json", help="Arquivo JSON de exemplos")
    parser.add_argument("--microdados-limpos", default="microdados_limpos", help="Diretorio microdados_limpos")
    args = parser.parse_args()

    exemplos_path = Path(args.exemplos)
    microdados_limpos = Path(args.microdados_limpos)

    if not exemplos_path.exists():
        raise SystemExit(f"Arquivo nao encontrado: {exemplos_path}")
    if not microdados_limpos.exists():
        raise SystemExit(f"Diretorio nao encontrado: {microdados_limpos}")

    validar(exemplos_path, microdados_limpos)


if __name__ == "__main__":
    main()
