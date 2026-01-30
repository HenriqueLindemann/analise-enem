#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitarios para o modulo _utils.

Execute com: python -m pytest tests/test_utils.py -v
"""

import json
import tempfile
from pathlib import Path

import pytest

import _utils


class TestLinguaPorTp:
    """Testes para a funcao lingua_por_tp."""

    def test_none_retorna_ingles(self):
        assert _utils.lingua_por_tp(None) == "ingles"

    def test_zero_retorna_ingles(self):
        assert _utils.lingua_por_tp(0) == "ingles"
        assert _utils.lingua_por_tp("0") == "ingles"
        assert _utils.lingua_por_tp(" 0 ") == "ingles"

    def test_um_retorna_espanhol(self):
        assert _utils.lingua_por_tp(1) == "espanhol"
        assert _utils.lingua_por_tp("1") == "espanhol"
        assert _utils.lingua_por_tp(" 1 ") == "espanhol"

    def test_outros_valores_retornam_espanhol(self):
        """Qualquer valor diferente de 0 deve retornar espanhol."""
        assert _utils.lingua_por_tp(2) == "espanhol"
        assert _utils.lingua_por_tp("abc") == "espanhol"


class TestToFloat:
    """Testes para a funcao to_float."""

    def test_ponto_decimal(self):
        assert _utils.to_float("123.45") == 123.45

    def test_virgula_decimal(self):
        assert _utils.to_float("123,45") == 123.45

    def test_numero_inteiro(self):
        assert _utils.to_float("500") == 500.0
        assert _utils.to_float(500) == 500.0

    def test_float_nativo(self):
        assert _utils.to_float(123.45) == 123.45


class TestAddSrcToPath:
    """Testes para a funcao add_src_to_path."""

    def test_src_adicionado_ao_path(self):
        import sys
        _utils.add_src_to_path()
        assert str(_utils.SRC_DIR) in sys.path

    def test_idempotente(self):
        """Chamar multiplas vezes nao adiciona duplicatas."""
        import sys
        initial_count = sys.path.count(str(_utils.SRC_DIR))
        _utils.add_src_to_path()
        _utils.add_src_to_path()
        _utils.add_src_to_path()
        assert sys.path.count(str(_utils.SRC_DIR)) == max(1, initial_count)


class TestCarregarCodigosPresentes:
    """Testes para a funcao carregar_codigos_presentes."""

    def test_formato_codigo(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"agrupar_por": "codigo", "codigos": [100, 200, 300]}, f)
            f.flush()
            path = Path(f.name)

        try:
            result = _utils.carregar_codigos_presentes(path, "codigo")
            assert result == {"100", "200", "300"}
        finally:
            path.unlink()

    def test_formato_ano_area_codigo(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({
                "agrupar_por": "ano-area-codigo",
                "chaves": [[2021, "MT", "912"], [2021, "CN", "913"]]
            }, f)
            f.flush()
            path = Path(f.name)

        try:
            result = _utils.carregar_codigos_presentes(path, "ano-area-codigo")
            assert (2021, "MT", "912") in result
            assert (2021, "CN", "913") in result
        finally:
            path.unlink()

    def test_erro_formato_incompativel(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"agrupar_por": "codigo", "codigos": [100]}, f)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="esperado 'ano-area-codigo'"):
                _utils.carregar_codigos_presentes(path, "ano-area-codigo")
        finally:
            path.unlink()


class TestInfoMapeamento:
    """Testes para a funcao info_mapeamento."""

    def test_codigo_encontrado(self):
        mapeamento = {
            912: {
                "ano": 2021,
                "area": "CN",
                "tipo_aplicacao": "1a_aplicacao",
                "cor": "rosa",
                "eh_especial": False,
            }
        }
        result = _utils.info_mapeamento(mapeamento, 912)
        assert result["tipo_aplicacao"] == "1a_aplicacao"
        assert result["cor"] == "rosa"
        assert result["mapeado_ano"] == 2021
        assert result["mapeado_area"] == "CN"

    def test_codigo_nao_encontrado(self):
        mapeamento = {}
        result = _utils.info_mapeamento(mapeamento, 999)
        assert result["tipo_aplicacao"] == "nao_mapeado"
        assert result["cor"] == "nao_mapeado"
        assert result["mapeado_ano"] is None


class TestExports:
    """Testes para verificar que __all__ exporta corretamente."""

    def test_all_exports_existem(self):
        for name in _utils.__all__:
            assert hasattr(_utils, name), f"{name} em __all__ mas nao existe no modulo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
