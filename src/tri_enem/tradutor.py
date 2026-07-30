# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Tradutor de Respostas LC

Este módulo lida com as diferenças de estrutura LC entre anos:
- 2009: 45 itens no arquivo, posições 91-135, sem TP_LINGUA
- 2010-2019: 50 itens (ambas línguas), posições 91-135
- 2020+: 50 itens (ambas línguas), posições 1-45; as digitais 691–694
  de 2020 têm duas versões completas e totalizam 90 linhas

O tradutor garante que o usuário sempre forneça 45 respostas e
mapeia corretamente para os itens da prova.
"""

import pandas as pd
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class ConfiguracaoLC:
    """Configuração de LC para um ano específico."""
    ano: int
    tem_tp_lingua_itens: bool  # Se ITENS_PROVA tem TP_LINGUA
    tem_tp_lingua_dados: bool  # Se DADOS_ENEM tem TP_LINGUA
    n_itens_arquivo: int       # 45 ou 50
    posicao_inicio: int        # 91 (antigo) ou 1 (novo)
    # Posições das questões de língua (as 5 primeiras do gabarito)
    posicoes_lingua: List[int]


# Configurações por ano
CONFIGURACOES_LC = {
    2009: ConfiguracaoLC(
        ano=2009,
        tem_tp_lingua_itens=False,
        tem_tp_lingua_dados=False,
        n_itens_arquivo=45,
        posicao_inicio=91,
        posicoes_lingua=[91, 92, 93, 94, 95],
    ),
    # Anos com estrutura antiga (posições 91-135) - 2010 a 2015
    **{ano: ConfiguracaoLC(
        ano=ano,
        tem_tp_lingua_itens=True,
        tem_tp_lingua_dados=True,
        n_itens_arquivo=50,
        posicao_inicio=91,
        posicoes_lingua=[91, 92, 93, 94, 95],
    ) for ano in range(2010, 2016)},
    
    # Anos com estrutura nova (posições 1-45/50) - 2016 em diante
    **{ano: ConfiguracaoLC(
        ano=ano,
        tem_tp_lingua_itens=True,
        tem_tp_lingua_dados=True,
        n_itens_arquivo=50,
        posicao_inicio=1,
        posicoes_lingua=[1, 2, 3, 4, 5],
    ) for ano in range(2016, 2030)},
}


def obter_config_lc(ano: int) -> ConfiguracaoLC:
    """Obtém configuração LC para um ano."""
    if ano in CONFIGURACOES_LC:
        return CONFIGURACOES_LC[ano]
    # Fallback para formato novo
    return ConfiguracaoLC(
        ano=ano,
        tem_tp_lingua_itens=True,
        tem_tp_lingua_dados=True,
        n_itens_arquivo=50,
        posicao_inicio=1,
        posicoes_lingua=[1, 2, 3, 4, 5],
    )


def filtrar_itens_lc(df_itens: pd.DataFrame, co_prova: int, tp_lingua: int, config: ConfiguracaoLC) -> pd.DataFrame:
    """
    Filtra itens LC para obter exatamente 45 itens com a língua correta.
    
    Args:
        df_itens: DataFrame com todos os itens do ano
        co_prova: Código da prova
        tp_lingua: 0=inglês, 1=espanhol
        config: Configuração LC do ano
    
    Returns:
        DataFrame com 45 itens ordenados por posição
    """
    lc = df_itens[(df_itens['SG_AREA'] == 'LC') & (df_itens['CO_PROVA'] == co_prova)].copy()

    # As provas digitais de LC de 2020 (691–694) armazenam dois cadernos
    # completos sob o mesmo CO_PROVA. Nesse caso TP_VERSAO_DIGITAL não é uma
    # duplicata descartável: a versão 0 contém inglês e a versão 1 contém
    # espanhol, inclusive com posições diferentes para os 40 itens comuns.
    # Selecionar sempre a versão menor desalinha toda a prova de espanhol.
    if (
        config.tem_tp_lingua_itens
        and "TP_VERSAO_DIGITAL" in lc.columns
        and tp_lingua in (0, 1)
    ):
        versao = lc[
            pd.to_numeric(
                lc["TP_VERSAO_DIGITAL"], errors="coerce"
            ).eq(tp_lingua)
        ]
        if (
            len(versao) == 45
            and versao["CO_POSICAO"].nunique() == 45
            and tp_lingua
            in {
                int(valor)
                for valor in versao["TP_LINGUA"].dropna().unique()
                if int(valor) in (0, 1)
            }
        ):
            lc = versao

    # Não troca silenciosamente o idioma solicitado. Algumas provas especiais
    # oferecem apenas uma língua (por exemplo 2012/LC/165).
    if config.tem_tp_lingua_itens and 'TP_LINGUA' in lc.columns:
        disponiveis = {
            int(valor) for valor in lc["TP_LINGUA"].dropna().unique()
            if int(valor) in (0, 1)
        }
        if tp_lingua not in disponiveis:
            nomes = {0: "inglês", 1: "espanhol"}
            ofertadas = ", ".join(nomes[x] for x in sorted(disponiveis)) or "nenhuma"
            raise ValueError(
                f"Prova LC {co_prova} não oferece "
                f"{nomes.get(tp_lingua, tp_lingua)}; disponível: {ofertadas}"
            )
        lc = lc[(pd.isna(lc['TP_LINGUA'])) | (lc['TP_LINGUA'] == tp_lingua)]

    return deduplicar_itens_por_posicao(lc)


def deduplicar_itens_por_posicao(lc: pd.DataFrame) -> pd.DataFrame:
    """
    Ordena por posição e escolhe deterministicamente a primeira ocorrência.

    Os pares de língua são filtrados antes desta função e as digitais de 2020
    são separadas por ``TP_VERSAO_DIGITAL``. As adaptadas 187–190 de 2013
    ainda contêm duas coleções sem discriminador público; para que continuem
    calculáveis, conservamos a primeira coleção na ordem oficial normalizada.
    A precisão observada dessas provas permanece registrada no catálogo e deve
    ser mostrada como aviso junto da estimativa.
    """
    if 'TP_VERSAO_DIGITAL' in lc.columns:
        lc = lc.sort_values(by=['CO_POSICAO', 'TP_VERSAO_DIGITAL'],
                            na_position='first', kind='stable')
    else:
        lc = lc.sort_values('CO_POSICAO', kind='stable')

    return lc.drop_duplicates(subset=["CO_POSICAO"], keep="first")


def mapear_respostas_para_itens(respostas_45: str, itens: pd.DataFrame) -> List[Tuple[int, str, str]]:
    """
    Mapeia string de 45 respostas para os itens da prova.
    
    A string de respostas sempre tem 45 caracteres:
    - Posições 0-4: língua estrangeira (inglês ou espanhol)
    - Posições 5-44: questões comuns
    
    Returns:
        Lista de (posição_item, resposta_dada, gabarito)
    """
    if len(respostas_45) != 45:
        raise ValueError(f"String de respostas deve ter 45 caracteres, tem {len(respostas_45)}")
    
    resultado = []
    itens_list = itens.sort_values('CO_POSICAO').to_dict('records')
    
    for idx, item in enumerate(itens_list):
        if idx >= 45:
            break
        resposta = respostas_45[idx] if idx < len(respostas_45) else '?'
        gabarito = str(item['TX_GABARITO'])
        resultado.append((item['CO_POSICAO'], resposta, gabarito))
    
    return resultado


def filtrar_respostas_lc(respostas_str: str, tp_lingua: int, config: ConfiguracaoLC) -> str:
    """
    Filtra respostas LC para obter apenas as 45 válidas.
    
    Alguns registros de 2010 em diante têm 50 caracteres com padding "99999":
    - TP_LINGUA=0: inglês nas posições 0-4, padding em 5-9 e 40 comuns;
    - TP_LINGUA=1: padding em 0-4, espanhol em 5-9 e 40 comuns.
    
    Args:
        respostas_str: String de respostas original (45 ou 50 chars)
        tp_lingua: 0=inglês, 1=espanhol  
        config: Configuração LC do ano
    
    Returns:
        String com exatamente 45 respostas válidas
    """
    if len(respostas_str) == 45:
        # Já tem 45 caracteres, retornar direto
        return respostas_str
    
    if len(respostas_str) == 50:
        # Formato com padding: remover somente o bloco literal "99999".
        # Se inglês (tp_lingua=0): caracteres 0-44 são válidos, 45-49 são "9"s
        # Se espanhol (tp_lingua=1): caracteres 0-4 são "9"s, 5-49 são válidos
        
        if tp_lingua == 0:
            # Inglês: pos 0-4 (inglês) + pos 10-49 (comuns)
            # Pula pos 5-9 que é espanhol (99999)
            if respostas_str[5:10] != "99999":
                raise ValueError(
                    "Resposta LC de 50 caracteres deve conter padding "
                    "'99999' nas posições do idioma não escolhido"
                )
            return respostas_str[:5] + respostas_str[10:]
        else:
            # Espanhol: pos 5-49 (espanhol + comuns)
            # Pula pos 0-4 que é inglês (99999)
            if respostas_str[:5] != "99999":
                raise ValueError(
                    "Resposta LC de 50 caracteres deve conter padding "
                    "'99999' nas posições do idioma não escolhido"
                )
            return respostas_str[5:50]
    
    # Formato desconhecido: o chamador valida o comprimento e apresenta erro.
    return respostas_str
