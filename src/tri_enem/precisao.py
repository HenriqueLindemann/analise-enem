# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Confiabilidade da nota, medida em participantes reais que não entraram no ajuste."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping

from .calibracao_modelos import LIMITE_ERRO_RARO_CENSO

SEVERIDADE_POR_STATUS = {
    "ok": "sucesso",
    "aviso_leve": "info",
    "aviso_forte": "atencao",
    "erro_alto": "alerta",
    "erro_raro": "atencao",
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
    "erro_raro",
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
        "Prova sem participantes válidos nos microdados públicos do INEP. A "
        "nota usa a escala da área, comum a todas as provas; o resultado é uma "
        "estimativa."
    )


def _msg_sem_itens() -> str:
    return (
        "Os parâmetros dos itens desta prova não estão disponíveis nos dados "
        "públicos usados pelo projeto; a nota não pode ser calculada."
    )


def _msg_nao_calibrada() -> str:
    return (
        "Não há resultados oficiais suficientes para conferir a precisão "
        "desta prova. A nota deve ser tratada como estimativa."
    )


def classificar_perfil_validacao(
    status: str,
    erro_p95: float | None,
    n_acima_2: int | None,
    n_teste: int | None,
) -> str:
    """Resume o desempenho típico sem alterar o status técnico estrito.

    O perfil intermediário indica divergências concentradas em até 5% dos
    participantes testados, com p95 de até 2 pontos.
    """
    if status == "ok":
        return PERFIL_CALIBRACAO_VERIFICADA
    if status == "erro_raro":
        return PERFIL_BOA_COM_EXCECOES
    if (
        status in {"aviso_leve", "aviso_forte", "erro_alto"}
        and erro_p95 is not None
        and erro_p95 <= 2.0 + 1e-12
        and n_acima_2 is not None
        and n_teste is not None
        and n_teste >= 30
        and n_acima_2 / n_teste <= 0.05 + 1e-12
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
    if status == "erro_raro":
        return (
            "A nota coincide com a oficial para quase todos os participantes "
            "desta prova, mas alguns tiveram diferença acima de 2 pontos."
        )
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
        "confiavel": False,
        "aviso": aviso or _msg_catalogo_indisponivel(),
        "severidade": "atencao",
        "status": "nao_calibrado",
        "n_validacao": None,
        "n_acima_2": None,
        "percentual_ate_2": None,
        "perfil": PERFIL_SEM_VALIDACAO,
        "validado_em": None,
        "motivo": "catalogo_indisponivel",
    }


def formatar_percentual(valor: float) -> str:
    """99,98%; 100% sem casas decimais."""
    return "100%" if valor >= 100 else f"{valor:.2f}".replace(".", ",") + "%"


def formatar_resumo_validacao(
    precisao: Mapping[str, Any],
    formato: str = "texto",
) -> str | None:
    """Uma linha: participantes conferidos, diferença média e quantos ficaram a até 2 pontos."""
    n = precisao.get("n_validacao")
    if not n:
        return None
    partes = [f"Conferida com {int(n):,} participantes".replace(",", ".")]
    if precisao.get("mae") is not None:
        mae = float(precisao["mae"])
        unidade = "ponto" if mae <= 1 else "pontos"
        partes.append(f"diferença média de {mae:.2f} {unidade}".replace(".", ","))
    if precisao.get("percentual_ate_2") is not None:
        partes.append(f"{formatar_percentual(precisao['percentual_ate_2'])} até 2 pontos")
    separador = " · " if formato == "reportlab" else "; "
    return separador.join(partes) + "."


def formatar_proporcao_censo(precisao: Mapping[str, Any]) -> str | None:
    """"Cerca de 1 em cada N participantes…", só para provas com erro raro."""
    n, acima = precisao.get("n_validacao"), precisao.get("n_acima_2")
    status = precisao.get("status_precisao") or precisao.get("status")
    if status != "erro_raro" or not n or not acima:
        return None
    razao = n / acima
    casas = max(0, len(str(int(razao))) - 2)
    cada = int(round(razao, -casas)) if casas else max(1, round(razao))
    cada_txt = f"{cada:,}".replace(",", ".")
    return f"Cerca de 1 em cada {cada_txt} participantes teve diferença acima de 2 pontos."


# Cores de calibração padrão (WCAG AA/AAA)
COR_CALIBRACAO_BOA = "#15803D"        # Verde escuro
COR_CALIBRACAO_MODERADA = "#B45309"   # Âmbar escuro
COR_CALIBRACAO_RUIM = "#B91C1C"       # Vermelho escuro


