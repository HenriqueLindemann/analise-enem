# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Utilitários para o relatório PDF.

Funções auxiliares: formatação, etc.
A função verificar_precisao_prova foi movida para o pacote principal (tri_enem.precisao).
"""

from typing import Dict

# Re-exportar para compatibilidade com código antigo
from ..precisao import verificar_precisao_prova


def formatar_dificuldade(param_b: float) -> str:
    """Formata o parâmetro b de dificuldade."""
    if param_b < -1:
        return f"{param_b:+.1f} (muito fácil)"
    elif param_b < 0:
        return f"{param_b:+.1f} (fácil)"
    elif param_b < 1:
        return f"{param_b:+.1f} (média)"
    elif param_b < 2:
        return f"{param_b:+.1f} (difícil)"
    else:
        return f"{param_b:+.1f} (muito difícil)"
