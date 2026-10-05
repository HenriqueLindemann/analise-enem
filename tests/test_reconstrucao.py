# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Regressões das causas de erro identificadas nos microdados reais."""
import sys
import json
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import _utils

_utils.add_src_to_path()
sys.path.insert(0, str(_utils.ROOT))

from tri_enem import CalculadorTRI
from tri_enem.calculador import ItemTRI
from tri_enem.calibracao_modelos import (
    ajustar_com_extremos, aplicar_modelo, reajustar_modelo, selecionar_modelo,
)
from tools.recalibrar_validacao import _linhas_validas


CASOS_REAIS = json.loads((_utils.ROOT / "tests/fixtures/reconstruction_regressions.json").read_text())


@pytest.mark.parametrize("caso", CASOS_REAIS,
                         ids=[f"{c['ano']}-{c['area']}-{c['co_prova']}-{c['tp_lingua']}" for c in CASOS_REAIS])
def test_reconstrucoes_reproduzem_notas_oficiais_de_casos_reais(caso):
    # Casos positivos escolhidos para regressão de causas específicas. A
    # avaliação completa, incluindo as exceções, fica nos dois validadores.
    calc = CalculadorTRI()
    resultado = calc.calcular_nota(caso["ano"], caso["area"], caso["co_prova"],
                                    caso["respostas"], caso["tp_lingua"])
    assert abs(resultado["nota"]-caso["nota_oficial"]) <= caso["limite_erro"]
    itens, u = calc.preparar_respostas_batch(caso["ano"], caso["area"], caso["co_prova"],
                                            [caso["respostas"]], caso["tp_lingua"])
    assert calc.estimar_theta_eap_batch(u, itens)[0] == pytest.approx(resultado["theta"], abs=1e-12)


def test_hash_de_identidade_preserva_ausencia_entre_pandas_2_e_3():
    from tools.recalibrar_validacao import _hashes_estaveis
    ranks = _hashes_estaveis(2017, "MT", pd.Series([403, 404, 403]),
                            pd.Series([pd.NA]*3, dtype="Int64"),
                            pd.Series(["123456", "123457", "123458"]))
    assert ranks.tolist() == [11067129484477073370, 4210898128058055470, 10830673567767389033]


def test_diagnostico_pode_piorar_aviso_mas_nao_promover_qualidade():
    from tri_enem.calibracao_modelos import classificar_validacao, evidencia_adicional_mais_adversa
    from tri_enem.precisao import validacao_para_apresentacao, formatar_resumo_validacao
    primaria = {"n":40,"erro_maximo":.06,"mae":.025,"faixas_cobertas":["400_500","500_600"]}
    diagnostico = {"n":90,"erro_maximo":12.,"mae":.16,"origem":"diagnostico_calibracao"}
    info = {"validacao":primaria,"validacao_residual":{**primaria,"erro_maximo":.05},
            "diagnostico_calibracao":diagnostico}
    adversa = evidencia_adicional_mais_adversa(info)
    assert classificar_validacao(primaria,primaria['faixas_cobertas'],adversa) == (
        "aviso_forte", "diagnostico_erro_maximo_ate_15")
    assert classificar_validacao({**primaria,"n":20},primaria['faixas_cobertas'],adversa)[0] == "nao_calibrado"
    assert validacao_para_apresentacao(info) == diagnostico
    assert formatar_resumo_validacao({"n_validacao":90,"origem_metricas":"diagnostico_calibracao"}).startswith("Observada")


def test_confirmacao_nao_promove_status_ou_cobertura_insuficiente():
    from tri_enem.calibracao_modelos import classificar_validacao
    m = {"n": 50, "erro_maximo": 7., "faixas_cobertas": ["400_500", "500_600"]}
    boa = {"n": 200, "erro_maximo": .05}
    assert classificar_validacao(m, m["faixas_cobertas"], boa)[0] == "aviso_forte"
    assert classificar_validacao({**m, "n": 20}, m["faixas_cobertas"], boa)[0] == "nao_calibrado"


def test_grade_finita_bate_com_soma_direta_e_batch():
    itens = [ItemTRI(j, "A", a, b, c, j, metodo_quadratura="grade_41")
             for j, (a, b, c) in enumerate([(2.1, .7, .2), (3.7, 2.9, .15), (1.8, -.5, .25)])]
    calc = CalculadorTRI(reconstrucoes={})
    u = np.array([[0, 0, 0], [1, 0, 1], [1, 1, 1]])
    x = np.arange(-4, 4.01, .2)
    p = np.array([t.param_c + (1-t.param_c)/(1+np.exp(-t.param_a*(x-t.param_b))) for t in itens]).T
    esperado = []
    for r in u:
        posterior = np.prod(p**r * (1-p)**(1-r), axis=1) * np.exp(-x*x/2)
        esperado.append(np.sum(x*posterior)/np.sum(posterior))
    assert calc.estimar_theta_eap_batch(u, itens) == pytest.approx(esperado, abs=1e-12)
    assert [calc.estimar_theta_eap(r, itens) for r in u] == pytest.approx(esperado, abs=1e-12)
    gh = calc.estimar_theta_eap(u[-1], [replace(t, metodo_quadratura="gauss_hermite_80") for t in itens])
    assert abs(gh-esperado[-1]) > .001


