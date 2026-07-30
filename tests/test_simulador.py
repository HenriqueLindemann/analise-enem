# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Contrato público de resolução de prova do simulador."""

from __future__ import annotations

import pytest

import _utils

_utils.add_src_to_path()

from tri_enem import SimuladorNota  # noqa: E402


def test_nao_escolhe_primeira_prova_quando_ha_ambiguidade():
    simulador = SimuladorNota()
    with pytest.raises(ValueError, match="Informe co_prova ou cor_prova"):
        simulador.calcular("MT", 2023, "A" * 45)


def test_calculo_por_combinacao_completa_permanece_disponivel():
    simulador = SimuladorNota()
    resultado = simulador.calcular(
        "MT",
        2023,
        "A" * 45,
        cor_prova="azul",
        tipo_aplicacao="1a_aplicacao",
    )
    assert resultado.co_prova == 1211


def test_cor_sem_aplicacao_nao_assume_primeira_aplicacao():
    simulador = SimuladorNota()
    with pytest.raises(ValueError, match="tipo_aplicacao"):
        simulador.calcular("MT", 2023, "A" * 45, cor_prova="azul")
