# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Testes da classificação de confiabilidade por prova.

Verificam o invariante central da apresentação de resultados: uma prova cuja
nota não é confiável nunca deve ser exibida sem aviso. Anteriormente, 16
provas com status 'erro_alto' possuíam mensagem nula em
coeficientes_data.json e eram apresentadas sem qualquer sinalização.
"""

import json
from pathlib import Path

import pytest

import _utils

_utils.add_src_to_path()

from tri_enem import (  # noqa: E402
    formatar_resumo_validacao,
    verificar_precisao_prova,
)
import tri_enem.precisao as precisao_module  # noqa: E402
from tri_enem.precisao import (  # noqa: E402
    MAE_OK,
    MAE_AVISO_LEVE,
    MAE_AVISO_FORTE,
    SEVERIDADE_POR_STATUS,
)

DADOS = Path(_utils.SRC_DIR) / "tri_enem" / "coeficientes_data.json"


@pytest.fixture(scope="module")
def dados():
    with open(DADOS, encoding="utf-8") as f:
        return json.load(f)


def _chaves_por_status(dados, alvo):
    if int(dados.get("schema_version", 2)) >= 3:
        return [
            k for k, v in dados.get("por_prova", {}).items()
            if (v.get("qualidade") or {}).get("status") == alvo
        ]
    return [
        k for k, v in dados.get("status_provas", {}).items()
        if v.get("status") == alvo
    ]


def test_resumo_para_usuario_e_curto_e_sem_codigos_internos():
    resumo = formatar_resumo_validacao({
        "n_validacao": 300,
        "mae": 0.38,
        "erro_p95": 1.82,
        "erro_maximo": 6.51,
        "n_acima_2": 6,
        "perfil": "boa_na_maioria_com_excecoes",
        "status": "aviso_forte",
    })

    assert resumo == (
        "Validação: 300 casos reais · erro médio: 0,38 · "
        "em 95% dos casos: até 1,82 · maior diferença: 6,51 · "
        "6 exceções · confiável na maioria"
    )
    assert "MAE" not in resumo
    assert "p95" not in resumo
    assert "aviso_forte" not in resumo


def _todas_chaves(dados):
    if int(dados.get("schema_version", 2)) >= 3:
        return list(dados.get("por_prova", {}))
    return list(dados.get("status_provas", {}))


def _consultar(chave):
    ano, area, co_prova = chave.split(",")
    return verificar_precisao_prova(int(ano), area, int(co_prova))


class TestInvarianteNaoSilenciar:
    """Prova não confiável deve sempre apresentar aviso e severidade."""

    def test_toda_prova_nao_confiavel_tem_aviso(self, dados):
        sem_aviso = []
        for chave in _todas_chaves(dados):
            r = _consultar(chave)
            if not r["confiavel"] and not r["aviso"]:
                sem_aviso.append(chave)
        assert not sem_aviso, f"provas sem aviso: {sem_aviso[:10]}"

    def test_toda_prova_nao_confiavel_tem_severidade(self, dados):
        sem_sev = []
        for chave in _todas_chaves(dados):
            r = _consultar(chave)
            if not r["confiavel"] and not r["severidade"]:
                sem_sev.append(chave)
        assert not sem_sev, f"provas sem severidade: {sem_sev[:10]}"

    def test_erro_alto_sempre_avisa(self, dados):
        chaves = _chaves_por_status(dados, "erro_alto")
        assert chaves, "fixture sem provas erro_alto"
        for chave in chaves:
            r = _consultar(chave)
            assert r["aviso"], f"{chave} sem aviso"
            assert r["severidade"] in {"atencao", "alerta"}, chave
            assert r["confiavel"] is False, chave

    def test_provas_sem_participantes_explicam_a_causa(self, dados):
        alvo = (
            "sem_participantes"
            if int(dados.get("schema_version", 2)) >= 3
            else "falhou"
        )
        chaves = _chaves_por_status(dados, alvo)
        assert chaves, f"catálogo sem provas {alvo!r}"
        for chave in chaves:
            r = _consultar(chave)
            assert "sem participantes" in r["aviso"].lower(), chave


@pytest.fixture(scope="module")
def avisos(dados):
    """Conjunto de todas as mensagens distintas produzidas pelo catálogo."""
    vistos = set()
    for chave in _todas_chaves(dados):
        aviso = _consultar(chave)["aviso"]
        if aviso:
            vistos.add(aviso)
    return vistos


class TestMensagens:
    """As mensagens destinam-se ao usuário final, não ao desenvolvedor."""

    def test_existem_avisos(self, avisos):
        assert avisos

    def test_sem_jargao_tecnico(self, avisos):
        proibidos = ["MAE", "R²", "slope", "intercept", "theta", "θ",
                     "calibração parcial", "Falha:"]
        for aviso in avisos:
            for termo in proibidos:
                assert termo not in aviso, f"jargão {termo!r} em: {aviso}"

    def test_sem_emoji(self, avisos):
        for aviso in avisos:
            assert all(ord(c) < 0x2000 for c in aviso), f"emoji em: {aviso}"

    def test_terminam_com_ponto(self, avisos):
        for aviso in avisos:
            assert aviso.rstrip().endswith("."), f"sem pontuação final: {aviso}"


class TestClassificacaoPorMae:
    """Coerência entre status, severidade e confiabilidade."""

    def test_limiares_ordenados(self):
        assert MAE_OK < MAE_AVISO_LEVE < MAE_AVISO_FORTE

    def test_prova_ok_exibe_confirmacao_positiva(self, dados):
        chaves = _chaves_por_status(dados, "ok")
        assert chaves
        for chave in chaves[:200]:
            r = _consultar(chave)
            assert "boa calibração" in r["aviso"].lower()
            assert r["confiavel"] is True
            assert r["severidade"] == "sucesso"
            assert r["perfil"] == "calibracao_verificada"

    def test_perfil_intermediario_nao_esconde_excecoes(self, dados):
        encontrados = []
        for chave in _todas_chaves(dados):
            r = _consultar(chave)
            if r["perfil"] != "boa_na_maioria_com_excecoes":
                continue
            encontrados.append(chave)
            assert r["confiavel"] is False
            assert r["severidade"] == "atencao"
            assert "maioria dos casos" in r["aviso"].lower()
            assert "confiável" in r["aviso"].lower()
            assert "exceções" in r["aviso"].lower()
            assert not any(
                caractere.isdigit() for caractere in r["aviso"]
            ), r["aviso"]
        assert encontrados

    def test_severidade_coerente_com_status(self, dados):
        for chave in _todas_chaves(dados):
            r = _consultar(chave)
            assert r["severidade"] == SEVERIDADE_POR_STATUS.get(r["status"]) \
                or not r["confiavel"], chave

    def test_prova_desconhecida_e_marcada(self):
        r = verificar_precisao_prova(2023, "MT", 999999)
        assert r["status"] == "nao_calibrado"
        assert r["confiavel"] is False
        assert r["aviso"]

    def test_aceita_argumentos_em_string(self):
        r = verificar_precisao_prova("2023", "MT", "1211")
        assert r["status"] != "desconhecido"

    def test_normaliza_area_para_maiusculas(self):
        assert verificar_precisao_prova(2023, "mt", 1211) == (
            verificar_precisao_prova(2023, "MT", 1211)
        )

    def test_catalogo_corrompido_falha_fechado(self, tmp_path, monkeypatch):
        corrompido = tmp_path / "coeficientes_data.json"
        corrompido.write_text("{não é json", encoding="utf-8")
        monkeypatch.setattr(precisao_module, "DATA_FILE", corrompido)
        r = verificar_precisao_prova(2023, "MT", 1211)
        assert r["confiavel"] is False
        assert r["status"] == "nao_calibrado"
        assert r["aviso"]

    @pytest.mark.parametrize(
        "conteudo",
        [
            {"schema_version": "inválido", "por_prova": {}},
            {"schema_version": 3, "por_prova": []},
            {
                "schema_version": 3,
                "por_prova": {
                    "2023,MT,1211": {
                        "qualidade": {"status": "ok"},
                        "validacao": {
                            "n": 30,
                            "mae": 0.1,
                            "erro_p95": 0.2,
                            "erro_maximo": "NaN",
                            "faixas_cobertas": ["(400,500]", "(500,600]"],
                            "faixas_existentes": ["(400,500]", "(500,600]"],
                        },
                    }
                },
            },
        ],
    )
    def test_catalogo_estruturalmente_corrompido_falha_fechado(
        self, conteudo, tmp_path, monkeypatch
    ):
        corrompido = tmp_path / "coeficientes_data.json"
        corrompido.write_text(json.dumps(conteudo), encoding="utf-8")
        monkeypatch.setattr(precisao_module, "DATA_FILE", corrompido)
        r = verificar_precisao_prova(2023, "MT", 1211)
        assert r["confiavel"] is False
        assert r["status"] == "nao_calibrado"
        assert r["aviso"]

    def test_lc_2009_tem_validacao_catalogada(self):
        """
        LC 2009 constava como não reconstituível, com MAE de 45 a 70 pontos.

        A causa era um item anulado sem CO_ITEM que o carregador descartava,
        deslocando o pareamento de todas as posições seguintes. Preservado o
        item, as quatro provas precisam ter validação calculada. A classificação
        final continua sendo determinada exclusivamente pelo holdout.
        """
        for co_prova in (57, 58, 59, 60):
            r = verificar_precisao_prova(2009, "LC", co_prova)
            assert r["status"] not in {
                "nao_calibrado",
                "sem_participantes",
                "sem_itens",
            }, co_prova
            assert r["n_validacao"], co_prova
