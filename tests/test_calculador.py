# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Testes do motor de cálculo TRI.

Executam integralmente offline, a partir dos itens versionados em
`microdados_limpos/` e dos exemplos reais em `fixtures/`. Não dependem dos
microdados brutos do INEP.

Organizam-se em três camadas:

1. Regressão (golden): fixa nota e theta de casos reais que abrangem todo
   ano × área. Qualquer alteração no motor que modifique um resultado é
   detectada.
2. Coerência: `calcular_nota` e `analisar_todas_questoes` devem retornar a
   mesma nota para a mesma entrada.
3. Propriedades do modelo ML3/EAP que devem ser satisfeitas em qualquer
   configuração de itens.
"""

import json
from pathlib import Path

import pytest

import _utils

_utils.add_src_to_path()

from tri_enem import CalculadorTRI  # noqa: E402
from tri_enem.calculador import ItemTRI  # noqa: E402


FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN_PATH = FIXTURES / "golden_notas.json"

# Tolerancia do golden: apertada o suficiente para pegar mudanca de
# coeficiente ou de modelo, frouxa o suficiente para absorver diferencas
# de ultimo bit entre versoes de numpy/BLAS.
TOL_NOTA = 1e-6
TOL_THETA = 1e-9


@pytest.fixture(scope="module")
def calc():
    return CalculadorTRI()


@pytest.fixture(scope="module")
def golden():
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


def _ids(casos):
    return [f"{c['ano']}-{c['area']}-{c['co_prova']}" for c in casos]


def _carregar_golden():
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


CASOS = _carregar_golden()


class TestRegressaoGolden:
    """Fixa os resultados de referência do motor (nota, theta e acertos)."""

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_nota_nao_mudou(self, calc, caso):
        r = calc.calcular_nota(
            caso["ano"], caso["area"], caso["co_prova"],
            caso["respostas"], caso["tp_lingua"],
        )
        assert r["nota"] == pytest.approx(caso["nota"], abs=TOL_NOTA)
        assert r["theta"] == pytest.approx(caso["theta"], abs=TOL_THETA)
        assert r["acertos"] == caso["acertos"]
        assert r["total_itens"] == caso["total_itens"]

    def test_golden_cobre_todos_os_anos(self):
        anos = {c["ano"] for c in CASOS}
        assert anos == set(range(2009, 2026)), f"anos faltando: {set(range(2009, 2026)) - anos}"

    def test_golden_cobre_todas_as_areas(self):
        assert {c["area"] for c in CASOS} == {"LC", "CH", "CN", "MT"}


class TestCoerenciaEntreInterfaces:
    """
    A nota do CLI (`calcular_nota`) e a da interface web
    (`analisar_todas_questoes`) devem ser idênticas, pois ambas dependem do
    coeficiente específico da prova. A divergência que motivou este teste
    decorria da omissão de `co_prova` nas funções de análise, que recaíam no
    coeficiente médio da área e produziam desvio de até 1,25 ponto.
    """

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_analise_bate_com_calculo(self, calc, caso):
        direto = calc.calcular_nota(
            caso["ano"], caso["area"], caso["co_prova"],
            caso["respostas"], caso["tp_lingua"],
        )
        analise = calc.analisar_todas_questoes(
            caso["ano"], caso["area"], caso["co_prova"],
            caso["respostas"], caso["tp_lingua"],
        )
        assert analise["nota"] == pytest.approx(direto["nota"], abs=TOL_NOTA)
        assert analise["theta"] == pytest.approx(direto["theta"], abs=TOL_THETA)
        assert analise["total_acertos"] == direto["acertos"]


class TestProbabilidadeAcerto:
    """Propriedades do modelo logistico de 3 parametros."""

    @staticmethod
    def _item(a=1.0, b=0.0, c=0.2):
        return ItemTRI(posicao=1, gabarito="A", param_a=a, param_b=b,
                       param_c=c, co_item=1)

    def test_no_nivel_da_dificuldade_e_media_entre_c_e_1(self, calc):
        """Em theta == b, P = c + (1-c)/2."""
        item = self._item(b=0.5, c=0.2)
        assert calc.probabilidade_acerto(0.5, item) == pytest.approx(0.6)

    def test_tende_ao_chute_em_theta_muito_baixo(self, calc):
        item = self._item(c=0.25)
        assert calc.probabilidade_acerto(-50.0, item) == pytest.approx(0.25, abs=1e-9)

    def test_tende_a_um_em_theta_muito_alto(self, calc):
        item = self._item(c=0.25)
        assert calc.probabilidade_acerto(50.0, item) == pytest.approx(1.0, abs=1e-9)

    def test_monotonica_crescente_em_theta(self, calc):
        item = self._item()
        valores = [calc.probabilidade_acerto(t, item)
                   for t in [-3, -2, -1, 0, 1, 2, 3]]
        assert valores == sorted(valores)
        assert len(set(valores)) == len(valores)

    def test_nunca_sai_do_intervalo(self, calc):
        item = self._item(a=2.5, b=1.5, c=0.17)
        for t in [-1000, -10, 0, 10, 1000]:
            p = calc.probabilidade_acerto(t, item)
            assert 0.0 <= p <= 1.0

    def test_sem_overflow_em_argumento_extremo(self, calc):
        """Guarda dos limites +-700 no expoente (calculador.py)."""
        item = self._item(a=100.0)
        assert calc.probabilidade_acerto(1e6, item) == 1.0
        assert calc.probabilidade_acerto(-1e6, item) == self._item(a=100.0).param_c


class TestEstimacaoEAP:
    """Propriedades da estimacao Expected a Posteriori."""

    @staticmethod
    def _prova(n=45):
        # Dificuldades distribuídas de -2 a 2, equivalentes a uma prova real.
        return [
            ItemTRI(posicao=i + 1, gabarito="A", param_a=1.2,
                    param_b=-2.0 + 4.0 * i / (n - 1), param_c=0.2, co_item=i + 1)
            for i in range(n)
        ]

    def test_mais_acertos_gera_theta_maior(self, calc):
        itens = self._prova()
        thetas = [
            calc.estimar_theta_eap([1] * k + [0] * (45 - k), itens)
            for k in [0, 10, 20, 30, 40, 45]
        ]
        assert thetas == sorted(thetas)

    def test_theta_fica_dentro_da_faixa_da_quadratura(self, calc):
        itens = self._prova()
        for k in [0, 23, 45]:
            theta = calc.estimar_theta_eap([1] * k + [0] * (45 - k), itens)
            assert -6.0 < theta < 6.0

    def test_itens_anulados_nao_afetam_theta(self, calc):
        """Item anulado deve ser desconsiderado, independentemente da resposta."""
        itens = self._prova()
        itens[3].abandonado = True
        respostas = [1] * 20 + [0] * 25

        com_acerto = list(respostas)
        com_acerto[3] = 1
        com_erro = list(respostas)
        com_erro[3] = 0

        assert calc.estimar_theta_eap(com_acerto, itens) == pytest.approx(
            calc.estimar_theta_eap(com_erro, itens), abs=1e-12
        )


class TestConverterRespostas:
    @staticmethod
    def _itens(gabaritos):
        return [
            ItemTRI(posicao=i + 1, gabarito=g, param_a=1.0, param_b=0.0,
                    param_c=0.2, co_item=i + 1)
            for i, g in enumerate(gabaritos)
        ]

    def test_acertos_e_erros(self, calc):
        itens = self._itens("ABCDE")
        assert calc.converter_respostas("ABCDE", itens) == [1, 1, 1, 1, 1]
        assert calc.converter_respostas("EDCBA", itens) == [0, 0, 1, 0, 0]

    def test_case_insensitive(self, calc):
        itens = self._itens("ABC")
        assert calc.converter_respostas("abc", itens) == [1, 1, 1]

    def test_string_curta_completa_com_erro(self, calc):
        """Respostas ausentes são contabilizadas como erro, sem exceder o índice."""
        itens = self._itens("ABCDE")
        assert calc.converter_respostas("AB", itens) == [1, 1, 0, 0, 0]

    def test_resposta_em_branco_conta_erro(self, calc):
        itens = self._itens("ABC")
        assert calc.converter_respostas(".B.", itens) == [0, 1, 0]


class TestCarregarItens:
    def test_prova_real_tem_45_itens(self, calc):
        itens = calc.carregar_itens(2023, "MT", 1211)
        assert len(itens) == 45

    def test_lc_filtra_por_lingua_e_devolve_45(self, calc):
        """LC tem 50 linhas no arquivo; o filtro de lingua reduz para 45."""
        for tp_lingua in (0, 1):
            itens = calc.carregar_itens(2023, "LC", 1201, tp_lingua=tp_lingua)
            assert len(itens) == 45, f"tp_lingua={tp_lingua}"

    def test_lc_ingles_e_espanhol_diferem(self, calc):
        ingles = calc.carregar_itens(2023, "LC", 1201, tp_lingua=0)
        espanhol = calc.carregar_itens(2023, "LC", 1201, tp_lingua=1)
        assert [i.co_item for i in ingles] != [i.co_item for i in espanhol]

    def test_itens_vem_ordenados_por_posicao(self, calc):
        itens = calc.carregar_itens(2023, "CH", 1191)
        posicoes = [i.posicao for i in itens]
        assert posicoes == sorted(posicoes)

    def test_sem_posicoes_duplicadas(self, calc):
        itens = calc.carregar_itens(2023, "CN", 1221)
        posicoes = [i.posicao for i in itens]
        assert len(posicoes) == len(set(posicoes))

    def test_prova_inexistente_levanta_erro(self, calc):
        with pytest.raises(ValueError, match="Prova nao encontrada|Prova não encontrada"):
            calc.carregar_itens(2023, "MT", 999999)

    def test_ano_inexistente_levanta_erro(self, calc):
        with pytest.raises(FileNotFoundError):
            calc.carregar_itens(1999, "MT", 1211)

    def test_cache_devolve_mesma_lista(self, calc):
        assert calc.carregar_itens(2023, "MT", 1211) is calc.carregar_itens(2023, "MT", 1211)


RESPOSTAS_MT_2023 = "CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE"


@pytest.fixture(scope="module")
def analise(calc):
    return calc.analisar_todas_questoes(2023, "MT", 1211, RESPOSTAS_MT_2023)


class TestAnaliseDeQuestoes:
    """A análise por questão fornece os dados da interface e do relatório."""

    def test_soma_acertos_e_erros_bate_com_total(self, analise):
        assert analise["total_acertos"] + analise["total_erros"] == analise["total_itens"]

    def test_erros_ordenados_por_ganho_decrescente(self, analise):
        ganhos = [q["ganho_se_acertasse"] for q in analise["erros"]]
        assert ganhos == sorted(ganhos, reverse=True)

    def test_acertos_ordenados_por_perda_decrescente(self, analise):
        perdas = [q["perda_se_errasse"] for q in analise["acertos"]]
        assert perdas == sorted(perdas, reverse=True)

    def test_acertar_uma_questao_a_mais_sempre_ajuda(self, analise):
        assert all(q["ganho_se_acertasse"] > 0 for q in analise["erros"])

    def test_errar_um_acerto_sempre_prejudica(self, analise):
        assert all(q["perda_se_errasse"] > 0 for q in analise["acertos"])

    def test_idx_area_dentro_do_intervalo(self, analise):
        for q in analise["acertos"] + analise["erros"]:
            assert 0 <= q["idx_area"] <= 44
