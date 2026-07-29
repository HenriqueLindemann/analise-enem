# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Testes ponta a ponta: da entrada do usuário até a nota.

Cobrem o percurso completo que uma resposta digitada faz, nas três interfaces
que o projeto expõe, com as mesmas 45 letras que o usuário realmente informa:

    web  ->  streamlit_app.calculador.CalculadorEnem.calcular_area
    CLI  ->  CalculadorTRI.analisar_todas_questoes   (meu_simulado.py)
    CLI  ->  SimuladorNota.calcular                  (examples/, validação)

O que se verifica, por ano e área:

1. As três interfaces produzem a mesma nota. Antes destes testes, a nota de LC
   divergia entre elas em oito anos de prova, com desvios de até 168 pontos,
   porque cada caminho tratava a string de respostas de forma diferente.
2. A nota resultante bate com a nota oficial do participante, dentro do limiar
   de precisão registrado para a prova. A suíte anterior comparava o motor
   apenas consigo mesmo e passava com o defeito presente.
3. A seleção do usuário (ano, tipo de aplicação, cor, língua) resolve o mesmo
   código de prova em todas as interfaces.
4. A letra devolvida na análise por questão é a que o usuário digitou naquela
   posição, e a contagem de acertos confere com a recontagem manual.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

import _utils

_utils.add_src_to_path()

from tri_enem import CalculadorTRI, MapeadorProvas, SimuladorNota  # noqa: E402
from tri_enem import verificar_precisao_prova  # noqa: E402

_CATALOGO = json.loads(
    (_utils.SRC_DIR / "tri_enem" / "coeficientes_data.json").read_text(
        encoding="utf-8"
    )
)
_PROVAS_OK = {
    chave
    for chave, info in _CATALOGO.get("por_prova", {}).items()
    if (info.get("qualidade") or {}).get("status") == "ok"
}


# Limiar por prova: a nota calculada deve ficar dentro do erro já medido e
# registrado para aquela prova, com uma folga. Provas sinalizadas como não
# confiáveis (LC 2009 e reaplicações sem calibração própria) são cobertas pelo
# teste de coerência entre interfaces, mas não pelo de acurácia.
FOLGA_MAE = 3.0
MAE_MINIMO_ACEITAVEL = 2.0

# Tolerância entre interfaces: devem ser bit-a-bit iguais, pois compartilham o
# mesmo motor. A folga cobre apenas ruído de último bit.
TOL_ENTRE_INTERFACES = 1e-9


# ---------------------------------------------------------------------------
# Montagem dos casos
# ---------------------------------------------------------------------------

def _carregar_casos():
    """
    Um caso por (ano, área): um participante real cuja prova é resolvível pela
    combinação de ano, tipo de aplicação e cor que o usuário escolhe na
    interface.
    """
    exemplos = json.loads(_utils.EXEMPLOS_PATH.read_text(encoding="utf-8"))
    mapeador = MapeadorProvas()

    por_ano_area = defaultdict(list)
    for e in exemplos:
        por_ano_area[(int(e["ano"]), e["area"])].append(e)

    casos = []
    for (ano, area), lista in sorted(por_ano_area.items()):
        resolviveis = []
        for e in lista:
            info = mapeador.descobrir_prova_por_codigo(
                int(e["co_prova"]), ano=ano, area=area
            )
            if info is None:
                continue
            caso = {
                "ano": ano,
                "area": area,
                "co_prova": int(e["co_prova"]),
                "cor": info.cor,
                "tipo_aplicacao": info.tipo_aplicacao,
                "tp_lingua": e["tp_lingua"],
                "lingua": _utils.lingua_por_tp(e["tp_lingua"]),
                "respostas_brutas": e["respostas"],
                "nota_oficial": _utils.to_float(e["nota_oficial"]),
            }
            confiavel = f"{ano},{area},{int(e['co_prova'])}" in _PROVAS_OK
            resolviveis.append((caso, confiavel))
            if confiavel:
                break
        if resolviveis:
            # Exercita uma prova verificada sempre que o par ano × área a
            # oferece. Os quatro pares historicamente problemáticos continuam
            # cobertos pelo caminho de coerência com a primeira prova válida.
            casos.append(
                next(
                    (caso for caso, confiavel in resolviveis if confiavel),
                    resolviveis[0][0],
                )
            )

    return casos


