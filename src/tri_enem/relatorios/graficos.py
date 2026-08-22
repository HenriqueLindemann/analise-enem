# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Componentes gráficos vetoriais do relatório PDF."""

from __future__ import annotations

from math import ceil
from typing import List, Sequence

from reportlab.graphics.shapes import Drawing, Group, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.units import cm, inch

from .base import AreaAnalise, QuestaoAnalise
from .estilos import Cores, Medidas
from ..formatacao import formatar_numero


def _largura_em_pontos(largura: float | None) -> float:
    if largura is None:
        return Medidas.LARGURA_UTIL
    # Compatibilidade com a API antiga, cuja largura era dada em polegadas.
    return largura * inch if largura <= 20 else largura


def grafico_barras_notas(
    areas: Sequence[AreaAnalise], largura: float | None = None,
) -> Drawing:
    """Barras vetoriais em escala fixa de 0 a 1000."""

    width = _largura_em_pontos(largura)
    height = Medidas.BARRAS_ALTURA_BASE + max(1, len(areas)) * Medidas.BARRAS_ALTURA_AREA
    drawing = Drawing(width, height)
    drawing._kind = "barras_notas"
    drawing._escala = (0, 1000)
    if not areas:
        drawing.add(String(
            width / 2, height / 2, "Sem resultados de áreas",
            textAnchor="middle", fontName="Helvetica", fontSize=8,
            fillColor=Cores.CINZA,
        ))
        return drawing

    label_width, value_width = 38, 42
    bar_x = label_width
    bar_width = width - label_width - value_width
    row_height = (height - 8) / len(areas)
    for referencia, rotulo in ((500, "500"), (700, "700")):
        x = bar_x + bar_width * referencia / 1000
        drawing.add(Line(x, 8, x, height - 5, strokeColor=Cores.CINZA_CLARO,
                         strokeWidth=0.45, strokeDashArray=[2, 2]))
        drawing.add(String(x, height - 2, rotulo, textAnchor="middle",
                           fontName="Helvetica", fontSize=6.2,
                           fillColor=Cores.CINZA))

    for indice, area in enumerate(areas):
        cy = height - 9 - (indice + 0.5) * row_height
        bar_height = min(11, row_height * 0.48)
        nota = min(1000.0, max(0.0, float(area.nota)))
        drawing.add(String(0, cy - 2.7, area.sigla.upper(),
                           fontName="Helvetica-Bold", fontSize=8.0,
                           fillColor=Cores.PRIMARIA))
        drawing.add(Rect(bar_x, cy - bar_height / 2, bar_width, bar_height,
                         rx=1.6, ry=1.6,
                         fillColor=Cores.BARRA_FUNDO, strokeColor=None))
        drawing.add(Rect(bar_x, cy - bar_height / 2,
                         max(0.8, bar_width * nota / 1000), bar_height,
                         rx=1.6, ry=1.6,
                         fillColor=Cores.NOTA, strokeColor=None))
        drawing.add(String(width, cy - 2.8, formatar_numero(area.nota),
                           textAnchor="end", fontName="Helvetica-Bold",
                           fontSize=8.0, fillColor=Cores.PRIMARIA))
    return drawing


def _adicionar_padrao_estado(
    drawing: Drawing, estado: str, x: float, y: float,
    width: float, height: float,
) -> None:
    """Sinal redundante à cor: uma diagonal para erro, contorno para anulada."""

    if estado == "erro":
        drawing.add(Line(
            x + 2, y + 1.7, x + width - 2, y + 1.7,
            strokeColor=Cores.ERRO_CLARO, strokeWidth=0.9,
        ))
    elif estado == "anulada":
        drawing.add(Rect(
            x + 1.5, y + 1.5, width - 3, height - 3,
            rx=1, ry=1, fillColor=None, strokeColor=Cores.ANULADA_CLARO,
            strokeWidth=0.65,
        ))


