# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Tabelas tipográficas e adaptativas do relatório PDF."""

from dataclasses import dataclass
import math
from typing import List, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table, TableStyle

from .base import AreaAnalise, QuestaoAnalise
from .estilos import Cores, Medidas
from .utils import formatar_numero


MODO_EQUILIBRADO = "equilibrado"
MODO_ASSIMETRICO = "assimetrico"
MODO_GRUPO_UNICO = "grupo_unico"


@dataclass(frozen=True)
class DiagnosticoPreparado:
    modo: str
    erros: List[QuestaoAnalise]
    acertos: List[QuestaoAnalise]


def preparar_diagnostico(
    questoes: Sequence[QuestaoAnalise],
) -> DiagnosticoPreparado:
    """Classifica cada questão válida uma vez e ordena por impacto."""

    erros = sorted(
        (q for q in questoes if not q.anulada and not q.acertou),
        key=lambda q: (-float(q.impacto), q.posicao),
    )
    acertos = sorted(
        (q for q in questoes if not q.anulada and q.acertou),
        key=lambda q: (-float(q.impacto), q.posicao),
    )
    return DiagnosticoPreparado(
        modo=selecionar_modo_diagnostico(len(erros), len(acertos)),
        erros=erros,
        acertos=acertos,
    )


def selecionar_modo_diagnostico(total_erros: int, total_acertos: int) -> str:
    """Escolhe a composição que usa melhor a altura da página."""

    if total_erros < 0 or total_acertos < 0:
        raise ValueError("As contagens do diagnóstico não podem ser negativas")
    menor, maior = sorted((total_erros, total_acertos))
    if menor == 0:
        return MODO_GRUPO_UNICO
    if menor * 2 <= maior:
        return MODO_ASSIMETRICO
    return MODO_EQUILIBRADO


def _texto_celula(valor) -> str:
    if valor is None:
        return "–"
    if isinstance(valor, float) and math.isnan(valor):
        return "–"
    texto = str(valor).strip()
    return "–" if not texto or texto == "." or texto.lower() == "nan" else texto


def _dificuldade(valor) -> str:
    if valor is None:
        return "–"
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "–"
    return "–" if math.isnan(numero) else formatar_numero(numero, 2, sinal=True)


_CABECALHO = ParagraphStyle(
    "CabecalhoTabelaRelatorio", fontName="Helvetica-Bold", fontSize=7.2,
    leading=8.4, textColor=Cores.PRIMARIA, alignment=1,
)
_TITULO_GRUPO = ParagraphStyle(
    "TituloGrupoDiagnostico", fontName="Helvetica-Bold", fontSize=8.2,
    leading=10, textColor=Cores.PRIMARIA, alignment=0,
)
_MENSAGEM = ParagraphStyle(
    "MensagemDiagnostico", fontName="Helvetica-Oblique", fontSize=7.0,
    leading=9, textColor=Cores.CINZA, alignment=0,
)
_TITULO_ERROS = ParagraphStyle(
    "TituloErrosDiagnostico", parent=_TITULO_GRUPO,
    textColor=Cores.ERRO, fontSize=8.4, leading=10.2,
)
_TITULO_ACERTOS = ParagraphStyle(
    "TituloAcertosDiagnostico", parent=_TITULO_GRUPO,
    textColor=Cores.ACERTO, fontSize=7.8, leading=9.4,
)
_NUMERO_ACERTO = ParagraphStyle(
    "NumeroAcertoDiagnostico", fontName="Helvetica-Bold", fontSize=7.5,
    leading=8.0, textColor=Cores.ACERTO, alignment=1,
)


def _cabecalho_grupo(tipo: str) -> List:
    impacto = "Ganho se<br/>acertasse" if tipo == "erros" else "Perda se<br/>errasse"
    return [
        Paragraph("Questão", _CABECALHO),
        Paragraph("Sua<br/>resposta", _CABECALHO),
        Paragraph("Gabarito", _CABECALHO),
        Paragraph("Dificuldade<br/>(b)", _CABECALHO),
        Paragraph(impacto, _CABECALHO),
    ]


def _linha_questao(q: QuestaoAnalise) -> List[str]:
    return [
        str(q.posicao), _texto_celula(q.resposta_dada), _texto_celula(q.gabarito),
        _dificuldade(q.param_b), f"{formatar_numero(q.impacto)} pts",
    ]


