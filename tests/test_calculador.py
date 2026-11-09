# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""
Testes do motor de cálculo TRI.

Executam integralmente offline, a partir dos itens empacotados em
`src/tri_enem/data/itens/` e dos exemplos reais em `fixtures/`. Não dependem dos
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

import numpy as np
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


class TestOrigemDosItens:
    def test_caminho_externo_incompleto_nao_recai_no_pacote(self, tmp_path):
        calculador = CalculadorTRI(str(tmp_path))
        with pytest.raises(FileNotFoundError, match=str(tmp_path)):
            calculador.listar_provas(2023)

    @pytest.mark.parametrize(
        ("area", "co_prova", "tp_lingua"),
        [
            ("CH", 187, None),
            ("CN", 188, None),
            ("LC", 189, 0),
            ("LC", 189, 1),
            ("MT", 190, None),
        ],
    )
    def test_versoes_adaptadas_ambiguas_de_2013_continuam_calculaveis(
        self, calc, area, co_prova, tp_lingua
    ):
        itens = calc.carregar_itens(2013, area, co_prova, tp_lingua)
        assert len(itens) == 45
        assert len({item.posicao for item in itens}) == 45


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


def test_probabilidade_sem_overflow_em_argumento_extremo(calc):
    """Guarda dos limites +-700 no expoente."""
    item = ItemTRI(posicao=1, gabarito="A", param_a=100.0, param_b=0.0,
                   param_c=0.2, co_item=1)
    assert calc.probabilidade_acerto(1e6, item) == 1.0
    assert calc.probabilidade_acerto(-1e6, item) == 0.2


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

    def test_caminhos_escalar_e_vetorizado_sao_equivalentes(self, calc):
        itens = self._prova()
        matriz = [
            [1] * k + [0] * (45 - k)
            for k in (0, 1, 10, 22, 44, 45)
        ]
        escalar = np.asarray([
            calc.estimar_theta_eap(respostas, itens) for respostas in matriz
        ])
        vetorizado = calc.estimar_theta_eap_batch(
            matriz, itens, batch_size=2
        )
        assert vetorizado == pytest.approx(escalar, abs=2e-14)

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_eap_preserva_soma_escalar_de_referencia(self, calc, caso):
        """Compara a otimização com a verossimilhança escalar independente."""
        itens, respostas, _ = calc._preparar_calculo(
            caso["ano"], caso["area"], caso["co_prova"],
            caso["respostas"], caso["tp_lingua"],
        )
        pontos, pesos = calc.quadratura()
        log_l = np.asarray([
            calc.log_verossimilhanca(ponto, respostas, itens)
            for ponto in pontos
        ])
        l = np.exp(log_l - log_l.max())
        referencia = np.sum(pontos * l * pesos) / np.sum(l * pesos)
        assert calc.estimar_theta_eap(respostas, itens) == pytest.approx(
            referencia, rel=0, abs=2e-14,
        )

    def test_quadratura_e_grade_de_40_pontos_com_prior_normal(self):
        pontos, pesos = CalculadorTRI.quadratura()
        assert len(pontos) == 40
        assert pontos[0] == -4.0 and pontos[-1] == 4.0
        assert np.allclose(np.diff(pontos), 8 / 39)
        assert pesos == pytest.approx(np.exp(-pontos ** 2 / 2) / np.exp(-pontos ** 2 / 2).sum())

    def test_eap_preserva_limites_e_anulados(self, calc):
        itens = self._prova()
        itens[0].param_a = 1000.0
        itens[1].param_c = 1.0
        itens[2].param_c = 0.0
        itens[3].abandonado = True
        itens[3].param_a = float("nan")
        pontos, pesos = calc.quadratura()
        for respostas in ([0] * 45, [1] * 45, [0, 1] * 22 + [0], []):
            log_l = np.asarray([
                calc.log_verossimilhanca(ponto, respostas, itens)
                for ponto in pontos
            ])
            l = np.exp(log_l - log_l.max())
            referencia = np.sum(pontos * l * pesos) / np.sum(l * pesos)
            assert calc.estimar_theta_eap(respostas, itens) == pytest.approx(
                referencia, rel=0, abs=2e-14,
            )

    @pytest.mark.parametrize("mudanca", [
        "param_a", "param_b", "param_c", "abandonado", "D", "pontos",
    ])
    def test_cache_acompanha_mudancas_numericas(self, mudanca):
        calc = CalculadorTRI()
        itens = self._prova()
        respostas = [1] * 20 + [0] * 25
        calc.estimar_theta_eap(respostas, itens)
        if mudanca == "D":
            calc.D = 1.7
        elif mudanca == "pontos":
            calc._pontos_quad = calc._pontos_quad * 0.9
        elif mudanca == "abandonado":
            itens[0].abandonado = True
        else:
            setattr(itens[0], mudanca, getattr(itens[0], mudanca) + 0.15)
        pontos, pesos = calc._pontos_quad, calc._pesos_quad
        logs = np.asarray([
            calc.log_verossimilhanca(ponto, respostas, itens) for ponto in pontos
        ])
        l = np.exp(logs - logs.max())
        referencia = np.sum(pontos * l * pesos) / np.sum(l * pesos)
        assert calc.estimar_theta_eap(respostas, itens) == pytest.approx(
            referencia, rel=0, abs=2e-14,
        )

    def test_calculador_compartilhado_preserva_resultados_em_threads(self):
        from concurrent.futures import ThreadPoolExecutor
        from copy import deepcopy

        calc = CalculadorTRI()
        itens = self._prova()
        respostas = [[1] * k + [0] * (45 - k) for k in range(0, 46, 5)]
        referencias = [calc.estimar_theta_eap(r, itens) for r in respostas]
        calc._cache_logs_quadratura.clear()
        with ThreadPoolExecutor(max_workers=8) as pool:
            valores = list(pool.map(
                lambda r: calc.estimar_theta_eap(r, deepcopy(itens)), respostas * 3,
            ))
        assert valores == referencias * 3

    def test_prova_totalmente_anulada_eap_e_batch(self):
        calc = CalculadorTRI()
        itens = self._prova()
        for item in itens:
            item.abandonado = True
        assert calc.estimar_theta_eap([1] * 45, itens) == pytest.approx(0, abs=1e-15)
        assert np.array_equal(calc.estimar_theta_eap_batch([[1] * 45], itens), [0])