def grade_questoes(
    questoes: Sequence[QuestaoAnalise], largura: float | None = None,
    colunas: int = 15,
) -> Drawing:
    """Grade vetorial: somente números nas células e padrões na legenda."""

    if colunas < 1:
        raise ValueError("colunas deve ser maior que zero")
    width = _largura_em_pontos(largura)
    height = Medidas.GRADE_ALTURA
    drawing = Drawing(width, height)
    drawing._kind = "grade_questoes"
    if not questoes:
        drawing.add(Rect(0, 13, width, height - 13,
                         fillColor=Cores.CINZA_MUITO_CLARO,
                         strokeColor=Cores.CINZA_CLARO, strokeWidth=0.5))
        drawing.add(String(width / 2, height / 2 + 3,
                           "Dados de questões não disponíveis",
                           textAnchor="middle", fontName="Helvetica",
                           fontSize=7, fillColor=Cores.CINZA))
        return drawing

    ordenadas = sorted(questoes, key=lambda q: q.posicao)
    linhas = ceil(len(ordenadas) / colunas)
    legend_height = 15
    grid_height = height - legend_height
    cell_width = min(26, width / colunas)
    grid_width = cell_width * colunas
    grid_x = (width - grid_width) / 2
    cell_height = grid_height / max(3, linhas)
    for indice, questao in enumerate(ordenadas):
        coluna, linha = indice % colunas, indice // colunas
        x = grid_x + coluna * cell_width + 1.2
        y = height - (linha + 1) * cell_height + 1.2
        w, h = cell_width - 2.4, cell_height - 2.4
        if questao.anulada:
            cor, estado = Cores.ANULADA, "anulada"
        elif questao.acertou:
            cor, estado = Cores.ACERTO, "acerto"
        else:
            cor, estado = Cores.ERRO, "erro"
        drawing.add(Rect(x, y, w, h, rx=1.6, ry=1.6,
                         fillColor=cor, strokeColor=None))
        _adicionar_padrao_estado(drawing, estado, x, y, w, h)
        drawing.add(String(x + w / 2, y + h / 2 - 2.6, str(questao.posicao),
                           textAnchor="middle", fontName="Helvetica-Bold",
                           fontSize=8.7, fillColor=colors.white))

    legenda = (("acerto", Cores.ACERTO), ("erro", Cores.ERRO),
               ("anulada", Cores.ANULADA))
    x = grid_x
    for texto, cor in legenda:
        drawing.add(Rect(x, 0.5, 8, 7, rx=1.2, ry=1.2,
                         fillColor=cor, strokeColor=None))
        _adicionar_padrao_estado(drawing, texto, x, 0.5, 8, 7)
        drawing.add(String(x + 11, 1.1, texto, fontName="Helvetica",
                           fontSize=6.2, fillColor=Cores.CINZA))
        x += 55
    return drawing


def preparar_impacto(
    questoes: Sequence[QuestaoAnalise],
) -> List[QuestaoAnalise]:
    """Exclui anuladas e ordena todas as questões por impacto."""

    validas = sorted(
        (q for q in questoes if not q.anulada),
        key=lambda q: (-float(q.impacto), q.posicao),
    )
    return validas


