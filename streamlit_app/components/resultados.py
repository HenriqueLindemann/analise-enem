# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de exibição de resultados para o Streamlit.
"""

import streamlit as st
from typing import Dict, List

from tri_enem import MapeadorProvas, normalizar_posicoes_resultados
from tri_enem.formatacao import formatar_numero
from tri_enem.precisao import formatar_aviso_curto as _formatar_aviso_curto_tri

from ..config import AREAS_ENEM
from .graficos import (
    grafico_notas_barras, 
    grafico_impacto, 
    grade_questoes,
    grafico_pizza_acertos,
)


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
                value=formatar_numero(r['nota']),
                delta=f"{r['acertos']}/{r['total_itens']} acertos",
                delta_color="off"
            )
    
    with cols[-1]:
        st.metric(
            label="MÉDIA GERAL SIMPLES",
            value=formatar_numero(media),
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
    resultado = normalizar_posicoes_resultados(
        [resultado],
        MapeadorProvas().listar_ordem_provas(resultado.get('ano', 2024)),
    )[0]
    sigla = resultado['sigla']
    nome = AREAS_ENEM.get(sigla, sigla)

    # Preparar dados das questões
    questoes_acertadas = resultado.get('questoes_acertadas', [])
    questoes_erradas = resultado.get('questoes_erradas', [])
    questoes_anuladas = resultado.get('anuladas', []) or [
        {'posicao': posicao}
        for posicao in resultado.get('questoes_anuladas', [])
    ]
    
    # Converter para formato esperado pelos gráficos
    todas_questoes = []
    for q in questoes_acertadas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': True,
            'anulada': False,
            'gabarito': q['gabarito'],
            'resposta_dada': q['resposta_dada'],
            'impacto': q.get('perda_se_errasse', 0),
            'param_b': q.get('param_b', 0),
        })
    for q in questoes_erradas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': False,
            'anulada': False,
            'gabarito': q['gabarito'],
            'resposta_dada': q['resposta_dada'],
            'impacto': q.get('ganho_se_acertasse', 0),
            'param_b': q.get('param_b', 0),
        })
    for q in questoes_anuladas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': False,
            'anulada': True,
            'gabarito': q.get('gabarito', 'X'),
            'resposta_dada': q.get('resposta_dada', '.'),
            'impacto': 0,
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
        total_validos = max(0, resultado.get('total_itens', 0))
        acertos_validos = max(0, resultado.get('acertos', 0))
        erros_validos = max(0, total_validos - acertos_validos)
        st.plotly_chart(
            grafico_pizza_acertos(acertos_validos, erros_validos),
            key=f"pizza_{sigla}",
            config={'displayModeBar': False}
        )
        taxa_pct = (acertos_validos / total_validos * 100) if total_validos > 0 else 0
        st.markdown(
            f'<div class="taxa-pizza">Taxa: {formatar_numero(taxa_pct, 0)}%</div>',
            unsafe_allow_html=True,
        )
    
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
            'b': formatar_numero(q.get('param_b', 0), 2, sinal=True),
            'Ganho': formatar_numero(q.get('ganho_se_acertasse', 0), sinal=True),
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
            'b': formatar_numero(q.get('param_b', 0), 2, sinal=True),
            'Perda': f"-{formatar_numero(q.get('perda_se_errasse', 0))}",
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


def formatar_aviso_curto(resultado: Dict) -> str:
    """
    Retorna a mensagem breve de confiabilidade usada também no PDF.

    Somente o estado da estimativa recebe cor e negrito; o restante permanece
    neutro para preservar a hierarquia visual e a acessibilidade.
    """
    return _formatar_aviso_curto_tri(resultado, formato="html")


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

    with st.expander("Mais detalhes sobre a precisão", expanded=False):
        if n_validacao:
            st.caption(f"Validada em {n_validacao} resultados oficiais.")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Resultados oficiais", f"{n_validacao}")
            c1.caption("usados na validação")

            mae_str = f"{formatar_numero(mae, 2)} pts" if mae is not None else "—"
            c2.metric("Erro absoluto médio", mae_str)
            c2.caption("diferença média para nota oficial")

            p95_str = f"até {formatar_numero(erro_p95, 2)} pts" if erro_p95 is not None else "—"
            c3.metric("95% das estimativas", p95_str)
            c3.caption("diferença para a nota oficial")

            max_str = f"{formatar_numero(erro_maximo, 2)} pts" if erro_maximo is not None else "—"
            c4.metric("Maior diferença", max_str)
            c4.caption("maior valor observado")

            info_items = []
            if percentual_ate_2 is not None:
                casos_ok = n_validacao - (n_acima_2 or 0)
                pct_str = f"{formatar_numero(percentual_ate_2)}%"
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
