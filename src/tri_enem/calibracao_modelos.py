# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Faixas de nota, ranking de candidatos e status de precisão."""

from __future__ import annotations

from typing import Any, Dict, Sequence

import numpy as np

LIMITES_FAIXAS = np.asarray(
    [-np.inf, 400, 500, 600, 700, 800, 900, 1000, np.inf],
    dtype=float,
)
ROTULOS_FAIXAS = (
    "ate_400",
    "400_500",
    "500_600",
    "600_700",
    "700_800",
    "800_900",
    "900_1000",
    "acima_1000",
)


def faixa_nota(nota: float) -> str:
    """Classifica nota positiva, incluindo explicitamente valores >1000."""
    indice = int(np.searchsorted(LIMITES_FAIXAS[1:], float(nota), side="left"))
    return ROTULOS_FAIXAS[min(max(indice, 0), len(ROTULOS_FAIXAS) - 1)]


def ranking_erro_medio(metricas, complexidade=2):
    """Objetivo da seleção de reconstruções de itens: erro médio, depois cauda."""
    return (metricas.get("mae_ponderado", metricas["mae"]), complexidade,
            metricas["erro_p95"], metricas["erro_maximo"])


LIMITE_ERRO_RARO_CENSO = 5  # notas acima de 2 pontos; 1 ou 2 são registros corrompidos isolados


def classificar_validacao(
    metricas: Dict[str, Any] | None,
    faixas_existentes: Sequence[str],
    censo: Dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Status pelo censo (todos os participantes) se o teste verificou a prova.

    Sem teste suficiente, a prova segue ``nao_calibrado``; sem censo, vale o maior erro do teste.
    """
    status, motivo = _status_teste(metricas, faixas_existentes)
    if not censo or status == "nao_calibrado":
        return status, motivo
    if censo.get("acima_2", 0) >= LIMITE_ERRO_RARO_CENSO:
        return "erro_raro", "censo_acima_2"
    return "ok", "censo_ate_2"


def _status_teste(metricas, faixas_existentes) -> tuple[str, str]:
    if not metricas or metricas.get("n", 0) < 30:
        return "nao_calibrado", "teste_insuficiente"
    cobertas = set(metricas.get("faixas_cobertas", []))
    existentes = set(faixas_existentes)
    if len(existentes) < 2 or not existentes.issubset(cobertas):
        return "nao_calibrado", "faixas_incompletas"
    erro = float(metricas["erro_maximo"])
    if erro <= 2.0 + 1e-12:
        return "ok", "erro_maximo_ate_2"
    if erro <= 5.0 + 1e-12:
        return "aviso_leve", "erro_maximo_ate_5"
    if erro <= 15.0 + 1e-12:
        return "aviso_forte", "erro_maximo_ate_15"
    return "erro_alto", "erro_maximo_acima_15"
