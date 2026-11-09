# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Formatação compartilhada pelas interfaces de apresentação."""


def formatar_numero(valor: float, casas: int = 1, sinal: bool = False) -> str:
    """Formata um número decimal em português sem alterar seu valor interno."""

    prefixo = "+" if sinal else ""
    return format(float(valor), f"{prefixo}.{casas}f").replace(".", ",")
