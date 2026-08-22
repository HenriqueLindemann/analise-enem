# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Casos funcionais e estruturais do relatório PDF A4."""

from pathlib import Path

import pytest

pypdf = pytest.importorskip("pypdf")
pytest.importorskip("reportlab")
from reportlab.graphics.shapes import Drawing

import _utils

_utils.add_src_to_path()

from tri_enem.relatorios.base import AreaAnalise, DadosRelatorio, QuestaoAnalise
from tri_enem.formatacao import formatar_numero
from tri_enem.relatorios.estilos import Medidas
from tri_enem.relatorios.gerador import RelatorioPDF
from tri_enem.relatorios.graficos import (
    grafico_barras_notas,
    grafico_impacto_questoes,
    grade_questoes,
    preparar_impacto,
)
from tri_enem.relatorios.tabelas import (
    _faixa_acertos,
    preparar_diagnostico,
    tabela_diagnostico_questoes,
    tabela_resumo_areas,
)
from tri_enem.relatorios.utils import formatar_lingua


def _criar_area_sintetica(
    sigla: str,
    nome: str,
    total_erros: int,
    total_itens: int = 45,
    inicio: int = 1,
) -> AreaAnalise:
    """Cria uma área com impacto decrescente e estado determinístico."""

    total_erros = max(0, min(total_erros, total_itens))
    questoes = []
    for indice in range(total_itens):
        posicao = inicio + indice
        errou = indice < total_erros
        questoes.append(QuestaoAnalise(
            posicao=posicao,
            gabarito="A",
            resposta_dada="B" if errou else "A",
            acertou=not errou,
            param_a=1.5,
            param_b=-2.0 + indice * 0.1,
            param_c=0.2,
            impacto=(30.0 if errou else 15.0) / (indice + 1),
        ))
    acertos = total_itens - total_erros
    return AreaAnalise(
        sigla=sigla,
        nome=nome,
        ano=2023,
        co_prova=1211,
        nota=400.0 + acertos * 12.0,
        theta=-2.0 + acertos * 0.1,
        acertos=acertos,
        total_itens=total_itens,
        questoes=questoes,
        cor_prova="Azul",
        lingua="ingles" if sigla == "LC" else None,
    )


def _dados(areas):
    return DadosRelatorio(
        titulo="Desempenho no Simulado ENEM",
        ano_prova=2023,
        areas=list(areas),
        cor_prova="Azul",
        tipo_aplicacao="1ª Aplicação",
        origem_geracao="notatri.com",
    )


def _gerar(tmp_path: Path, areas, nome: str = "relatorio.pdf"):
    caminho = tmp_path / nome
    resultado = RelatorioPDF().gerar(_dados(areas), str(caminho))
    return Path(resultado), pypdf.PdfReader(resultado)


def test_componentes_graficos_sao_vetoriais():
    area = _criar_area_sintetica("MT", "Matemática", 12)
    assert isinstance(grafico_barras_notas([area]), Drawing)
    assert isinstance(grade_questoes(area.questoes), Drawing)
    assert isinstance(grafico_impacto_questoes(area.questoes), Drawing)


def test_formatacao_decimal_compartilhada_e_em_portugues():
    assert formatar_numero(677.4) == "677,4"
    assert formatar_numero(0.58, 2, sinal=True) == "+0,58"


def test_impacto_mostra_todas_as_questoes_validas_na_ordem():
    area = _criar_area_sintetica("MT", "Matemática", 12)
    area.questoes[4].anulada = True
    area.questoes[21].anulada = True
    preparadas = preparar_impacto(area.questoes)
    assert len(preparadas) == 43
    assert {q.posicao for q in preparadas} == set(range(1, 46)) - {5, 22}
    assert [q.impacto for q in preparadas] == sorted(
        (q.impacto for q in preparadas), reverse=True,
    )
    grafico = grafico_impacto_questoes(area.questoes)
    assert grafico.hAlign == "CENTER"
    assert grafico._margens_plot[0] == grafico._margens_plot[1]


def test_diagnostico_separa_validas_uma_unica_vez():
    area = _criar_area_sintetica("MT", "Matemática", 22)
    area.questoes[1].anulada = True
    area.questoes[30].anulada = True
    preparado = preparar_diagnostico(area.questoes)
    posicoes = [q.posicao for q in preparado.erros + preparado.acertos]
    assert len(posicoes) == len(set(posicoes)) == 43
    assert set(posicoes) == set(range(1, 46)) - {2, 31}
    assert all(not q.acertou for q in preparado.erros)
    assert all(q.acertou for q in preparado.acertos)


