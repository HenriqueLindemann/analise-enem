# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Adapta resultados do motor para a estrutura dos relatórios."""

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Iterable, List, Mapping

from ..config import NOMES_AREAS
from ..mapeador_provas import MapeadorProvas
from ..posicoes import normalizar_posicoes_resultados
from .base import AreaAnalise, DadosRelatorio, QuestaoAnalise


_TIPOS_APLICACAO = {
    "1a_aplicacao": "1ª Aplicação",
    "digital": "Digital",
    "reaplicacao": "Reaplicação",
    "segunda_oportunidade": "Segunda Oportunidade",
}


def adaptar_resultados_para_relatorio(
    resultados: Iterable[Any],
    ano: int,
    *,
    titulo: str = "Desempenho no Simulado ENEM",
    tipo_aplicacao: str = "",
    cor_prova: str = "",
    origem_geracao: str = "notatri.com",
    data_geracao: datetime | None = None,
) -> DadosRelatorio:
    """Converte resultados resumidos ou detalhados em dados de relatório.

    A normalização acontece nesta fronteira de apresentação e sempre recebe
    cópias dos resultados. Assim, o mesmo adaptador pode ser usado pelo CLI e
    pelo Streamlit sem alterar listas guardadas em ``session_state``.
    """
    ano = int(ano)
    mapeador = MapeadorProvas()
    resultados_mapeados = [_para_mapeamento(resultado) for resultado in resultados]
    resultados_normalizados = normalizar_posicoes_resultados(
        resultados_mapeados,
        mapeador.listar_ordem_provas(ano),
    )

    return DadosRelatorio(
        titulo=titulo,
        ano_prova=ano,
        tipo_aplicacao=_TIPOS_APLICACAO.get(
            str(tipo_aplicacao or ""), str(tipo_aplicacao or "")
        ),
        cor_prova=str(cor_prova or "").capitalize(),
        origem_geracao=origem_geracao,
        data_geracao=data_geracao or datetime.now().astimezone(),
        areas=[_adaptar_area(resultado, ano) for resultado in resultados_normalizados],
    )


def _para_mapeamento(resultado: Any) -> Mapping[str, Any]:
    if isinstance(resultado, Mapping):
        mapeamento = dict(resultado)
    elif is_dataclass(resultado):
        mapeamento = asdict(resultado)
    else:
        raise TypeError(
            "Cada resultado deve ser um mapeamento ou uma instância de dataclass"
        )

    # ``analisar_todas_questoes`` usa nomes curtos; os wrappers de apresentação
    # já os tornam explícitos, mas o adaptador também aceita a saída avançada.
    if isinstance(mapeamento.get("acertos"), (list, tuple)):
        mapeamento.setdefault("questoes_acertadas", mapeamento["acertos"])
    if isinstance(mapeamento.get("erros"), (list, tuple)):
        mapeamento.setdefault("questoes_erradas", mapeamento["erros"])
    return mapeamento


def _adaptar_area(resultado: Mapping[str, Any], ano_padrao: int) -> AreaAnalise:
    sigla = str(resultado.get("sigla", resultado.get("area", ""))).upper()
    if not sigla:
        raise ValueError("Resultado sem sigla de área")

    acertos_valor = resultado.get("acertos")
    if isinstance(acertos_valor, (list, tuple)):
        acertos = len(acertos_valor)
    else:
        acertos = int(
            acertos_valor
            if acertos_valor is not None
            else resultado.get("total_acertos", 0)
        )
    total_itens = resultado.get("total_itens")
    if total_itens is None:
        total_itens = acertos + len(resultado.get("questoes_erradas", []) or [])

    return AreaAnalise(
        sigla=sigla,
        nome=resultado.get("nome") or NOMES_AREAS.get(sigla, sigla),
        ano=int(resultado.get("ano") or ano_padrao),
        co_prova=int(resultado.get("co_prova") or 0),
        nota=float(resultado["nota"]),
        theta=float(resultado.get("theta", 0.0)),
        acertos=acertos,
        total_itens=int(total_itens),
        questoes=_adaptar_questoes(resultado),
        lingua=resultado.get("lingua"),
        cor_prova=resultado.get("cor_prova"),
    )


def _adaptar_questoes(resultado: Mapping[str, Any]) -> List[QuestaoAnalise]:
    anuladas = resultado.get("anuladas") or [
        {"posicao": posicao}
        for posicao in (
            resultado.get(
                "questoes_anuladas_caderno",
                resultado.get("questoes_anuladas", []),
            )
            or []
        )
    ]
    fontes = (
        ("questoes_acertadas", True, "perda_se_errasse"),
        ("questoes_erradas", False, "ganho_se_acertasse"),
        ("anuladas", False, None),
    )
    questoes = []

    for campo, acertou_padrao, campo_impacto in fontes:
        if campo == "anuladas":
            entradas = anuladas
        else:
            alias = "acertos" if campo == "questoes_acertadas" else "erros"
            entradas = resultado.get(campo) or []
            if not entradas and isinstance(resultado.get(alias), (list, tuple)):
                entradas = resultado[alias]
        for entrada in entradas or []:
            questao = dict(entrada) if isinstance(entrada, Mapping) else {
                "posicao": entrada,
            }
            anulada = campo == "anuladas" or bool(questao.get("anulada"))
            posicao = questao.get("posicao", questao.get("posicao_caderno"))
            if posicao is None:
                raise ValueError(f"Questão de {campo} sem posição")
            impacto = (
                0.0
                if anulada
                else questao.get(campo_impacto, questao.get("impacto", 0.0))
            )
            questoes.append(
                QuestaoAnalise(
                    posicao=int(posicao),
                    gabarito=questao.get("gabarito", "X" if anulada else "?"),
                    resposta_dada=questao.get("resposta_dada", "."),
                    acertou=bool(questao.get("acertou", acertou_padrao))
                    and not anulada,
                    param_a=float(questao.get("param_a", 0.0) or 0.0),
                    param_b=float(questao.get("param_b", 0.0) or 0.0),
                    param_c=float(questao.get("param_c", 0.0) or 0.0),
                    impacto=float(impacto or 0.0),
                    co_item=questao.get("co_item"),
                    anulada=anulada,
                )
            )

    return questoes
