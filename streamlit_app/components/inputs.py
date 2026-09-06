# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de entrada de dados para o Streamlit.
"""

import streamlit as st
from .live_input import st_keyup
from typing import Dict, List, Optional, Tuple
import html
from ..config import AREAS_ENEM, ORDEM_AREAS, ORDEM_CORES


TOTAL_RESPOSTAS = 45
TAMANHO_BLOCO = 5


def input_respostas(
    ano: int, mapeador, tipo_aplicacao: str,
) -> Tuple[Dict[str, str], Dict[str, Optional[str]]]:
    """
    Renderiza os inputs de respostas para cada área.
    
    Args:
        ano: Ano da prova selecionado
        mapeador: Instância do mapeador (ordem das provas por ano)
        tipo_aplicacao: Aplicação selecionada para consultar as cores
    
    Returns:
        Respostas e cores por área; cor None indica área indisponível
    """
    respostas = {}
    cores = {}
    
    st.markdown("### Suas Respostas")
    st.caption("Digite suas 45 respostas para cada área usando as letras A, B, C, D, E. "
               "Use ponto (.) para questões não respondidas. Você pode preencher só as provas que desejar.")
    
    ordem_provas = _obter_ordem_provas(ano, mapeador)
    st.session_state['ordem_provas_atual'] = ordem_provas
    st.session_state['ano_respostas'] = ano
    
    for inicio in range(0, len(ordem_provas), 2):
        for idx, (area, coluna) in enumerate(zip(ordem_provas[inicio:inicio + 2], st.columns(2)), start=inicio + 1):
            with coluna, st.container(border=True, key=f"respostas_{area}"):
                st.markdown(f"**{AREAS_ENEM[area]}**")
                disponiveis = mapeador.listar_cores_disponiveis(ano, area, tipo_aplicacao)
                if disponiveis:
                    ordenadas = sorted(disponiveis, key=lambda c: (ORDEM_CORES.index(c) if c in ORDEM_CORES else 99, c))
                    chave = f"cor_{area}"
                    if st.session_state.get(chave) not in ordenadas:
                        st.session_state[chave] = ordenadas[0]
                    cores[area] = st.selectbox("Cor do caderno", ordenadas, key=chave,
                                               format_func=str.capitalize,
                                               help="Confira a cor na capa do caderno de questões.")
                else:
                    cores[area] = None
                    st.caption("Área não disponível nesta aplicação.")
                _render_input_prova(respostas, area, idx)

    st.session_state['respostas_por_area'] = {
        area: respostas.get(area, '') for area in ORDEM_AREAS
    }
    return respostas, cores


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


def _render_input_prova(respostas: Dict[str, str], area: str, ordem_idx: int) -> None:
    """Renderiza o bloco de input para uma prova na ordem indicada."""
    inicio = (ordem_idx - 1) * TOTAL_RESPOSTAS + 1
    fim = ordem_idx * TOTAL_RESPOSTAS

    st.caption(f"Prova {ordem_idx} (Questões {inicio}-{fim}) · {area}")

    label = f"Respostas {area}"
    key = f"resp_{area.lower()}"
    valor_atual = st.session_state.get(key, '')
    
    valor_digitado = _campo_respostas(label, valor_atual, key)
    respostas[area] = (valor_digitado or '').upper()

    _render_visualizacao_respostas(respostas.get(area, ''), area.lower(), offset_start=inicio)
    _mostrar_contador(respostas.get(area, ''))


def _campo_respostas(label: str, valor_atual: str, key: str) -> str:
    """Usa digitação em tempo real e recua para o campo nativo se necessário."""

    try:
        return st_keyup(
            label,
            value=valor_atual,
            max_chars=TOTAL_RESPOSTAS,
            key=key,
            debounce=100,
        )
    except ValueError as exc:
        if "is not registered" not in str(exc):
            raise
    return st.text_input(
        label,
        value=valor_atual,
        max_chars=TOTAL_RESPOSTAS,
        key=key,
    )


def _mostrar_contador(respostas: str):
    """Mostra contador de caracteres e validação."""
    total = TOTAL_RESPOSTAS
    n = len(respostas)
    
    if n == 0:
        st.caption(f"0/{total} respostas")
        return
    
    # Validar caracteres
    invalidos = [c for c in respostas if c not in 'ABCDE.*']
    
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
            
        if len(resp) != TOTAL_RESPOSTAS:
            erros.append(f"{area}: Deve ter {TOTAL_RESPOSTAS} respostas (tem {len(resp)})")
        
        invalidos = [c for c in resp if c not in 'ABCDE.*']
        if invalidos:
            erros.append(f"{area}: Caracteres inválidos: {', '.join(sorted(set(invalidos)))}")
    
    return len(erros) == 0, erros
