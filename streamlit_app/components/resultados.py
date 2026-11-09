# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de exibição de resultados para o Streamlit.
"""

from copy import deepcopy
from html import escape

import streamlit as st
from typing import Dict, List

from tri_enem import MapeadorProvas, normalizar_posicoes_resultados
from tri_enem.formatacao import formatar_numero
from tri_enem.precisao import formatar_aviso_curto as _formatar_aviso_curto_tri
from tri_enem.precisao import formatar_percentual

from ..config import AREAS_ENEM
from .graficos import grafico_impacto, grade_questoes


def _grafico_impacto_por_sessao(sigla: str, questoes: List[Dict]):
    """Guarda só a figura atual de cada área, isolada na sessão do usuário.

    Serializar uma Figure em cache_data volta a executar os validadores do
    Plotly ao desserializar. Reusar a figura da própria sessão evita esse
    trabalho; a comparação de dados invalida qualquer mudança no gráfico.
    """
    graficos = st.session_state.setdefault('graficos_resultados', {})
    salvo = graficos.get(sigla)
    if salvo is None or salvo['questoes'] != questoes:
        salvo = {
            'questoes': deepcopy(questoes),
            'figura': grafico_impacto(questoes, ""),
        }
        graficos[sigla] = salvo
    return salvo['figura']


def exibir_resumo_geral(resultados: List[Dict]):
    """Média em destaque e uma barra por área, na escala de 0 a 1000."""
    if not resultados:
        st.warning("Nenhum resultado para exibir.")
        return

    media = sum(r['nota'] for r in resultados) / len(resultados)
    total_acertos = sum(r['acertos'] for r in resultados)
    total_questoes = sum(r['total_itens'] for r in resultados)

    linhas = []
    for r in resultados:
        nome = escape(AREAS_ENEM.get(r['sigla'], r['sigla']))
        nota = formatar_numero(r['nota'])
        largura = max(0.0, min(100.0, r['nota'] / 10))
        linhas.append(
            '<li class="resumo-area">'
            f'<span class="resumo-nome">{nome}<small>{r["acertos"]}/{r["total_itens"]} acertos</small></span>'
            f'<span class="resumo-barra" aria-hidden="true"><i style="width:{largura:.1f}%"></i></span>'
            f'<strong class="resumo-nota">{nota}</strong></li>'
        )
    st.markdown(
        '<div class="resumo">'
        '<p class="resumo-media"><span>Média simples</span>'
        f'<strong>{formatar_numero(media)}</strong>'
        f'<span>{total_acertos}/{total_questoes} acertos</span></p>'
        '<ul class="resumo-areas" aria-label="Nota por área (0 a 1000)">' + ''.join(linhas) + '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )


def exibir_resultado_area(resultado: Dict):
    """
    Exibe o resultado detalhado de uma área com todos os gráficos visíveis.
    
    Args:
        resultado: Dict com resultado completo da área
    """
    resultado = normalizar_posicoes_resultados(
        [resultado],
        MapeadorProvas().listar_ordem_provas(resultado.get('ano', 2024)),
    )[0]
    sigla = resultado['sigla']
    nome = AREAS_ENEM.get(sigla, sigla)

    # Preparar dados das questões
    questoes_acertadas = resultado.get('questoes_acertadas', [])
    questoes_erradas = resultado.get('questoes_erradas', [])
    questoes_anuladas = resultado.get('anuladas', []) or [
        {'posicao': posicao}
        for posicao in resultado.get('questoes_anuladas', [])
    ]
    
    # Converter para formato esperado pelos gráficos
    todas_questoes = []
    for q in questoes_acertadas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': True,
            'anulada': False,
            'gabarito': q['gabarito'],
            'resposta_dada': q['resposta_dada'],
            'impacto': q.get('perda_se_errasse', 0),
            'param_b': q.get('param_b', 0),
        })
    for q in questoes_erradas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': False,
            'anulada': False,
            'gabarito': q['gabarito'],
            'resposta_dada': q['resposta_dada'],
            'impacto': q.get('ganho_se_acertasse', 0),
            'param_b': q.get('param_b', 0),
        })
    for q in questoes_anuladas:
        todas_questoes.append({
            'posicao': q['posicao'],
            'acertou': False,
            'anulada': True,
            'gabarito': q.get('gabarito', 'X'),
            'resposta_dada': q.get('resposta_dada', '.'),
            'impacto': 0,
            'param_b': q.get('param_b', 0),
        })

    # Resumo compacto: a taxa e a legenda acompanham a grade em qualquer tela.
    st.markdown("##### Grade de Questões")
    acertos = len(questoes_acertadas)
    erros = len(questoes_erradas)
    validas = acertos + erros
    taxa = f"{formatar_numero(100 * acertos / validas, 0)}% de acertos" if validas else "Sem questões válidas"
    st.markdown(
        '<div class="grade-painel">'
        f'<div class="grade-resumo"><strong>{taxa}</strong>'
        '<div class="grade-legenda">'
        f'<span class="legenda--acerto"><i aria-hidden="true"></i>{acertos} acertos</span>'
        f'<span class="legenda--erro"><i aria-hidden="true"></i>{erros} erros</span>'
        f'<span class="legenda--anulada"><i aria-hidden="true"></i>{len(questoes_anuladas)} anuladas</span>'
        '</div></div>'
        + grade_questoes(todas_questoes)
        + '</div>',
        unsafe_allow_html=True,
    )

    # Seção 2: Gráfico de impacto
    st.markdown("##### Impacto das Questões na Nota")
    st.caption("Ordenado do maior para o menor impacto | Verde = Acerto | Vermelho = Erro")
    with st.container(key=f"impacto_scroll_{sigla}"):
        with st.container(key=f"impacto_fig_{sigla}"):
            st.plotly_chart(
                _grafico_impacto_por_sessao(sigla, todas_questoes),
                key=f"impacto_{sigla}",
                config={'displayModeBar': False, 'scrollZoom': False, 'doubleClick': False},
            )

    # HTML sem controles de planilha; a ordem é estável e explícita.
    st.markdown("##### Questões em detalhe")
    st.markdown(
        '<div class="diagnostico">'
        + _tabela_questoes(questoes_erradas, acertou=False)
        + _tabela_questoes(questoes_acertadas, acertou=True)
        + '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Maior impacto primeiro. Os pontos estimam a mudança na nota ao alterar "
        "somente aquela resposta; não devem ser somados. "
        "Dificuldade (b): quanto maior o valor, mais difícil o item."
    )

    # Aviso de calibração discreto (sem fundo colorido) com detalhes explicativos
    exibir_aviso_acuracia(resultado)


def _tabela_questoes(questoes: List[Dict], *, acertou: bool) -> str:
    """Tabela completa, com ordem fixa e rolagem vertical acessível."""
    titulo = "Acertos" if acertou else "Erros"
    classe = "acertos" if acertou else "erros"
    impacto = "Perda se errasse" if acertou else "Ganho se acertasse"
    chave = "perda_se_errasse" if acertou else "ganho_se_acertasse"
    ordenadas = sorted(questoes, key=lambda q: (-q.get(chave, 0), q['posicao']))

    def resposta(valor):
        return "Em branco" if valor in (None, "", ".") else escape(str(valor))

    def tabela(itens):
        linhas = []
        for q in itens:
            dificuldade = q.get('param_b')
            b = formatar_numero(dificuldade, 2, sinal=True) if dificuldade is not None else "—"
            alternativas = f'<strong>{resposta(q.get("gabarito"))}</strong>'
            if not acertou:
                alternativas = (
                    f'<span>{resposta(q.get("resposta_dada"))}</span>'
                    '<span class="resposta-seta" aria-hidden="true"> → </span>'
                    '<span class="sr-only">; gabarito: </span>'
                    + alternativas
                )
            linhas.append(
                '<tr><th scope="row">'
                f'Q{escape(str(q["posicao"]))}<small>b: {b}</small></th>'
                f'<td>{alternativas}</td>'
                f'<td class="questao-impacto">{formatar_numero(q.get(chave, 0))}'
                ' <span>pts</span></td></tr>'
            )
        return (
            f'<table class="questoes-tabela"><caption class="sr-only">{titulo}: {impacto.lower()}</caption>'
            '<thead><tr><th scope="col">Questão</th>'
            f'<th scope="col">{"Gabarito" if acertou else "Sua resposta<br><span>→ Gabarito</span>"}</th>'
            f'<th scope="col">{"Perda" if acertou else "Ganho"}<br><span>em pontos</span></th></tr></thead>'
            '<tbody>' + ''.join(linhas) + '</tbody></table>'
        )

    conteudo = (
        f'<div class="questoes-scroll" role="region" aria-label="Todas as questões: {titulo.lower()}" tabindex="0">'
        + tabela(ordenadas) + '</div>'
    ) if ordenadas else (
        '<p class="diagnostico-vazio">' + ("Nenhum acerto." if acertou else "Nenhum erro. Parabéns!") + '</p>'
    )
    return (
        f'<section class="diagnostico-grupo diagnostico--{classe}" aria-label="{titulo}">'
        f'<div class="diagnostico-titulo" role="heading" aria-level="6">{titulo} '
        f'<span class="diagnostico-contagem">{len(ordenadas)}</span></div>'
        f'<p class="diagnostico-descricao">{"Quanto a nota cairia se você errasse." if acertou else "Quanto a nota subiria se você acertasse."}</p>'
        + conteudo + '</section>'
    )


def formatar_aviso_curto(resultado: Dict) -> str:
    """
    Retorna a mensagem breve de confiabilidade usada também no PDF.

    Somente o estado da estimativa recebe cor e negrito; o restante permanece
    neutro para preservar a hierarquia visual e a acessibilidade.
    """
    return _formatar_aviso_curto_tri(resultado, formato="html")


def formatar_inteiro(valor: int) -> str:
    return f"{int(valor):,}".replace(",", ".")


def exibir_aviso_acuracia(resultado: Dict):
    """Frase curta de confiabilidade e, recolhida, a comparação com todos os participantes."""
    frase = formatar_aviso_curto(resultado)
    if not frase:
        return

    st.markdown(frase, unsafe_allow_html=True)

    n = resultado.get('n_validacao')
    mae = resultado.get('mae_validacao')
    acima_2 = resultado.get('n_acima_2')
    percentual_ate_2 = resultado.get('percentual_ate_2')
    co_prova = resultado.get('co_prova')
    aviso = resultado.get('aviso_precisao')

    with st.expander("Mais detalhes sobre a precisão", expanded=False):
        if n:
            st.caption(
                "Comparação entre a nota calculada e a oficial de todos os "
                "participantes desta prova."
            )
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Participantes", formatar_inteiro(n))
            c2.metric("Diferença média",
                      f"{formatar_numero(mae, 2)} pts" if mae is not None else "—")
            c3.metric("Até 2 pontos",
                      formatar_percentual(percentual_ate_2) if percentual_ate_2 is not None else "—")
            c4.metric("Acima de 2 pontos",
                      formatar_inteiro(acima_2) if acima_2 is not None else "—")
            rodape = [f"Prova {co_prova}"] if co_prova else []
            st.caption(" · ".join(rodape + ["Microdados oficiais do INEP"]))
        elif aviso:
            st.caption(aviso)