def test_grade_de_acertos_ordena_por_maior_impacto():
    area = _criar_area_sintetica("MT", "Matemática", 0, total_itens=3)
    area.questoes[0].impacto = 2.0
    area.questoes[1].impacto = 9.0
    area.questoes[2].impacto = 5.0

    bloco = _faixa_acertos(area.questoes, Medidas.LARGURA_UTIL)
    grade = bloco._cellvalues[1][0]
    textos = [
        celula.getPlainText()
        for celula in grade._cellvalues[0]
        if hasattr(celula, "getPlainText")
    ]

    assert [texto[0] for texto in textos] == ["2", "3", "1"]


@pytest.mark.parametrize("erros", [0, 1, 22, 30, 35, 44, 45])
def test_uma_area_cabe_em_uma_pagina_em_casos_extremos(erros, tmp_path):
    caminho, reader = _gerar(
        tmp_path,
        [_criar_area_sintetica("MT", "Matemática e suas Tecnologias", erros)],
        f"uma-area-{erros}.pdf",
    )
    conteudo = caminho.read_bytes()
    assert conteudo.startswith(b"%PDF-")
    assert conteudo.rstrip().endswith(b"%%EOF")
    assert len(reader.pages) == 1
    if erros == 0:
        assert "Sem erros, parabéns!" in (reader.pages[0].extract_text() or "")


@pytest.mark.parametrize("erros", [0, 22, 45])
def test_quatro_areas_geram_capa_e_uma_pagina_por_area(erros, tmp_path):
    areas = [
        _criar_area_sintetica("LC", "Linguagens, Códigos e suas Tecnologias", erros),
        _criar_area_sintetica("CH", "Ciências Humanas e suas Tecnologias", erros),
        _criar_area_sintetica("CN", "Ciências da Natureza e suas Tecnologias", erros),
        _criar_area_sintetica("MT", "Matemática e suas Tecnologias", erros),
    ]
    _, reader = _gerar(tmp_path, areas, f"quatro-areas-{erros}.pdf")
    assert len(reader.pages) == 5


def test_pdf_e_totalmente_vetorial_e_preserva_texto_importante(tmp_path):
    areas = [
        _criar_area_sintetica("LC", "Linguagens, Códigos e suas Tecnologias", 6),
        _criar_area_sintetica("MT", "Matemática e suas Tecnologias", 30),
    ]
    _, reader = _gerar(tmp_path, areas)
    assert all(len(page.images) == 0 for page in reader.pages)
    texto = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Carl Sagan" in texto
    assert "Dificuldade (b)" in texto
    assert "Impacto por questão" in texto
    assert "Erros (6)" in texto
    assert "Acertos (39)" in texto
    assert "pts" in texto
    assert "Desenvolvido por" in texto
    assert "Henrique Lindemann" in texto
    assert "por maior ganho estimado" not in texto
    assert "A média é aritmética" not in texto

    links = set()
    for page in reader.pages:
        for referencia in page.get("/Annots", []):
            anotacao = referencia.get_object()
            acao = anotacao.get("/A")
            if acao and acao.get("/URI"):
                links.add(acao.get("/URI"))
    assert "https://github.com/HenriqueLindemann/analise-enem" in links
    assert "https://www.linkedin.com/in/henriquelindemann/" in links


def test_numeracao_antiga_e_anuladas_sao_preservadas(tmp_path):
    area = _criar_area_sintetica(
        "LC", "Linguagens, Códigos e suas Tecnologias", 9, inicio=91,
    )
    for indice in (3, 28):
        area.questoes[indice].anulada = True
    area.acertos = len(area.questoes_acertadas)
    caminho, reader = _gerar(tmp_path, [area], "prova-antiga.pdf")
    texto = reader.pages[0].extract_text() or ""
    assert caminho.exists()
    assert "Inglês" in texto
    assert "2 anuladas (Q94, Q119)" in texto
    assert area.total_itens_validos == 43
    assert all(q.posicao not in {94, 119} for q in preparar_impacto(area.questoes))


def test_tabela_resume_denominador_valido_e_diagnostico():
    area = _criar_area_sintetica("MT", "Matemática", 10)
    area.questoes[0].anulada = True
    area.acertos = len(area.questoes_acertadas)
    resumo = tabela_resumo_areas([area])
    assert sum(resumo._colWidths) == pytest.approx(Medidas.LARGURA_UTIL)
    assert resumo._cellvalues[1][3] == "35/44"
    assert resumo._cellvalues[1][4] == "1"
    diagnostico = tabela_diagnostico_questoes(area.questoes)
    assert sum(diagnostico._colWidths) == pytest.approx(Medidas.LARGURA_UTIL)
    assert diagnostico.total_erros == 9
    assert diagnostico.total_acertos == 35


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("ingles", "Inglês"), ("espanhol", "Espanhol"), (None, "")],
)
def test_idioma_formatado_para_apresentacao(entrada, esperado):
    assert formatar_lingua(entrada) == esperado


def test_relatorio_sem_areas_e_rejeitado(tmp_path):
    with pytest.raises(ValueError, match="ao menos uma área"):
        RelatorioPDF().gerar(_dados([]), str(tmp_path / "vazio.pdf"))
