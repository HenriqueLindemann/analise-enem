# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Integridade e cobertura dos parâmetros de itens distribuídos no wheel."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path

import _utils

_utils.add_src_to_path()


def _sha256(recurso) -> str:
    digest = hashlib.sha256()
    with recurso.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def test_manifesto_cobre_e_confere_todos_os_anos():
    raiz = files("tri_enem").joinpath("data", "itens")
    manifesto = json.loads(raiz.joinpath("manifest.json").read_text("utf-8"))
    assert manifesto["years"] == list(range(2009, 2026))
    assert len(manifesto["files"]) == 17
    for info in manifesto["files"]:
        recurso = raiz.joinpath(*info["arquivo"].split("/"))
        assert recurso.is_file(), info["arquivo"]
        assert recurso.stat().st_size == info["bytes_normalizado"]
        assert _sha256(recurso) == info["sha256_normalizado"]


def test_fixture_auxiliar_nao_contem_identificadores_pessoais():
    caminho = Path(__file__).parent / "fixtures" / "exemplos_microdados.json"
    exemplos = json.loads(caminho.read_text(encoding="utf-8"))
    proibidos = {"id", "id_col", "nu_inscricao", "nu_sequencial", "identificador"}
    assert exemplos
    assert all(proibidos.isdisjoint({chave.lower() for chave in caso}) for caso in exemplos)
