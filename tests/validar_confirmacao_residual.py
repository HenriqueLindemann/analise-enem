#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Recalcula offline a confirmação residual dos quatro reparos.

As fixtures verificam a separação do holdout primário e da confirmação
secundária. Use --cache-dir para conferir também a exclusão de todos os casos
locais de desenvolvimento.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from tri_enem.calibracao_modelos import faixa_nota  # noqa: E402
from tools.avaliar_catalogo import (  # noqa: E402
    assinatura, avaliar, carregar_inconsistentes, ler_fixture, reconstrucao_efetiva, sha256,
)


def comparar(actual, expected, label, failures):
    """Compara todos os campos esperados, incluindo faixas e R² por prova."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            failures.append(f"{label}: objeto ausente")
            return
        for key, value in expected.items():
            comparar(actual.get(key), value, f"{label}.{key}", failures)
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if (not isinstance(actual, (int, float)) or isinstance(actual, bool)
                or not np.isclose(actual, expected, rtol=0, atol=1e-6)):
            failures.append(f"{label}: métrica diverge ({actual!r} != {expected!r})")
    elif actual != expected:
        failures.append(f"{label}: valor diverge")


def validar(catalogo_path=None, fixtures_dir=None, cache_dir=None):
    fixtures_dir = fixtures_dir or ROOT / "tests/fixtures"
    catalogo_path = catalogo_path or ROOT / "src/tri_enem/coeficientes_data.json"
    manifest = json.loads((fixtures_dir / "residual_confirmation_manifest.json").read_text())
    primary = json.loads((fixtures_dir / "validation_manifest.json").read_text())
    catalogo_completo = json.loads(catalogo_path.read_text())
    catalogo = catalogo_completo["por_prova"]
    failures = []
    hashes = {catalogo_path: manifest.get("current_catalogo_sha256", manifest["published_catalogo_sha256"]),
              fixtures_dir / "residual_confirmation.jsonl.gz": manifest["fixture_sha256"],
              fixtures_dir / "validation_manifest.json": manifest["primary_manifest_sha256"],
              fixtures_dir / "validation_holdout.jsonl.gz": manifest["primary_fixture_sha256"],
              fixtures_dir / "reconstruction_confirmation.jsonl.gz": manifest["secondary_fixture_sha256"]}
    for path, expected in hashes.items():
        if sha256(path) != expected:
            failures.append(f"hash divergente: {path.name}")
    if (manifest.get("models_refitted") is not False
            or manifest.get("models_published") is not True
            or manifest.get("overlapping_cases") != 0
            or manifest.get("identity_algorithm") != primary["sampling"]["identity_algorithm"]):
        failures.append("estado de confirmação/congelamento inválido")
    if manifest["modelos_sha256"] != primary["residual_repair"]["frozen_models_sha256"]:
        failures.append("hash dos modelos congelados diverge")
    rows = ler_fixture(fixtures_dir / "residual_confirmation.jsonl.gz")
    expected_fields = {"case_id", "ano", "area", "co_prova", "tp_lingua",
                       "nota_oficial", "respostas", "faixa", "split"}
    for row in rows:
        if (set(row) != expected_fields or not np.isfinite(row["nota_oficial"])
                or row["nota_oficial"] <= 0 or row["faixa"] != faixa_nota(row["nota_oficial"])):
            failures.append("campos, nota ou faixa inválidos na fixture residual")
    ids = [r["case_id"] for r in rows]
    if (len(ids) != len(set(ids)) or len(ids) != manifest["cases"]
            or any(r.get("split") != "confirmacao_residual" for r in rows)
            or any(len(i) != 24 or any(c not in "0123456789abcdef" for c in i) for i in ids)):
        failures.append("casos duplicados, identidade, contagem ou split inválido")
    fingerprint = assinatura(ids)
    for expected in (manifest["case_ids_sha256"], manifest["before"]["case_ids_sha256"],
                     manifest["after"]["case_ids_sha256"]):
        if fingerprint != expected:
            failures.append("hash dos casos diverge: comparação pareada inválida")
    ids = set(ids)
    for name in ("validation_holdout", "reconstruction_confirmation"):
        previous = {r["case_id"] for r in ler_fixture(fixtures_dir / f"{name}.jsonl.gz")}
        if ids & previous:
            failures.append(f"sobreposição com {name}")
    keys = {f"{r['ano']},{r['area']},{r['co_prova']}" for r in rows}
    if (keys != set(manifest["published_proofs"]) or keys != set(manifest["frozen_models"])
            or keys != set(manifest["after"]["por_prova"])
            or keys != set(manifest["before"]["por_prova"])
            or keys & set(manifest["sem_casos_novos"])):
        failures.append("cobertura dos modelos/casos diverge")
    for key in sorted(keys):
        # A escala congelada foi substituída pela escala única; os reparos de
        # itens continuam os mesmos.
        frozen = reconstrucao_efetiva(manifest["frozen_models"][key].get("reconstrucao_itens"))
        if catalogo[key].get("reconstrucao_itens") != frozen:
            failures.append(f"{key}: reparo publicado diverge do congelado: reconstrucao_itens")
    # O "before" contém métricas históricas e a identidade da avaliação pareada.
    actual = avaliar(catalogo_completo, rows, carregar_inconsistentes())
    if actual["excluidos"] != manifest["after"].get("excluded_inconsistent"):
        failures.append("registros excluídos divergem do manifesto")
    comparar({k: actual[k] for k in ("total", "por_prova", "case_ids_sha256")},
             {k: manifest["after"][k] for k in ("total", "por_prova", "case_ids_sha256")},
             "after", failures)
    for key, metrics in actual["por_prova"].items():
        comparar(catalogo[key].get("validacao_residual"), metrics,
                 f"{key}.validacao_residual", failures)
        if metrics["n"] != manifest["before"]["por_prova"][key]["n"]:
            failures.append(f"{key}: contagem pareada histórica diverge")
    if actual["total"]["n"] != manifest["before"]["total"]["n"]:
        failures.append("contagem total pareada histórica diverge")
    if cache_dir is not None:
        excluded = set()
        for name, expected in manifest["excluded_caches"].items():
            path = cache_dir / name
            if sha256(path) != expected["cache_sha256"]:
                failures.append(f"hash do cache divergente: {name}")
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                cache = json.load(stream)
            cs = [c for roles in cache["splits"].values() for cases in roles.values() for c in cases]
            cached_ids = [c["case_id"] for c in cs]
            if (len(cached_ids) != expected["cases"] or len(set(cached_ids)) != len(cached_ids)
                    or assinatura(cached_ids) != expected["case_ids_sha256"]):
                failures.append(f"identidades do cache divergentes: {name}")
            excluded.update(cached_ids)
        if len(excluded) != manifest["excluded_cases"] or ids & excluded:
            failures.append("exclusão do desenvolvimento completo diverge")
        frozen_path = cache_dir / "reparos_residuais_congelados.json"
        frozen = json.loads(frozen_path.read_text())
        if (sha256(frozen_path) != manifest["modelos_sha256"]
                or not frozen.get("models_frozen") or frozen.get("holdout_consulted")):
            failures.append("arquivo congelado diverge da confirmação")
        for key in keys:
            original = frozen["por_prova"][key]["proposta"]
            for field, expected in manifest["frozen_models"][key].items():
                if original.get(field) != expected:
                    failures.append(f"{key}: modelo atual diverge do arquivo congelado: {field}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogo", type=Path)
    parser.add_argument("--fixtures-dir", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    args = parser.parse_args()
    try:
        failures = validar(args.catalogo, args.fixtures_dir, args.cache_dir)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        failures = [f"artefatos inválidos: {exc}"]
    if failures:
        print("\n".join(failures))
        return 1
    alcance = "desenvolvimento completo" if args.cache_dir else "fixtures primária/secundária"
    print(f"Confirmação residual: hashes, separação ({alcance}), reparos atuais e métricas conferidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
