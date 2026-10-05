# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Confiabilidade da nota, medida em holdout de microdados oficiais."""

from __future__ import annotations

from copy import deepcopy

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
        "Não há resultados oficiais suficientes para conferir a precisão "
        "desta prova. A nota deve ser tratada como estimativa."
    )


def formatar_desempenho_tipico(tipico: Mapping[str, Any] | None) -> str | None:
    """Explica a evidência média sem exigir vocabulário estatístico."""
    if not tipico or not tipico.get('n') or tipico.get('mae') is None:
        return None
    erro = f"{float(tipico['mae']):.2f}".replace('.', ',')
    unidade = "ponto" if abs(float(tipico['mae'])) <= 1 else "pontos"
    if tipico.get('independente'):
        return (f"Em {tipico['n']} novos resultados oficiais, a diferença média "
                f"estimada para a nota oficial foi de {erro} {unidade}.")
    return (f"Nos {tipico['n']} resultados oficiais examinados, a diferença média "
            f"estimada foi de {erro} {unidade}. Esses resultados já foram usados na "
            "pesquisa, por isso essa diferença não comprova a precisão para outras pessoas.")


def classificar_perfil_validacao(
    status: str,
    erro_p95: float | None,
    n_acima_2: int | None,
    n_validacao: int | None,
    independente_media: bool | None = None,
) -> str:
    """Resume o desempenho típico sem alterar o status técnico estrito.

    ``ok`` continua reservado às provas cujo erro máximo satisfaz o contrato.
    O perfil intermediário serve apenas para comunicar que as divergências
    ficaram concentradas em uma pequena minoria do holdout.
    """
    if independente_media is False:
        return PERFIL_SEM_VALIDACAO
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
    formato: str = "texto",
) -> str | None:
    """Resume a evidência do holdout em linguagem direta e organizada."""
    n_validacao = precisao.get("n_validacao")
    if not n_validacao:
        return None

    def numero(valor: Any) -> str:
        return f"{float(valor):.2f}".replace(".", ",")

    def pontos(valor: Any) -> str:
        unidade = "ponto" if abs(float(valor)) <= 1 else "pontos"
        return f"{numero(valor)} {unidade}"

    verbo = "Observada" if precisao.get("origem_metricas") == "diagnostico_calibracao" else "Validada"
    validacao = f"{verbo} em {int(n_validacao)} resultados oficiais."
    metricas = []
    if precisao.get("mae") is not None:
        metricas.append(
            f"Erro absoluto médio: {pontos(precisao['mae'])}"
        )
    if precisao.get("erro_p95") is not None:
        metricas.append(
            f"95% das estimativas diferiram até {pontos(precisao['erro_p95'])}"
        )
    if precisao.get("erro_maximo") is not None:
        metricas.append(
            f"Maior diferença observada: {pontos(precisao['erro_maximo'])}"
        )
    tipico = precisao.get("desempenho_tipico")
    explicacao = formatar_desempenho_tipico(tipico)
    if explicacao:
        metricas.append(explicacao)
    if formato == "reportlab":
        metricas_compactas = [f"{int(n_validacao)} resultados oficiais"]
        if precisao.get("mae") is not None:
            metricas_compactas.append(
                f"erro absoluto médio: {pontos(precisao['mae'])}"
            )
        if precisao.get("erro_p95") is not None:
            metricas_compactas.append(
                f"95% das estimativas: diferença de até {pontos(precisao['erro_p95'])}"
            )
        if precisao.get("erro_maximo") is not None:
            metricas_compactas.append(
                f"maior diferença observada: {pontos(precisao['erro_maximo'])}"
            )
        return " · ".join(metricas_compactas)
    if not metricas:
        return validacao
    return validacao + " · " + " · ".join(metricas)


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

    tipico = precisao.get('desempenho_tipico')
    if isinstance(tipico, dict) and tipico.get('independente') is False:
        x = _destaque("estimativa", COR_CALIBRACAO_MODERADA)
        return _frase(f"Esta nota é uma {x}. Há poucos resultados oficiais para conferir sua precisão.")

    if status == "ok" or perfil == PERFIL_CALIBRACAO_VERIFICADA or severidade == "sucesso":
        x = _destaque("alta confiabilidade", COR_CALIBRACAO_BOA)
        return _frase(f"Estimativa com {x} nesta prova.")

    if perfil == PERFIL_BOA_COM_EXCECOES:
        x = _destaque("confiável", COR_CALIBRACAO_MODERADA)
        return _frase(f"Estimativa {x} na maioria dos casos desta prova.")

    if status == "sem_participantes":
        x = _destaque("não verificada", COR_CALIBRACAO_MODERADA)
        return _frase(f"Confiabilidade {x} nesta prova (amostra oficial insuficiente).")

    if status == "sem_itens":
        x = _destaque("indisponível", COR_CALIBRACAO_RUIM)
        return _frase(f"Estimativa {x} para esta prova (parâmetros ausentes nos dados públicos).")

    if status == "nao_calibrado":
        x = _destaque("não verificada", COR_CALIBRACAO_MODERADA)
        return _frase(f"Confiabilidade {x} nesta prova (amostra de validação insuficiente).")

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


