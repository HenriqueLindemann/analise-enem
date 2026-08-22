# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Utilitários de formatação para o relatório PDF."""

from __future__ import annotations

import math


_LINGUAS_APRESENTACAO = {
    "ingles": "Inglês",
    "inglês": "Inglês",
    "english": "Inglês",
    "espanhol": "Espanhol",
    "spanish": "Espanhol",
}


def formatar_lingua(lingua: str | None) -> str:
    """Converte o identificador interno de LC em texto para apresentação."""
    if lingua is None:
        return ""
    texto = str(lingua).strip()
    if not texto:
        return ""
    return _LINGUAS_APRESENTACAO.get(texto.casefold(), texto.capitalize())


def formatar_dificuldade(param_b: float | None) -> str:
    """Formata o parâmetro b de dificuldade."""
    if param_b is None or math.isnan(param_b):
        return "–"
    elif param_b < -1:
        return f"{param_b:+.1f} (muito fácil)"
    elif param_b < 0:
        return f"{param_b:+.1f} (fácil)"
    elif param_b < 1:
        return f"{param_b:+.1f} (média)"
    elif param_b < 2:
        return f"{param_b:+.1f} (difícil)"
    else:
        return f"{param_b:+.1f} (muito difícil)"