def _tabela_grupo(
    questoes: Sequence[QuestaoAnalise], tipo: str, largura: float,
    duas_colunas: bool = False,
) -> Table:
    cabecalho = _cabecalho_grupo(tipo)
    if duas_colunas:
        metade = ceil_div(len(questoes), 2)
        esquerda, direita = questoes[:metade], questoes[metade:]
        dados = [cabecalho + [""] + cabecalho]
        for indice in range(metade):
            linha = _linha_questao(esquerda[indice]) + [""]
            linha += _linha_questao(direita[indice]) if indice < len(direita) else [""] * 5
            dados.append(linha)
        meia = (largura - 8) / 2
        proporcoes = (0.15, 0.19, 0.17, 0.22, 0.27)
        widths = [meia * p for p in proporcoes] + [8] + [meia * p for p in proporcoes]
    else:
        dados = [cabecalho] + [_linha_questao(q) for q in questoes]
        proporcoes = (0.15, 0.19, 0.17, 0.22, 0.27)
        widths = [largura * p for p in proporcoes]

    tabela = Table(dados, colWidths=widths, repeatRows=1, hAlign="LEFT")
    estilo = [
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.4),
        ("LEADING", (0, 1), (-1, -1), 8.6),
        ("TEXTCOLOR", (0, 1), (-1, -1), Cores.SECUNDARIA),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, Cores.PRIMARIA),
        ("LINEBELOW", (0, 1), (-1, -1), 0.2, Cores.LINHA_GRADE),
        ("TOPPADDING", (0, 0), (-1, 0), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1.8),
        ("TOPPADDING", (0, 1), (-1, -1), 1.55),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 1.55),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.3),
    ]
    if duas_colunas:
        estilo.extend([
            ("LINEBELOW", (0, 0), (4, 0), 0.6, Cores.PRIMARIA),
            ("LINEBELOW", (6, 0), (10, 0), 0.6, Cores.PRIMARIA),
            ("LINEBELOW", (5, 0), (5, -1), 0, colors.white),
        ])
    tabela.setStyle(TableStyle(estilo))
    return tabela


def ceil_div(valor: int, divisor: int) -> int:
    return (valor + divisor - 1) // divisor


def _bloco_grupo(
    questoes: Sequence[QuestaoAnalise], tipo: str, largura: float,
    duas_colunas: bool,
) -> List:
    if tipo == "erros":
        titulo = "Erros · ganho estimado se acertasse"
    else:
        titulo = "Acertos · perda estimada se errasse"
    return [
        Paragraph(f"{titulo} ({len(questoes)})", _TITULO_GRUPO),
        _tabela_grupo(questoes, tipo, largura, duas_colunas),
    ]


def tabela_diagnostico_questoes(
    questoes: Sequence[QuestaoAnalise], largura: float | None = None,
) -> Table:
    """Prioriza erros detalhados e resume acertos apenas pelos números."""

    largura = largura or Medidas.LARGURA_UTIL
    preparado = preparar_diagnostico(questoes)
    conteudo: List = []
    if preparado.erros:
        conteudo.append(_titulo_faixa(
            f"Erros ({len(preparado.erros)})",
            largura, Cores.ERRO_CLARO, Cores.ERRO, _TITULO_ERROS,
        ))
        conteudo.append(_tabela_erros_compacta(preparado.erros, largura))
    else:
        conteudo.append(_titulo_faixa(
            "Sem erros, parabéns!",
            largura, Cores.ACERTO_CLARO, Cores.ACERTO, _TITULO_ACERTOS,
        ))

    if preparado.acertos:
        conteudo.append(_faixa_acertos(preparado.acertos, largura))
    else:
        conteudo.append(_titulo_faixa(
            "Acertos (0)", largura, Cores.ACERTO_CLARO,
            Cores.ACERTO, _TITULO_ACERTOS,
        ))
    if not preparado.erros and not preparado.acertos:
        conteudo = [Paragraph(
            "Não há questões válidas para diagnosticar.", _MENSAGEM,
        )]
    tabela = Table([[conteudo]], colWidths=[largura], hAlign="LEFT")

    tabela.modo_diagnostico = preparado.modo
    tabela.total_erros = len(preparado.erros)
    tabela.total_acertos = len(preparado.acertos)
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return tabela


def _titulo_faixa(
    texto: str, largura: float, fundo, linha, estilo: ParagraphStyle,
) -> Table:
    faixa = Table([[Paragraph(texto, estilo)]], colWidths=[largura])
    faixa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fundo),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, linha),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return faixa