def validacao_para_apresentacao(info: Mapping[str, Any]) -> Dict[str, Any]:
    """Mostra a amostra com maior erro máximo, sem misturar suas métricas."""
    primaria = info.get("validacao") or {}
    escolhida = primaria
    for key in ("validacao_confirmacao", "validacao_residual", "validacao_media", "diagnostico_calibracao"):
        confirmacao = info.get(key)
        if confirmacao is None:
            continue
        if not isinstance(confirmacao, dict):
            raise ValueError("confirmação inválida")
        n = _inteiro_nao_negativo(confirmacao.get("n"))
        maior = _numero_finito(confirmacao.get("erro_maximo"))
        if not n or maior is None or maior < 0:
            raise ValueError("confirmação inválida")
        if maior > float(escolhida.get("erro_maximo", -1)):
            escolhida = confirmacao
    return escolhida


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

    transformacao = transformacao_bruta or {}
    try:
        validacao = validacao_para_apresentacao(info)
        n_primaria = _inteiro_nao_negativo((validacao_bruta or {}).get("n")) or 0
        mae = _numero_finito(validacao.get("mae"))
        erro_maximo = _numero_finito(validacao.get("erro_maximo"))
        erro_p95 = _numero_finito(validacao.get("erro_p95"))
        r_squared = _numero_finito(validacao.get("r_squared"))
        n_validacao = _inteiro_nao_negativo(validacao.get("n"))
        n_acima_2 = _inteiro_nao_negativo(validacao.get("acima_2"))
    except ValueError:
        return _resultado_fechado()

    faixas_cobertas = validacao.get("faixas_cobertas", [])
    faixas_existentes = (validacao_bruta or {}).get("faixas_existentes", [])
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
        or n_primaria < 30
        or n_acima_2 != 0
        or erro_maximo > 2.0 + 1e-12
        or len(faixas_existentes) < 2
        or set((validacao_bruta or {}).get("faixas_cobertas", [])) != set(faixas_existentes)
    ):
        return _resultado_fechado()
    if (
        n_acima_2 is not None
        and n_validacao is not None
        and n_acima_2 > n_validacao
    ):
        return _resultado_fechado()

    tipico = info.get('desempenho_tipico')
    perfil = classificar_perfil_validacao(
        status, erro_p95, n_acima_2, n_validacao,
        tipico.get('independente') if isinstance(tipico, dict) else None
    )
    percentual_ate_2 = (
        100.0 * (n_validacao - n_acima_2) / n_validacao
        if n_validacao and n_acima_2 is not None
        else None
    )
    if tipico is not None:
        try:
            if not isinstance(tipico, dict):
                return _resultado_fechado()
            nt = _inteiro_nao_negativo(tipico.get('n'))
            mt = _numero_finito(tipico.get('mae'))
            pt = _numero_finito(tipico.get('erro_p95'))
            if (not nt or mt is None or mt < 0 or pt is None or pt < 0
                    or not isinstance(tipico.get('independente'), bool)):
                return _resultado_fechado()
        except ValueError:
            return _resultado_fechado()
    aviso = _msg_por_metricas(status, perfil)
    limitada = tipico is not None and tipico['independente'] is False
    if limitada:
        aviso = ("Esta nota é uma estimativa. Há poucos resultados oficiais para "
                 "conferir sua precisão.")
    return {
        "mae": mae,
        "r_squared": r_squared,
        "confiavel": status == "ok" and not limitada,
        "aviso": aviso,
        "severidade": (
            "atencao"
            if perfil == PERFIL_BOA_COM_EXCECOES or (limitada and status == 'ok')
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
        "origem_metricas": validacao.get("origem"),
        "criterio_modelo": (info.get("calibracao") or {}).get("objetivo_selecao"),
        "desempenho_tipico": deepcopy(tipico),
    }
