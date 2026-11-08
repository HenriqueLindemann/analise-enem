# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Casos funcionais e estruturais do relatório PDF A4."""

from pathlib import Path

import pytest

pypdf = pytest.importorskip("pypdf")
pikepdf = pytest.importorskip("pikepdf")
pytest.importorskip("reportlab")
from reportlab.graphics.shapes import Drawing

import _utils

_utils.add_src_to_path()

from tri_enem.relatorios.base import AreaAnalise, DadosRelatorio, QuestaoAnalise
from tri_enem.formatacao import formatar_numero
from tri_enem.relatorios.estilos import Medidas
from tri_enem.relatorios.gerador import RelatorioPDF
from tri_enem.relatorios.graficos import (
    descrever_grade,
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
from tri_enem.relatorios.utils import formatar_cor, formatar_lingua


def _criar_area_sintetica(
    sigla: str,
    nome: str,
    total_erros: int,
    total_itens: int = 45,
    inicio: int = 1,
    prova: tuple = (2023, 1211),
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
        ano=prova[0],
        co_prova=prova[1],
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
    rotulos_etiquetas = [
        item.contents[0].text
        for item in grafico.contents
        if hasattr(item, "contents") and item.contents and hasattr(item.contents[0], "text")
    ]
    assert any(r.endswith("*") for r in rotulos_etiquetas)
    textos_grafico = [
        item.text for item in grafico.contents if hasattr(item, "text")
    ]
    assert "Erro (*)" in textos_grafico


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


PROVA_ERRO_RARO = (2010, 97)  # aviso com a proporção do censo


@pytest.mark.parametrize("erros, prova", [
    *((e, (2023, 1211)) for e in (0, 1, 22, 24, 28, 30, 35, 44, 45)),
    *((e, PROVA_ERRO_RARO) for e in (0, 24, 28, 45)),
])
def test_uma_area_cabe_em_uma_pagina_em_casos_extremos(erros, prova, tmp_path):
    caminho, reader = _gerar(
        tmp_path,
        [_criar_area_sintetica("MT", "Matemática e suas Tecnologias", erros, prova=prova)],
        f"uma-area-{erros}-{prova[1]}.pdf",
    )
    conteudo = caminho.read_bytes()
    assert conteudo.startswith(b"%PDF-")
    assert conteudo.rstrip().endswith(b"%%EOF")
    assert len(reader.pages) == 1
    texto = reader.pages[0].extract_text() or ""
    assert "Carl Sagan" not in texto
    if prova == PROVA_ERRO_RARO:
        assert "Cerca de 1 em cada" in texto
    if erros == 0:
        assert "Sem erros, parabéns!" in texto
        assert "Dificuldade (b): valor" not in texto
    else:
        assert texto.index("Ganho se acertasse") < texto.index("Dificuldade (b): valor")
        assert texto.index("Dificuldade (b): valor") < texto.index("Acertos (")


@pytest.mark.parametrize("anuladas, prova", [(0, (2023, 1211)), (2, (2023, 1211)), (2, PROVA_ERRO_RARO)])
def test_uma_area_respeita_altura_util_para_qualquer_contagem_de_erros(anuladas, prova):
    relatorio = RelatorioPDF()
    validas = 45 - anuladas
    for erros in range(validas + 1):
        area = _criar_area_sintetica(
            "MT", "Matemática e suas Tecnologias", erros + anuladas, prova=prova,
        )
        for indice in range(anuladas):
            area.questoes[indice].anulada = True
        area.acertos = len(area.questoes_acertadas)
        dados = _dados([area])
        pagina = relatorio._pagina_area(
            area,
            incluir_identidade=True,
            dados=dados,
            incluir_explicacao_b=True,
            incluir_diagnostico=True,
        )
        altura = relatorio._validar_altura_pagina(
            pagina, f"1 área com {erros} erros e {anuladas} anuladas",
        )
        assert altura <= Medidas.ALTURA_UTIL + 0.5


@pytest.mark.parametrize("quantidade", [2, 3, 4])
def test_multiplas_areas_geram_capa_citacao_e_pagina_por_area(
    quantidade, tmp_path,
):
    definicoes = [
        ("LC", "Linguagens, Códigos e suas Tecnologias"),
        ("CH", "Ciências Humanas e suas Tecnologias"),
        ("CN", "Ciências da Natureza e suas Tecnologias"),
        ("MT", "Matemática e suas Tecnologias"),
    ]
    areas = [
        _criar_area_sintetica(sigla, nome, 22)
        for sigla, nome in definicoes[:quantidade]
    ]
    _, reader = _gerar(tmp_path, areas, f"{quantidade}-areas.pdf")

    assert len(reader.pages) == quantidade + 1
    textos = [pagina.extract_text() or "" for pagina in reader.pages]
    assert "Carl Sagan" in textos[0]
    assert all("Carl Sagan" not in texto for texto in textos[1:])


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


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("azul", "Azul"), ("Azul", "Azul"), (None, ""),
     ("roxa_videoprova_libras", "Roxa videoprova em Libras"),
     ("cinza_adaptada_ledor", "Cinza adaptada ledor")],
)
def test_cor_formatada_para_apresentacao(entrada, esperado):
    assert formatar_cor(entrada) == esperado


