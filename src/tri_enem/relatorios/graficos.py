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


# Cores consistentes - Paleta minimalista
COR_ACERTO = '#27AE60'        # Verde esmeralda
COR_ACERTO_ESCURO = '#1E8449'
COR_ERRO = '#E74C3C'          # Vermelho coral
COR_ERRO_ESCURO = '#C0392B'
COR_PRIMARIA = '#3498DB'      # Azul suave
COR_CINZA = '#7F8C8D'
COR_CINZA_CLARO = '#BDC3C7'
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
    Barras horizontais minimalistas mostrando nota de cada área.
    Design limpo com cores suaves.
    """
    fig, ax = plt.subplots(figsize=(largura, 1.4))
    
    siglas = [a.sigla for a in areas]
    notas = [a.nota for a in areas]
    
    # Cores baseadas na nota - gradiente suave
    cores = []
    for n in notas:
        if n >= 700:
            cores.append(COR_ACERTO)
        elif n >= 500:
            cores.append(COR_PRIMARIA)
        else:
            cores.append(COR_ERRO)
    
    y_pos = np.arange(len(areas))
    
    # Barras com bordas arredondadas via alpha
    bars = ax.barh(y_pos, notas, color=cores, height=0.55, alpha=0.85, 
                   edgecolor='white', linewidth=0.5)
    
    # Linhas de referência sutis
    ax.axvline(x=500, color=COR_CINZA_CLARO, linestyle='-', linewidth=0.5, alpha=0.5)
    ax.axvline(x=700, color=COR_CINZA_CLARO, linestyle='-', linewidth=0.5, alpha=0.5)
    
    # Labels - fonte limpa
    ax.set_yticks(y_pos)
    ax.set_yticklabels(siglas, fontsize=9, fontweight='medium', color='#2C3E50')
    ax.set_xlim(0, 1000)
    ax.set_xticks([0, 500, 700, 1000])
    ax.tick_params(axis='x', labelsize=7, colors=COR_CINZA)
    
    # Valores nas barras - discretos
    for bar, nota, area in zip(bars, notas, areas):
        ax.text(nota + 12, bar.get_y() + bar.get_height()/2, 
                f'{nota:.0f}', 
                va='center', fontsize=8, fontweight='medium', color='#2C3E50')
    
    # Remover bordas - minimalista
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    
    plt.tight_layout(pad=0.3)
    return _fig_para_image(fig, largura)


def grafico_impacto_questoes(questoes: List[QuestaoAnalise], titulo: str = "", 
                              largura: float = 7.5) -> Image:
    """
    Gráfico de impacto minimalista.
    Design limpo com números sutis.
    """
    if not questoes:
        fig, ax = plt.subplots(figsize=(largura, 0.5))
        ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color=COR_CINZA)
        ax.axis('off')
        return _fig_para_image(fig, largura)
    
    # Ordenar por impacto DECRESCENTE
    questoes_ord = sorted(questoes, key=lambda q: q.impacto, reverse=True)
    
    n = len(questoes_ord)
    fig, ax = plt.subplots(figsize=(largura, 2.0))
    
    x_pos = np.arange(n)
    valores = [q.impacto for q in questoes_ord]
    max_valor = max(valores) if valores else 1
    
    # Cores suaves
    cores = [COR_ACERTO if q.acertou else COR_ERRO for q in questoes_ord]
    
    # Barras com transparência
    bar_width = 0.80
    bars = ax.bar(x_pos, valores, color=cores, width=bar_width, alpha=0.8, 
                  edgecolor='white', linewidth=0.3)
    
    # Números das questões - mais discretos
    for i, (bar, q) in enumerate(zip(bars, questoes_ord)):
        y_pos = bar.get_height() + max_valor * 0.02
        cor_texto = COR_ACERTO_ESCURO if q.acertou else COR_ERRO_ESCURO
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, str(q.posicao),
                ha='center', va='bottom', fontsize=5, fontweight='medium',
                color=cor_texto, rotation=90)
    
    ax.set_ylim(0, max_valor * 1.22)
    ax.set_xticks([])
    ax.set_xlabel('← maior impacto                                                menor impacto →', 
                  fontsize=6, color=COR_CINZA, style='italic')
    ax.set_ylabel('')
    
    ax.tick_params(axis='y', labelsize=6, colors=COR_CINZA)
    
    # Grid muito sutil
    ax.yaxis.grid(True, linestyle='-', alpha=0.15, color=COR_CINZA_CLARO)
    ax.set_axisbelow(True)
    
    # Estilo minimalista
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_linewidth(0.3)
    ax.spines['left'].set_color(COR_CINZA_CLARO)
    
    # Legenda compacta e discreta
    patches = [
        mpatches.Patch(color=COR_ACERTO, label='Acerto', alpha=0.8),
        mpatches.Patch(color=COR_ERRO, label='Erro', alpha=0.8),
    ]
    ax.legend(handles=patches, loc='upper right', fontsize=6, framealpha=0.95,
              handlelength=0.8, handleheight=0.6, edgecolor='none', 
              facecolor='white')
    
    plt.tight_layout(pad=0.2)
    return _fig_para_image(fig, largura)


def grade_questoes(questoes: List[QuestaoAnalise], largura: float = 6, 
                   colunas: int = 15) -> Image:
    """
    Grade visual minimalista das questões.
    Design limpo com bordas arredondadas.
    """
    n = len(questoes)
    if n == 0:
        fig, ax = plt.subplots(figsize=(largura, 0.5))
        ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', color=COR_CINZA)
        ax.axis('off')
        return _fig_para_image(fig, largura)
    
    linhas = (n + colunas - 1) // colunas
    questoes_ord = sorted(questoes, key=lambda q: q.posicao)
    
    # Figura proporcional - mais compacta
    altura = max(0.5, linhas * 0.32)
    fig, ax = plt.subplots(figsize=(largura, altura))
    
    for i, q in enumerate(questoes_ord):
        col = i % colunas
        linha = linhas - 1 - (i // colunas)
        
        cor_fundo = COR_ACERTO if q.acertou else COR_ERRO
        
        # Retângulo com bordas mais arredondadas
        rect = mpatches.FancyBboxPatch(
            (col + 0.08, linha + 0.12), 0.84, 0.76,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor=cor_fundo, edgecolor='white', linewidth=0.8, alpha=0.75
        )
        ax.add_patch(rect)
        
        # Número - fonte mais leve
        ax.text(col + 0.5, linha + 0.5, str(q.posicao), 
                ha='center', va='center', fontsize=7, fontweight='medium',
                color='white')
    
    ax.set_xlim(-0.05, colunas + 0.05)
    ax.set_ylim(-0.05, linhas + 0.05)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout(pad=0.05)
    return _fig_para_image(fig, largura)


def legenda_grafico_impacto() -> str:
    """Retorna texto da legenda do gráfico de impacto."""
    return "Verde = acerto · Vermelho = erro"
