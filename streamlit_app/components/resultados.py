# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de exibição de resultados para o Streamlit.
"""

import streamlit as st
from typing import Dict, List, Optional

from .graficos import (
    grafico_notas_barras, 
    grafico_impacto, 
    grade_questoes,
    grafico_pizza_acertos,
    grafico_comparativo_areas,
)


# Nomes completos das áreas
NOMES_AREAS = {
    'LC': 'Linguagens e Códigos',
    'CH': 'Ciências Humanas',
    'CN': 'Ciências da Natureza',
    'MT': 'Matemática',
}

# Emojis das áreas
EMOJIS_AREAS = {
    'LC': '📚',
    'CH': '🌍',
    'CN': '🔬',
    'MT': '📐',
}


def exibir_resumo_geral(resultados: List[Dict]):
    """
    Exibe o resumo geral com todas as notas e média.
    
    Args:
        resultados: Lista de resultados por área
    """
    if not resultados:
        st.warning("Nenhum resultado para exibir.")
        return
    
    # Calcular média
    notas = [r['nota'] for r in resultados]
    media = sum(notas) / len(notas)
    total_acertos = sum(r['acertos'] for r in resultados)
    total_questoes = sum(r['total_itens'] for r in resultados)
    
    # Métricas principais
    st.markdown("### Resumo Geral")
    
    cols = st.columns(len(resultados) + 1)
    
    for i, r in enumerate(resultados):
        with cols[i]:
            st.metric(
                label=f"{r['sigla']}",
                value=f"{r['nota']:.0f}",
                delta=f"{r['acertos']}/{r['total_itens']} acertos",
                delta_color="off"
            )
    
    with cols[-1]:
        st.metric(
            label="MÉDIA",
            value=f"{media:.0f}",
            delta=f"{total_acertos}/{total_questoes} total",
            delta_color="off"
        )
    
    # Gráfico de barras
    st.plotly_chart(
        grafico_notas_barras(resultados), 
        key="resumo_barras",
        config={'displayModeBar': False}
    )


def exibir_resultado_area(resultado: Dict):
    """
    Exibe o resultado detalhado de uma área com todos os gráficos visíveis.
    
    Args:
        resultado: Dict com resultado completo da área
    """
    sigla = resultado['sigla']
    nome = NOMES_AREAS.get(sigla, sigla)
    emoji = EMOJIS_AREAS.get(sigla, '📝')
    
    # Preparar dados das questões
    questoes_acertadas = resultado.get('questoes_acertadas', [])
    questoes_erradas = resultado.get('questoes_erradas', [])
    
    # Converter para formato esperado pelos gráficos
    todas_questoes = []
    for q in questoes_acertadas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': True,
            'gabarito': q['gabarito'],
            'resposta_dada': q['resposta_dada'],
            'impacto': q.get('perda_se_errasse', 0),
            'param_b': q.get('param_b', 0),
        })
    for q in questoes_erradas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': False,
            'gabarito': q['gabarito'],
            'resposta_dada': q['resposta_dada'],
            'impacto': q.get('ganho_se_acertasse', 0),
            'param_b': q.get('param_b', 0),
        })
    
    # Aviso de precisão se houver
    aviso = resultado.get('aviso_precisao')
    if aviso:
        st.error(aviso)
    
    # Seção 1: Grade de questões + Pizza
    st.markdown("##### Grade de Questões")
    col_grade, col_pizza = st.columns([3, 1])
    
    with col_grade:
        st.plotly_chart(
            grade_questoes(todas_questoes),
            key=f"grade_{sigla}",
            config={'displayModeBar': False}
        )
    
    with col_pizza:
        st.plotly_chart(
            grafico_pizza_acertos(resultado['acertos'], resultado['total_itens'] - resultado['acertos']),
            key=f"pizza_{sigla}",
            config={'displayModeBar': False}
        )
        st.caption(f"Taxa: {resultado['acertos']/resultado['total_itens']*100:.0f}%")
    
    # Seção 2: Gráfico de impacto
    st.markdown("##### Impacto das Questões na Nota")
    st.caption("Ordenado do maior para o menor impacto | Verde = Acerto | Vermelho = Erro")
    st.plotly_chart(
        grafico_impacto(todas_questoes, ""),
        key=f"impacto_{sigla}",
        config={'displayModeBar': False}
    )
    
    # Seção 3: Tabelas de erros e acertos
    col_erros, col_acertos = st.columns(2)
    
    with col_erros:
        st.markdown(f"##### Erros ({len(questoes_erradas)})")
        if questoes_erradas:
            _exibir_tabela_erros(questoes_erradas)
        else:
            st.success("Nenhum erro!")
    
    with col_acertos:
        st.markdown(f"##### Acertos ({len(questoes_acertadas)})")
        if questoes_acertadas:
            _exibir_tabela_acertos(questoes_acertadas)
        else:
            st.info("Nenhum acerto.")


def _exibir_tabela_erros(questoes: List[Dict]):
    """Exibe tabela de erros no estilo do relatório PDF."""
    import pandas as pd
    
    dados = []
    for q in questoes:
        dados.append({
            'Q': q['posicao'],
            'Resp': q['resposta_dada'],
            'Gab': q['gabarito'],
            'b': f"{q.get('param_b', 0):.2f}",
            'Ganho': f"+{q.get('ganho_se_acertasse', 0):.1f}",
        })
    
    df = pd.DataFrame(dados)
    
    # Aplicar estilo com fundo vermelho claro
    def estilo_erro(row):
        return ['background-color: #ffe6e6'] * len(row)
    
    df_styled = df.style.apply(estilo_erro, axis=1)
    
    st.dataframe(
        df_styled,
        width='stretch',
        hide_index=True,
        column_config={
            'Q': st.column_config.NumberColumn('Q', width='small', help='Número da questão'),
            'Resp': st.column_config.TextColumn('Resp', width='small', help='Sua resposta'),
            'Gab': st.column_config.TextColumn('Gab', width='small', help='Gabarito correto'),
            'b': st.column_config.TextColumn('b', width='small', help='Dificuldade (quanto maior, mais difícil)'),
            'Ganho': st.column_config.TextColumn('Ganho', width='small', help='Pontos que você ganharia se acertasse'),
        }
    )


def _exibir_tabela_acertos(questoes: List[Dict]):
    """Exibe tabela de acertos no estilo do relatório PDF."""
    import pandas as pd
    
    dados = []
    for q in questoes:
        dados.append({
            'Q': q['posicao'],
            'Resp': q['resposta_dada'],
            'Gab': q['gabarito'],
            'b': f"{q.get('param_b', 0):.2f}",
            'Perda': f"-{q.get('perda_se_errasse', 0):.1f}",
        })
    
    df = pd.DataFrame(dados)
    
    # Aplicar estilo com fundo verde claro
    def estilo_acerto(row):
        return ['background-color: #e6ffe6'] * len(row)
    
    df_styled = df.style.apply(estilo_acerto, axis=1)
    
    st.dataframe(
        df_styled,
        width='stretch',
        hide_index=True,
        column_config={
            'Q': st.column_config.NumberColumn('Q', width='small', help='Número da questão'),
            'Resp': st.column_config.TextColumn('Resp', width='small', help='Sua resposta (correta!)'),
            'Gab': st.column_config.TextColumn('Gab', width='small', help='Gabarito correto'),
            'b': st.column_config.TextColumn('b', width='small', help='Dificuldade (quanto maior, mais difícil)'),
            'Perda': st.column_config.TextColumn('Perda', width='small', help='Pontos que você perderia se errasse'),
        }
    )