CASOS = _carregar_casos()


def _ids(casos):
    return [f"{c['ano']}-{c['area']}" for c in casos]


@pytest.fixture(scope="module")
def calc():
    return CalculadorTRI()


@pytest.fixture(scope="module")
def sim():
    return SimuladorNota()


@pytest.fixture(scope="module")
def web():
    """
    Wrapper da interface web. É o mesmo objeto usado pelo app Streamlit; o
    decorador de cache funciona fora de uma sessão, então o teste exercita o
    código real da web, não uma reimplementação.
    """
    pytest.importorskip("streamlit")
    app_dir = _utils.ROOT / "streamlit_app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    from calculador import CalculadorEnem  # noqa: PLC0415

    return CalculadorEnem()


def _respostas_digitadas(calc, caso):
    """
    As 45 letras que o usuário digitaria.

    Os microdados guardam as respostas de LC de 2014 a 2021 em 50 posições, com
    um bloco por idioma; o usuário informa apenas as 45 da prova que fez.
    """
    return calc.normalizar_respostas(
        caso["respostas_brutas"], caso["area"], caso["ano"],
        None if caso["tp_lingua"] is None else int(caso["tp_lingua"]),
    )


def _tp_lingua(caso):
    if caso["area"] != "LC":
        return None
    return 0 if caso["lingua"] == "ingles" else 1


# ---------------------------------------------------------------------------
# Sanidade da montagem
# ---------------------------------------------------------------------------

class TestCoberturaDosCasos:
    def test_cobre_todos_os_anos(self):
        anos = {c["ano"] for c in CASOS}
        assert anos == set(range(2009, 2026)), f"anos sem caso: {set(range(2009, 2026)) - anos}"

    def test_cobre_todas_as_areas(self):
        assert {c["area"] for c in CASOS} == {"LC", "CH", "CN", "MT"}

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_usuario_digita_sempre_45_letras(self, calc, caso):
        assert len(_respostas_digitadas(calc, caso)) == 45


# ---------------------------------------------------------------------------
# 1. As três interfaces concordam
# ---------------------------------------------------------------------------

class TestInterfacesConcordam:
    """
    Web e CLI devem devolver exatamente a mesma nota para a mesma entrada.

    Este é o teste que faltava: o anterior comparava `calcular_nota` com
    `analisar_todas_questoes`, que percorriam o mesmo caminho e por isso
    concordavam mesmo quando a nota de LC da web estava 168 pontos errada.
    """

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_web_bate_com_cli(self, calc, sim, web, caso):
        digitadas = _respostas_digitadas(calc, caso)

        r_web = web.calcular_area(
            ano=caso["ano"], area=caso["area"], respostas=digitadas,
            cor=caso["cor"], tipo_aplicacao=caso["tipo_aplicacao"],
            lingua=caso["lingua"],
        )
        assert r_web is not None and "erro" not in r_web, r_web

        r_simulado = calc.analisar_todas_questoes(
            caso["ano"], caso["area"], caso["co_prova"], digitadas, _tp_lingua(caso),
        )
        r_sim = sim.calcular(
            area=caso["area"], ano=caso["ano"], respostas=digitadas,
            lingua=caso["lingua"], cor_prova=caso["cor"],
            tipo_aplicacao=caso["tipo_aplicacao"],
        )

        assert r_web["nota"] == pytest.approx(r_simulado["nota"], abs=TOL_ENTRE_INTERFACES)
        assert r_web["nota"] == pytest.approx(r_sim.nota, abs=TOL_ENTRE_INTERFACES)
        assert r_web["acertos"] == r_simulado["total_acertos"] == r_sim.acertos
        assert r_web["total_itens"] == r_sim.total_itens

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_selecao_do_usuario_resolve_a_mesma_prova(self, sim, web, caso):
        """Ano + tipo + cor devem levar ao mesmo código de prova nas duas pontas."""
        r_web = web.calcular_area(
            ano=caso["ano"], area=caso["area"],
            respostas="A" * 45, cor=caso["cor"],
            tipo_aplicacao=caso["tipo_aplicacao"], lingua=caso["lingua"],
        )
        r_sim = sim.calcular(
            area=caso["area"], ano=caso["ano"], respostas="A" * 45,
            lingua=caso["lingua"], cor_prova=caso["cor"],
            tipo_aplicacao=caso["tipo_aplicacao"],
        )
        assert r_web["co_prova"] == r_sim.co_prova == caso["co_prova"]


