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
