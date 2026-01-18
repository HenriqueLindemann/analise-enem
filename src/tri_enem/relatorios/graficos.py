"""
Gráficos para o relatório PDF.

Visualizações: barras de progresso, gráfico de impacto, grade de questões.
"""

from typing import List
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib import colors

from .estilos import Cores
from .base import AreaAnalise, QuestaoAnalise


def grafico_barras_notas(areas: List[AreaAnalise], largura: float = 450, altura: float = 60) -> Drawing:
    """
    Cria barras horizontais de progresso para cada área.
    Compacto: todas as áreas em uma visualização.
    """
    d = Drawing(largura, altura)
    
    n_areas = len(areas)
    altura_barra = 10
    espaco = 5
    y_inicial = altura - 15
    
    for i, area in enumerate(areas):
        y = y_inicial - i * (altura_barra + espaco)
        
        # Label da área
        label = String(0, y, f"{area.sigla}")
        label.fontSize = 8
        label.fontName = 'Helvetica-Bold'
        d.add(label)
        
        # Nota
        nota = String(22, y, f"{area.nota:.0f}")
        nota.fontSize = 8
        nota.fillColor = Cores.PRIMARIA
        d.add(nota)
        
        # Barra de fundo
        x_barra = 50
        largura_barra = 280
        
        fundo = Rect(x_barra, y - 2, largura_barra, altura_barra)
        fundo.fillColor = Cores.BARRA_FUNDO
        fundo.strokeColor = None
        d.add(fundo)
        
        # Barra de progresso
        progresso = min(1.0, area.nota / 1000) * largura_barra
        barra = Rect(x_barra, y - 2, progresso, altura_barra)
        # Gradiente de cor baseado na nota
        if area.nota >= 700:
            cor = Cores.ACERTO
        elif area.nota >= 500:
            cor = colors.HexColor('#FFC107')  # Amarelo
        else:
            cor = Cores.ERRO
        barra.fillColor = cor
        barra.strokeColor = None
        d.add(barra)
        
        # Marcadores 500, 700
        for ref in [500, 700]:
            x_ref = x_barra + (ref / 1000) * largura_barra
            linha = Line(x_ref, y - 4, x_ref, y + altura_barra)
            linha.strokeColor = Cores.LINHA_GRADE
            linha.strokeWidth = 0.5
            d.add(linha)
        
        # Acertos
        pct = (area.acertos / area.total_itens * 100) if area.total_itens > 0 else 0
        info = String(x_barra + largura_barra + 8, y, f"{area.acertos}/{area.total_itens} ({pct:.0f}%)")
        info.fontSize = 7
        info.fillColor = Cores.CINZA
        d.add(info)
    
    return d


def grafico_impacto_erros(erros: List[QuestaoAnalise], largura: float = 450, altura: float = 80) -> Drawing:
    """
    Gráfico de barras verticais mostrando impacto de cada erro.
    Eixo X = número da questão, Eixo Y = impacto (decrescente da esquerda pra direita).
    """
    if not erros:
        return Drawing(largura, 20)
    
    d = Drawing(largura, altura)
    
    # Ordenar por impacto (maior primeiro)
    erros_ord = sorted(erros, key=lambda q: q.impacto, reverse=True)
    
    n_erros = len(erros_ord)
    margem_esq = 25
    margem_dir = 10
    margem_baixo = 18
    margem_cima = 5
    
    area_grafico = largura - margem_esq - margem_dir
    altura_grafico = altura - margem_baixo - margem_cima
    
    # Calcular largura das barras
    largura_barra = min(15, (area_grafico - n_erros) / n_erros)
    espaco = 2
    
    # Encontrar máximo para escala
    max_impacto = max(q.impacto for q in erros_ord)
    
    # Eixo Y (impacto)
    linha_y = Line(margem_esq, margem_baixo, margem_esq, altura - margem_cima)
    linha_y.strokeColor = Cores.CINZA
    linha_y.strokeWidth = 0.5
    d.add(linha_y)
    
    # Eixo X
    linha_x = Line(margem_esq, margem_baixo, largura - margem_dir, margem_baixo)
    linha_x.strokeColor = Cores.CINZA
    linha_x.strokeWidth = 0.5
    d.add(linha_x)
    
    # Label eixo Y
    label_y = String(2, altura - 10, "Impacto")
    label_y.fontSize = 6
    label_y.fillColor = Cores.CINZA
    d.add(label_y)
    
    # Barras
    for i, q in enumerate(erros_ord):
        x = margem_esq + 5 + i * (largura_barra + espaco)
        
        # Altura proporcional ao impacto
        h = (q.impacto / max_impacto) * altura_grafico if max_impacto > 0 else 0
        
        # Barra
        barra = Rect(x, margem_baixo, largura_barra, h)
        # Cor baseada na dificuldade
        if q.param_b < 0:
            barra.fillColor = colors.HexColor('#FF5722')  # Laranja - fácil (prioridade)
        elif q.param_b < 1:
            barra.fillColor = Cores.ERRO  # Vermelho - médio
        else:
            barra.fillColor = colors.HexColor('#9E9E9E')  # Cinza - difícil
        barra.strokeColor = None
        d.add(barra)
        
        # Número da questão (abaixo)
        if n_erros <= 25 or i % 2 == 0:  # Mostrar todos se poucos, senão alternados
            num = String(x + largura_barra/2, margem_baixo - 10, str(q.posicao))
            num.fontSize = 5
            num.textAnchor = 'middle'
            num.fillColor = Cores.CINZA
            d.add(num)
        
        # Valor do impacto no topo (só para os maiores)
        if i < 3:
            val = String(x + largura_barra/2, margem_baixo + h + 2, f"+{q.impacto:.0f}")
            val.fontSize = 5
            val.textAnchor = 'middle'
            val.fillColor = Cores.PRIMARIA
            d.add(val)
    
    return d


def grade_questoes(questoes: List[QuestaoAnalise], largura: float = 450, colunas: int = 15) -> Drawing:
    """
    Grade visual compacta das 45 questões.
    Verde = acerto, Vermelho = erro.
    """
    n_questoes = len(questoes)
    linhas = (n_questoes + colunas - 1) // colunas
    
    celula_w = largura / colunas
    celula_h = 14
    altura = linhas * celula_h + 5
    
    d = Drawing(largura, altura)
    
    # Ordenar por posição
    questoes_ord = sorted(questoes, key=lambda q: q.posicao)
    
    for i, q in enumerate(questoes_ord):
        col = i % colunas
        linha = i // colunas
        
        x = col * celula_w
        y = altura - 5 - linha * celula_h
        
        # Retângulo de fundo
        rect = Rect(x + 1, y - celula_h + 3, celula_w - 2, celula_h - 2)
        if q.acertou:
            rect.fillColor = Cores.ACERTO_CLARO
            rect.strokeColor = Cores.ACERTO
        else:
            rect.fillColor = Cores.ERRO_CLARO
            rect.strokeColor = Cores.ERRO
        rect.strokeWidth = 0.5
        d.add(rect)
        
        # Número da questão
        num = String(x + celula_w/2, y - celula_h/2 - 1, str(q.posicao))
        num.fontSize = 7
        num.textAnchor = 'middle'
        if q.acertou:
            num.fillColor = colors.HexColor('#1B5E20')
        else:
            num.fillColor = colors.HexColor('#B71C1C')
        d.add(num)
    
    return d


def legenda_grafico_impacto() -> str:
    """Retorna texto da legenda do gráfico de impacto."""
    return "Barras ordenadas por impacto (maior → menor) | 🟧 Fácil (prioridade) | 🟥 Médio | ⬜ Difícil"