# ---------------------------------------------------------------------------
# 2. Acurácia contra a nota oficial
# ---------------------------------------------------------------------------

def _casos_confiaveis():
    out = []
    for c in CASOS:
        p = verificar_precisao_prova(c["ano"], c["area"], c["co_prova"])
        if not p.get("confiavel"):
            continue
        mae = p.get("mae")
        limite = max(MAE_MINIMO_ACEITAVEL, (mae or 0.0) + FOLGA_MAE)
        out.append({**c, "limite": limite, "mae_registrado": mae})
    return out


CASOS_CONFIAVEIS = _casos_confiaveis()


class TestAcuraciaContraNotaOficial:
    """
    A nota estimada é comparada à nota oficial do participante.

    Sem este teste o motor podia errar por centenas de pontos sem que nada
    falhasse, desde que errasse de forma consistente entre as interfaces.
    """

    def test_ha_casos_confiaveis_suficientes(self):
        assert len(CASOS_CONFIAVEIS) >= 60, len(CASOS_CONFIAVEIS)

    @pytest.mark.parametrize("caso", CASOS_CONFIAVEIS, ids=_ids(CASOS_CONFIAVEIS))
    def test_nota_do_usuario_bate_com_a_oficial(self, calc, web, caso):
        digitadas = _respostas_digitadas(calc, caso)
        r = web.calcular_area(
            ano=caso["ano"], area=caso["area"], respostas=digitadas,
            cor=caso["cor"], tipo_aplicacao=caso["tipo_aplicacao"],
            lingua=caso["lingua"],
        )
        erro = abs(r["nota"] - caso["nota_oficial"])
        assert erro <= caso["limite"], (
            f"{caso['ano']}/{caso['area']}/{caso['co_prova']}: nota {r['nota']:.2f} "
            f"contra oficial {caso['nota_oficial']:.2f} (erro {erro:.2f} > "
            f"limite {caso['limite']:.2f})"
        )


# ---------------------------------------------------------------------------
# 3. A entrada é lida na posição certa
# ---------------------------------------------------------------------------

class TestPareamentoDaEntrada:
    """
    Garantias de que a letra digitada na posição N é confrontada com o gabarito
    do item N — a classe de defeito que produziu todos os erros grandes já
    observados no projeto.
    """

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_letra_devolvida_e_a_digitada(self, calc, caso):
        digitadas = _respostas_digitadas(calc, caso)
        analise = calc.analisar_todas_questoes(
            caso["ano"], caso["area"], caso["co_prova"], digitadas, _tp_lingua(caso),
        )
        for q in analise["acertos"] + analise["erros"]:
            assert q["resposta_dada"] == digitadas[q["idx_area"]], (
                f"posição {q['idx_area']}: análise diz {q['resposta_dada']!r}, "
                f"usuário digitou {digitadas[q['idx_area']]!r}"
            )

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_acerto_declarado_confere_com_o_gabarito(self, calc, caso):
        digitadas = _respostas_digitadas(calc, caso)
        analise = calc.analisar_todas_questoes(
            caso["ano"], caso["area"], caso["co_prova"], digitadas, _tp_lingua(caso),
        )
        for q in analise["acertos"]:
            assert q["resposta_dada"].upper() == q["gabarito"].upper()
        for q in analise["erros"]:
            assert q["resposta_dada"].upper() != q["gabarito"].upper()

    @pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
    def test_contagem_de_acertos_confere_com_recontagem(self, calc, caso):
        """Recontagem independente contra os gabaritos dos itens carregados."""
        digitadas = _respostas_digitadas(calc, caso)
        itens = calc.carregar_itens(
            caso["ano"], caso["area"], caso["co_prova"], _tp_lingua(caso),
        )
        esperado = sum(
            1 for i, item in enumerate(itens)
            if not item.abandonado and digitadas[i].upper() == item.gabarito.upper()
        )
        r = calc.calcular_nota(
            caso["ano"], caso["area"], caso["co_prova"], digitadas, _tp_lingua(caso),
        )
        assert r["acertos"] == esperado

    def test_entrada_de_tamanho_errado_e_recusada(self, calc):
        """
        Erro explícito em vez de nota silenciosamente errada.

        Passar a string bruta de 50 posições de LC ao motor produzia, antes,
        uma nota deslocada sem qualquer sinalização.
        """
        with pytest.raises(ValueError, match="respostas"):
            calc.calcular_nota(2023, "MT", 1211, "ABC")
        with pytest.raises(ValueError, match="respostas"):
            calc.calcular_nota(2023, "MT", 1211, "A" * 50)

    def test_uma_letra_a_mais_certa_aumenta_a_nota(self, calc):
        """Monotonicidade percebida pelo usuário na interface."""
        itens = calc.carregar_itens(2023, "MT", 1211)
        gabarito = "".join(
            i.gabarito if not i.abandonado else "." for i in itens
        )
        errado = "".join("A" if g != "A" else "B" for g in gabarito)

        notas = []
        for k in (0, 10, 20, 30, 45):
            resp = gabarito[:k] + errado[k:]
            notas.append(calc.calcular_nota(2023, "MT", 1211, resp)["nota"])
        assert notas == sorted(notas)
        assert len(set(notas)) == len(notas)

    def test_prova_em_branco_produz_a_menor_nota(self, calc):
        """O usuário pode deixar posições sem marcar, e '.' não é gabarito."""
        itens = calc.carregar_itens(2023, "MT", 1211)
        gabarito = "".join(
            i.gabarito if not i.abandonado else "." for i in itens
        )
        branco = calc.calcular_nota(2023, "MT", 1211, "." * 45)
        cheio = calc.calcular_nota(2023, "MT", 1211, gabarito)
        assert branco["acertos"] == 0
        assert branco["nota"] < cheio["nota"]


