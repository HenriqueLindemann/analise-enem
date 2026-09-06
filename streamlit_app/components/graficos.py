# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Visualizações para o Streamlit: gráficos em Plotly e a grade de
questões em HTML/CSS (leve, responsiva e acessível sem canvas).
"""

import plotly.graph_objects as go
from typing import List, Dict
import numpy as np
import html

from tri_enem.formatacao import formatar_numero


# Cores consistentes - Paleta minimalista
COR_ACERTO = '#27AE60'        # Verde esmeralda
COR_ACERTO_ESCURO = '#1E8449'
COR_ERRO = '#E74C3C'          # Vermelho coral
COR_ERRO_ESCURO = '#C0392B'
COR_ANULADA = '#94A3B8'       # Cinza ardósia (anulada)
COR_ANULADA_ESCURO = '#64748B'
COR_PRIMARIA = '#3498DB'      # Azul suave
COR_SECUNDARIA = '#9B59B6'    # Roxo
COR_CINZA = '#7F8C8D'
COR_CINZA_CLARO = '#BDC3C7'
COR_FUNDO = '#FAFAFA'

# Cores da Grade de Questões (alinhadas ao CSS e relatório PDF)
COR_GRADE_ACERTO = '#23845a'
COR_GRADE_ERRO = '#c84b45'


def grafico_notas_barras(resultados: List[Dict]) -> go.Figure:
    """
    Gráfico de barras horizontais mostrando nota de cada área.
    
    Args:
        resultados: Lista de dicts com 'sigla', 'nome', 'nota', 'acertos', 'total_itens'
        
    Returns:
        Figura Plotly
    """
    if not resultados:
        return go.Figure()
    
    siglas = [r['sigla'] for r in resultados]
    notas = [r['nota'] for r in resultados]
    limite_superior = max(
        1000, int(np.ceil((max(notas) * 1.10) / 100.0) * 100)
    )
    acertos = [f"{r['acertos']}/{r['total_itens']}" for r in resultados]
    
    # Cores baseadas na nota
    cores = []
    for n in notas:
        if n >= 700:
            cores.append(COR_ACERTO)
        elif n >= 500:
            cores.append(COR_PRIMARIA)
        else:
            cores.append(COR_ERRO)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=siglas,
        x=notas,
        orientation='h',
        marker_color=cores,
        text=[f"{formatar_numero(n)} pts ({a})" for n, a in zip(notas, acertos)],
        customdata=[formatar_numero(n) for n in notas],
        textposition='outside',
        textfont=dict(size=12, color='#2C3E50'),
        hovertemplate="<b>%{y}</b><br>Nota: %{customdata} pontos<extra></extra>"
    ))
    
    # Linhas de referência
    fig.add_vline(x=500, line_dash="dash", line_color=COR_CINZA_CLARO, opacity=0.5)
    fig.add_vline(x=700, line_dash="dash", line_color=COR_CINZA_CLARO, opacity=0.5)
    
    # Média
    media = sum(notas) / len(notas)
    fig.add_vline(x=media, line_dash="solid", line_color=COR_SECUNDARIA, 
                  line_width=2, opacity=0.8,
                  annotation_text=f"Média: {formatar_numero(media)}",
                  annotation_position="top")
    
    fig.update_layout(
        title=dict(
            text="",
            font=dict(size=1)
        ),
        xaxis=dict(
            title="Nota",
            range=[0, limite_superior],
            tickvals=sorted({0, 500, 700, 1000, limite_superior}),
            gridcolor=COR_CINZA_CLARO,
            gridwidth=0.5,
        ),
        yaxis=dict(
            title=None,
            categoryorder='array',
            categoryarray=list(reversed(siglas))
        ),
        height=200,
        margin=dict(l=40, r=80, t=20, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif"),
    )
    
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def grafico_impacto(questoes: List[Dict], titulo: str = "") -> go.Figure:
    """
    Gráfico de impacto das questões (maior para menor).
    Questões anuladas são desconsideradas.
    
    Args:
        questoes: Lista de dicts com 'posicao', 'impacto', 'acertou'
        titulo: Título opcional
        
    Returns:
        Figura Plotly
    """
    questoes_validas = [q for q in questoes if not q.get('anulada')]
    if not questoes_validas:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Ordenar por impacto decrescente
    questoes_ord = sorted(questoes_validas, key=lambda q: q['impacto'], reverse=True)
    
    posicoes = [str(q['posicao']) for q in questoes_ord]
    valores = [q['impacto'] for q in questoes_ord]
    cores = [COR_GRADE_ACERTO if q['acertou'] else COR_GRADE_ERRO for q in questoes_ord]
    max_valor = max(max(valores), 1.0) if valores else 1.0
    # Em itens muito difíceis acertados, o impacto pode ser levemente
    # negativo; incluir esse piso no eixo em vez de cortar a barra.
    min_valor = min(min(valores), 0.0)
    
    # Texto de hover
    hover_texts = []
    for q in questoes_ord:
        status = "Acerto" if q['acertou'] else "Erro"
        if q['acertou']:
            hover_texts.append(
                f"Q{q['posicao']} ({status})<br>Perda se errasse: "
                f"{formatar_numero(q['impacto'])} pts"
            )
        else:
            hover_texts.append(
                f"Q{q['posicao']} ({status})<br>Ganho se acertasse: "
                f"{formatar_numero(q['impacto'])} pts"
            )
    
    # Rótulo de questão vertical acima de cada barra (inspirado no relatório PDF)
    rotulos = [str(q['posicao']) for q in questoes_ord]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(range(len(posicoes))),
        y=valores,
        marker_color=cores,
        text=rotulos,
        textposition='outside',
        textangle=-90,
        textfont=dict(size=11, color=cores, family="Helvetica, Arial, sans-serif"),
        cliponaxis=False,
        hovertext=hover_texts,
        hoverinfo='text',
    ))

    margem_topo = 40 if titulo else 20
    topo_y = max(max_valor * 1.15, 1.0)

    annotations = [
        dict(
            text="<i><b>⬅ maior impacto</b></i>",
            x=0.25,
            xref="paper",
            y=-0.12,
            yref="paper",
            showarrow=False,
            font=dict(size=12, color='#7F8C8D', family="Helvetica, Arial, sans-serif"),
            xanchor="center",
        ),
        dict(
            text="<i><b>menor impacto ➡</b></i>",
            x=0.75,
            xref="paper",
            y=-0.12,
            yref="paper",
            showarrow=False,
            font=dict(size=12, color='#7F8C8D', family="Helvetica, Arial, sans-serif"),
            xanchor="center",
        ),
    ]

    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)) if titulo else dict(text="", font=dict(size=1)),
        annotations=annotations,
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
        ),
        yaxis=dict(
            title=dict(text="Pontos", font=dict(size=12, color='#2C3E50')),
            tickfont=dict(size=11, color='#64748B'),
            gridcolor='#E2E8F0',
            gridwidth=0.5,
            zeroline=True,
            zerolinecolor='#CBD5E1',
            zerolinewidth=0.8,
            range=[min_valor, topo_y],
        ),
        height=320,
        margin=dict(l=45, r=45, t=margem_topo, b=45),
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
    )
    
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def grade_questoes(questoes: List[Dict]) -> str:
    """Grade compacta com cores e padrões do PDF, além da descrição acessível."""
    celulas = []
    for q in sorted(questoes, key=lambda q: q['posicao']):
        if q.get('anulada'):
            classe, estado = 'anulada', 'Anulada pelo INEP'
            descricao = f"Q{q['posicao']}: {estado}. Desconsiderada no cálculo TRI."
        else:
            classe, estado = ('acerto', 'Acerto') if q['acertou'] else ('erro', 'Erro')
            descricao = (f"Q{q['posicao']}: {estado}. Gabarito: {q.get('gabarito', '?')}. "
                         f"Resposta: {q.get('resposta_dada', '?')}.")
        descricao = html.escape(descricao, quote=True)
        numero = html.escape(str(q['posicao']))
        celulas.append(
            f'<div class="questao questao--{classe}" role="listitem" '
            f'aria-label="{descricao}" title="{descricao}">{numero}</div>'
        )
    return ('<div class="grade-questoes" role="list" aria-label="Grade de questões">'
            + ''.join(celulas) + '</div>')


def grafico_pizza_acertos(acertos: int, erros: int) -> go.Figure:
    """
    Gráfico de pizza simples mostrando proporção acertos/erros.
    
    Args:
        acertos: Número de acertos
        erros: Número de erros
        
    Returns:
        Figura Plotly
    """
    if acertos < 0 or erros < 0:
        raise ValueError("acertos e erros devem ser não negativos")

    total = acertos + erros
    if total == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Sem dados",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(
            height=200,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
        return fig

    fig = go.Figure(data=[go.Pie(
        labels=['Acertos', 'Erros'],
        values=[acertos, erros],
        hole=0.4,
        marker_colors=[COR_ACERTO, COR_ERRO],
        textinfo='label+value',
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value} questões<br>%{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        annotations=[dict(
            text=f'{acertos}/{total}',
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )]
    )
    
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig
