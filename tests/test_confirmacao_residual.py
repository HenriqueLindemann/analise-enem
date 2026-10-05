# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Adulterações que a validação do modelo atual deve detectar."""
import gzip
import json
from pathlib import Path
import shutil

import pytest

from validar_confirmacao_residual import assinatura, ler_fixture, sha256, validar

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def artifacts(tmp_path):
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    for name in ("validation_manifest.json", "validation_holdout.jsonl.gz",
                 "reconstruction_confirmation.jsonl.gz", "residual_confirmation.jsonl.gz",
                 "residual_confirmation_manifest.json"):
        shutil.copyfile(ROOT / "tests/fixtures" / name, fixtures / name)
    catalogo = tmp_path / "catalogo.json"
    shutil.copyfile(ROOT / "src/tri_enem/coeficientes_data.json", catalogo)
    return catalogo, fixtures


def modificar_manifest(fixtures, change):
    path = fixtures / "residual_confirmation_manifest.json"
    manifest = json.loads(path.read_text())
    change(manifest)
    path.write_text(json.dumps(manifest))


def test_confirmacao_valida_somente_modelos_atuais(artifacts):
    catalogo, fixtures = artifacts
    manifest = json.loads((fixtures / "residual_confirmation_manifest.json").read_text())
    assert "before_models" not in manifest
    assert validar(catalogo, fixtures) == []


def test_detecta_metricas_adulteradas(artifacts):
    catalogo, fixtures = artifacts
    modificar_manifest(fixtures, lambda m: m["after"]["total"].update(mae=0.))
    assert any("after.total.mae" in f for f in validar(catalogo, fixtures))


def test_detecta_modelo_alterado_mesmo_com_hash_atualizado(artifacts):
    catalogo, fixtures = artifacts
    data = json.loads(catalogo.read_text())
    data["por_prova"]["2009,CH,72"]["transformacao"]["intercept"] += 1
    catalogo.write_text(json.dumps(data))
    modificar_manifest(fixtures, lambda m: m.update(current_catalogo_sha256=sha256(catalogo)))
    assert any("modelo publicado diverge" in f for f in validar(catalogo, fixtures))


def test_detecta_sobreposicao_mesmo_com_hashes_atualizados(artifacts):
    catalogo, fixtures = artifacts
    rows = ler_fixture(fixtures / "residual_confirmation.jsonl.gz")
    rows[0]["case_id"] = ler_fixture(fixtures / "validation_holdout.jsonl.gz")[0]["case_id"]
    path = fixtures / "residual_confirmation.jsonl.gz"
    with gzip.open(path, "wt") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")
    fingerprint = assinatura(r["case_id"] for r in rows)
    def change(manifest):
        manifest.update(fixture_sha256=sha256(path), case_ids_sha256=fingerprint)
        for role in ("before", "after"):
            manifest[role]["case_ids_sha256"] = fingerprint
    modificar_manifest(fixtures, change)
    assert any("sobreposição" in f for f in validar(catalogo, fixtures))


def test_relatorio_identifica_diagnostico_de_treino():
    from tools.recalibrar_validacao import gerar_relatorio
    catalogo = json.loads((ROOT / "src/tri_enem/coeficientes_data.json").read_text())
    manifest = json.loads((ROOT / "tests/fixtures/validation_manifest.json").read_text())
    report = gerar_relatorio(catalogo, manifest)
    assert "diagnóstico de treino/seleção" in report