# ---------------------------------------------------------------------------
# 4. Língua estrangeira em LC
# ---------------------------------------------------------------------------

def _casos_lc():
    return [c for c in CASOS if c["area"] == "LC"]


class TestLinguaEstrangeira:
    """
    As cinco primeiras questões de LC dependem da língua escolhida. Nas provas
    impressas, só elas mudam. As digitais 691–694 de 2020 armazenam duas
    versões completas, com itens comuns também distribuídos de modo distinto.
    """

    @pytest.mark.parametrize("caso", _casos_lc(), ids=_ids(_casos_lc()))
    def test_ingles_e_espanhol_usam_itens_diferentes(self, calc, caso):
        ingles = calc.carregar_itens(caso["ano"], "LC", caso["co_prova"], 0)
        espanhol = calc.carregar_itens(caso["ano"], "LC", caso["co_prova"], 1)

        assert len(ingles) == len(espanhol) == 45
        # 2009 não registra a língua e 2012/LC/165 só oferece inglês: nesses
        # casos as duas listas coincidem, o que é o comportamento correto.
        divergentes = [
            i for i, (a, b) in enumerate(zip(ingles, espanhol))
            if a.co_item != b.co_item
        ]
        if caso["ano"] == 2020 and caso["co_prova"] in {691, 692, 693, 694}:
            assert any(i >= 5 for i in divergentes)
        else:
            assert all(i < 5 for i in divergentes), (
                f"questões comuns divergiram entre línguas: {divergentes}"
            )

    @pytest.mark.parametrize("caso", _casos_lc(), ids=_ids(_casos_lc()))
    def test_lingua_escolhida_e_respeitada_ponta_a_ponta(self, calc, web, caso):
        """A língua da sidebar precisa chegar ao filtro de itens."""
        digitadas = _respostas_digitadas(calc, caso)
        notas = {}
        for lingua in ("ingles", "espanhol"):
            r = web.calcular_area(
                ano=caso["ano"], area="LC", respostas=digitadas,
                cor=caso["cor"], tipo_aplicacao=caso["tipo_aplicacao"],
                lingua=lingua,
            )
            notas[lingua] = r["nota"]

        esperada = notas[caso["lingua"]]
        direto = calc.calcular_nota(
            caso["ano"], "LC", caso["co_prova"], digitadas, _tp_lingua(caso),
        )["nota"]
        assert esperada == pytest.approx(direto, abs=TOL_ENTRE_INTERFACES)
