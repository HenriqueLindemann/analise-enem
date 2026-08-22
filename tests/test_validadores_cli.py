# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Códigos de saída dos validadores de artefatos publicados."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "src" / "tri_enem" / "coeficientes_data.json"
MANIFESTO = ROOT / "tests" / "fixtures" / "validation_manifest.json"
RELATORIO = ROOT / "docs" / "VALIDATION_REPORT.md"


def test_validador_reprova_catalogo_ok_com_erro_2_01(tmp_path):
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    if catalogo.get("schema_version") != 3:
        pytest.skip("catálogo v3 ainda não foi gerado")
    chave = next(
        (
            chave
            for chave, info in catalogo["por_prova"].items()
            if (info.get("qualidade") or {}).get("status") == "ok"
        ),
        None,
    )
    assert chave is not None, "catálogo v3 sem nenhuma prova ok"
    catalogo["por_prova"][chave]["validacao"]["erro_maximo"] = 2.01
    adulterado = tmp_path / "coeficientes_data.json"
    adulterado.write_text(
        json.dumps(catalogo, ensure_ascii=False), encoding="utf-8"
    )
    resultado = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests" / "validar_holdout.py"),
            "--catalogo",
            str(adulterado),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert resultado.returncode != 0
    assert "ok com erro máximo >2" in resultado.stdout


def test_validador_reprova_relatorio_derivado_adulterado(tmp_path):
    from validar_holdout import validar_relatorio_derivado

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    adulterado = tmp_path / "VALIDATION_REPORT.md"
    adulterado.write_text(
        RELATORIO.read_text(encoding="utf-8") + "\nconteúdo obsoleto\n",
        encoding="utf-8",
    )

    falha = validar_relatorio_derivado(catalogo, MANIFESTO, adulterado)

    assert falha == "relatório derivado desatualizado"


def test_validar_respostas_meu_simulado():
    import meu_simulado

    v = meu_simulado.validar_respostas

    # Entradas vazias continuam válidas (a área é simplesmente ignorada).
    assert v(None, "Linguagens", "LC") is True
    assert v("", "Matemática", "MT") is True
    assert v("." * 45, "Ciências Humanas", "CH") is True

    # 45 posições: letras (maiúsculas ou minúsculas), '.' e '*'.
    assert v("ABCDE" * 9, "Linguagens", "LC") is True
    assert v("abcde" * 9, "Matemática", "MT") is True
    assert v("ABCD*" * 9, "Ciências da Natureza", "CN") is True

    # LC aceita a linha de 50 posições dos microdados, com padding '9'.
    assert v("AAAAA" + "99999" + "B" * 40, "Linguagens", "LC") is True
    # Fora da LC, 50 posições são rejeitadas.
    assert v("A" * 50, "Matemática", "MT") is False

    # Comprimentos errados em qualquer área.
    assert v("ABCDE", "Linguagens", "LC") is False
    assert v("A" * 44, "Matemática", "MT") is False
    assert v("A" * 49, "Linguagens", "LC") is False

    # Caracteres inválidos; '9' só é aceito na LC de 50 posições.
    assert v("XYZ" * 15, "Matemática", "MT") is False
    assert v("A" * 44 + "9", "Linguagens", "LC") is False


def test_validar_todas_respostas_streamlit():
    pytest.importorskip("streamlit")
    from streamlit_app.components.inputs import validar_todas_respostas

    respostas_validas = {
        "LC": "ABCDE" * 9,
        "CH": "ABCD*" * 9,
        "CN": "." * 45,
        "MT": "",
    }
    valido, erros = validar_todas_respostas(respostas_validas)
    assert valido is True
    assert erros == []

    respostas_invalidas = {
        "LC": "ABCDE",  # tamanho incorreto
        "CH": "ABCDE12345" + "A" * 35,  # caracteres inválidos
    }
    valido, erros = validar_todas_respostas(respostas_invalidas)
    assert valido is False
    assert len(erros) == 2
