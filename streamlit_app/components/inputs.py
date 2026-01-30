# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de entrada de dados para o Streamlit.
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional
import html
from config import AREAS_ENEM, ORDEM_AREAS


TOTAL_RESPOSTAS = 45
TAMANHO_BLOCO = 5
PLACEHOLDERS = {
    'LC': "Ex: ACABCDCEACABCACCBEAB...",
    'CH': "Ex: EDAAAADBCAABBABEECBB...",
    'CN': "Ex: DABCEDEBEECBEABEBDCB...",
    'MT': "Ex: DCCAEBABDDCABEACCBCC...",
}


def input_configuracoes(mapeador) -> Tuple[int, str, str, Dict[str, str]]:
    """
    Renderiza os inputs de configuração (ano, tipo, língua, cores).
    
    Args:
        mapeador: Instância do MapeadorProvas
        
    Returns:
        Tupla (ano, tipo_aplicacao, lingua, cores_por_area)
    """
    anos = mapeador.listar_anos_disponiveis()
    
    # Ano
    ano = st.selectbox(
        "Ano da prova",
        options=sorted(anos, reverse=True),
        index=0,
        help="Selecione o ano do ENEM"
    )
    
    # Tipo de aplicação
    tipos_possiveis = set()
    for area in ['LC', 'CH', 'CN', 'MT']:
        tipos = mapeador.listar_tipos_disponiveis(ano, area)
        tipos_possiveis.update(tipos)
    
    tipos_formatados = {
        '1a_aplicacao': '1ª Aplicação',
        'digital': 'Digital',
        'reaplicacao': 'Reaplicação',
        'segunda_oportunidade': 'Segunda Oportunidade',
    }
    
    tipos_ordenados = ['1a_aplicacao', 'digital', 'reaplicacao', 'segunda_oportunidade']
    tipos_disponiveis = [t for t in tipos_ordenados if t in tipos_possiveis]
    
    tipo_aplicacao = st.selectbox(
        "Tipo de aplicação",
        options=tipos_disponiveis,
        format_func=lambda x: tipos_formatados.get(x, x),
        index=0,
        help="Tipo de aplicação do exame"
    )
    
    # Língua estrangeira
    lingua = st.selectbox(
        "Língua estrangeira",
        options=['ingles', 'espanhol'],
        format_func=lambda x: 'Inglês' if x == 'ingles' else 'Espanhol',
        index=0,
        help="Língua estrangeira para Linguagens"
    )
    
    # Cores por área
    with st.expander("Cores das provas", expanded=True):
        st.caption("A cor da prova está na capa do caderno de questões.")
        
        # Ordem padrão das cores
        ordem_cores = ['azul', 'amarela', 'rosa', 'cinza', 'branca', 'verde', 'laranja']
        
        cores_por_area = {}
        areas_nomes = [
            ('LC', 'Linguagens'),
            ('CH', 'Humanas'),
            ('CN', 'Natureza'),
            ('MT', 'Matemática')
        ]
        
        for sigla, nome in areas_nomes:
            cores_disponiveis = mapeador.listar_cores_disponiveis(ano, sigla, tipo_aplicacao)
            if cores_disponiveis:
                # Ordenar cores de forma consistente
                cores_ordenadas = sorted(
                    cores_disponiveis,
                    key=lambda c: ordem_cores.index(c) if c in ordem_cores else 99
                )
                cor = st.selectbox(
                    nome,
                    options=cores_ordenadas,
                    format_func=lambda x: x.capitalize(),
                    index=0,
                    key=f"cor_{sigla}"
                )
                cores_por_area[sigla] = cor
            else:
                st.caption(f"{nome}: Não disponível")
                cores_por_area[sigla] = None
    
    return ano, tipo_aplicacao, lingua, cores_por_area


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
    """Obtém a ordem das provas a partir do backend, com fallback seguro."""
    if mapeador is None:
        return ORDEM_AREAS.copy()

    candidatos = [
        "listar_ordem_provas",
        "obter_ordem_provas",
        "get_ordem_provas",
    ]

    for nome in candidatos:
        func = getattr(mapeador, nome, None)
        if callable(func):
            try:
                ordem = func(ano)
            except Exception:
                ordem = None
            return _normalizar_ordem_provas(ordem)

    return ORDEM_AREAS.copy()


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
    placeholder = PLACEHOLDERS.get(area, "Ex: ABCDEABCDEABCDEABCDE...")
    key = f"resp_{area.lower()}"

    respostas[area] = st.text_input(
        label,
        max_chars=TOTAL_RESPOSTAS,
        key=key,
        label_visibility="collapsed",
        placeholder=placeholder
    ).upper()

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
    invalidos = [c for c in respostas if c not in 'ABCDE.']
    
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
    if c == ".":
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
        
        invalidos = [c for c in resp if c not in 'ABCDE.']
        if invalidos:
            erros.append(f"{area}: Caracteres inválidos: {set(invalidos)}")
    
    return len(erros) == 0, erros
