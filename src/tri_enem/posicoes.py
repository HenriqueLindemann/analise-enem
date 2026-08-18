# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Conversões entre a posição dos itens e a numeração do caderno.

O motor usa ``CO_POSICAO`` para parear respostas e itens. Essa posição não é
necessariamente a mesma que o número impresso no caderno: a ordem das áreas
muda nas provas antigas. As funções deste módulo fazem a conversão apenas
para estruturas de apresentação.
"""

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Sequence


_CAMPOS_QUESTOES = ("questoes_acertadas", "questoes_erradas", "anuladas")


def normalizar_posicoes_resultados(
    resultados: Iterable[Mapping[str, Any]],
    ordem_provas: Sequence[str],
) -> List[Dict[str, Any]]:
    """Retorna cópias com a numeração global exibida no caderno.

    O motor mantém ``posicao`` como ``CO_POSICAO`` bruto para preservar o
    pareamento dos itens. Os consumidores que exibem um caderno precisam usar
    ``idx_area`` e a ordem das áreas, pois provas antigas não usam a mesma
    sequência de áreas de 2017 em diante.

    Nenhum dicionário de entrada é alterado, inclusive listas e dicionários de
    questões aninhados. Registros sem ``idx_area`` são mantidos como estão;
    resultados resumidos devem fornecer ``questoes_anuladas_caderno`` ou já
    trazer ``questoes_anuladas`` na numeração canônica.
    """
    indices = {
        str(sigla).upper(): indice
        for indice, sigla in enumerate(ordem_provas)
    }
    normalizados = []

    for resultado in resultados:
        copia = deepcopy(dict(resultado))
        sigla = str(copia.get("sigla", copia.get("area", ""))).upper()
        area_indice = indices.get(sigla)

        for campo in _CAMPOS_QUESTOES:
            if campo not in copia or copia[campo] is None:
                continue

            questoes_normalizadas = []
            for questao in copia[campo]:
                if not isinstance(questao, Mapping):
                    questoes_normalizadas.append(deepcopy(questao))
                    continue

                questao_copia = deepcopy(dict(questao))
                idx_area = _obter_idx_area(questao_copia.get("idx_area"))
                if area_indice is not None and idx_area is not None:
                    posicao_bruta = questao_copia.get(
                        "posicao_bruta", questao_copia.get("posicao")
                    )
                    if posicao_bruta is not None:
                        questao_copia["posicao_bruta"] = posicao_bruta
                    posicao = posicao_caderno(
                        sigla, idx_area, ordem_provas
                    )
                    questao_copia["posicao_caderno"] = posicao
                    questao_copia["posicao"] = posicao
                elif questao_copia.get("posicao_caderno") is not None:
                    questao_copia["posicao"] = questao_copia["posicao_caderno"]

                questoes_normalizadas.append(questao_copia)
            copia[campo] = questoes_normalizadas

        tem_detalhes = any(campo in copia for campo in _CAMPOS_QUESTOES)
        if tem_detalhes:
            anuladas = [
                questao
                for questao in copia.get("anuladas", []) or []
                if isinstance(questao, Mapping)
            ]
            # ``anuladas`` é a fonte usual; a busca abaixo também aceita
            # detalhes marcados dentro das listas de acertos/erros.
            if not anuladas:
                anuladas = [
                    questao
                    for campo in ("questoes_acertadas", "questoes_erradas")
                    for questao in copia.get(campo, []) or []
                    if isinstance(questao, Mapping) and questao.get("anulada")
                ]

            if anuladas:
                posicoes_anuladas = [
                    questao["posicao"]
                    for questao in anuladas
                    if "posicao" in questao
                ]
            else:
                posicoes_anuladas = list(
                    copia.get(
                        "questoes_anuladas_caderno",
                        copia.get("questoes_anuladas", []),
                    )
                    or []
                )

            copia["questoes_anuladas"] = list(posicoes_anuladas)
            copia["questoes_anuladas_caderno"] = list(posicoes_anuladas)
        elif "questoes_anuladas_caderno" in copia:
            copia["questoes_anuladas_caderno"] = list(
                copia["questoes_anuladas_caderno"] or []
            )
            copia["questoes_anuladas"] = list(
                copia["questoes_anuladas_caderno"]
            )

        normalizados.append(copia)

    return normalizados


def posicao_caderno(
    area: str,
    idx_area: int,
    ordem_provas: Sequence[str],
) -> int:
    """Converte o índice relativo da área para a questão do caderno.

    ``idx_area`` é zero-based e corresponde à ordem dos 45 itens usados pelo
    motor. A função não aceita ``CO_POSICAO``: essa distinção evita usar a
    posição bruta como se fosse a numeração impressa.
    """
    indices = {
        str(sigla).upper(): indice
        for indice, sigla in enumerate(ordem_provas)
    }
    try:
        indice_area = indices[str(area).upper()]
    except KeyError as exc:
        raise ValueError(f"Área sem posição no caderno: {area!r}") from exc

    if not 0 <= idx_area < 45:
        raise ValueError(f"idx_area fora do intervalo 0..44: {idx_area!r}")
    return indice_area * 45 + idx_area + 1


def _obter_idx_area(valor: Any):
    if valor is None:
        return None
    try:
        idx_area = int(valor)
    except (TypeError, ValueError):
        return None
    return idx_area if 0 <= idx_area < 45 else None
