# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de exibição de resultados para o Streamlit.
"""

import streamlit as st
from typing import Dict, List

from .graficos import (
    grafico_notas_barras, 
    grafico_impacto, 
    grade_questoes,
    grafico_pizza_acertos,
)


# Nomes completos das áreas
NOMES_AREAS = {
    'LC': 'Linguagens e Códigos',
    'CH': 'Ciências Humanas',
    'CN': 'Ciências da Natureza',
    'MT': 'Matemática',
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
                value=f"{r['nota']:.1f}",
                delta=f"{r['acertos']}/{r['total_itens']} acertos",
                delta_color="off"
            )
    
    with cols[-1]:
        st.metric(
            label="MÉDIA",
            value=f"{media:.1f}",
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

    # Aviso de calibração discreto (sem fundo colorido) com detalhes explicativos
    exibir_aviso_acuracia(resultado)


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


# Cores legíveis de alto contraste para calibração em tema claro (WCAG AA/AAA)
COR_CALIBRACAO_BOA = "#15803D"        # Verde escuro (boa calibração)
COR_CALIBRACAO_MODERADA = "#B45309"   # Amarelo/Âmbar escuro legível (calibração moderada/estimada)
COR_CALIBRACAO_RUIM = "#B91C1C"       # Vermelho escuro (calibração ruim/indisponível)


def formatar_aviso_curto(resultado: Dict) -> str:
    """
    Retorna uma frase no formato 'Esta prova tem uma calibração [X] (detalhes)'.
    O termo [X] é formatado em negrito com cores legíveis de alto contraste:
      - Verde (#15803D): boa
      - Amarelo/Âmbar (#B45309): moderada / por ajuste médio / não verificada / estimada
      - Vermelho (#B91C1C): ruim / indisponível
    """
    if not resultado.get('aviso_precisao') and not resultado.get('severidade_precisao'):
        return ""

    status = resultado.get('status_precisao')
    perfil = resultado.get('perfil_precisao')
    severidade = resultado.get('severidade_precisao')

    if status == 'ok' or perfil == 'calibracao_verificada' or severidade == 'sucesso':
        x = f'<span style="color: {COR_CALIBRACAO_BOA}; font-weight: bold;">boa</span>'
        return f"Esta prova tem uma calibração {x} (estimativa verificada em dados oficiais)."

    if perfil == 'boa_na_maioria_com_excecoes':
        x = f'<span style="color: {COR_CALIBRACAO_MODERADA}; font-weight: bold;">moderada</span>'
        return f"Esta prova tem uma calibração {x} (confiável na maioria dos casos)."

    if status == 'sem_participantes':
        x = f'<span style="color: {COR_CALIBRACAO_MODERADA}; font-weight: bold;">por ajuste médio</span>'
        return f"Esta prova tem uma calibração {x} (participantes insuficientes nos microdados)."

    if status == 'sem_itens':
        x = f'<span style="color: {COR_CALIBRACAO_RUIM}; font-weight: bold;">não possui calibração</span>'
        return f"Esta prova {x} (parâmetros dos itens ausentes nos dados públicos)."

    if status == 'nao_calibrado':
        x = f'<span style="color: {COR_CALIBRACAO_MODERADA}; font-weight: bold;">não possui calibração verificada</span>'
        return f"Esta prova {x} (amostra insuficiente para validação)."

    if severidade == 'alerta' or status == 'erro_alto':
        x = f'<span style="color: {COR_CALIBRACAO_RUIM}; font-weight: bold;">ruim</span>'
        return f"Esta prova tem uma calibração {x} (estimativa com variação relevante)."

    if severidade == 'atencao' or status in {'aviso_forte', 'aviso_leve'}:
        x = f'<span style="color: {COR_CALIBRACAO_MODERADA}; font-weight: bold;">estimada</span>'
        return f"Esta prova tem uma calibração {x} (sujeita a variações)."

    x = f'<span style="color: {COR_CALIBRACAO_MODERADA}; font-weight: bold;">estimada</span>'
    return f"Esta prova tem uma calibração {x}."


def exibir_aviso_acuracia(resultado: Dict):
    """
    Exibe a mensagem curta de calibração e expander nativo com métricas detalhadas.
    """
    frase = formatar_aviso_curto(resultado)
    if not frase:
        return

    st.markdown(frase, unsafe_allow_html=True)

    n_validacao = resultado.get('n_validacao')
    mae = resultado.get('mae_validacao') if resultado.get('mae_validacao') is not None else resultado.get('mae')
    erro_p95 = resultado.get('erro_p95')
    erro_maximo = resultado.get('erro_maximo')
    n_acima_2 = resultado.get('n_acima_2')
    percentual_ate_2 = resultado.get('percentual_ate_2')
    modelo = resultado.get('modelo_nota')
    status = resultado.get('status_precisao')
    co_prova = resultado.get('co_prova')
    aviso = resultado.get('aviso_precisao')

    with st.expander("Mais detalhes da calibração", expanded=False):
        if n_validacao:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Casos Reais", f"{n_validacao}")
            c1.caption("participantes avaliados")

            mae_str = f"{mae:.2f} pts".replace('.', ',') if mae is not None else "—"
            c2.metric("Erro Médio", mae_str)
            c2.caption("diferença média para nota oficial")

            p95_str = f"até {erro_p95:.2f} pts".replace('.', ',') if erro_p95 is not None else "—"
            c3.metric("95% dos Casos", p95_str)
            c3.caption("erro da grande maioria")

            max_str = f"{erro_maximo:.2f} pts".replace('.', ',') if erro_maximo is not None else "—"
            c4.metric("Maior Erro", max_str)
            c4.caption("pior caso observado")

            info_items = []
            if percentual_ate_2 is not None:
                casos_ok = n_validacao - (n_acima_2 or 0)
                pct_str = f"{percentual_ate_2:.1f}%".replace('.', ',')
                info_items.append(f"**{pct_str} dos casos** com erro ≤ 2,0 pts ({casos_ok}/{n_validacao})")
            if co_prova:
                info_items.append(f"Prova {co_prova}")
            if modelo:
                info_items.append(f"Ajuste TRI: {modelo}")
            info_items.append("Microdados oficiais do INEP")
            st.caption(" · ".join(info_items))
        else:
            if status == 'sem_participantes':
                st.caption("Prova sem participantes suficientes nos microdados do INEP. Aplicado ajuste médio.")
            elif status == 'nao_calibrado':
                st.caption("Amostra insuficiente para validação completa. Calculado como estimativa padrão.")
            elif status == 'sem_itens':
                st.caption("Parâmetros dos itens indisponíveis nos dados públicos.")
            elif aviso:
                st.caption(aviso)
