# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Gráficos para o relatório PDF usando matplotlib.

Gera imagens que são inseridas no PDF via reportlab.
"""

from typing import List, Optional
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Backend sem GUI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.platypus import Image
from reportlab.lib.units import inch

from .base import AreaAnalise, QuestaoAnalise


# Cores consistentes
COR_ACERTO = '#4CAF50'
COR_ACERTO_ESCURO = '#1B5E20'
COR_ERRO = '#F44336'
COR_ERRO_ESCURO = '#B71C1C'
COR_PRIMARIA = '#1565C0'
COR_CINZA = '#757575'
COR_FUNDO = '#FAFAFA'


def _fig_para_image(fig, largura: float = 6, dpi: int = 300) -> Image:
    """Converte figura matplotlib para Image do reportlab."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    
    # Calcular altura proporcional
    img = Image(buf)
    aspect = img.imageHeight / img.imageWidth
    img.drawWidth = largura * inch
    img.drawHeight = largura * aspect * inch
    
    return img


def grafico_barras_notas(areas: List[AreaAnalise], largura: float = 6) -> Image:
    """
    Barras horizontais mostrando nota de cada área.
    Inclui marcadores em 500 e 700.
    """
    fig, ax = plt.subplots(figsize=(largura, 1.2))
    
    siglas = [a.sigla for a in areas]
    notas = [a.nota for a in areas]
    cores = [COR_ACERTO if n >= 700 else ('#FFC107' if n >= 500 else COR_ERRO) for n in notas]
    
    y_pos = np.arange(len(areas))
    
    # Barras
    bars = ax.barh(y_pos, notas, color=cores, height=0.6, alpha=0.85)
    
    # Linhas de referência
    ax.axvline(x=500, color=COR_CINZA, linestyle='--', linewidth=0.8, alpha=0.5)
    ax.axvline(x=700, color=COR_CINZA, linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(siglas, fontsize=9, fontweight='bold')
    ax.set_xlim(0, 1000)
    ax.set_xticks([0, 250, 500, 700, 1000])
    ax.tick_params(axis='x', labelsize=7)
    
    # Valores nas barras
    for bar, nota, area in zip(bars, notas, areas):
        pct = area.acertos / area.total_itens * 100 if area.total_itens > 0 else 0
        ax.text(nota + 10, bar.get_y() + bar.get_height()/2, 
                f'{nota:.0f}  ({area.acertos}/{area.total_itens})', 
                va='center', fontsize=7, color=COR_CINZA)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(0.5)
    ax.spines['left'].set_visible(False)
    
    plt.tight_layout(pad=0.2)
    return _fig_para_image(fig, largura)


def grafico_impacto_questoes(questoes: List[QuestaoAnalise], titulo: str = "", 
                              largura: float = 7.5) -> Image:
    """
    Gráfico de barras mostrando impacto de TODAS as questões.
    
    - Ordenado por impacto (maior → menor da esquerda pra direita)
    - Eixo Y: módulo do impacto (sempre positivo)
    - Eixo X: número da questão visível acima de cada barra
    - Verde = acerto, Vermelho = erro
    """
    if not questoes:
        fig, ax = plt.subplots(figsize=(largura, 0.5))
        ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center')
        ax.axis('off')
        return _fig_para_image(fig, largura)
    
    # Ordenar por impacto DECRESCENTE
    questoes_ord = sorted(questoes, key=lambda q: q.impacto, reverse=True)
    
    n = len(questoes_ord)
    # Figura mais larga para caber todas as questões
    fig, ax = plt.subplots(figsize=(largura, 2.2))
    
    # Posições no eixo X (0, 1, 2, ...)
    x_pos = np.arange(n)
    
    # Valores = módulo do impacto (sempre positivo)
    valores = [q.impacto for q in questoes_ord]
    max_valor = max(valores) if valores else 1
    
    # Cores: verde para acerto, vermelho para erro
    cores = [COR_ACERTO if q.acertou else COR_ERRO for q in questoes_ord]
    
    # Barras
    bar_width = 0.85
    bars = ax.bar(x_pos, valores, color=cores, width=bar_width, alpha=0.9, edgecolor='none')
    
    # Número da questão ACIMA de cada barra (sempre legível)
    for i, (bar, q) in enumerate(zip(bars, questoes_ord)):
        y_pos = bar.get_height() + max_valor * 0.02
        cor_texto = COR_ACERTO_ESCURO if q.acertou else COR_ERRO_ESCURO
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, str(q.posicao),
                ha='center', va='bottom', fontsize=5.5, fontweight='bold',
                color=cor_texto, rotation=90)
    
    # Ajustar limite Y para caber os números
    ax.set_ylim(0, max_valor * 1.25)
    
    # Remover ticks do eixo X (números já estão acima das barras)
    ax.set_xticks([])
    ax.set_xlabel('Questões ordenadas por impacto (maior → menor)', fontsize=7)
    ax.set_ylabel('Impacto', fontsize=7)
    if titulo:
        ax.set_title(titulo, fontsize=9, fontweight='bold', pad=3)
    
    ax.tick_params(axis='y', labelsize=6)
    
    # Grid horizontal sutil
    ax.yaxis.grid(True, linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Estilo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(0.5)
    ax.spines['left'].set_linewidth(0.5)
    
    # Legenda compacta no canto
    patches = [
        mpatches.Patch(color=COR_ACERTO, label='Acertos'),
        mpatches.Patch(color=COR_ERRO, label='Erros'),
    ]
    ax.legend(handles=patches, loc='upper right', fontsize=6, framealpha=0.9,
              handlelength=1, handleheight=0.7)
    
    plt.tight_layout(pad=0.2)
    return _fig_para_image(fig, largura)


def grade_questoes(questoes: List[QuestaoAnalise], largura: float = 6, 
                   colunas: int = 15) -> Image:
    """
    Grade visual compacta das questões.
    Verde = acerto, Vermelho = erro.
    Mostra número da questão em cada célula.
    """
    n = len(questoes)
    if n == 0:
        fig, ax = plt.subplots(figsize=(largura, 0.5))
        ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center')
        ax.axis('off')
        return _fig_para_image(fig, largura)
    
    linhas = (n + colunas - 1) // colunas
    questoes_ord = sorted(questoes, key=lambda q: q.posicao)
    
    # Figura proporcional
    altura = max(0.6, linhas * 0.35)
    fig, ax = plt.subplots(figsize=(largura, altura))
    
    for i, q in enumerate(questoes_ord):
        col = i % colunas
        linha = linhas - 1 - (i // colunas)  # Inverter para questão 1 ficar em cima
        
        cor_fundo = COR_ACERTO if q.acertou else COR_ERRO
        cor_texto = COR_ACERTO_ESCURO if q.acertou else COR_ERRO_ESCURO
        
        # Retângulo
        rect = mpatches.FancyBboxPatch(
            (col + 0.05, linha + 0.1), 0.9, 0.8,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor=cor_fundo, edgecolor='white', linewidth=1, alpha=0.7
        )
        ax.add_patch(rect)
        
        # Número
        ax.text(col + 0.5, linha + 0.5, str(q.posicao), 
                ha='center', va='center', fontsize=8, fontweight='bold',
                color='white')
    
    ax.set_xlim(-0.1, colunas + 0.1)
    ax.set_ylim(-0.1, linhas + 0.1)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout(pad=0.1)
    return _fig_para_image(fig, largura)


def legenda_grafico_impacto() -> str:
    """Retorna texto da legenda do gráfico de impacto."""
    return "Ordenado por impacto (maior → menor) | Verde = acertos | Vermelho = erros"