def test_relatorio_sem_areas_e_rejeitado(tmp_path):
    with pytest.raises(ValueError, match="ao menos uma área"):
        RelatorioPDF().gerar(_dados([]), str(tmp_path / "vazio.pdf"))


_OPERADORES_DE_PINTURA = {
    "Tj", "TJ", "'", '"', "S", "s", "f", "F", "f*", "B", "B*", "b", "b*", "sh", "Do",
}


def _area_sem_validas() -> AreaAnalise:
    area = _criar_area_sintetica("CN", "Ciências da Natureza", 0, total_itens=3)
    for questao in area.questoes:
        questao.anulada = True
    area.acertos = 0
    return area


def _elementos_estrutura(pdf) -> list:
    elementos = []

    def visitar(no):
        elementos.append(no)
        filhos = no.get("/K")
        if not isinstance(filhos, pikepdf.Array):
            filhos = [] if filhos is None else [filhos]
        for filho in filhos:
            if isinstance(filho, pikepdf.Dictionary) and filho.get("/Type") == "/StructElem":
                visitar(filho)

    visitar(pdf.Root.StructTreeRoot.K)
    return elementos


def _arvore_de_pais(pdf) -> dict:
    nums = pdf.Root.StructTreeRoot.ParentTree.Nums
    return {int(nums[i]): nums[i + 1] for i in range(0, len(nums), 2)}


@pytest.mark.parametrize("caso", ["uma_sem_erros", "uma_so_erros", "quatro", "sem_validas"])
def test_todo_conteudo_desenhado_e_marcado_ou_artefato(caso, tmp_path):
    areas = {
        "uma_sem_erros": lambda: [_criar_area_sintetica("MT", "Matemática", 0)],
        "uma_so_erros": lambda: [_criar_area_sintetica("MT", "Matemática", 45)],
        "quatro": lambda: [
            _criar_area_sintetica(sigla, sigla, 22) for sigla in ("LC", "CH", "CN", "MT")
        ],
        "sem_validas": lambda: [_area_sem_validas()],
    }[caso]()
    caminho, _ = _gerar(tmp_path, areas, f"{caso}.pdf")

    with pikepdf.open(caminho) as pdf:
        pais = _arvore_de_pais(pdf)
        for numero, pagina in enumerate(pdf.pages, start=1):
            elementos = pais[int(pagina.obj.StructParents)]
            pilha, mcids = [], set()
            for operandos, operador in pikepdf.parse_content_stream(pagina):
                operador = str(operador)
                if operador in ("BMC", "BDC"):
                    assert not pilha, f"sequência aninhada na página {numero}"
                    propriedades = operandos[1] if operador == "BDC" else None
                    mcid = None
                    if isinstance(propriedades, pikepdf.Dictionary) and "/MCID" in propriedades:
                        mcid = int(propriedades.MCID)
                        mcids.add(mcid)
                    pilha.append((str(operandos[0]), mcid))
                elif operador == "EMC":
                    pilha.pop()
                elif operador in _OPERADORES_DE_PINTURA:
                    assert pilha, f"{operador} sem marcação na página {numero}"
                    tag, mcid = pilha[-1]
                    assert tag == "/Artifact" or mcid is not None
            assert not pilha
            assert mcids == set(range(len(elementos)))