class TestConverterRespostas:
    @staticmethod
    def _itens(gabaritos):
        return [
            ItemTRI(posicao=i + 1, gabarito=g, param_a=1.0, param_b=0.0,
                    param_c=0.2, co_item=i + 1)
            for i, g in enumerate(gabaritos)
        ]

    def test_contrato_da_entrada(self, calc):
        """Minúsculas valem; branco, asterisco e respostas faltantes contam erro."""
        itens = self._itens("ABCDE")
        assert calc.converter_respostas("abCDA", itens) == [1, 1, 1, 1, 0]
        assert calc.converter_respostas(".B*", itens) == [0, 1, 0, 0, 0]


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

    def test_lc_digital_2020_seleciona_versao_completa_do_idioma(self, calc):
        df = calc._carregar_df_itens(2020)
        for lingua in (0, 1):
            itens = calc.carregar_itens(2020, "LC", 691, tp_lingua=lingua)
            esperado = (
                df[
                    (df["SG_AREA"] == "LC")
                    & (df["CO_PROVA"] == 691)
                    & (df["TP_VERSAO_DIGITAL"] == lingua)
                ]
                .sort_values("CO_POSICAO")
            )
            assert len(itens) == len(esperado) == 45
            assert [item.co_item for item in itens] == (
                esperado["CO_ITEM"].astype(int).tolist()
            )

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

    def test_lc_exige_idioma_valido(self, calc):
        with pytest.raises(ValueError, match="tp_lingua"):
            calc.carregar_itens(2023, "LC", 1201)
        with pytest.raises(ValueError, match="tp_lingua"):
            calc.carregar_itens(2023, "LC", 1201, tp_lingua=2)

    def test_nao_substitui_idioma_indisponivel(self, calc):
        with pytest.raises(ValueError, match="não oferece espanhol"):
            calc.carregar_itens(2012, "LC", 165, tp_lingua=1)


class TestValidacaoEntradaNucleo:
    def test_rejeita_caractere_fora_do_contrato(self, calc):
        with pytest.raises(ValueError, match="caracteres inválidos"):
            calc.calcular_nota(2023, "MT", 1211, "A" * 44 + "9")

    def test_padding_nove_so_e_removido_em_lc_50(self, calc):
        resposta = "BCBAB99999BACBEACBDCCABAEAAABCCCDECDCECADAAEBCECBD"
        resultado = calc.calcular_nota(
            2014, "LC", 213, resposta, tp_lingua=0
        )
        assert resultado["total_itens"] == 45
        adulterada = resposta[:5] + "AAAAA" + resposta[10:]
        with pytest.raises(ValueError, match="padding"):
            calc.calcular_nota(2014, "LC", 213, adulterada, tp_lingua=0)


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


