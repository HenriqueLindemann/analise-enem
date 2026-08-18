# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Testes para detecção e exibição de questões anuladas (TRI, PDF e Web).
"""

import os
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
import pytest

import _utils
_utils.add_src_to_path()

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# O núcleo deve rodar com a instalação CLI. Os imports opcionais ficam
# isolados para que somente os testes dos respectivos adaptadores sejam pulados.
from tri_enem import CalculadorTRI, MapeadorProvas, SimuladorNota
from tri_enem.posicoes import normalizar_posicoes_resultados
from tri_enem.relatorios.base import DadosRelatorio, AreaAnalise, QuestaoAnalise
from tri_enem.relatorios import adaptar_resultados_para_relatorio

try:
    from tri_enem.relatorios.gerador import RelatorioPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from streamlit_app.calculador import CalculadorEnem
    from streamlit_app.components.graficos import (
        grade_questoes as st_grade_questoes,
        grafico_impacto as st_grafico_impacto,
    )
    HAS_WEB = True
except ImportError:
    HAS_WEB = False


@pytest.fixture(scope="module")
def calc():
    return CalculadorTRI()


def test_calcular_nota_com_questao_anulada(calc):
    # Prova 2024 CN 1a aplicação verde (cod 1421) tem 1 questão anulada (Q124)
    respostas = "A" * 45
    resultado = calc.calcular_nota(2024, "CN", 1421, respostas)

    assert "total_anulados" in resultado
    assert "questoes_anuladas" in resultado
    assert resultado["total_anulados"] == 1
    assert 124 in resultado["questoes_anuladas"]
    assert resultado["total_itens"] == 44  # 45 - 1


def test_analisar_todas_questoes_com_multiplas_anuladas(calc):
    # Prova 2023 MT 1a aplicação azul (cod 1211) tem 2 questões anuladas (Q161 e Q164)
    respostas = "A" * 45
    analise = calc.analisar_todas_questoes(2023, "MT", 1211, respostas)

    assert "anuladas" in analise
    assert "total_anulados" in analise
    assert "questoes_anuladas" in analise
    assert analise["total_anulados"] == 2
    assert sorted(analise["questoes_anuladas"]) == [161, 164]
    assert len(analise["anuladas"]) == 2
    assert analise["total_itens"] == 43


@pytest.mark.parametrize(
    ("ano", "area", "co_prova", "lingua", "brutas", "caderno"),
    [
        (2009, "CN", 49, None, [27, 31], [72, 76]),
        (2016, "LC", 299, "ingles", [23, 39], [113, 129]),
    ],
)
def test_resultado_nota_resumido_expoe_numero_do_caderno(
    ano, area, co_prova, lingua, brutas, caderno
):
    resultado = SimuladorNota().calcular(
        area, ano, "A" * 45, lingua=lingua, co_prova=co_prova
    )

    assert resultado.questoes_anuladas == caderno
    assert resultado.questoes_anuladas_brutas == brutas


def test_normalizacao_nao_muta_resultado_detalhado_e_recalcula_anuladas():
    original = {
        "sigla": "CN",
        "anuladas": [
            {"idx_area": 26, "posicao": 27, "anulada": True},
            {"idx_area": 30, "posicao": 31, "anulada": True},
        ],
        "questoes_anuladas": [27, 31],
    }
    antes = deepcopy(original)

    normalizado = normalizar_posicoes_resultados(
        [original], ["CH", "CN", "LC", "MT"]
    )

    assert original == antes
    assert normalizado[0] is not original
    assert [q["posicao"] for q in normalizado[0]["anuladas"]] == [72, 76]
    assert normalizado[0]["questoes_anuladas"] == [72, 76]
    assert normalizado[0]["questoes_anuladas_caderno"] == [72, 76]

    segunda = normalizar_posicoes_resultados(
        normalizado, ["CH", "CN", "LC", "MT"]
    )
    assert segunda == normalizado


def test_prova_sem_questao_anulada(calc):
    # Prova 2024 MT 1a aplicação verde (cod 1409) não possui questão anulada
    respostas = "A" * 45
    resultado = calc.calcular_nota(2024, "MT", 1409, respostas)
    assert resultado["total_anulados"] == 0
    assert resultado["questoes_anuladas"] == []
    assert resultado["total_itens"] == 45

    analise = calc.analisar_todas_questoes(2024, "MT", 1409, respostas)
    assert analise["total_anulados"] == 0
    assert analise["anuladas"] == []
    assert analise["questoes_anuladas"] == []
    assert analise["total_itens"] == 45


@pytest.mark.parametrize(
    ("ano", "area", "co_prova", "esperadas"),
    [
        (2009, "CN", 49, [72, 76]),
        (2016, "LC", 299, [113, 129]),
    ],
)
@pytest.mark.skipif(not HAS_WEB, reason="extra web não instalado")
def test_streamlit_renumera_anuladas_conforme_ordem_do_caderno(
    ano, area, co_prova, esperadas
):
    calc_enem = CalculadorEnem()
    mapeador = MapeadorProvas()
    cor = next(
        prova.cor
        for prova in mapeador.listar_todas_provas(ano)
        if prova.codigo == co_prova
    )

    resultado = calc_enem.calcular_area(
        ano=ano,
        area=area,
        respostas="A" * 45,
        cor=cor,
        tipo_aplicacao="1a_aplicacao",
    )

    assert sorted(resultado["questoes_anuladas"]) == esperadas
    assert sorted(q["posicao"] for q in resultado["anuladas"]) == esperadas


def test_area_analise_propriedades_anuladas():
    questoes = [
        QuestaoAnalise(posicao=1, gabarito='A', resposta_dada='A', acertou=True, param_a=1.0, param_b=0.0, param_c=0.2, impacto=10.0),
        QuestaoAnalise(posicao=2, gabarito='B', resposta_dada='C', acertou=False, param_a=1.0, param_b=0.5, param_c=0.2, impacto=15.0),
        QuestaoAnalise(posicao=3, gabarito='X', resposta_dada='.', acertou=False, param_a=0.0, param_b=0.0, param_c=0.0, impacto=0.0, anulada=True),
    ]
    area = AreaAnalise(
        sigla="CN",
        nome="Ciências da Natureza",
        ano=2024,
        co_prova=1421,
        nota=650.0,
        theta=0.5,
        acertos=1,
        total_itens=2,
        questoes=questoes,
    )

    assert area.total_anulados == 1
    assert len(area.questoes_anuladas) == 1
    assert area.questoes_anuladas[0].posicao == 3
    assert len(area.questoes_acertadas) == 1
    assert len(area.questoes_erradas) == 1
    assert area.texto_anuladas_breve() == "1 anulada (Q3)"


def test_area_analise_formata_plural_de_anuladas():
    questoes = [
        QuestaoAnalise(
            posicao=3,
            gabarito='X',
            resposta_dada='.',
            acertou=False,
            param_a=0.0,
            param_b=0.0,
            param_c=0.0,
            impacto=0.0,
            anulada=True,
        ),
        QuestaoAnalise(
            posicao=4,
            gabarito='X',
            resposta_dada='A',
            acertou=False,
            param_a=0.0,
            param_b=0.0,
            param_c=0.0,
            impacto=0.0,
            anulada=True,
        ),
    ]
    area = AreaAnalise(
        sigla="CN",
        nome="Ciências da Natureza",
        ano=2024,
        co_prova=1421,
        nota=650.0,
        theta=0.5,
        acertos=0,
        total_itens=0,
        questoes=questoes,
    )

    assert area.texto_anuladas_breve() == "2 anuladas (Q3, Q4)"


def test_cli_formata_singular_e_plural_de_anuladas():
    from meu_simulado import formatar_contagem_resultado

    base = {'acertos': 10, 'total_itens': 44}
    assert formatar_contagem_resultado({**base, 'total_anulados': 1}) == (
        "10/44 válidas + 1 anulada"
    )
    assert formatar_contagem_resultado({**base, 'total_anulados': 2}) == (
        "10/44 válidas + 2 anuladas"
    )


@pytest.mark.skipif(not HAS_PDF, reason="extra PDF não instalado")
def test_geracao_relatorio_pdf_com_anulada():
    questoes = [
        QuestaoAnalise(posicao=1, gabarito='A', resposta_dada='A', acertou=True, param_a=1.0, param_b=0.0, param_c=0.2, impacto=10.0),
        QuestaoAnalise(posicao=2, gabarito='B', resposta_dada='C', acertou=False, param_a=1.0, param_b=0.5, param_c=0.2, impacto=15.0),
        QuestaoAnalise(posicao=124, gabarito='X', resposta_dada='.', acertou=False, param_a=0.0, param_b=0.0, param_c=0.0, impacto=0.0, anulada=True),
    ]
    area = AreaAnalise(
        sigla="CN",
        nome="Ciências da Natureza",
        ano=2024,
        co_prova=1421,
        nota=650.0,
        theta=0.5,
        acertos=1,
        total_itens=2,
        questoes=questoes,
        cor_prova="Verde",
    )
    dados = DadosRelatorio(
        titulo="Simulado ENEM 2024",
        ano_prova=2024,
        areas=[area],
    )

    relatorio = RelatorioPDF()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        caminho_gerado = relatorio.gerar(dados, tmp_path)
        assert os.path.exists(caminho_gerado)
        assert os.path.getsize(caminho_gerado) > 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.skipif(not (HAS_PDF and HAS_WEB), reason="extras web/PDF não instalados")
def test_geradores_aceitam_resultado_resumido(tmp_path, calc):
    resultado = calc.calcular_nota(2024, "CN", 1421, "A" * 45)

    from streamlit_app.components.impressao import _gerar_pdf

    pdf_web = _gerar_pdf([resultado], 2024, "1a_aplicacao", "verde")
    assert pdf_web and pdf_web.startswith(b"%PDF-")

    import meu_simulado

    caminho = tmp_path / "resumido.pdf"
    pdf_cli = meu_simulado.gerar_relatorio_pdf(
        [resultado],
        2024,
        "Simulado",
        str(caminho),
    )
    assert pdf_cli == str(caminho.absolute())
    assert caminho.read_bytes().startswith(b"%PDF-")


@pytest.mark.parametrize(
    ("ano", "area", "co_prova", "esperadas"),
    [
        (2009, "CN", 49, [72, 76]),
        (2016, "LC", 299, [113, 129]),
    ],
)
@pytest.mark.skipif(not (HAS_PDF and HAS_WEB), reason="extras web/PDF não instalados")
def test_pdf_gera_resultado_de_prova_antiga_com_numero_do_caderno(
    tmp_path, ano, area, co_prova, esperadas
):
    calc_enem = CalculadorEnem()
    mapeador = MapeadorProvas()
    cor = next(
        prova.cor
        for prova in mapeador.listar_todas_provas(ano)
        if prova.codigo == co_prova
    )
    resultado = calc_enem.calcular_area(
        ano=ano,
        area=area,
        respostas="A" * 45,
        cor=cor,
        tipo_aplicacao="1a_aplicacao",
    )

    from streamlit_app.components.impressao import _gerar_pdf

    assert sorted(q["posicao"] for q in resultado["anuladas"]) == esperadas
    pdf_web = _gerar_pdf([resultado], ano, "1a_aplicacao", cor)
    assert pdf_web and pdf_web.startswith(b"%PDF-")

    import meu_simulado

    caminho_cli = tmp_path / f"{ano}_{area}.pdf"
    pdf_cli = meu_simulado.gerar_relatorio_pdf(
        [resultado], ano, "Simulado", str(caminho_cli)
    )
    assert pdf_cli == str(caminho_cli.absolute())
    assert caminho_cli.read_bytes().startswith(b"%PDF-")


@pytest.mark.skipif(not HAS_WEB, reason="extra web não instalado")
def test_graficos_streamlit_com_anulada():
    questoes_st = [
        {'posicao': 1, 'acertou': True, 'anulada': False, 'impacto': 10.0, 'gabarito': 'A', 'resposta_dada': 'A'},
        {'posicao': 2, 'acertou': False, 'anulada': False, 'impacto': 15.0, 'gabarito': 'B', 'resposta_dada': 'C'},
        {'posicao': 124, 'acertou': False, 'anulada': True, 'impacto': 0.0, 'gabarito': 'X', 'resposta_dada': '.'},
    ]
    fig_grade = st_grade_questoes(questoes_st)
    assert fig_grade is not None
    assert len(fig_grade.data) == 3

    fig_impacto = st_grafico_impacto(questoes_st)
    assert fig_impacto is not None
    # Deve conter apenas as 2 válidas
    assert len(fig_impacto.data[0].x) == 2


@pytest.mark.skipif(not HAS_WEB, reason="extra web não instalado")
def test_graficos_tratam_entrada_vazia_ou_colunas_invalidas():
    from streamlit_app.components.graficos import grafico_pizza_acertos

    fig = grafico_pizza_acertos(0, 0)
    assert not fig.data
    assert fig.layout.annotations[0].text == "Sem dados"

    with pytest.raises(ValueError, match="colunas"):
        st_grade_questoes([], colunas=0)


@pytest.mark.skipif(not HAS_WEB, reason="extra web não instalado")
def test_calculador_enem_wrapper():
    calc_enem = CalculadorEnem()
    resultado = calc_enem.calcular_area(
        ano=2024,
        area="CN",
        respostas="A" * 45,
        cor="verde",
        tipo_aplicacao="1a_aplicacao",
    )
    assert resultado is not None
    assert "total_anulados" in resultado
    assert "questoes_anuladas" in resultado
    assert resultado["total_anulados"] == 1
    assert 124 in resultado["questoes_anuladas"]


@pytest.mark.parametrize(
    ("ano", "area", "co_prova", "lingua", "esperadas", "brutas"),
    [
        (2009, "CN", 49, None, [72, 76], [27, 31]),
        (2016, "LC", 299, "ingles", [113, 129], [23, 39]),
        (2023, "MT", 1211, None, [161, 164], [161, 164]),
    ],
)
@pytest.mark.skipif(not HAS_WEB, reason="extra web não instalado")
def test_interfaces_e_adaptador_usam_as_mesmas_posicoes(
    ano, area, co_prova, lingua, esperadas, brutas
):
    import meu_simulado

    mapeador = MapeadorProvas()
    info = next(
        prova for prova in mapeador.listar_todas_provas(ano)
        if prova.codigo == co_prova
    )
    respostas = "A" * 45

    resumido = SimuladorNota().calcular(
        area, ano, respostas, lingua=lingua, co_prova=co_prova
    )
    calculador = CalculadorTRI()
    calculador_enem = CalculadorEnem()
    resultado_web = calculador_enem.calcular_area(
        ano=ano,
        area=area,
        respostas=respostas,
        cor=info.cor,
        tipo_aplicacao=info.tipo_aplicacao,
        lingua=lingua or "ingles",
    )
    resultado_cli = meu_simulado.calcular_e_analisar(
        calculador,
        area,
        ano,
        respostas,
        lingua=lingua,
        co_prova=co_prova,
        tipo_aplicacao=info.tipo_aplicacao,
    )
    analise_avancada = calculador.analisar_todas_questoes(
        ano, area, co_prova, respostas,
        None if lingua is None else (0 if lingua == "ingles" else 1),
    )

    assert resumido.questoes_anuladas == esperadas
    assert resumido.questoes_anuladas_brutas == brutas
    assert resultado_web["questoes_anuladas"] == esperadas
    assert resultado_cli["questoes_anuladas"] == esperadas
    assert [q["posicao"] for q in resultado_web["anuladas"]] == esperadas
    assert [q["posicao"] for q in resultado_cli["anuladas"]] == esperadas
    assert resultado_web["nota"] == pytest.approx(resumido.nota)
    assert resultado_cli["nota"] == pytest.approx(resumido.nota)

    for resultado in (resultado_web, resultado_cli, analise_avancada):
        dados = adaptar_resultados_para_relatorio([resultado], ano)
        area_relatorio = dados.areas[0]
        assert [q.posicao for q in area_relatorio.questoes_anuladas] == esperadas


@pytest.mark.skipif(not (HAS_PDF and HAS_WEB), reason="extras web/PDF não instalados")
def test_dois_geradores_enviam_dados_equivalentes_sem_mutar_resultados(
    monkeypatch, tmp_path
):
    import meu_simulado
    from streamlit_app.components.impressao import _gerar_pdf

    mapeador = MapeadorProvas()
    info = next(
        prova for prova in mapeador.listar_todas_provas(2009)
        if prova.codigo == 49
    )
    resultado_web = CalculadorEnem().calcular_area(
        ano=2009,
        area="CN",
        respostas="A" * 45,
        cor=info.cor,
        tipo_aplicacao=info.tipo_aplicacao,
    )
    resultado_cli = deepcopy(resultado_web)
    antes_web = deepcopy(resultado_web)
    antes_cli = deepcopy(resultado_cli)
    enviados = []

    from tri_enem.relatorios.gerador import RelatorioPDF

    def capturar(self, dados, caminho):
        enviados.append(dados)
        Path(caminho).write_bytes(b"%PDF-test")
        return str(caminho)

    monkeypatch.setattr(RelatorioPDF, "gerar", capturar)

    assert _gerar_pdf([resultado_web], 2009, info.tipo_aplicacao, info.cor)
    caminho = tmp_path / "cli.pdf"
    assert meu_simulado.gerar_relatorio_pdf(
        [resultado_cli], 2009, "Simulado", str(caminho),
        tipo_aplicacao=info.tipo_aplicacao,
        cor_prova=info.cor,
    ) == str(caminho.absolute())

    assert resultado_web == antes_web
    assert resultado_cli == antes_cli
    assert len(enviados) == 2

    assinaturas = [
        [
            (
                area.sigla,
                area.nota,
                area.acertos,
                area.total_itens,
                [(q.posicao, q.anulada) for q in area.questoes],
            )
            for area in dados.areas
        ]
        for dados in enviados
    ]
    assert assinaturas[0] == assinaturas[1]
    assert [q.posicao for q in enviados[0].areas[0].questoes_anuladas] == [72, 76]
