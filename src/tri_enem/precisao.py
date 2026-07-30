# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Confiabilidade da nota, medida em holdout de microdados oficiais."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping

SEVERIDADE_POR_STATUS = {
    "ok": "sucesso",
    "aviso_leve": "info",
    "aviso_forte": "atencao",
    "erro_alto": "alerta",
    "nao_calibrado": "atencao",
    "sem_participantes": "atencao",
    "sem_itens": "alerta",
}

DATA_FILE = Path(__file__).parent / "coeficientes_data.json"
PERFIL_CALIBRACAO_VERIFICADA = "calibracao_verificada"
PERFIL_BOA_COM_EXCECOES = "boa_na_maioria_com_excecoes"
PERFIL_ESTIMATIVA = "estimativa"
PERFIL_SEM_VALIDACAO = "sem_validacao"
STATUS_VALIDOS = {
    "ok",
    "aviso_leve",
    "aviso_forte",
    "erro_alto",
    "nao_calibrado",
    "sem_participantes",
    "sem_itens",
}


def _msg_catalogo_indisponivel() -> str:
    return (
        "Não foi possível consultar a validação desta prova. O resultado deve "
        "ser interpretado como estimativa."
    )


def _msg_sem_participantes() -> str:
    return (
        "Prova sem participantes válidos nos microdados públicos do INEP. Foi "
        "aplicado o ajuste médio da área; o resultado é uma estimativa."
    )


def _msg_sem_itens() -> str:
    return (
        "Os parâmetros dos itens desta prova não estão disponíveis nos dados "
        "públicos usados pelo projeto; a nota não pode ser calculada."
    )


def _msg_nao_calibrada() -> str:
    return (
        "Prova sem holdout suficiente para garantir o limite de precisão. O "
        "resultado deve ser interpretado como estimativa."
    )


def classificar_perfil_validacao(
    status: str,
    erro_p95: float | None,
    n_acima_2: int | None,
    n_validacao: int | None,
) -> str:
    """Resume o desempenho típico sem alterar o status técnico estrito.

    ``ok`` continua reservado às provas cujo erro máximo satisfaz o contrato.
    O perfil intermediário serve apenas para comunicar que as divergências
    ficaram concentradas em uma pequena minoria do holdout.
    """
    if status == "ok":
        return PERFIL_CALIBRACAO_VERIFICADA
    if (
        status in {"aviso_leve", "aviso_forte", "erro_alto"}
        and erro_p95 is not None
        and erro_p95 <= 2.0 + 1e-12
        and n_acima_2 is not None
        and n_validacao is not None
        and n_validacao >= 30
        and n_acima_2 / n_validacao <= 0.05 + 1e-12
    ):
        return PERFIL_BOA_COM_EXCECOES
    if status in {"sem_participantes", "sem_itens", "nao_calibrado"}:
        return PERFIL_SEM_VALIDACAO
    return PERFIL_ESTIMATIVA


def _msg_por_metricas(status: str, perfil: str) -> str:
    if status == "ok":
        return (
            "Esta prova tem boa calibração, verificada com casos reais dos "
            "microdados oficiais."
        )
    if status == "sem_participantes":
        return _msg_sem_participantes()
    if status == "sem_itens":
        return _msg_sem_itens()
    if status == "nao_calibrado":
        return _msg_nao_calibrada()
    if perfil == PERFIL_BOA_COM_EXCECOES:
        return (
            "A calibração apresentou erro baixo e a estimativa foi confiável "
            "na maioria dos casos reais. Houve exceções, por isso o resultado "
            "continua sendo uma estimativa."
        )
    return (
        "A validação desta prova apresentou diferenças relevantes entre a "
        "estimativa e as notas oficiais. O resultado deve ser interpretado "
        "como estimativa."
    )


def _resultado_fechado(aviso: str | None = None) -> Dict[str, Any]:
    return {
        "mae": None,
        "r_squared": None,
        "confiavel": False,
        "aviso": aviso or _msg_catalogo_indisponivel(),
        "severidade": "atencao",
        "status": "nao_calibrado",
        "n_validacao": None,
        "erro_maximo": None,
        "erro_p95": None,
        "n_acima_2": None,
        "percentual_ate_2": None,
        "perfil": PERFIL_SEM_VALIDACAO,
        "faixas_cobertas": [],
        "faixas_existentes": [],
        "modelo": None,
        "validado_em": None,
        "motivo": "catalogo_indisponivel",
    }


def formatar_resumo_validacao(
    precisao: Mapping[str, Any],
) -> str | None:
    """Resume as métricas em linguagem curta, sem códigos internos."""
    n_validacao = precisao.get("n_validacao")
    if not n_validacao:
        return None

    def numero(valor: Any) -> str:
        return f"{float(valor):.2f}".replace(".", ",")

    partes = [f"Validação: {int(n_validacao)} casos reais"]
    if precisao.get("mae") is not None:
        partes.append(f"erro médio: {numero(precisao['mae'])}")
    if precisao.get("erro_p95") is not None:
        partes.append(
            f"em 95% dos casos: até {numero(precisao['erro_p95'])}"
        )
    if precisao.get("erro_maximo") is not None:
        partes.append(
            f"maior diferença: {numero(precisao['erro_maximo'])}"
        )

    n_excecoes = precisao.get("n_acima_2")
    if n_excecoes is not None:
        n_excecoes = int(n_excecoes)
        if n_excecoes == 0:
            partes.append("nenhuma exceção observada")
        elif n_excecoes == 1:
            partes.append("1 exceção")
        else:
            partes.append(f"{n_excecoes} exceções")

    rotulos = {
        PERFIL_CALIBRACAO_VERIFICADA: "boa calibração verificada",
        PERFIL_BOA_COM_EXCECOES: "confiável na maioria",
        PERFIL_ESTIMATIVA: "variação relevante",
        PERFIL_SEM_VALIDACAO: "validação limitada",
    }
    perfil = precisao.get("perfil")
    if perfil in rotulos:
        partes.append(rotulos[perfil])
    return " · ".join(partes)