class TestConfiguracaoLC:
    """A configuração LC de anos futuros vem do fallback e deve ser idêntica."""

    def test_fallback_igual_ao_ultimo_ano_com_dados(self):
        from tri_enem.tradutor import obter_config_lc

        base = obter_config_lc(2025)
        futuro = obter_config_lc(2026)
        assert futuro.tem_tp_lingua_itens == base.tem_tp_lingua_itens
        assert futuro.tem_tp_lingua_dados == base.tem_tp_lingua_dados
        assert futuro.n_itens_arquivo == base.n_itens_arquivo
        assert futuro.posicao_inicio == base.posicao_inicio
        assert futuro.posicoes_lingua == base.posicoes_lingua


class TestNotaGabarito:
    """O INEP atribui ao gabarito a nota de outro caderno da edição.

    Em MT/2025/1471 o item 97593 foi abandonado ("problema de convergência"),
    mas mantém o gabarito A: só quem também o acerta recebe 980,3.
    """

    @staticmethod
    def _gabarito(calc, ano, area, prova, tp_lingua=None):
        itens = calc.carregar_itens(ano, area, prova, tp_lingua)
        return "".join(i.gabarito if i.gabarito in "ABCDE" else "A" for i in itens), itens

    def test_gabarito_completo_recebe_nota_catalogada(self, calc):
        respostas, _ = self._gabarito(calc, 2025, "MT", 1471)
        resultado = calc.calcular_nota(2025, "MT", 1471, respostas)
        assert resultado["nota"] == pytest.approx(980.3)
        assert resultado["acertos"] == resultado["total_itens"]

    def test_errar_item_abandonado_com_gabarito_mantem_nota_do_modelo(self, calc):
        respostas, itens = self._gabarito(calc, 2025, "MT", 1471)
        idx = next(i for i, item in enumerate(itens) if item.co_item == 97593)
        respostas = respostas[:idx] + "D" + respostas[idx + 1:]
        resultado = calc.calcular_nota(2025, "MT", 1471, respostas)
        assert resultado["acertos"] == resultado["total_itens"]
        assert resultado["nota"] == pytest.approx(967.7, abs=0.05)

    def test_lote_aplica_a_mesma_regra(self, calc):
        respostas, itens = self._gabarito(calc, 2025, "MT", 1471)
        errou = "B" if respostas[0] != "B" else "C"
        lote = [respostas, errou + respostas[1:]]
        esperadas = [calc.calcular_nota(2025, "MT", 1471, r)["nota"] for r in lote]
        assert calc.calcular_notas_batch(2025, "MT", 1471, lote) == pytest.approx(esperadas, abs=1e-12)

    def test_analise_de_questoes_usa_a_mesma_nota(self, calc):
        respostas, _ = self._gabarito(calc, 2025, "MT", 1471)
        analise = calc.analisar_todas_questoes(2025, "MT", 1471, respostas)
        assert analise["nota"] == pytest.approx(980.3)
        perda = max(q["perda_se_errasse"] for q in analise["acertos"])
        assert perda > 12.5

    def test_regra_vale_por_idioma(self, calc):
        ingles, _ = self._gabarito(calc, 2024, "LC", 1395, 0)
        assert calc.calcular_nota(2024, "LC", 1395, ingles, 0)["nota"] == pytest.approx(795.8)

    def test_sem_nota_catalogada_usa_o_modelo(self, calc):
        respostas, itens = self._gabarito(calc, 2023, "CH", 1191)
        assert calc.nota_gabarito(2023, "CH", 1191) is None
        theta = calc.estimar_theta_eap([1] * len(itens), itens)
        nota = calc.calcular_nota(2023, "CH", 1191, respostas)["nota"]
        assert nota == pytest.approx(calc.transformar_escala(theta, 2023, "CH"))

    def test_fontes_externas_nao_recebem_regra_do_pacote(self, calc):
        externo = CalculadorTRI(str(calc.base_path))
        assert externo.nota_gabarito(2025, "MT", 1471) is None
