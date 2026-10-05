# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de entrada de dados para o Streamlit.
"""

import streamlit as st
from .live_input import st_keyup
from typing import Dict, List, Tuple
import html
from tri_enem import descrever_cor
from ..config import AREAS_ENEM, ORDEM_AREAS, ORDEM_CORES


TOTAL_RESPOSTAS = 45
TAMANHO_BLOCO = 5
TEXTO_AJUDA = (
    "Digite as letras de A a E, com ponto nas questões em branco. "
    "Toque numa questão para ir até ela: o que digitar entra ali, sem mover as outras. "
    "Preencha só as provas que quiser."
)


def input_respostas(
    ano: int, mapeador, tipo_aplicacao: str,
) -> Tuple[Dict[str, str], Dict[str, str | None], str]:
    """
    Renderiza os inputs de respostas para cada área.
    
    Args:
        ano: Ano da prova selecionado
        mapeador: Instância do mapeador (ordem das provas por ano)
        tipo_aplicacao: Aplicação selecionada para consultar as cores
    
    Returns:
        Respostas, cores por área (None indica área indisponível) e língua
    """
    respostas = {}
    cores = {}
    
    st.markdown("### Suas respostas")
    st.caption(TEXTO_AJUDA)

    ordem_provas = _obter_ordem_provas(ano, mapeador)
    st.session_state['ordem_provas_atual'] = ordem_provas
    st.session_state['ano_respostas'] = ano

    lingua = "ingles"
    largura_cor = _largura_cor(ano, mapeador, tipo_aplicacao)
    for idx, area in enumerate(ordem_provas, start=1):
        with st.container(border=True, key=f"respostas_{area}", gap="xsmall"):
            with st.container(horizontal=True, vertical_alignment="center", gap="xsmall"):
                st.markdown(f"**{AREAS_ENEM[area]}**", width="content")
                st.space("stretch")
                # Os seletores quebram linha juntos; no celular ocupam a largura (styles.css).
                with st.container(horizontal=True, gap="xsmall", width="content", key=f"opcoes_{area}"):
                    if area == "LC":
                        lingua = st.selectbox("Língua estrangeira", ["ingles", "espanhol"],
                                              key="lingua_prova", label_visibility="collapsed", width=120,
                                              format_func=lambda l: "Inglês" if l == "ingles" else "Espanhol")
                    cores[area] = _selecionar_cor(ano, area, mapeador, tipo_aplicacao, largura_cor)
            _render_input_prova(respostas, area, idx, cores[area])

    st.session_state['respostas_por_area'] = {
        area: respostas.get(area, '') for area in ORDEM_AREAS
    }
    return respostas, cores, lingua


def _selecionar_cor(ano: int, area: str, mapeador, tipo_aplicacao: str, largura: int = 160) -> str | None:
    """Cor do caderno; None quando a área não existe nesta aplicação."""
    disponiveis = mapeador.listar_cores_disponiveis(ano, area, tipo_aplicacao)
    if not disponiveis:
        st.caption("Área não disponível nesta aplicação.", width="content")
        return None
    base = lambda c: c.split("_")[0]
    ordenadas = sorted(disponiveis, key=lambda c: (ORDEM_CORES.index(base(c)) if base(c) in ORDEM_CORES else 99, c))
    chave = f"cor_{area}"
    if st.session_state.get(chave) not in ordenadas:
        st.session_state[chave] = ordenadas[0]
    return st.selectbox("Cor do caderno", ordenadas, key=chave, width=largura,
                        label_visibility="collapsed",
                        format_func=_nome_caderno)


def _largura_cor(ano: int, mapeador, tipo_aplicacao: str) -> int:
    """Largura comum aos seletores, com o nome de caderno mais longo da aplicação."""
    nomes = [_nome_caderno(cor) for area in ORDEM_AREAS
             for cor in mapeador.listar_cores_disponiveis(ano, area, tipo_aplicacao)]
    # ~6,4 px por caractere na fonte do seletor, mais preenchimento e seta.
    # No mínimo, 160 + 120 da língua cabem lado a lado num celular de 360 px.
    return min(320, max(160, round(6.4 * max(map(len, nomes), default=0) + 60)))


def _nome_caderno(cor: str) -> str:
    """'azul' -> 'Caderno azul'; 'cinza_adaptada' -> 'Cinza adaptado'.

    Sem o prefixo, os nomes especiais cabem no seletor de um celular de 360 px.
    """
    nome = descrever_cor(cor, masculino=True)
    return f"Caderno {nome}" if "_" not in cor else nome[:1].upper() + nome[1:]


def _obter_ordem_provas(ano: int, mapeador=None) -> List[str]:
    """Obtém a ordem das provas a partir do backend, com padrão seguro."""
    if mapeador is None:
        return ORDEM_AREAS.copy()

    try:
        ordem = mapeador.listar_ordem_provas(ano)
    except Exception:
        ordem = None
    return _normalizar_ordem_provas(ordem)


def _normalizar_ordem_provas(ordem) -> List[str]:
    """Normaliza a ordem para siglas válidas (LC, CH, CN, MT)."""
    if not ordem:
        return ORDEM_AREAS.copy()

    seen = set()
    normalizada = []
    for item in ordem:
        sigla = str(item).strip().upper()
        if sigla in AREAS_ENEM and sigla not in seen:
            normalizada.append(sigla)
            seen.add(sigla)

    if len(normalizada) != len(ORDEM_AREAS):
        return ORDEM_AREAS.copy()

    return normalizada


def _render_input_prova(respostas: Dict[str, str], area: str, ordem_idx: int, cor: str | None = None) -> None:
    """Renderiza o campo de uma prova, numerado pela posição e destacado na cor do caderno."""
    inicio = (ordem_idx - 1) * TOTAL_RESPOSTAS + 1
    key = f"resp_{area.lower()}"
    valor_atual = st.session_state.get(key, '')

    try:
        # O componente mostra numeração, contagem e posição do cursor.
        valor = st_keyup(f"Respostas {area}", value=valor_atual, max_chars=TOTAL_RESPOSTAS,
                         key=key, debounce=100, inicio=inicio,
                         cor=cor.split("_")[0] if cor else None)
        respostas[area] = (valor or '').upper()
        return
    except ValueError as exc:
        if "is not registered" not in str(exc):
            raise

    fim = ordem_idx * TOTAL_RESPOSTAS
    st.caption(f"Prova {ordem_idx} (Questões {inicio}-{fim}) · {area}")
    valor = st.text_input(f"Respostas {area}", value=valor_atual, max_chars=TOTAL_RESPOSTAS, key=key)
    respostas[area] = (valor or '').upper()
    _render_visualizacao_respostas(respostas[area], area.lower(), offset_start=inicio)
    _mostrar_contador(respostas[area])


def _mostrar_contador(respostas: str):
    """Mostra contador de caracteres e validação."""
    total = TOTAL_RESPOSTAS
    n = len(respostas) - respostas.count('_')
    
    if n == 0:
        st.caption(f"0/{total} respostas")
        return
    
    # Validar caracteres ("_" é questão pulada)
    invalidos = [c for c in respostas if c not in 'ABCDE.*_']
    
    if invalidos:
        st.error(f"Caracteres inválidos: {', '.join(sorted(set(invalidos)))}")
    elif n < total:
        st.caption(f"{n}/{total} respostas · faltam {total - n}")
    elif n == total:
        st.caption(f"{total}/{total} respostas · completo")
    else:
        st.error(f"{n}/{total} respostas (excedeu)")


def _render_visualizacao_respostas(respostas: str, key: str, offset_start: int = 1) -> None:
    """Mostra uma visualizacao agrupada das respostas em blocos de 5."""
    total = TOTAL_RESPOSTAS
    bloco = TAMANHO_BLOCO

    base = respostas[:total]
    if len(base) < total:
        base = base + ("_" * (total - len(base)))

    grupos = []
    for i in range(0, total, bloco):
        letras = "".join(_formatar_char_html(c) for c in base[i:i + bloco])
        grupos.append(
            f'<div class="resp-grupo"><div class="resp-visual__ruler">{offset_start + i}</div>'
            f'<div class="resp-visual__blocks">{letras}</div></div>'
        )
    st.markdown(
        f'<div class="resp-visual" data-key="{html.escape(key, quote=True)}">'
        + "".join(grupos) + '</div>', unsafe_allow_html=True,
    )


def _formatar_char_html(c: str) -> str:
    """Formata um caractere de resposta para HTML com classes de estado."""
    safe = html.escape(c)
    if c == "_":
        return f'<span class="resp-char resp-char--empty">{safe}</span>'
    if c in "ABCDE":
        return f'<span class="resp-char">{safe}</span>'
    if c in ".*":
        return f'<span class="resp-char resp-char--dot">{safe}</span>'
    return f'<span class="resp-char resp-char--invalid">{safe}</span>'


def validar_todas_respostas(respostas: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Valida todas as respostas.
    
    Returns:
        Tupla (todas_validas, lista_de_erros)
    """
    erros = []
    
    for area, resp in respostas.items():
        if not resp or resp == "." * TOTAL_RESPOSTAS:
            continue
            
        # "_" marca questão pulada, ainda sem resposta.
        feitas = len(resp) - resp.count('_')
        if feitas != TOTAL_RESPOSTAS or len(resp) != TOTAL_RESPOSTAS:
            erros.append(f"{area}: Deve ter {TOTAL_RESPOSTAS} respostas (tem {feitas})")

        invalidos = [c for c in resp if c not in 'ABCDE.*_']
        if invalidos:
            erros.append(f"{area}: Caracteres inválidos: {', '.join(sorted(set(invalidos)))}")
    
    return len(erros) == 0, erros
