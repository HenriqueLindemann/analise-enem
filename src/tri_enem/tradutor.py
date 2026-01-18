# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Tradutor de Respostas LC

Este módulo lida com as diferenças de estrutura LC entre anos:
- 2009: 45 itens no arquivo, posições 91-135, sem TP_LINGUA
- 2010-2019: 50 itens (ambas línguas), posições 91-135
- 2020+: 50 itens (ambas línguas), posições 1-45

O tradutor garante que o usuário sempre forneça 45 respostas e
mapeia corretamente para os itens da prova.
"""

import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional
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
    
    if config.n_itens_arquivo == 45:
        # 2009: já tem apenas 45 itens, não precisa filtrar
        # Mas precisamos verificar se são os itens da língua correta
        return lc.sort_values('CO_POSICAO')
    
    # 50 itens: filtrar por TP_LINGUA
    if config.tem_tp_lingua_itens and 'TP_LINGUA' in lc.columns:
        # Manter itens comuns (TP_LINGUA=NaN) + itens da língua escolhida
        lc = lc[(pd.isna(lc['TP_LINGUA'])) | (lc['TP_LINGUA'] == tp_lingua)]
    
    return lc.sort_values('CO_POSICAO')


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
    
    Anos 2015-2020 têm 50 chars com "99999" padding:
    - Se TP_LINGUA=0 (inglês): "ABCDE..." + "99999..." -> retorna primeiros 45
    - Se TP_LINGUA=1 (espanhol): "99999..." + "AB CDE..." -> remove primeiros 5, retorna próximos 45
    
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
        # Formato com padding: remover os 5 "9"s
        # Se inglês (tp_lingua=0): caracteres 0-44 são válidos, 45-49 são "9"s
        # Se espanhol (tp_lingua=1): caracteres 0-4 são "9"s, 5-49 são válidos
        
        if tp_lingua == 0:
            # Inglês: pos 0-4 (inglês) + pos 10-49 (comuns)
            # Pula pos 5-9 que é espanhol (99999)
            return respostas_str[:5] + respostas_str[10:]
        else:
            # Espanhol: pos 5-49 (espanhol + comuns)
            # Pula pos 0-4 que é inglês (99999)
            return respostas_str[5:50]
    
    # Formato desconhecido, retornar como está
    return respostas_str[:45] if len(respostas_str) >= 45 else respostas_str

