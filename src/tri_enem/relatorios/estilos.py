# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Estilos para o relatório PDF.

Centraliza cores, fontes e estilos reutilizáveis.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# =============================================================================
#                              CORES
# =============================================================================

class Cores:
    """Paleta de cores do relatório."""
    
    # Principais
    PRIMARIA = colors.HexColor('#1a237e')
    SECUNDARIA = colors.HexColor('#303f9f')
    DESTAQUE = colors.HexColor('#1565c0')
    
    # Acertos e erros
    ACERTO = colors.HexColor('#4CAF50')
    ACERTO_CLARO = colors.HexColor('#C8E6C9')
    ERRO = colors.HexColor('#F44336')
    ERRO_CLARO = colors.HexColor('#FFCDD2')
    
    # Neutras
    CINZA = colors.HexColor('#757575')
    CINZA_CLARO = colors.HexColor('#E0E0E0')
    CINZA_MUITO_CLARO = colors.HexColor('#F5F5F5')
    
    # Para gráficos
    BARRA_FUNDO = colors.HexColor('#EEEEEE')
    LINHA_GRADE = colors.HexColor('#BDBDBD')


# =============================================================================
#                              ESTILOS
# =============================================================================

def criar_estilos():
    """Cria e retorna os estilos personalizados do relatório."""
    
    styles = getSampleStyleSheet()
    
    # Título principal
    styles.add(ParagraphStyle(
        name='TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=2,
        alignment=TA_CENTER,
        textColor=Cores.PRIMARIA
    ))
    
    # Subtítulo
    styles.add(ParagraphStyle(
        name='Subtitulo',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=10,
        alignment=TA_CENTER,
        textColor=Cores.CINZA
    ))
    
    # Título de área
    styles.add(ParagraphStyle(
        name='TituloArea',
        parent=styles['Heading2'],
        fontSize=11,
        spaceBefore=8,
        spaceAfter=4,
        textColor=Cores.SECUNDARIA
    ))
    
    # Nota em destaque
    styles.add(ParagraphStyle(
        name='NotaDestaque',
        parent=styles['Normal'],
        fontSize=20,
        alignment=TA_CENTER,
        textColor=Cores.DESTAQUE,
        spaceAfter=2
    ))
    
    # Texto normal
    styles.add(ParagraphStyle(
        name='TextoNormal',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=2
    ))
    
    # Texto pequeno
    styles.add(ParagraphStyle(
        name='TextoPequeno',
        parent=styles['Normal'],
        fontSize=7,
        textColor=Cores.CINZA
    ))
    
    # Disclaimer
    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontSize=6,
        textColor=Cores.CINZA,
        alignment=TA_CENTER,
        spaceBefore=5
    ))
    
    # Legenda
    styles.add(ParagraphStyle(
        name='Legenda',
        parent=styles['Normal'],
        fontSize=6,
        textColor=Cores.CINZA,
        alignment=TA_CENTER
    ))
    
    return styles
