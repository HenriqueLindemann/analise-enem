# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Estilos para o relatório PDF.

Design minimalista e moderno.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# =============================================================================
#                              CORES (Paleta Minimalista)
# =============================================================================

class Cores:
    """Paleta de cores refinada - tons suaves e elegantes."""
    
    # Principais - azuis sofisticados
    PRIMARIA = colors.HexColor('#2C3E50')      # Azul escuro elegante
    SECUNDARIA = colors.HexColor('#34495E')    # Azul acinzentado
    DESTAQUE = colors.HexColor('#3498DB')      # Azul vibrante mas suave
    
    # Acertos e erros - tons mais suaves
    ACERTO = colors.HexColor('#27AE60')        # Verde esmeralda
    ACERTO_CLARO = colors.HexColor('#D5F5E3')
    ERRO = colors.HexColor('#E74C3C')          # Vermelho coral
    ERRO_CLARO = colors.HexColor('#FADBD8')
    
    # Neutras - escala de cinzas refinada
    CINZA = colors.HexColor('#7F8C8D')         # Cinza médio
    CINZA_CLARO = colors.HexColor('#BDC3C7')   # Cinza claro
    CINZA_MUITO_CLARO = colors.HexColor('#ECF0F1')  # Quase branco
    BRANCO = colors.HexColor('#FFFFFF')
    
    # Para gráficos
    BARRA_FUNDO = colors.HexColor('#F8F9FA')
    LINHA_GRADE = colors.HexColor('#DEE2E6')


# =============================================================================
#                              ESTILOS (Design Minimalista)
# =============================================================================

def criar_estilos():
    """Cria estilos minimalistas e elegantes para o relatório."""
    
    styles = getSampleStyleSheet()
    
    # Título principal - grande e limpo
    styles.add(ParagraphStyle(
        name='TituloPrincipal',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        spaceAfter=0,
        spaceBefore=0,
        alignment=TA_CENTER,
        textColor=Cores.PRIMARIA,
        leading=26
    ))
    
    # Subtítulo - sutil e elegante
    styles.add(ParagraphStyle(
        name='Subtitulo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        spaceAfter=15,
        alignment=TA_CENTER,
        textColor=Cores.CINZA,
        leading=14
    ))
    
    # Média destaque - número grande e impactante
    styles.add(ParagraphStyle(
        name='NotaDestaque',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        alignment=TA_CENTER,
        textColor=Cores.DESTAQUE,
        spaceAfter=3,
        spaceBefore=5
    ))
    
    # Label da média
    styles.add(ParagraphStyle(
        name='NotaLabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        alignment=TA_CENTER,
        textColor=Cores.CINZA,
        spaceAfter=10
    ))
    
    # Título de área - clean com linha
    styles.add(ParagraphStyle(
        name='TituloArea',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        textColor=Cores.PRIMARIA,
        borderPadding=0,
        leading=14
    ))
    
    # Subtítulo de seção
    styles.add(ParagraphStyle(
        name='SubtituloSecao',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        spaceBefore=8,
        spaceAfter=4,
        textColor=Cores.SECUNDARIA,
        leftIndent=0
    ))
    
    # Texto normal
    styles.add(ParagraphStyle(
        name='TextoNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        spaceAfter=3,
        textColor=Cores.SECUNDARIA
    ))
    
    # Texto pequeno
    styles.add(ParagraphStyle(
        name='TextoPequeno',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        textColor=Cores.CINZA
    ))
    
    # Legenda compacta
    styles.add(ParagraphStyle(
        name='Legenda',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        textColor=Cores.CINZA,
        alignment=TA_CENTER,
        spaceBefore=2,
        spaceAfter=0
    ))
    
    # Disclaimer - discreto no rodapé
    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6,
        textColor=Cores.CINZA,
        alignment=TA_CENTER,
        spaceBefore=3,
        leading=9
    ))
    
    # Aviso de precisão - sutil mas visível
    styles.add(ParagraphStyle(
        name='AvisoPrecisao',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        textColor=colors.HexColor('#D35400'),
        backColor=colors.HexColor('#FEF9E7'),
        borderColor=colors.HexColor('#F39C12'),
        borderWidth=0.5,
        borderPadding=5,
        borderRadius=3,
        spaceBefore=4,
        spaceAfter=6,
        leftIndent=0,
        rightIndent=0
    ))
    
    return styles
