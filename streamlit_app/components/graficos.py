# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Visualizações gráficas para o Streamlit usando Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
import numpy as np


# Cores consistentes - Paleta minimalista
COR_ACERTO = '#27AE60'        # Verde esmeralda
COR_ACERTO_ESCURO = '#1E8449'
COR_ERRO = '#E74C3C'          # Vermelho coral
COR_ERRO_ESCURO = '#C0392B'
COR_PRIMARIA = '#3498DB'      # Azul suave
COR_SECUNDARIA = '#9B59B6'    # Roxo
COR_CINZA = '#7F8C8D'
COR_CINZA_CLARO = '#BDC3C7'
COR_FUNDO = '#FAFAFA'


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
        text=[f"{n:.0f} pts ({a})" for n, a in zip(notas, acertos)],
        textposition='outside',
        textfont=dict(size=12, color='#2C3E50'),
        hovertemplate="<b>%{y}</b><br>Nota: %{x:.1f} pontos<extra></extra>"
    ))
    
    # Linhas de referência
    fig.add_vline(x=500, line_dash="dash", line_color=COR_CINZA_CLARO, opacity=0.5)
    fig.add_vline(x=700, line_dash="dash", line_color=COR_CINZA_CLARO, opacity=0.5)
    
    # Média
    media = sum(notas) / len(notas)
    fig.add_vline(x=media, line_dash="solid", line_color=COR_SECUNDARIA, 
                  line_width=2, opacity=0.8,
                  annotation_text=f"Média: {media:.0f}",
                  annotation_position="top")
    
    fig.update_layout(
        title=dict(
            text="",
            font=dict(size=1)
        ),
        xaxis=dict(
            title="Nota",
            range=[0, 1000],
            tickvals=[0, 500, 700, 1000],
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
    
    return fig


def grafico_impacto(questoes: List[Dict], titulo: str = "") -> go.Figure:
    """
    Gráfico de impacto das questões (maior para menor).
    
    Args:
        questoes: Lista de dicts com 'posicao', 'impacto', 'acertou'
        titulo: Título opcional
        
    Returns:
        Figura Plotly
    """
    if not questoes:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Ordenar por impacto decrescente
    questoes_ord = sorted(questoes, key=lambda q: q['impacto'], reverse=True)
    
    posicoes = [str(q['posicao']) for q in questoes_ord]
    valores = [q['impacto'] for q in questoes_ord]
    cores = [COR_ACERTO if q['acertou'] else COR_ERRO for q in questoes_ord]
    
    # Texto de hover
    hover_texts = []
    for q in questoes_ord:
        status = "Acerto" if q['acertou'] else "Erro"
        if q['acertou']:
            hover_texts.append(f"Q{q['posicao']} ({status})<br>Perda se errasse: {q['impacto']:.1f} pts")
        else:
            hover_texts.append(f"Q{q['posicao']} ({status})<br>Ganho se acertasse: {q['impacto']:.1f} pts")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=list(range(len(posicoes))),
        y=valores,
        marker_color=cores,
        marker_opacity=0.85,
        text=posicoes,
        textposition='outside',
        textfont=dict(size=8),
        hovertext=hover_texts,
        hoverinfo='text',
    ))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)),
        xaxis=dict(
            title="← maior impacto                                  menor impacto →",
            showticklabels=False,
            showgrid=False,
        ),
        yaxis=dict(
            title="Pontos",
            gridcolor=COR_CINZA_CLARO,
            gridwidth=0.5,
        ),
        height=280,
        margin=dict(l=50, r=20, t=40, b=50),
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
    )
    
    return fig


def grade_questoes(questoes: List[Dict], colunas: int = 15) -> go.Figure:
    """
    Grade visual das questões (acertos/erros).
    
    Args:
        questoes: Lista de dicts com 'posicao', 'acertou'
        colunas: Número de colunas na grade
        
    Returns:
        Figura Plotly
    """
    if not questoes:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Ordenar por posição
    questoes_ord = sorted(questoes, key=lambda q: q['posicao'])
    n = len(questoes_ord)
    linhas = (n + colunas - 1) // colunas
    
    # Calcular taxa de acertos para ajustar altura
    acertos = sum(1 for q in questoes_ord if q['acertou'])
    taxa_acertos = acertos / n if n > 0 else 0.5
    
    fig = go.Figure()
    
    # Criar dados para heatmap-like visualization
    for i, q in enumerate(questoes_ord):
        col = i % colunas
        linha = linhas - 1 - (i // colunas)
        
        cor = COR_ACERTO if q['acertou'] else COR_ERRO
        status = "✓ Acerto" if q['acertou'] else "✗ Erro"
        
        fig.add_trace(go.Scatter(
            x=[col + 0.5],
            y=[linha + 0.5],
            mode='markers+text',
            marker=dict(
                size=40,
                color=cor,
                symbol='square',
                opacity=0.8,
                line=dict(color='white', width=2)
            ),
            text=[str(q['posicao'])],
            textposition='middle center',
            textfont=dict(color='white', size=11, family="Arial", weight='bold'),
            hovertext=f"Q{q['posicao']}: {status}<br>Gabarito: {q.get('gabarito', '?')}<br>Resposta: {q.get('resposta_dada', '?')}",
            hoverinfo='text',
            showlegend=False,
        ))
    
    # Ajustar altura baseada em linhas e taxa de acertos
    # Mais acertos = gráfico mais alto proporcionalmente
    altura_base = max(200, linhas * 60)
    altura_ajustada = altura_base * (0.7 + 0.6 * taxa_acertos)
    
    fig.update_layout(
        xaxis=dict(
            range=[0, colunas],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            range=[0, linhas],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            scaleanchor='x',
        ),
        height=int(altura_ajustada),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='white',
        plot_bgcolor='white',
    )
    
    return fig


def grafico_pizza_acertos(acertos: int, erros: int) -> go.Figure:
    """
    Gráfico de pizza simples mostrando proporção acertos/erros.
    
    Args:
        acertos: Número de acertos
        erros: Número de erros
        
    Returns:
        Figura Plotly
    """
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
            text=f'{acertos}/{acertos+erros}',
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )]
    )
    
    return fig


def grafico_comparativo_areas(resultados: List[Dict]) -> go.Figure:
    """
    Gráfico radar comparando as áreas.
    
    Args:
        resultados: Lista de dicts com 'sigla', 'nota'
        
    Returns:
        Figura Plotly
    """
    if not resultados:
        return go.Figure()
    
    siglas = [r['sigla'] for r in resultados]
    notas = [r['nota'] for r in resultados]
    
    # Fechar o polígono
    siglas_closed = siglas + [siglas[0]]
    notas_closed = notas + [notas[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=notas_closed,
        theta=siglas_closed,
        fill='toself',
        fillcolor=f'rgba(52, 152, 219, 0.3)',
        line=dict(color=COR_PRIMARIA, width=2),
        hovertemplate="<b>%{theta}</b><br>Nota: %{r:.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1000],
                tickvals=[0, 250, 500, 750, 1000],
            ),
        ),
        height=300,
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=False,
    )
    
    return fig