@lru_cache(maxsize=8)
def _carregar_data_cache(
    caminho: str, mtime_ns: int, tamanho: int
) -> Dict[str, Any] | None:
    del mtime_ns, tamanho  # Fazem parte da chave e invalidam após substituição.
    try:
        data = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _carregar_data() -> Dict[str, Any] | None:
    try:
        stat = DATA_FILE.stat()
    except OSError:
        return None
    return _carregar_data_cache(
        str(DATA_FILE.resolve()), stat.st_mtime_ns, stat.st_size
    )


def _numero_finito(valor: Any) -> float | None:
    if valor is None:
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError("métrica numérica inválida") from None
    if not math.isfinite(numero):
        raise ValueError("métrica não finita")
    return numero


def _inteiro_nao_negativo(valor: Any) -> int | None:
    if valor is None:
        return None
    if isinstance(valor, bool):
        raise ValueError("contagem inválida")
    try:
        inteiro = int(valor)
    except (TypeError, ValueError):
        raise ValueError("contagem inválida") from None
    if inteiro < 0 or float(valor) != inteiro:
        raise ValueError("contagem inválida")
    return inteiro


def verificar_precisao_prova(ano: int, area: str, co_prova: int) -> Dict[str, Any]:
    """Retorna métricas de holdout e falha fechado quando não há catálogo."""
    try:
        ano = int(ano)
        co_prova = int(co_prova)
        area = str(area).upper()
    except (TypeError, ValueError):
        return _resultado_fechado()

    data = _carregar_data()
    if data is None:
        return _resultado_fechado()

    key = f"{ano},{area},{co_prova}"
    try:
        if int(data.get("schema_version")) != 3:
            return _resultado_fechado()
        por_prova = data.get("por_prova", {})
        if not isinstance(por_prova, dict):
            return _resultado_fechado()
        info = por_prova.get(key)
    except (TypeError, ValueError, AttributeError):
        return _resultado_fechado()
    if not isinstance(info, dict):
        return _resultado_fechado(_msg_nao_calibrada())

    validacao_bruta = info.get("validacao")
    qualidade = info.get("qualidade")
    transformacao_bruta = info.get("transformacao")
    if not isinstance(qualidade, dict):
        return _resultado_fechado()
    status = qualidade.get("status")
    if status not in STATUS_VALIDOS:
        return _resultado_fechado()
    if validacao_bruta is not None and not isinstance(validacao_bruta, dict):
        return _resultado_fechado()
    if transformacao_bruta is not None and not isinstance(
        transformacao_bruta, dict
    ):
        return _resultado_fechado()

    validacao = validacao_bruta or {}
    transformacao = transformacao_bruta or {}
    try:
        mae = _numero_finito(validacao.get("mae"))
        erro_maximo = _numero_finito(validacao.get("erro_maximo"))
        erro_p95 = _numero_finito(validacao.get("erro_p95"))
        r_squared = _numero_finito(validacao.get("r_squared"))
        n_validacao = _inteiro_nao_negativo(validacao.get("n"))
        n_acima_2 = _inteiro_nao_negativo(validacao.get("acima_2"))
    except ValueError:
        return _resultado_fechado()

    faixas_cobertas = validacao.get("faixas_cobertas", [])
    faixas_existentes = validacao.get("faixas_existentes", [])
    if not isinstance(faixas_cobertas, list) or not isinstance(
        faixas_existentes, list
    ):
        return _resultado_fechado()
    if status == "ok" and (
        mae is None
        or erro_maximo is None
        or erro_p95 is None
        or n_validacao is None
        or n_acima_2 is None
        or n_validacao < 30
        or n_acima_2 != 0
        or erro_maximo > 2.0 + 1e-12
        or len(faixas_existentes) < 2
        or set(faixas_cobertas) != set(faixas_existentes)
    ):
        return _resultado_fechado()
    if (
        n_acima_2 is not None
        and n_validacao is not None
        and n_acima_2 > n_validacao
    ):
        return _resultado_fechado()

    perfil = classificar_perfil_validacao(
        status, erro_p95, n_acima_2, n_validacao
    )
    percentual_ate_2 = (
        100.0 * (n_validacao - n_acima_2) / n_validacao
        if n_validacao and n_acima_2 is not None
        else None
    )
    return {
        "mae": mae,
        "r_squared": r_squared,
        "confiavel": status == "ok",
        "aviso": _msg_por_metricas(status, perfil),
        "severidade": (
            "atencao"
            if perfil == PERFIL_BOA_COM_EXCECOES
            else SEVERIDADE_POR_STATUS.get(status, "atencao")
        ),
        "status": status,
        "n_validacao": n_validacao,
        "erro_maximo": erro_maximo,
        "erro_p95": erro_p95,
        "n_acima_2": n_acima_2,
        "percentual_ate_2": percentual_ate_2,
        "perfil": perfil,
        "faixas_cobertas": faixas_cobertas,
        "faixas_existentes": faixas_existentes,
        "modelo": transformacao.get("tipo"),
        "validado_em": qualidade.get("validado_em"),
        "motivo": qualidade.get("motivo"),
    }