def grafico_impacto_questoes(
    questoes: Sequence[QuestaoAnalise], titulo: str = "",
    largura: float | None = None, dpi: int = 300,
) -> Drawing:
    """Gráfico vetorial clássico: uma barra vertical por questão válida."""

    validas = preparar_impacto(questoes)
    width = _largura_em_pontos(largura)
    if not validas:
        height = 2.3 * cm
        drawing = Drawing(width, height)
        drawing._kind = "impacto_vazio"
        drawing.add(Rect(0, 0, width, height,
                         fillColor=Cores.CINZA_MUITO_CLARO,
                         strokeColor=Cores.CINZA_CLARO, strokeWidth=0.5))
        drawing.add(String(width / 2, height / 2,
                           "Sem questões válidas para calcular impacto",
                           textAnchor="middle", fontName="Helvetica",
                           fontSize=8, fillColor=Cores.CINZA))
        return drawing

    maximo = max(max(float(q.impacto), 0.0) for q in validas)
    escala = max(1.0, maximo * 1.16)
    height = Medidas.GRAFICO_IMPACTO_ALTURA
    drawing = Drawing(width, height)
    drawing.hAlign = "CENTER"
    drawing._kind = "impacto_vetorial"
    drawing._escala = (0, escala)
    drawing._ordem_leitura = "maior_para_menor"

    plot_x, plot_y = 29, 18
    plot_width, plot_height = width - 2 * plot_x, height - 30
    drawing._margens_plot = (plot_x, width - plot_x - plot_width)
    for indice in range(5):
        fracao = indice / 4
        y = plot_y + plot_height * fracao
        drawing.add(String(plot_x - 5, y - 2, f"{escala * fracao:.0f}",
                           textAnchor="end", fontName="Helvetica",
                           fontSize=5.5, fillColor=Cores.CINZA))
    drawing.add(Line(plot_x, plot_y, plot_x, plot_y + plot_height,
                     strokeColor=Cores.CINZA_CLARO, strokeWidth=0.5))
    drawing.add(Line(plot_x, plot_y, plot_x + plot_width, plot_y,
                     strokeColor=Cores.CINZA_CLARO, strokeWidth=0.5))

    passo = plot_width / max(1, len(validas))
    bar_width = min(9.2, passo * 0.76)
    for indice, questao in enumerate(validas):
        valor = max(0.0, float(questao.impacto))
        x = plot_x + indice * passo + (passo - bar_width) / 2
        bar_height = plot_height * valor / escala
        cor = Cores.ACERTO if questao.acertou else Cores.ERRO
        altura_barra = max(0.7, bar_height)
        raio = min(0.8, altura_barra / 2)
        drawing.add(Rect(x, plot_y, bar_width, altura_barra,
                         rx=raio, ry=raio, fillColor=cor, strokeColor=None))
        if not questao.acertou and bar_height > 4:
            drawing.add(Line(x + 1, plot_y + bar_height - 4,
                             x + bar_width - 1, plot_y + bar_height - 1,
                             strokeColor=Cores.ERRO_CLARO, strokeWidth=0.55))
        rotulo_y = min(plot_y + bar_height + 3, height - 18)
        etiqueta = Group()
        etiqueta.add(String(0, 0, str(questao.posicao), textAnchor="start",
                             fontName="Helvetica-Bold", fontSize=7.2,
                             fillColor=cor))
        etiqueta.translate(x + bar_width / 2 + 2.35, rotulo_y)
        etiqueta.rotate(90)
        drawing.add(etiqueta)

    drawing.add(String(plot_x + plot_width * 0.34, 10.5, "← maior impacto",
                       textAnchor="middle", fontName="Helvetica-Oblique",
                       fontSize=6.3, fillColor=Cores.CINZA))
    drawing.add(String(plot_x + plot_width * 0.68, 10.5, "menor impacto →",
                       textAnchor="middle", fontName="Helvetica-Oblique",
                       fontSize=6.3, fillColor=Cores.CINZA))

    legend_x = width - 68
    for offset, texto, cor, erro in (
        (0, "Acerto", Cores.ACERTO, False),
        (12, "Erro", Cores.ERRO, True),
    ):
        y = height - 25 - offset
        drawing.add(Rect(legend_x, y, 7, 7, rx=1.1, ry=1.1,
                         fillColor=cor, strokeColor=None))
        if erro:
            drawing.add(Line(legend_x + 1, y + 1, legend_x + 6, y + 6,
                             strokeColor=Cores.ERRO_CLARO, strokeWidth=0.55))
        drawing.add(String(legend_x + 10, y + 0.6, texto,
                           fontName="Helvetica", fontSize=7.0,
                           fillColor=Cores.SECUNDARIA))
    return drawing