def test_estrutura_logica_para_leitores_de_tela(tmp_path):
    lc = _criar_area_sintetica("LC", "Linguagens, Códigos e suas Tecnologias", 6)
    lc.questoes[3].anulada = True
    lc.acertos = len(lc.questoes_acertadas)
    mt = _criar_area_sintetica("MT", "Matemática e suas Tecnologias", 30)
    caminho, _ = _gerar(tmp_path, [lc, mt])

    with pikepdf.open(caminho) as pdf:
        assert pdf.Root.MarkInfo.Marked
        assert str(pdf.Root.Lang) == "pt-BR"
        assert pdf.Root.ViewerPreferences.DisplayDocTitle
        with pdf.open_metadata() as meta:
            assert meta["dc:title"] == "Desempenho no Simulado ENEM 2023"

        elementos = _elementos_estrutura(pdf)
        titulos = [int(str(e.S)[2]) for e in elementos if str(e.S) in ("/H1", "/H2", "/H3")]
        assert titulos.count(1) == 1 and titulos[0] == 1
        assert all(atual <= anterior + 1 for anterior, atual in zip(titulos, titulos[1:]))

        figuras = [e for e in elementos if e.S == "/Figure"]
        assert len(figuras) == 1 + 2 * len([lc, mt])
        assert all(str(figura.Alt) and "/BBox" in figura.A for figura in figuras)
        assert f"LC: {formatar_numero(lc.nota)}" in str(figuras[0].Alt)
        assert "Anuladas (1): 4." in str(figuras[1].Alt)

        tabelas = [e for e in elementos if e.S == "/Table"]
        assert len(tabelas) == 3
        for tabela in tabelas:
            linhas = list(tabela.K)
            assert len({len(linha.K) for linha in linhas}) == 1
            assert all(c.S == "/TH" and c.A.Scope == "/Column" for c in linhas[0].K)
            assert all(linha.K[0].S == "/TH" and linha.K[0].A.Scope == "/Row"
                       for linha in linhas[1:])

        pais = _arvore_de_pais(pdf)
        for pagina in pdf.pages:
            assert pagina.obj.Tabs == "/S"
            for anotacao in pagina.obj.Annots:
                assert str(anotacao.Contents)
                assert pais[int(anotacao.StructParent)].S == "/Link"

        marcadores = [item.title for item in pdf.open_outline().root]
        assert marcadores == ["Desempenho no Simulado ENEM"]
        assert [item.title for item in pdf.open_outline().root[0].children][-2:] == [
            "LC — Linguagens, Códigos e suas Tecnologias (Inglês)",
            "MT — Matemática e suas Tecnologias",
        ]


def test_descricao_da_grade_lista_cada_resultado():
    area = _criar_area_sintetica("MT", "Matemática", 2, total_itens=5)
    area.questoes[4].anulada = True
    assert descrever_grade(area.questoes) == (
        "Grade das 5 questões por resultado. "
        "Acertos (2): 3, 4; Erros (2): 1, 2; Anuladas (1): 5."
    )


def test_tabela_resumo_areas_abrevia_nomes_longos_e_cabe_em_todo_o_catalogo():
    from tri_enem.config import NOMES_AREAS
    from tri_enem.mapeador_provas import MapeadorProvas

    relatorio = RelatorioPDF()
    mapeador = MapeadorProvas()
    por_cor = {}
    for prova in mapeador.listar_todas_provas():
        if prova.cor not in por_cor or prova.codigo > por_cor[prova.cor].codigo:
            por_cor[prova.cor] = prova

    provas = list(por_cor.values())
    for inicio in range(0, len(provas), 4):
        bloco = (provas[inicio:inicio + 4] + provas[:4])[:4]
        areas = []
        for (sigla, nome), prova in zip(NOMES_AREAS.items(), bloco):
            area = _criar_area_sintetica(
                sigla, nome, 12, prova=(prova.ano, prova.codigo),
            )
            area.cor_prova = prova.cor
            areas.append(area)
        pagina = relatorio._pagina_resumo(_dados(areas), areas)
        relatorio._validar_altura_pagina(pagina, f"capa com bloco {inicio}")

        tabela = next(
            el for el in pagina
            if getattr(el, "_cellvalues", None)
            and el._cellvalues[0][0] == "Área"
        )
        for linha, area in enumerate(areas, start=1):
            assert tabela._cellvalues[linha][0] == f"{area.sigla} · {area.nome}"
            assert tabela._cellvalues[linha][1].endswith(f" · {area.co_prova}")

    casos = [
        ("LC", "Linguagens, Códigos e suas Tecnologias", "laranja_atendimento_especializado", 1632),
        ("CH", "Ciências Humanas e suas Tecnologias", "branca", 1585),
        ("CN", "Ciências da Natureza e suas Tecnologias", "laranja_ampliada", 1623),
        ("MT", "Matemática e suas Tecnologias", "roxa_videoprova_libras_superampliada", 1393),
    ]
    areas_caso = []
    for sigla, nome, cor, codigo in casos:
        area = _criar_area_sintetica(sigla, nome, 10, prova=(2025, codigo))
        area.cor_prova = cor
        areas_caso.append(area)
    resumo = tabela_resumo_areas(areas_caso)
    assert [resumo._cellvalues[i][1] for i in range(1, 5)] == [
        "Laranja atend. esp. · 1632",
        "Branca · 1585",
        "Laranja ampliada · 1623",
        "Roxa Libras superampl. · 1393",
    ]


