"""
Tabelas para o relatório PDF.

Tabelas de erros, acertos e resumos.
"""

from typing import List
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import cm

from .estilos import Cores
from .base import QuestaoAnalise


def tabela_erros_completa(erros: List[QuestaoAnalise], largura_max: float = 450) -> Table:
    """
    Tabela com TODOS os erros ordenados por impacto.
    Compacta: fonte pequena, padding mínimo.
    """
    if not erros:
        return None
    
    # Ordenar por impacto
    erros_ord = sorted(erros, key=lambda q: q.impacto, reverse=True)
    
    # Cabeçalho
    dados = [['#', 'Q', 'Você', 'Gab.', 'b', 'Impacto']]
    
    for i, q in enumerate(erros_ord, 1):
        dados.append([
            str(i),
            str(q.posicao),
            q.resposta_dada,
            q.gabarito,
            f'{q.param_b:+.1f}',
            f'+{q.impacto:.1f}'
        ])
    
    # Larguras proporcionais
    col_widths = [0.6*cm, 0.8*cm, 0.9*cm, 0.9*cm, 1.0*cm, 1.2*cm]
    
    tabela = Table(dados, colWidths=col_widths)
    
    estilo = [
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), Cores.ERRO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 6),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Corpo
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        
        # Padding mínimo
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.3, Cores.CINZA_CLARO),
        
        # Alternância de cores
    ]
    
    # Adicionar alternância de fundo
    for i in range(1, len(dados)):
        if i % 2 == 0:
            estilo.append(('BACKGROUND', (0, i), (-1, i), Cores.CINZA_MUITO_CLARO))
    
    tabela.setStyle(TableStyle(estilo))
    
    return tabela


def tabela_resumo_areas(areas, largura_max: float = 450) -> Table:
    """
    Tabela resumo compacta com todas as áreas.
    """
    dados = [['Área', 'Nota', 'Acertos', '%']]
    
    for area in areas:
        pct = (area.acertos / area.total_itens * 100) if area.total_itens > 0 else 0
        dados.append([
            f"{area.sigla} - {area.nome[:20]}",
            f'{area.nota:.1f}',
            f'{area.acertos}/{area.total_itens}',
            f'{pct:.0f}%'
        ])
    
    # Média
    if areas:
        media = sum(a.nota for a in areas) / len(areas)
        total_a = sum(a.acertos for a in areas)
        total_q = sum(a.total_itens for a in areas)
        pct_total = (total_a / total_q * 100) if total_q > 0 else 0
        dados.append(['MÉDIA', f'{media:.1f}', f'{total_a}/{total_q}', f'{pct_total:.0f}%'])
    
    col_widths = [5*cm, 1.5*cm, 2*cm, 1.2*cm]
    tabela = Table(dados, colWidths=col_widths)
    
    estilo = [
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), Cores.PRIMARIA),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Corpo
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        
        # Última linha (média)
        ('BACKGROUND', (0, -1), (-1, -1), Cores.CINZA_CLARO),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_CLARO),
    ]
    
    tabela.setStyle(TableStyle(estilo))
    return tabela
