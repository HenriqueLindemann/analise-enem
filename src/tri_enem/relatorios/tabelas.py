# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
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
    Tabela minimalista de erros ordenados por impacto.
    Design limpo sem bordas pesadas.
    """
    if not erros:
        return None
    
    # Ordenar por impacto
    erros_ord = sorted(erros, key=lambda q: q.impacto, reverse=True)
    
    # Cabeçalho com nomes completos
    dados = [['Questão', 'Sua Resp.', 'Gabarito', 'Parâmetro b', 'Ganho Potencial']]
    
    for q in erros_ord:
        dados.append([
            str(q.posicao),
            q.resposta_dada if q.resposta_dada != '.' else '–',
            q.gabarito,
            f'{q.param_b:.2f}',
            f'+{q.impacto:.1f} pts'
        ])
    
    # Larguras proporcionais
    col_widths = [1.3*cm, 1.6*cm, 1.4*cm, 2.0*cm, 2.5*cm]
    
    tabela = Table(dados, colWidths=col_widths)
    
    estilo = [
        # Cabeçalho - discreto
        ('BACKGROUND', (0, 0), (-1, 0), Cores.SECUNDARIA),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Corpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 1), (-1, -1), Cores.SECUNDARIA),
        
        # Coluna de ganho - destaque sutil
        ('FONTNAME', (-1, 1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (-1, 1), (-1, -1), Cores.DESTAQUE),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        
        # Bordas mínimas - apenas linha inferior
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, Cores.SECUNDARIA),
        ('LINEBELOW', (0, 1), (-1, -2), 0.3, Cores.CINZA_CLARO),
    ]
    
    # Alternância de fundo muito sutil
    for i in range(1, len(dados)):
        if i % 2 == 0:
            estilo.append(('BACKGROUND', (0, i), (-1, i), Cores.CINZA_MUITO_CLARO))
    
    tabela.setStyle(TableStyle(estilo))
    
    return tabela


def tabela_resumo_areas(areas, largura_max: float = 450) -> Table:
    """
    Tabela resumo minimalista.
    """
    dados = [['Área', 'Nota', 'Acertos', '%']]
    
    for area in areas:
        pct = (area.acertos / area.total_itens * 100) if area.total_itens > 0 else 0
        dados.append([
            f"{area.sigla} – {area.nome[:18]}",
            f'{area.nota:.0f}',
            f'{area.acertos}/{area.total_itens}',
            f'{pct:.0f}%'
        ])
    
    # Média
    if areas:
        media = sum(a.nota for a in areas) / len(areas)
        total_a = sum(a.acertos for a in areas)
        total_q = sum(a.total_itens for a in areas)
        pct_total = (total_a / total_q * 100) if total_q > 0 else 0
        dados.append(['MÉDIA', f'{media:.0f}', f'{total_a}/{total_q}', f'{pct_total:.0f}%'])
    
    col_widths = [4.5*cm, 1.3*cm, 1.8*cm, 1.0*cm]
    tabela = Table(dados, colWidths=col_widths)
    
    estilo = [
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), Cores.PRIMARIA),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Corpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 1), (-1, -1), Cores.SECUNDARIA),
        
        # Última linha (média)
        ('BACKGROUND', (0, -1), (-1, -1), Cores.CINZA_MUITO_CLARO),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        
        # Bordas mínimas
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, Cores.CINZA_CLARO),
    ]
    
    tabela.setStyle(TableStyle(estilo))
    return tabela