def formatar_aviso_curto(
    precisao: Mapping[str, Any],
    formato: str = "reportlab",
) -> str:
    """
    Retorna uma conclusão curta sobre a confiabilidade da estimativa.

    Formatos suportados:
    - 'reportlab': <font color="..."><b>[X]</b></font> (para PDF)
    - 'html': <span style="color: ...; font-weight: bold;">[X]</span> (para Streamlit)
    - 'texto': [X] (sem tags)
    """
    if not precisao:
        return ""

    if (
        not precisao.get("aviso")
        and not precisao.get("severidade")
        and not precisao.get("status")
        and not precisao.get("status_precisao")
    ):
        return ""

    status = precisao.get("status_precisao") or precisao.get("status")
    perfil = precisao.get("perfil_precisao") or precisao.get("perfil")
    severidade = precisao.get("severidade_precisao") or precisao.get("severidade")

    def _destaque(termo: str, cor: str) -> str:
        if formato == "reportlab":
            return f'<font color="{cor}"><b>{termo}</b></font>'
        elif formato == "html":
            return f'<span style="color: {cor}; font-weight: bold;">{termo}</span>'
        return termo

    def _frase(conteudo: str) -> str:
        if formato == "html":
            return f'<span style="color: var(--text-color);">{conteudo}</span>'
        return conteudo

    if status == "ok" or perfil == PERFIL_CALIBRACAO_VERIFICADA or severidade == "sucesso":
        x = _destaque("alta confiabilidade", COR_CALIBRACAO_BOA)
        return _frase(f"Estimativa com {x} nesta prova.")

    if status == "erro_raro":
        x = _destaque("quase todos", COR_CALIBRACAO_MODERADA)
        frase = f"Nota precisa para {x} nesta prova."
        proporcao = formatar_proporcao_censo(precisao)
        return _frase(f"{frase} {proporcao}" if proporcao else frase)

    if perfil == PERFIL_BOA_COM_EXCECOES:
        x = _destaque("confiável", COR_CALIBRACAO_MODERADA)
        return _frase(f"Estimativa {x} na maioria dos casos desta prova.")

    if status == "sem_participantes":
        x = _destaque("não verificada", COR_CALIBRACAO_MODERADA)
        return _frase(f"Confiabilidade {x} nesta prova (nenhum participante para conferir).")

    if status == "sem_itens":
        x = _destaque("indisponível", COR_CALIBRACAO_RUIM)
        return _frase(f"Estimativa {x} para esta prova (parâmetros ausentes nos dados públicos).")

    if status == "nao_calibrado":
        x = _destaque("não verificada", COR_CALIBRACAO_MODERADA)
        return _frase(f"Confiabilidade {x} nesta prova (poucos participantes para conferir).")

    if severidade == "alerta" or status == "erro_alto":
        x = _destaque("limitada", COR_CALIBRACAO_RUIM)
        return _frase(f"Estimativa com confiabilidade {x} nesta prova.")

    if severidade == "atencao" or status in {"aviso_forte", "aviso_leve"}:
        x = _destaque("maior variação", COR_CALIBRACAO_MODERADA)
        return _frase(f"Estimativa sujeita a {x} nesta prova.")

    x = _destaque("maior variação", COR_CALIBRACAO_MODERADA)
    return _frase(f"Estimativa sujeita a {x} nesta prova.")


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


def metricas_prova(info: Mapping[str, Any]) -> Dict[str, Any]:
    """Métricas exibidas: do censo (todos os participantes) ou, sem ele, do teste."""
    censo = info.get("censo")
    if censo is not None:
        if not isinstance(censo, dict):
            raise ValueError("censo inválido")
        return censo
    return metricas_teste(info)


def metricas_teste(info: Mapping[str, Any]) -> Dict[str, Any]:
    """Métricas do teste da prova (holdout e confirmações somados), ou {}."""
    teste = info.get("teste")
    if teste is None:
        return {}
    if not isinstance(teste, dict):
        raise ValueError("teste inválido")
    return teste


def verificar_precisao_prova(ano: int, area: str, co_prova: int) -> Dict[str, Any]:
    """Status e métricas da prova; falha fechado sem catálogo válido."""
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
        if int(data.get("schema_version")) != 4:
            return _resultado_fechado()
        por_prova = data.get("por_prova", {})
        if not isinstance(por_prova, dict):
            return _resultado_fechado()
        info = por_prova.get(key)
    except (TypeError, ValueError, AttributeError):
        return _resultado_fechado()
    if not isinstance(info, dict):
        return _resultado_fechado(_msg_nao_calibrada())

    qualidade = info.get("qualidade")
    if not isinstance(qualidade, dict):
        return _resultado_fechado()
    status = qualidade.get("status")
    if status not in STATUS_VALIDOS:
        return _resultado_fechado()
    if status in {"nao_calibrado", "sem_participantes", "sem_itens"}:
        return {**_resultado_fechado(), "status": status,
                "aviso": _msg_por_metricas(status, PERFIL_SEM_VALIDACAO),
                "severidade": SEVERIDADE_POR_STATUS[status],
                "validado_em": qualidade.get("validado_em"), "motivo": qualidade.get("motivo")}
    try:
        metricas = metricas_prova(info)
        n = _inteiro_nao_negativo(metricas.get("n"))
        mae = _numero_finito(metricas.get("mae"))
        acima_2 = _inteiro_nao_negativo(metricas.get("acima_2"))
    except ValueError:
        return _resultado_fechado()
    if n is not None and acima_2 is not None and acima_2 > n:
        return _resultado_fechado()
    limite_ok = LIMITE_ERRO_RARO_CENSO if info.get("censo") else 1
    if status == "ok" and (n is None or n < 30 or mae is None or acima_2 is None
                           or acima_2 >= limite_ok):
        return _resultado_fechado()
    if status == "erro_raro" and not (n and acima_2):
        return _resultado_fechado()

    perfil = classificar_perfil_validacao(
        status, metricas.get("erro_p95"), acima_2, n)
    return {
        "mae": mae,
        "confiavel": status == "ok",
        "aviso": _msg_por_metricas(status, perfil),
        "severidade": (
            "atencao" if perfil == PERFIL_BOA_COM_EXCECOES
            else SEVERIDADE_POR_STATUS.get(status, "atencao")
        ),
        "status": status,
        "n_validacao": n,
        "n_acima_2": acima_2,
        "percentual_ate_2": (
            math.floor(10000 * (n - acima_2) / n) / 100
            if n and acima_2 is not None else None
        ),
        "perfil": perfil,
        "validado_em": qualidade.get("validado_em"),
        "motivo": qualidade.get("motivo"),
    }
