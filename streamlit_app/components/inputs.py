# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de entrada de dados para o Streamlit.
"""

import streamlit as st
from st_keyup import st_keyup
from typing import Dict, List, Tuple
import html
from ..config import AREAS_ENEM, ORDEM_AREAS


TOTAL_RESPOSTAS = 45
TAMANHO_BLOCO = 5
PLACEHOLDERS = {
    'LC': "Ex: ACABCDCEACABCACCBEAB...",
    'CH': "Ex: EDAAAADBCAABBABEECBB...",
    'CN': "Ex: DABCEDEBEECBEABEBDCB...",
    'MT': "Ex: DCCAEBABDDCABEACCBCC...",
}


def input_respostas(ano: int, mapeador=None) -> Dict[str, str]:
    """
    Renderiza os inputs de respostas para cada área.
    
    Args:
        ano: Ano da prova selecionado
        mapeador: Instância do mapeador (ordem das provas por ano)
    
    Returns:
        Dict com sigla da área e string de respostas
    """
    respostas = {}
    
    st.markdown("### Suas Respostas")
    st.caption("Digite suas 45 respostas para cada área usando as letras A, B, C, D, E. "
               "Use ponto (.) para questões não respondidas.")
    
    ordem_provas = _obter_ordem_provas(ano, mapeador)
    _sincronizar_respostas_por_area(ordem_provas)
    st.session_state['ordem_provas_atual'] = ordem_provas
    st.session_state['ano_respostas'] = ano
    st.markdown("#### Provas")
    
    num_rows = (len(ordem_provas) + 1) // 2
    rows = [st.columns(2) for _ in range(num_rows)]
    
    for idx, area in enumerate(ordem_provas, start=1):
        row_idx = (idx - 1) // 2
        col_idx = (idx - 1) % 2
        with rows[row_idx][col_idx]:
            _render_input_prova(respostas, area, idx)
    
    st.session_state['respostas_por_area'] = {
        area: respostas.get(area, '') for area in ORDEM_AREAS
    }
    return respostas


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


def _sincronizar_respostas_por_area(ordem_provas_atual: List[str]) -> None:
    """Reaplica respostas por area quando a ordem muda."""
    ordem_anterior = st.session_state.get('ordem_provas_atual')
    if not ordem_anterior or ordem_anterior == ordem_provas_atual:
        return

    respostas_area = st.session_state.get('respostas_por_area')
    if not isinstance(respostas_area, dict):
        return

    for area in ORDEM_AREAS:
        key = f"resp_{area.lower()}"
        if area in respostas_area:
            st.session_state[key] = respostas_area[area]


def _render_input_prova(respostas: Dict[str, str], area: str, ordem_idx: int) -> None:
    """Renderiza o bloco de input para uma prova na ordem indicada."""
    nome_area = AREAS_ENEM.get(area, area)
    inicio = (ordem_idx - 1) * TOTAL_RESPOSTAS + 1
    fim = ordem_idx * TOTAL_RESPOSTAS

    st.markdown(f"**{nome_area}**")
    st.caption(f"Prova {ordem_idx} (Questoes {inicio}-{fim}) · {area}")

    label = f"Respostas {area}"
    key = f"resp_{area.lower()}"
    valor_atual = st.session_state.get(key, '')
    
    valor_digitado = st_keyup(
        label,
        value=valor_atual,
        max_chars=TOTAL_RESPOSTAS,
        key=key,
        debounce=100
    )
    respostas[area] = (valor_digitado or '').upper()

    _render_visualizacao_respostas(respostas.get(area, ''), area.lower(), offset_start=inicio)
    _mostrar_contador(respostas.get(area, ''), area.lower())


def _mostrar_contador(respostas: str, key: str):
    """Mostra contador de caracteres e validação."""
    total = TOTAL_RESPOSTAS
    n = len(respostas)
    
    if n == 0:
        st.caption(f"0/{total} respostas")
        return
    
    # Validar caracteres
    invalidos = [c for c in respostas if c not in 'ABCDE.*']
    
    if invalidos:
        st.error(f"Caracteres inválidos: {set(invalidos)}")
    elif n < total:
        st.warning(f"{n}/{total} respostas (faltam {total - n})")
    elif n == total:
        st.success(f"{total}/{total} respostas")
    else:
        st.error(f"{n}/{total} respostas (excedeu)")


def _render_visualizacao_respostas(respostas: str, key: str, offset_start: int = 1) -> None:
    """Mostra uma visualizacao agrupada das respostas em blocos de 5."""
    total = TOTAL_RESPOSTAS
    bloco = TAMANHO_BLOCO

    base = respostas[:total]
    if len(base) < total:
        base = base + ("_" * (total - len(base)))

    ruler = " | ".join([str(offset_start + i).ljust(bloco) for i in range(0, total, bloco)])
    blocks_html = _formatar_blocos_html(base, bloco)

    empty_class = " resp-visual--empty" if not respostas else ""
    html_block = f"""
    <div class="resp-visual{empty_class}" data-key="{key}">
        <div class="resp-visual__ruler">{html.escape(ruler)}</div>
        <div class="resp-visual__blocks">{blocks_html}</div>
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


def _formatar_blocos_html(respostas: str, bloco: int) -> str:
    """Formata as respostas em HTML, destacando vazios e invalidos."""
    grupos = []
    for i in range(0, len(respostas), bloco):
        trecho = respostas[i:i + bloco]
        grupos.append("".join(_formatar_char_html(c) for c in trecho))
    return " | ".join(grupos)


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
            
        if len(resp) != TOTAL_RESPOSTAS:
            erros.append(f"{area}: Deve ter {TOTAL_RESPOSTAS} respostas (tem {len(resp)})")
        
        invalidos = [c for c in resp if c not in 'ABCDE.*']
        if invalidos:
            erros.append(f"{area}: Caracteres inválidos: {set(invalidos)}")
    
    return len(erros) == 0, erros
