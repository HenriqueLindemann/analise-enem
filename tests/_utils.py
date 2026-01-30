#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitarios compartilhados para scripts em tests/.

Este modulo centraliza funcoes comuns usadas pelos scripts de teste e validacao.
Importado automaticamente via conftest.py que adiciona tests/ ao sys.path.

Encoding dos dados:
- Microdados ENEM: latin-1 
- Arquivos YAML/JSON: utf-8
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

import yaml

__all__ = [
    "add_src_to_path",
    "lingua_por_tp",
    "to_float",
    "carregar_mapeamento",
    "info_mapeamento",
    "listar_chaves_mapeamento",
    "carregar_codigos_presentes",
    "ROOT",
    "SRC_DIR",
    "LIMITE_DIF_PADRAO",
    "FIXTURES_DIR",
    "MAPEAMENTO_PATH",
    "CACHE_CODIGOS_PATH",
    "EXEMPLOS_PATH",
]

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

# === Configurações centralizadas ===
LIMITE_DIF_PADRAO = 2.0  # Limite de diferença (pontos) para marcar prova como problemática
FIXTURES_DIR = ROOT / "tests" / "fixtures"
MAPEAMENTO_PATH = ROOT / "src" / "tri_enem" / "mapeamento_provas.yaml"
CACHE_CODIGOS_PATH = FIXTURES_DIR / "codigos_presentes.json"
EXEMPLOS_PATH = FIXTURES_DIR / "exemplos_microdados.json"


def add_src_to_path() -> None:
    """Garante que src/ esteja no sys.path para imports do tri_enem."""
    src_str = str(SRC_DIR)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


def lingua_por_tp(tp_lingua: Optional[Any]) -> str:
    """Converte TP_LINGUA dos microdados para nome do idioma.

    Args:
        tp_lingua: Valor de TP_LINGUA (0=ingles, 1=espanhol, None=ingles)

    Returns:
        'ingles' ou 'espanhol'
    """
    if tp_lingua is None:
        return "ingles"
    return "ingles" if str(tp_lingua).strip() == "0" else "espanhol"


def to_float(value: Any) -> float:
    """Converte string para float, tratando virgula como separador decimal.

    Args:
        value: Valor a converter (string ou numerico)

    Returns:
        Valor como float
    """
    return float(str(value).replace(",", "."))


def carregar_mapeamento(path: Path) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, list]]:
    """Carrega mapeamento de provas do arquivo YAML.

    Args:
        path: Caminho para o arquivo mapeamento_provas.yaml

    Returns:
        Tupla (mapeamento, duplicados) onde:
        - mapeamento: dict[co_prova] -> info da prova
        - duplicados: dict[co_prova] -> lista de infos extras (se houver duplicatas)
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mapeamento: Dict[int, Dict[str, Any]] = {}
    duplicados: Dict[int, list] = {}

    for ano_key, dados_ano in data.items():
        if str(ano_key).startswith("_"):
            continue

        try:
            ano = int(ano_key)
        except ValueError:
            continue

        for area, dados_area in dados_ano.items():
            if area not in ["MT", "CN", "CH", "LC"]:
                continue
            if not isinstance(dados_area, dict):
                continue

            for tipo, cores in dados_area.items():
                if not isinstance(cores, dict):
                    continue

                for cor, codigo in cores.items():
                    try:
                        codigo_int = int(codigo)
                    except (TypeError, ValueError):
                        continue

                    info = {
                        "ano": ano,
                        "area": area,
                        "tipo_aplicacao": tipo,
                        "cor": cor,
                        "eh_especial": tipo == "especiais",
                    }

                    if codigo_int in mapeamento:
                        duplicados.setdefault(codigo_int, []).append(info)
                    else:
                        mapeamento[codigo_int] = info

    return mapeamento, duplicados


def info_mapeamento(mapeamento: Dict[int, Dict[str, Any]], co_prova: int) -> Dict[str, Any]:
    """Obtem informacoes de uma prova a partir do mapeamento.

    Args:
        mapeamento: Dict retornado por carregar_mapeamento()
        co_prova: Codigo da prova

    Returns:
        Dict com tipo_aplicacao, cor, eh_especial, mapeado_ano, mapeado_area
    """
    info = mapeamento.get(co_prova)
    if info is None:
        return {
            "tipo_aplicacao": "nao_mapeado",
            "cor": "nao_mapeado",
            "eh_especial": False,
            "mapeado_ano": None,
            "mapeado_area": None,
        }
    return {
        "tipo_aplicacao": info["tipo_aplicacao"],
        "cor": info["cor"],
        "eh_especial": info["eh_especial"],
        "mapeado_ano": info["ano"],
        "mapeado_area": info["area"],
    }


def listar_chaves_mapeamento(path: Path, agrupar_por: str) -> Set[Any]:
    """Lista todas as chaves (codigos de prova) do mapeamento.

    Args:
        path: Caminho para o arquivo YAML
        agrupar_por: 'codigo' ou 'ano-area-codigo'

    Returns:
        Set de codigos (strings) ou tuplas (ano, area, codigo)
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    chaves: Set[Any] = set()

    for ano_key, dados_ano in data.items():
        if str(ano_key).startswith("_"):
            continue

        try:
            ano = int(ano_key)
        except ValueError:
            continue

        for area, dados_area in dados_ano.items():
            if area not in ["MT", "CN", "CH", "LC"]:
                continue
            if not isinstance(dados_area, dict):
                continue

            for _, cores in dados_area.items():
                if not isinstance(cores, dict):
                    continue

                for _, codigo in cores.items():
                    try:
                        codigo_str = str(int(codigo))
                    except (TypeError, ValueError):
                        continue

                    if agrupar_por == "ano-area-codigo":
                        chaves.add((ano, area, codigo_str))
                    else:
                        chaves.add(codigo_str)

    return chaves


def carregar_codigos_presentes(path: Path, agrupar_por: str) -> Set[Any]:
    """Carrega cache de codigos presentes nos microdados.

    Args:
        path: Caminho para o arquivo JSON de cache
        agrupar_por: 'codigo' ou 'ano-area-codigo'

    Returns:
        Set de codigos ou tuplas

    Raises:
        ValueError: Se o formato do arquivo nao corresponde ao esperado
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    formato = data.get("agrupar_por")
    if formato and formato != agrupar_por:
        raise ValueError(f"Arquivo de codigos usa '{formato}', esperado '{agrupar_por}'")

    if agrupar_por == "ano-area-codigo":
        chaves = set()
        for item in data.get("chaves", []):
            if not isinstance(item, list) or len(item) != 3:
                continue
            ano, area, codigo = item
            try:
                ano_int = int(ano)
                area_str = str(area)
                codigo_str = str(codigo)
            except (TypeError, ValueError):
                continue
            chaves.add((ano_int, area_str, codigo_str))
        return chaves

    return {str(codigo) for codigo in data.get("codigos", [])}
