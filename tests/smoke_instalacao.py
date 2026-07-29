#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Smoke test do wheel instalado, executado fora da raiz do repositório."""

from __future__ import annotations

import math

from tri_enem import CalculadorTRI


def main() -> int:
    calc = CalculadorTRI()
    for ano in range(2009, 2026):
        provas_por_area = calc.listar_provas(ano)
        provas = [
            (area, codigo)
            for area, codigos in provas_por_area.items()
            for codigo in codigos
        ]
        if not provas:
            raise AssertionError(f"wheel sem provas calculáveis para {ano}")
        area, codigo = next(
            (prova for prova in provas if prova[0] != "LC"),
            provas[0],
        )
        lingua = 0 if area == "LC" and ano != 2009 else None
        itens = calc.carregar_itens(ano, area, codigo, lingua)
        respostas = "".join(
            "." if item.abandonado else item.gabarito for item in itens
        )
        resultado = calc.calcular_nota(
            ano, area, codigo, respostas, tp_lingua=lingua
        )
        if not math.isfinite(resultado["nota"]):
            raise AssertionError(f"nota não finita em {ano}/{area}/{codigo}")
    print("Wheel validado fora do repositório para todos os anos (2009–2025).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