def test_tabela_resumo_areas_usa_reticencias_em_ultimo_caso_e_preserva_codigo():
    area = _criar_area_sintetica(
        "LC", "Linguagens, Códigos e suas Tecnologias", 10, prova=(2025, 1632),
    )
    area.cor_prova = "caderno_experimental_com_descricao_extremamente_extensa"
    resumo = tabela_resumo_areas([area])
    RelatorioPDF()._validar_altura_pagina([resumo], "resumo com reticências")
    celula = resumo._cellvalues[1][1]
    assert "..." in celula
    assert celula.endswith(" · 1632")


def test_validador_detecta_vazamento_horizontal_em_tabela():
    from reportlab.platypus import Table, TableStyle

    tabela = Table([["Texto curto", "Texto excessivamente longo para caber nesta coluna"]], colWidths=[80, 40])
    tabela.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
    ]))
    with pytest.raises(RuntimeError, match="vaza na célula"):
        RelatorioPDF()._validar_altura_pagina([tabela], "tabela inválida")


@pytest.mark.parametrize("cenario, definicoes", [
    ("atendimento_especializado_e_ampliada", [
        ("LC", "Linguagens, Códigos e suas Tecnologias", "laranja_atendimento_especializado", 1632),
        ("CH", "Ciências Humanas e suas Tecnologias", "branca", 1585),
        ("CN", "Ciências da Natureza e suas Tecnologias", "laranja_ampliada", 1623),
        ("MT", "Matemática e suas Tecnologias", "azul", 1607),
    ]),
    ("cadernos_especiais_mais_longos", [
        ("LC", "Linguagens, Códigos e suas Tecnologias", "roxa_videoprova_libras_superampliada", 1393),
        ("CH", "Ciências Humanas e suas Tecnologias", "laranja_adaptada_ledor_segunda_oportunidade", 1042),
        ("CN", "Ciências da Natureza e suas Tecnologias", "laranja_adaptada_ledor_reaplicacao", 1370),
        ("MT", "Matemática e suas Tecnologias", "verde_superampliada_reaplicacao", 1368),
    ]),
    ("reticencias_em_nome_extremo", [
        ("LC", "Linguagens, Códigos e suas Tecnologias", "caderno_experimental_com_descricao_extremamente_extensa", 1632),
        ("MT", "Matemática e suas Tecnologias", "roxa_videoprova_libras_ampliada", 1416),
    ]),
])
def test_pdf_gerado_para_provas_especiais_nao_sobrepoe_colunas_na_primeira_pagina(
    cenario, definicoes, tmp_path,
):
    from reportlab.pdfbase.pdfmetrics import stringWidth

    areas = []
    for sigla, nome, cor, codigo in definicoes:
        area = _criar_area_sintetica(sigla, nome, 15, prova=(2025, codigo))
        area.cor_prova = cor
        areas.append(area)

    caminho, reader = _gerar(tmp_path, areas, f"especiais-{cenario}.pdf")
    assert caminho.exists()
    assert len(reader.pages) == len(areas) + 1

    por_linha = {}

    def visitar_texto(texto, cm_mat, tm_mat, font_dict, font_size):
        limpo = texto.strip()
        if not limpo:
            return
        fonte = (
            font_dict.get("/BaseFont", "/Helvetica").lstrip("/")
            if font_dict else "Helvetica"
        )
        x = cm_mat[0] * tm_mat[4] + cm_mat[2] * tm_mat[5] + cm_mat[4]
        y = cm_mat[1] * tm_mat[4] + cm_mat[3] * tm_mat[5] + cm_mat[5]
        largura = stringWidth(limpo, fonte, font_size)
        por_linha.setdefault(round(y, 1), []).append((x, x + largura, limpo))

    reader.pages[0].extract_text(visitor_text=visitar_texto)
    linhas_tabela = [
         sorted(itens, key=lambda item: item[0])
        for itens in por_linha.values()
        if len(itens) == 6
    ]
    assert len(linhas_tabela) == 1 + len(areas)
    for linha in linhas_tabela:
        for (_, x1, texto_esq), (x0_dir, _, texto_dir) in zip(linha, linha[1:]):
            assert x1 + 4.0 <= x0_dir, (
                f"Colisão horizontal na 1ª página entre {texto_esq!r} ({x1:.1f}) "
                f"e {texto_dir!r} ({x0_dir:.1f})"
            )

    texto_capa = reader.pages[0].extract_text() or ""
    for area in areas:
        assert f"· {area.co_prova}" in texto_capa

    # Nas páginas analíticas individuais o nome completo do caderno continua visível.
    for pagina, area in zip(reader.pages[1:], areas):
        texto_pagina = pagina.extract_text() or ""
        assert f"Prova {area.co_prova} · {formatar_cor(area.cor_prova)}" in texto_pagina