def test_reconstrucao_nao_modifica_csv_ou_instancia_original():
    original = CalculadorTRI(reconstrucoes={})
    itens = original.carregar_itens(2016, "CN", 351)
    ajustes = [{"a": t.param_a, "b": t.param_b, "c": t.param_c,
                "abandonado": t.abandonado, "gabarito": t.gabarito} for t in itens]
    idx = next(j for j, t in enumerate(itens) if t.co_item == 29265)
    ajustes[idx].update(abandonado=False, gabarito="A")
    config = {"2016,CN,351": {"quadratura": "grade_41", "itens": ajustes}}
    corrigido = CalculadorTRI(reconstrucoes=config)
    config["2016,CN,351"]["itens"][idx]["gabarito"] = "B"
    novos = corrigido.carregar_itens(2016, "CN", 351)
    assert novos[idx].gabarito == "A" and not novos[idx].abandonado
    assert itens[idx].gabarito == "X" and itens[idx].abandonado
    assert all(t.metodo_quadratura == "grade_41" for t in novos)
    assert all(t.metodo_quadratura == "gauss_hermite_80" for t in itens)


def test_reconstrucoes_do_pacote_nao_vazam_para_fontes_externas():
    calc = CalculadorTRI()
    externo = CalculadorTRI(str(calc.base_path))
    assert externo.reconstrucoes == {}


@pytest.mark.parametrize("campo,valor", [("a", -1), ("b", float("nan")), ("c", 1.5)])
def test_rejeita_parametros_reconstruidos_invalidos(campo, valor):
    c = CalculadorTRI(reconstrucoes={})
    itens = c.carregar_itens(2023, "MT", 1211)
    ajustes = [{"a": t.param_a, "b": t.param_b, "c": t.param_c,
                "abandonado": t.abandonado} for t in itens]
    ajustes[0][campo] = valor
    with pytest.raises(ValueError, match="parâmetros reconstruídos inválidos"):
        CalculadorTRI(reconstrucoes={"2023,MT,1211": {"itens": ajustes}}).carregar_itens(2023, "MT", 1211)


def test_quadratura_inconsistente_ou_desconhecida_e_rejeitada():
    c = CalculadorTRI(reconstrucoes={})
    itens = c.carregar_itens(2023, "MT", 1211)
    with pytest.raises(ValueError, match="mesmo método"):
        c.estimar_theta_eap([0]*45, [replace(itens[0], metodo_quadratura="grade_41"), *itens[1:]])
    with pytest.raises(ValueError, match="desconhecida"):
        CalculadorTRI(reconstrucoes={"2023,MT,1211": {"quadratura": "erro"}}).carregar_itens(2023, "MT", 1211)


def test_ancora_perfeita_preserva_todos_os_padroes_nao_extremos():
    x = np.linspace(-2, 2.5, 100)
    y = 500 + 110*x
    extremos = {"limites_internos": [-2.1, 2.6], "pontos": [[3., 850.]]}
    modelo = ajustar_com_extremos(np.r_[x, 3.], np.r_[y, 850.], extremos)
    assert aplicar_modelo(x, modelo) == pytest.approx(y, abs=1e-9)
    assert aplicar_modelo([3.], modelo)[0] == pytest.approx(850.)
    combinado = reajustar_modelo(modelo, np.r_[x, 3., 3.], np.r_[y, 850., 850.])
    assert aplicar_modelo([3.], combinado)[0] == pytest.approx(850.)
    assert np.all(np.diff(aplicar_modelo(np.linspace(-3, 4, 1000), combinado)) >= 0)
    selecionado = selecionar_modelo(np.r_[x, 3.], np.r_[y, 850.],
                                   np.r_[x, 2.6], np.r_[y, 786.], extremos)
    assert "ancoras_extremos" in selecionado["modelo"]


def test_ancoras_nao_invadem_intervalo_de_padroes_nao_extremos():
    with pytest.raises(ValueError, match="invade"):
        ajustar_com_extremos(np.arange(10), 500+100*np.arange(10),
                            {"limites_internos": [0, 10], "pontos": [[5, 1000]]})


def test_reajuste_com_arredondamento_nao_inverte_ordem_na_ancora():
    x = np.linspace(-2, 2, 100)
    extremos = {"limites_internos": [-2.001, 2.001], "pontos": [[-2.002, 299.91]]}
    modelo = ajustar_com_extremos(x, 500+100*x, extremos)
    reajustado = reajustar_modelo(modelo, x, 500+100*x-.02)
    assert np.all(np.diff(aplicar_modelo(np.linspace(-2.003, 2.003, 10000), reajustado)) >= -1e-12)


