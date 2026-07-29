# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Propriedades críticas da calibração e da amostragem v3."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

import _utils

_utils.add_src_to_path()
sys.path.insert(0, str(_utils.ROOT))

from tri_enem.calibracao_modelos import (  # noqa: E402
    ajustar_monotonica,
    aplicar_modelo,
    classificar_validacao,
    faixa_nota,
    reajustar_modelo,
)
from tools.recalibrar_validacao import (  # noqa: E402
    AmostraEstratificada,
    Caso,
    dividir_amostra,
    gerar_relatorio,
)


def _caso(indice: int, nota: float | None = None, rank: int | None = None) -> Caso:
    nota = float(nota if nota is not None else 401 + indice)
    return Caso(
        ano=2023,
        area="MT",
        co_prova=1211,
        tp_lingua=None,
        nota_oficial=nota,
        respostas="A" * 45,
        faixa=faixa_nota(nota),
        case_id=f"caso-{indice:04d}",
        rank=indice if rank is None else rank,
    )


def test_transformacao_e_extrapolacao_sao_monotonicas():
    theta = np.linspace(-3, 3, 200)
    nota = 500 + 100 * theta + 12 * np.sin(theta * 2)
    modelo = ajustar_monotonica(theta, nota, 17)
    grade = np.linspace(-6, 6, 1000)
    calculadas = aplicar_modelo(grade, modelo)
    assert np.all(np.diff(calculadas) >= -1e-12)


def test_reajuste_preserva_extremos_exclusivos_da_calibracao():
    theta_cal = np.linspace(-2, 2, 100)
    modelo = ajustar_monotonica(theta_cal, 500 + 100 * theta_cal, 9)
    combinado = np.concatenate([theta_cal, [-4, 4]])
    reajustado = reajustar_modelo(
        modelo, combinado, 500 + 100 * combinado
    )
    assert reajustado["theta_knots"][0] == pytest.approx(-2)
    assert reajustado["theta_knots"][-1] == pytest.approx(2)


def test_notas_acima_de_mil_tem_faixa_e_nao_sao_cortadas():
    modelo = {
        "tipo": "monotonica_linear",
        "theta_knots": [-2.0, 2.0],
        "score_knots": [300.0, 1000.0],
    }
    assert aplicar_modelo([3.0], modelo)[0] > 1000
    assert faixa_nota(1000.01) == "acima_1000"


def test_splits_nao_sobrepoem_e_reservam_extremos_no_holdout():
    amostra = AmostraEstratificada(cap=160)
    for indice in range(160):
        amostra.registrar_contagem(("2023,MT,1211", None, "500_600"), 1)
        amostra.adicionar(_caso(indice, nota=501 + indice / 2))
    split = dividir_amostra(amostra)["2023,MT,1211"]
    ids = {papel: {caso.case_id for caso in casos} for papel, casos in split.items()}
    assert len(ids["treino"]) == 100
    assert len(ids["selecao"]) == 30
    assert len(ids["holdout"]) == 30
    assert ids["treino"].isdisjoint(ids["selecao"])
    assert ids["treino"].isdisjoint(ids["holdout"])
    assert ids["selecao"].isdisjoint(ids["holdout"])
    notas_holdout = {caso.nota_oficial for caso in split["holdout"]}
    assert 501.0 in notas_holdout
    assert 580.5 in notas_holdout


def test_extremo_repetido_reserva_ocorrencias_em_treino_e_holdout():
    amostra = AmostraEstratificada(cap=20)
    casos = [_caso(i, nota=500 + i) for i in range(18)]
    casos.extend([
        _caso(100, nota=499, rank=100),
        _caso(101, nota=499, rank=101),
    ])
    for caso in casos:
        amostra.registrar_contagem(caso.estrato, 1)
        amostra.adicionar(caso)
    split = dividir_amostra(amostra)["2023,MT,1211"]
    assert any(caso.nota_oficial == 499 for caso in split["holdout"])
    assert any(caso.nota_oficial == 499 for caso in split["treino"])


def test_discrepancia_de_2_01_nunca_recebe_ok():
    metricas = {
        "n": 30,
        "erro_maximo": 2.01,
        "faixas_cobertas": ["500_600", "600_700"],
    }
    status, _ = classificar_validacao(metricas, ["500_600", "600_700"])
    assert status == "aviso_leve"


def test_relatorio_combina_resumo_humano_e_metricas_por_prova():
    catalogo = json.loads(
        Path(
            _utils.SRC_DIR / "tri_enem" / "coeficientes_data.json"
        ).read_text(encoding="utf-8")
    )
    manifesto = json.loads(
        Path(
            _utils.ROOT / "tests" / "fixtures" / "validation_manifest.json"
        ).read_text(encoding="utf-8")
    )
    relatorio = gerar_relatorio(catalogo, manifesto)
    assert "## Como interpretar este relatório" in relatorio
    assert "## Estatísticas por ano" in relatorio
    assert "## Estatísticas por área" in relatorio
    assert "## Listas de provas por status" in relatorio
    assert "## Detalhamento por prova" in relatorio
    assert "ENEM 2020 · Linguagens · Prova digital · Branca" in relatorio
    assert "| Status | Perfil | Motivo | Modelo | n | MAE | p95 |" in relatorio