def _tabela_erros_compacta(
    erros: Sequence[QuestaoAnalise], largura: float,
) -> Table:
    """Tabela única; a densidade varia sem ultrapassar a fonte mínima."""

    total = len(erros)
    if total > 38:
        fonte, leading, padding = 6.5, 6.6, 0.0
    elif total > 28:
        fonte, leading, padding = 6.8, 7.0, 0.2
    else:
        fonte, leading, padding = 7.3, 8.4, 1.25
    proporcoes = (0.15, 0.19, 0.17, 0.22, 0.27)
    tabela = Table(
        [_cabecalho_grupo("erros")] + [_linha_questao(q) for q in erros],
        colWidths=[largura * p for p in proporcoes], hAlign="LEFT",
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), Cores.ERRO_CLARO),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), fonte),
        ("LEADING", (0, 1), (-1, -1), leading),
        ("TEXTCOLOR", (0, 1), (-1, -1), Cores.SECUNDARIA),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.45, Cores.ERRO),
        ("LINEBELOW", (0, 1), (-1, -1), 0.18, Cores.LINHA_GRADE),
        ("TOPPADDING", (0, 0), (-1, 0), 1.1),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1.6),
        ("TOPPADDING", (0, 1), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 1), (-1, -1), padding),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    return tabela


def _faixa_acertos(
    acertos: Sequence[QuestaoAnalise], largura: float,
) -> Table:
    """Faixa secundária: somente os números, em ordem de posição."""

    por_posicao = sorted(acertos, key=lambda q: q.posicao)
    colunas = 10
    linhas = []
    for inicio in range(0, len(por_posicao), colunas):
        linha = []
        for questao in por_posicao[inicio:inicio + colunas]:
            impacto = formatar_numero(questao.impacto)
            linha.append(Paragraph(
                f"{questao.posicao}<br/><font name='Helvetica' size='6.1' "
                f"color='#607080'>{impacto} pts</font>",
                _NUMERO_ACERTO,
            ))
        linha.extend([""] * (colunas - len(linha)))
        linhas.append(linha)
    grade = Table(linhas, colWidths=[largura / colunas] * colunas)
    grade.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), Cores.ACERTO_CLARO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0.5),
    ]))
    titulo = _titulo_faixa(
        f"Acertos ({len(acertos)})", largura, Cores.ACERTO_CLARO,
        Cores.ACERTO, _TITULO_ACERTOS,
    )
    bloco = Table([[titulo], [grade]], colWidths=[largura])
    bloco.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return bloco


def tabela_erros_completa(erros: Sequence[QuestaoAnalise]) -> Optional[Table]:
    """Compatibilidade: tabela isolada de erros, agora com layout responsivo."""

    if not erros:
        return None
    ordenados = sorted(erros, key=lambda q: (-float(q.impacto), q.posicao))
    return _tabela_grupo(
        ordenados, "erros", Medidas.LARGURA_UTIL, len(ordenados) > 20,
    )


def tabela_resumo_areas(
    areas: Sequence[AreaAnalise], largura: float | None = None,
) -> Table:
    """Resumo com denominador válido e anuladas em coluna própria."""

    largura = largura or Medidas.LARGURA_UTIL
    dados = [["\u00c1rea", "Caderno / prova", "Nota TRI", "Acertos válidos", "Anuladas", "%"]]
    for area in areas:
        caderno = area.cor_prova.capitalize() if area.cor_prova else "–"
        if area.co_prova:
            caderno += f" · {area.co_prova}"
        dados.append([
            f"{area.sigla} · {area.nome}", caderno, formatar_numero(area.nota),
            f"{area.acertos}/{area.total_itens_validos}", str(area.total_anulados),
            f"{area.percentual_acertos:.0f}%",
        ])

    total_validos = sum(a.total_itens_validos for a in areas)
    total_acertos = sum(a.acertos for a in areas)
    total_anuladas = sum(a.total_anulados for a in areas)
    media = sum(a.nota for a in areas) / len(areas) if areas else 0.0
    percentual = 100 * total_acertos / total_validos if total_validos else 0.0
    dados.append([
        "MÉDIA GERAL SIMPLES", "", formatar_numero(media),
        f"{total_acertos}/{total_validos}", str(total_anuladas), f"{percentual:.0f}%",
    ])

    proporcoes = (0.33, 0.18, 0.12, 0.17, 0.10, 0.10)
    tabela = Table(dados, colWidths=[largura * p for p in proporcoes],
                   repeatRows=1, hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("TEXTCOLOR", (0, 0), (-1, -1), Cores.SECUNDARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), Cores.PRIMARIA),
        ("TEXTCOLOR", (0, -1), (-1, -1), Cores.PRIMARIA),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, Cores.PRIMARIA),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, Cores.LINHA_GRADE),
        ("LINEABOVE", (0, -1), (-1, -1), 0.7, Cores.PRIMARIA),
        ("TOPPADDING", (0, 0), (-1, -1), 6.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return tabela