def test_filtro_lc_com_ausencias_e_padding_no_pandas_3():
    respostas = [None, "ABCDE99999"+"A"*40, "99999ABCDE"+"A"*40, "A"*50, "A"*45]
    dados = pd.DataFrame({"TP_PRESENCA_LC": [1]*5, "CO_PROVA_LC": [1395]*5,
        "NU_NOTA_LC": [500]*5, "TX_RESPOSTAS_LC": pd.Series(respostas, dtype="string"),
        "TP_LINGUA": [0, 0, 1, 0, 0], "NU_INSCRICAO": list(range(5))})
    validos = _linhas_validas(dados, 2024, "LC", "NU_INSCRICAO")
    assert list(validos.index) == [1, 2, 4]


def test_gabarito_x_e_curva_omitida_sao_recuperados_sem_estimacao_continua():
    from tools.reconstruir_associacao_itens import refinar_gabaritos, theta_parametros
    rng = np.random.default_rng(912)
    par = np.array([[2., -.5, .2], [1.4, .8, .15], [2.7, 1.6, .25], [1.8, 2.2, .18]])
    u = rng.integers(0, 2, (500, 4))
    keys = np.array(list("ABCD"))
    raw = np.where(u, keys, "E")
    notas = 500 + 113*theta_parametros(u, par)
    inicial = par.copy()
    inicial[2] = [0, 0, .2]
    corrigido, gabaritos, custo = refinar_gabaritos(raw, notas, inicial, list("ABXD"), par)
    assert gabaritos[2] == "C"
    assert corrigido == pytest.approx(par)
    assert custo < 1e-15


def test_escolha_do_estimador_nao_depende_das_notas_do_holdout():
    from tools.recalibrar_validacao import AmostraEstratificada, Caso, calibrar_catalogo, _provas_mapeadas
    from tri_enem import MapeadorProvas
    from tri_enem.calibracao_modelos import faixa_nota
    calc = CalculadorTRI(reconstrucoes={})
    itens = calc.carregar_itens(2023, "MT", 1211)
    rng = np.random.default_rng(413)
    u = rng.random((230, 45)) < rng.uniform(.15, 1., (230, 1))
    u[[0, 120, 170]] = True
    grade = [replace(t, metodo_quadratura="grade_41") for t in itens]
    y = 500+129.63*calc.estimar_theta_eap_batch(u, grade)
    casos = []
    amostra = AmostraEstratificada()
    for j, (r, nota) in enumerate(zip(u, y)):
        texto = "".join(t.gabarito if v else "A" if t.gabarito != "A" else "B" for t, v in zip(itens, r))
        caso = Caso(2023, "MT", 1211, None, float(nota), texto,
                    faixa_nota(nota), f"sintetico-{j}", j)
        casos.append(caso)
        amostra.registrar_contagem(caso.estrato, 1)
    key = "2023,MT,1211"
    provas = {k: v for k, v in _provas_mapeadas(MapeadorProvas(), [2023]).items() if k == (2023, "MT", 1211)}
    split = {key: {"treino": casos[:120], "selecao": casos[120:170], "holdout": casos[170:]}}
    candidatos = {key: [{"quadratura": "grade_41", "origem": "grade_41"}]}
    a, _ = calibrar_catalogo(calc, provas, {}, amostra, split, "teste", candidatos)
    split[key]["holdout"] = [replace(c, nota_oficial=c.nota_oficial+80) for c in split[key]["holdout"]]
    b, _ = calibrar_catalogo(calc, provas, {}, amostra, split, "teste", candidatos)
    assert a["por_prova"][key]["reconstrucao_itens"]["quadratura"] == "grade_41"
    assert a["por_prova"][key]["transformacao"] == b["por_prova"][key]["transformacao"]
    assert a["por_prova"][key]["calibracao"] == b["por_prova"][key]["calibracao"]
    assert b["por_prova"][key]["validacao"]["mae"] > 79


def test_confirmacao_exclui_participantes_antes_da_amostragem(tmp_path, monkeypatch):
    import tools.recalibrar_validacao as ferramenta
    fonte = tmp_path / "dados.csv"
    pd.DataFrame({"NU_INSCRICAO": range(30), "TP_PRESENCA_MT": [1]*30,
        "CO_PROVA_MT": [1211]*30, "NU_NOTA_MT": np.linspace(450, 650, 30),
        "TX_RESPOSTAS_MT": ["A"*45]*30}).to_csv(fonte, sep=";", index=False)
    monkeypatch.setattr(ferramenta, "localizar_microdados", lambda base, ano: fonte)
    args = (tmp_path, [2023], {(2023, "MT", 1211): None}, {(2023, "MT", 1211, None)}, 7, 40)
    original, _, _ = ferramenta.amostrar_microdados(*args)
    ids = {c.case_id for rs in original.casos().values() for c in rs}
    excluidos = set(sorted(ids)[:5])
    nova, _, _ = ferramenta.amostrar_microdados(*args, excluir_case_ids=excluidos)
    restantes = {c.case_id for rs in nova.casos().values() for c in rs}
    assert restantes == ids - excluidos
