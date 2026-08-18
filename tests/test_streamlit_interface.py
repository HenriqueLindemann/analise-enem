# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Interface web: app.py, componentes de gráfico e relatório em PDF.

`test_e2e_usuario.py` cobre o cálculo, mas nunca executa a interface. Aqui o app
roda pelo AppTest do Streamlit.

As respostas são escritas direto em `session_state` porque o campo de digitação
é um componente de terceiros (`streamlit-keyup`) que o AppTest não aciona; a
chave é a mesma que ele escreve.
"""

import json
from pathlib import Path

import pytest

import _utils

_utils.add_src_to_path()

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

# Quem usa só o CLI não instala o streamlit; a suíte pula em vez de quebrar.
# A CI instala streamlit_app/requirements.txt, então lá nunca pula.
pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(ROOT / "streamlit_app" / "app.py")
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# O padrão de 3 s do AppTest não cobre a carga dos parâmetros.
TIMEOUT = 180


@pytest.fixture(scope="module")
def exemplos():
    with open(FIXTURES / "exemplos_microdados.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def caso_real(exemplos):
    """Um participante de 2023, com as quatro áreas e a nota oficial."""
    por_area = {}
    for area in ("LC", "CH", "CN", "MT"):
        e = next(x for x in exemplos if x["ano"] == 2023 and x["area"] == area)
        por_area[area] = e
    return por_area


def _questoes_para_grafico(resultado):
    """Mesma conversão de `resultados.py`: duas listas viram uma, com `acertou`."""
    questoes = []
    for q in resultado.get("questoes_acertadas", []):
        questoes.append({**q, "acertou": True,
                         "impacto": q.get("perda_se_errasse", 0)})
    for q in resultado.get("questoes_erradas", []):
        questoes.append({**q, "acertou": False,
                         "impacto": q.get("ganho_se_acertasse", 0)})
    return questoes


def _app_com_respostas(respostas_por_area):
    """Roda o app com as respostas já digitadas em cada área."""
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    for area, respostas in respostas_por_area.items():
        at.session_state[f"resp_{area.lower()}"] = respostas
    return at


class TestAppExecuta:
    """O app sobe e responde."""

    def test_app_roda_sem_excecao(self):
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
        at.run()
        assert not at.exception, at.exception

    def test_controles_essenciais_estao_presentes(self):
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
        at.run()
        rotulos = {s.label for s in at.selectbox}
        assert "Ano da prova" in rotulos
        assert "Tipo de aplicação" in rotulos
        assert "Língua estrangeira" in rotulos
        # Uma seleção de cor por área
        assert {"cor_LC", "cor_CH", "cor_CN", "cor_MT"} <= {
            s.key for s in at.selectbox if s.key
        }
        assert any("CALCULAR" in (b.label or "").upper() for b in at.button)
        assert any(
            "Agora com mais precisão!" in bloco.value
            for bloco in at.markdown
        )

    @pytest.mark.parametrize("ano", [2009, 2015, 2020, 2023, 2025])
    def test_troca_de_ano_nao_quebra(self, ano):
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
        at.run()
        seletor = next(s for s in at.selectbox if s.label == "Ano da prova")
        # As opções chegam já formatadas pelo format_func, como texto.
        assert str(ano) in seletor.options, f"{ano} não ofertado na interface"
        seletor.set_value(ano).run()
        assert not at.exception, at.exception
        assert at.session_state["ano_respostas"] == ano


class TestFluxoCompleto:
    """Digitar, calcular e ver a nota."""

    def test_calculo_produz_nota_correta_na_sessao(self, caso_real):
        """Ano, cor e língua vêm do exemplo, exercitando a resolução da prova."""
        from tri_enem import MapeadorProvas

        mapeador = MapeadorProvas()
        at = _app_com_respostas({a: e["respostas"] for a, e in caso_real.items()})

        at.selectbox[0].set_value(2023)          # Ano da prova
        for area, e in caso_real.items():
            info = next(p for p in mapeador.listar_todas_provas(2023)
                        if p.codigo == int(e["co_prova"]))
            at.session_state[f"cor_{area}"] = info.cor
        lingua = "espanhol" if int(caso_real["LC"]["tp_lingua"]) == 1 else "ingles"
        next(s for s in at.selectbox
             if s.label == "Língua estrangeira").set_value(lingua)
        at.run()

        botao = next(b for b in at.button if "CALCULAR" in (b.label or "").upper())
        botao.click().run()

        assert not at.exception, at.exception
        assert "resultados" in at.session_state, \
            "o cálculo não gravou resultados na sessão"
        resultados = at.session_state["resultados"]
        assert resultados

        por_area = {r["sigla"]: r for r in resultados}
        assert set(por_area) == {"LC", "CH", "CN", "MT"}
        for area, e in caso_real.items():
            calculada = por_area[area]["nota"]
            oficial = float(e["nota_oficial"])
            assert abs(calculada - oficial) < 2.0, (
                f"{area}: web deu {calculada:.2f}, oficial {oficial:.2f}"
            )

    @pytest.mark.parametrize("ano,co_prova,tem_alerta", [
        (2017, 403, True),    # erro_alto: não reproduz a nota oficial
        (2023, 1211, False),  # ok
    ])
    def test_prova_nao_confiavel_exibe_alerta(self, exemplos, ano, co_prova,
                                              tem_alerta):
        """Prova com erro_alto exibe mensagem discreta indicando variação relevante."""
        from tri_enem import MapeadorProvas

        e = next(x for x in exemplos if x["ano"] == ano and x["area"] == "MT")
        info = next(p for p in MapeadorProvas().listar_todas_provas(ano)
                    if p.codigo == co_prova)

        at = _app_com_respostas({"MT": e["respostas"]})
        at.selectbox[0].set_value(ano)
        at.session_state["cor_MT"] = info.cor
        at.run()
        next(b for b in at.button
             if "CALCULAR" in (b.label or "").upper()).click().run()

        resultado = [r for r in at.session_state["resultados"]
                     if r["sigla"] == "MT"][0]
        assert resultado["co_prova"] == co_prova
        resumo = resultado["resumo_validacao"]
        assert "erro médio" in resumo
        assert "maior diferença" in resumo
        assert "MAE" not in resumo
        assert "p95" not in resumo
        assert "aviso_forte" not in resumo
        if tem_alerta:
            assert resultado["severidade_precisao"] == "alerta"
            assert any(
                "variação relevante" in m.value.lower()
                for m in at.markdown
            )
        else:
            assert "boa" in resultado["aviso_precisao"].lower()
            assert resultado["severidade_precisao"] == "sucesso"
            assert any(
                "boa" in m.value.lower() and "calibração" in m.value.lower()
                for m in at.markdown
            )

    def test_calcular_sem_respostas_avisa_e_nao_quebra(self):
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
        at.run()
        botao = next(b for b in at.button if "CALCULAR" in (b.label or "").upper())
        botao.click().run()
        assert not at.exception, at.exception
        assert "resultados" not in at.session_state

    def test_expander_formata_plural_de_questoes_anuladas(self):
        from tri_enem import MapeadorProvas

        info = next(
            prova
            for prova in MapeadorProvas().listar_todas_provas(2023)
            if prova.codigo == 1211
        )
        at = _app_com_respostas({"MT": "A" * 45})
        at.selectbox[0].set_value(2023)
        at.session_state["cor_MT"] = info.cor
        at.run()
        next(
            b for b in at.button
            if "CALCULAR" in (b.label or "").upper()
        ).click().run()

        labels = [expander.label for expander in at.expander]
        assert any("Q161, Q164 anuladas" in label for label in labels)

    def test_respostas_incompletas_nao_produzem_nota(self, caso_real):
        at = _app_com_respostas({"MT": caso_real["MT"]["respostas"][:30]})
        at.run()
        botao = next(b for b in at.button if "CALCULAR" in (b.label or "").upper())
        botao.click().run()
        assert not at.exception, at.exception
        assert "resultados" not in at.session_state


class TestValidacaoDaEntrada:

    @pytest.mark.parametrize(
        "entrada,valida",
        [
            ("A" * 45, True),
            ("ABCDE" * 9, True),
            ("A" * 44 + ".", True),        # ponto = não respondida
            ("A" * 44, False),             # curta
            ("A" * 46, False),             # longa
            ("X" * 45, False),             # letra fora de A-E
        ],
    )
    def test_validar_todas_respostas(self, entrada, valida):
        from streamlit_app.components.inputs import validar_todas_respostas

        ok, erros = validar_todas_respostas({"MT": entrada})
        assert ok is valida, erros


@pytest.fixture(scope="module")
def resultado(exemplos):
    """Saída do motor para uma prova de 2023."""
    from streamlit_app.calculador import CalculadorEnem

    e = next(x for x in exemplos if x["ano"] == 2023 and x["area"] == "MT")
    return CalculadorEnem().calcular_area(
        ano=2023, area="MT", respostas=e["respostas"],
        cor="azul", tipo_aplicacao="1a_aplicacao",
    )


@pytest.fixture(scope="module")
def resultados_quatro_areas(exemplos):
    """As quatro áreas de um participante, como o PDF recebe."""
    from streamlit_app.calculador import CalculadorEnem

    calc = CalculadorEnem()
    saida = []
    for area in ("LC", "CH", "CN", "MT"):
        e = next(x for x in exemplos if x["ano"] == 2023 and x["area"] == area)
        r = calc.calcular_area(
            ano=2023, area=area, respostas=e["respostas"],
            cor="azul", tipo_aplicacao="1a_aplicacao",
        )
        if r:
            saida.append(r)
    return saida


class TestGraficos:
    """Chamados com a saída real do motor, para pegar mudança de chave."""

    def test_grade_de_questoes_tem_um_marcador_por_questao(self, resultado):
        from streamlit_app.components.graficos import grade_questoes

        questoes = _questoes_para_grafico(resultado)
        fig = grade_questoes(questoes)
        assert len(fig.data) == len(questoes)

    def test_grade_marca_acerto_e_erro_conforme_o_resultado(self, resultado):
        from streamlit_app.components.graficos import grade_questoes

        questoes = _questoes_para_grafico(resultado)
        fig = grade_questoes(questoes)
        rotulos = [t.hovertext or '' for t in fig.data]
        texto = ' '.join(str(r) for r in rotulos)
        assert texto.count('Acerto') == resultado['acertos']

    def test_pizza_soma_o_total_de_questoes(self, resultado):
        from streamlit_app.components.graficos import grafico_pizza_acertos

        acertos = resultado["acertos"]
        erros = len(resultado["questoes_erradas"])
        fig = grafico_pizza_acertos(acertos, erros)
        assert sum(fig.data[0].values) == acertos + erros

    def test_grafico_de_impacto_aceita_prova_sem_erros(self, resultado):
        """Quem acertou tudo não tem lista de erros."""
        from streamlit_app.components.graficos import grafico_impacto

        assert grafico_impacto([], titulo="MT") is not None

    def test_grafico_de_barras(self, resultado):
        from streamlit_app.components.graficos import grafico_notas_barras

        assert grafico_notas_barras([resultado]) is not None


class TestRelatorioPDF:
    """Geração do PDF, via src/tri_enem/relatorios/."""

    @pytest.mark.parametrize(
        ("severidade", "estilo"),
        [
            ("sucesso", "ValidacaoBoa"),
            ("info", "ValidacaoMedia"),
            ("atencao", "ValidacaoMedia"),
            ("alerta", "ValidacaoBaixa"),
            ("desconhecida", "ValidacaoBaixa"),
        ],
    )
    def test_cor_da_validacao_reflete_a_severidade(self, severidade, estilo):
        from tri_enem.relatorios.estilos import Cores, criar_estilos
        from tri_enem.relatorios.gerador import _estilo_validacao

        estilos = criar_estilos()
        fundos = {
            "ValidacaoBoa": Cores.ACERTO_CLARO,
            "ValidacaoMedia": Cores.ATENCAO_CLARO,
            "ValidacaoBaixa": Cores.ERRO_CLARO,
        }
        assert _estilo_validacao(severidade) == estilo
        assert estilos[estilo].backColor == fundos[estilo]

    def test_pdf_e_gerado_e_valido(self, resultados_quatro_areas):
        from streamlit_app.components.impressao import _gerar_pdf

        pdf = _gerar_pdf(resultados_quatro_areas, 2023, "1a_aplicacao", "azul")
        assert pdf is not None, "geração do PDF devolveu None"
        assert pdf.startswith(b"%PDF-"), "saída não é um PDF"
        assert pdf.rstrip().endswith(b"%%EOF"), "PDF truncado"
        assert len(pdf) > 10_000, f"PDF pequeno demais ({len(pdf)} bytes)"

    def test_pdf_de_uma_unica_area(self, resultados_quatro_areas):
        from streamlit_app.components.impressao import _gerar_pdf

        pdf = _gerar_pdf(resultados_quatro_areas[:1], 2023, "1a_aplicacao", "azul")
        assert pdf is not None and pdf.startswith(b"%PDF-")

    def test_pdf_sem_resultados_nao_estoura(self):
        from streamlit_app.components.impressao import _gerar_pdf

        pdf = _gerar_pdf([], 2023, "1a_aplicacao", "azul")
        assert pdf is None or pdf.startswith(b"%PDF-")


class TestAvisoAcuracia:
    """Verifica formatação discreta e curta dos avisos de acurácia com cores e negrito."""

    @pytest.mark.parametrize(
        "resultado_mock,esperado_contem,cor_esperada",
        [
            (
                {"status_precisao": "ok", "severidade_precisao": "sucesso", "aviso_precisao": "x"},
                "boa",
                "#15803D",
            ),
            (
                {
                    "status_precisao": "outro",
                    "perfil_precisao": "calibracao_verificada",
                    "aviso_precisao": "x",
                },
                "boa",
                "#15803D",
            ),
            (
                {
                    "status_precisao": "aviso_forte",
                    "perfil_precisao": "boa_na_maioria_com_excecoes",
                    "severidade_precisao": "atencao",
                    "aviso_precisao": "x",
                },
                "moderada",
                "#B45309",
            ),
            (
                {
                    "status_precisao": "sem_participantes",
                    "severidade_precisao": "atencao",
                    "aviso_precisao": "x",
                },
                "ajuste médio",
                "#B45309",
            ),
            (
                {
                    "status_precisao": "sem_itens",
                    "severidade_precisao": "alerta",
                    "aviso_precisao": "x",
                },
                "não possui calibração",
                "#B91C1C",
            ),
            (
                {
                    "status_precisao": "nao_calibrado",
                    "severidade_precisao": "atencao",
                    "aviso_precisao": "x",
                },
                "não possui calibração verificada",
                "#B45309",
            ),
            (
                {
                    "status_precisao": "erro_alto",
                    "severidade_precisao": "alerta",
                    "aviso_precisao": "x",
                },
                "ruim",
                "#B91C1C",
            ),
            (
                {
                    "status_precisao": "aviso_leve",
                    "severidade_precisao": "atencao",
                    "aviso_precisao": "x",
                },
                "estimada",
                "#B45309",
            ),
            (
                {
                    "status_precisao": "desconhecido",
                    "aviso_precisao": "x",
                },
                "estimada",
                "#B45309",
            ),
        ],
    )
    def test_formatar_aviso_curto(self, resultado_mock, esperado_contem, cor_esperada):
        from streamlit_app.components.resultados import formatar_aviso_curto

        aviso_curto = formatar_aviso_curto(resultado_mock)
        assert aviso_curto
        assert aviso_curto.startswith("Esta prova")
        assert esperado_contem.lower() in aviso_curto.lower()
        assert cor_esperada.lower() in aviso_curto.lower()
        assert "font-weight: bold" in aviso_curto.lower()

    def test_formatar_aviso_curto_vazio_quando_sem_aviso(self):
        from streamlit_app.components.resultados import formatar_aviso_curto

        assert formatar_aviso_curto({}) == ""
        assert formatar_aviso_curto({"nota": 500.0}) == ""

    def test_exibir_aviso_acuracia_renderiza_markdown_com_html(self, monkeypatch):
        import streamlit as st
        from streamlit_app.components.resultados import exibir_aviso_acuracia

        markdown_calls = []
        monkeypatch.setattr(st, "markdown", lambda msg, **kwargs: markdown_calls.append((msg, kwargs)))

        # Caso vazio: não deve renderizar
        exibir_aviso_acuracia({})
        assert len(markdown_calls) == 0

        # Caso com aviso: deve chamar st.markdown com unsafe_allow_html=True
        resultado = {
            "status_precisao": "ok",
            "severidade_precisao": "sucesso",
            "aviso_precisao": "Estimativa verificada",
        }
        exibir_aviso_acuracia(resultado)
        assert len(markdown_calls) == 1
        msg, kwargs = markdown_calls[0]
        assert "Esta prova" in msg
        assert "#15803D" in msg
        assert kwargs.get("unsafe_allow_html") is True
