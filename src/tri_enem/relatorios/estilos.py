# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Sistema visual e medidas do relatório PDF."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm


class Cores:
    """Paleta pequena, legível em tela, impressão e escala de cinza."""

    PRIMARIA = colors.HexColor("#18324A")
    SECUNDARIA = colors.HexColor("#334E68")
    NOTA = colors.HexColor("#56616B")
    TEXTO_ESCURO = PRIMARIA
    TEXTO = SECUNDARIA

    ACERTO = colors.HexColor("#23845A")
    ACERTO_CLARO = colors.HexColor("#E7F4ED")
    ERRO = colors.HexColor("#C84B45")
    ERRO_CLARO = colors.HexColor("#FAECEA")
    ANULADA = colors.HexColor("#7A8793")
    ANULADA_CLARO = colors.HexColor("#EEF1F4")
    ATENCAO = colors.HexColor("#9A6818")
    ATENCAO_CLARO = colors.HexColor("#FFF6DF")

    CINZA = colors.HexColor("#607080")
    CINZA_CLARO = colors.HexColor("#CBD3DA")
    CINZA_MUITO_CLARO = colors.HexColor("#F3F5F7")
    BRANCO = colors.white
    BARRA_FUNDO = colors.HexColor("#E8EDF1")
    LINHA_GRADE = colors.HexColor("#DCE2E7")


class Medidas:
    """Dimensões compartilhadas para que a paginação seja determinística."""

    PAGINA_LARGURA, PAGINA_ALTURA = A4
    MARGEM_HORIZONTAL = 1.2 * cm
    MARGEM_SUPERIOR = 1.15 * cm
    MARGEM_INFERIOR = 1.25 * cm
    LARGURA_UTIL = PAGINA_LARGURA - 2 * MARGEM_HORIZONTAL
    ALTURA_UTIL = PAGINA_ALTURA - MARGEM_SUPERIOR - MARGEM_INFERIOR

    GRAFICO_IMPACTO_ALTURA = 6.6 * cm
    GRADE_ALTURA = 2.75 * cm
    BARRAS_ALTURA_BASE = 0.9 * cm
    BARRAS_ALTURA_AREA = 0.75 * cm
    FONTE_MINIMA = 6.5
    FONTE_TABELA = 7.0
    FONTE_CORPO = 8.2

    ESPACO_XS = 3
    ESPACO_SM = 6
    ESPACO_MD = 10
    ESPACO_LG = 16


def criar_estilos():
    """Cria a hierarquia tipográfica usada em todas as páginas."""

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TituloPrincipal", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=24, leading=28,
        alignment=TA_CENTER, textColor=Cores.PRIMARIA,
        spaceBefore=0, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="Subtitulo", parent=styles["Normal"],
        fontName="Helvetica", fontSize=11, leading=14,
        alignment=TA_CENTER, textColor=Cores.CINZA,
        spaceBefore=0, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="SubtituloCompacto", parent=styles["Subtitulo"],
        fontSize=9.2, leading=11.5, alignment=TA_LEFT,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="TituloArea", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=13, leading=16,
        alignment=TA_LEFT, textColor=Cores.PRIMARIA,
        spaceBefore=0, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="SubtituloSecao", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9.5, leading=12,
        alignment=TA_LEFT, textColor=Cores.PRIMARIA,
        spaceBefore=3, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="TextoNormal", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.6, leading=11,
        alignment=TA_LEFT, textColor=Cores.SECUNDARIA,
        spaceBefore=0, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="TextoPequeno", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7.2, leading=9,
        alignment=TA_LEFT, textColor=Cores.CINZA,
        spaceBefore=0, spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="RotuloMetrica", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.7, leading=10.8,
        alignment=TA_CENTER, textColor=Cores.CINZA,
    ))
    styles.add(ParagraphStyle(
        name="ValorMetrica", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=24, leading=27,
        alignment=TA_CENTER, textColor=Cores.PRIMARIA,
    ))
    styles.add(ParagraphStyle(
        name="Legenda", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7.0, leading=8.5,
        alignment=TA_LEFT, textColor=Cores.CINZA,
        spaceBefore=1, spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="Disclaimer", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.3, leading=11,
        alignment=TA_CENTER, textColor=Cores.CINZA,
        spaceBefore=1, spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="AvisoCalibracao", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.2, leading=10.5,
        alignment=TA_LEFT, textColor=Cores.TEXTO_ESCURO,
        spaceBefore=2, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="MetricasValidacao", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=7.2, leading=9.5,
        alignment=TA_LEFT, textColor=Cores.CINZA,
        spaceBefore=0, spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="MetaCapa", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7.8, leading=10,
        alignment=TA_CENTER, textColor=Cores.CINZA,
        spaceBefore=0, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="MetaCompacta", parent=styles["MetaCapa"],
        fontSize=7.4, leading=9.2, alignment=TA_LEFT,
    ))

    # Nomes mantidos para consumidores antigos, agora sem caixas pesadas.
    for nome, cor in (
        ("ValidacaoBoa", Cores.ACERTO),
        ("ValidacaoMedia", Cores.ATENCAO),
        ("ValidacaoBaixa", Cores.ERRO),
    ):
        styles.add(ParagraphStyle(
            name=nome, parent=styles["AvisoCalibracao"], textColor=cor,
        ))
    return styles
