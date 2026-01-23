# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de entrada de dados para o Streamlit.
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional


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


def input_respostas() -> Dict[str, str]:
    """
    Renderiza os inputs de respostas para cada área.
    
    Returns:
        Dict com sigla da área e string de respostas
    """
    respostas = {}
    
    st.markdown("### Suas Respostas")
    st.caption("Digite suas 45 respostas para cada área usando as letras A, B, C, D, E. "
               "Use ponto (.) para questões não respondidas.")
    
    # Dia 1
    st.markdown("#### Dia 1")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Linguagens e Códigos (LC)**")
        respostas['LC'] = st.text_input(
            "Respostas LC",
            value="",
            max_chars=45,
            key="resp_lc",
            label_visibility="collapsed",
            placeholder="Ex: ACABCDCEACABCACCBEAB..."
        ).upper()
        _mostrar_contador(respostas.get('LC', ''), 'lc')
    
    with col2:
        st.markdown("**Ciências Humanas (CH)**")
        respostas['CH'] = st.text_input(
            "Respostas CH",
            value="",
            max_chars=45,
            key="resp_ch",
            label_visibility="collapsed",
            placeholder="Ex: EDAAAADBCAABBABEECBB..."
        ).upper()
        _mostrar_contador(respostas.get('CH', ''), 'ch')
    
    # Dia 2
    st.markdown("#### Dia 2")
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**Ciências da Natureza (CN)**")
        respostas['CN'] = st.text_input(
            "Respostas CN",
            value="",
            max_chars=45,
            key="resp_cn",
            label_visibility="collapsed",
            placeholder="Ex: DABCEDEBEECBEABEBDCB..."
        ).upper()
        _mostrar_contador(respostas.get('CN', ''), 'cn')
    
    with col4:
        st.markdown("**Matemática (MT)**")
        respostas['MT'] = st.text_input(
            "Respostas MT",
            value="",
            max_chars=45,
            key="resp_mt",
            label_visibility="collapsed",
            placeholder="Ex: DCCAEBABDDCABEACCBCC..."
        ).upper()
        _mostrar_contador(respostas.get('MT', ''), 'mt')
    
    return respostas


def _mostrar_contador(respostas: str, key: str):
    """Mostra contador de caracteres e validação."""
    n = len(respostas)
    
    if n == 0:
        st.caption("0/45 respostas")
        return
    
    # Validar caracteres
    invalidos = [c for c in respostas if c not in 'ABCDE.']
    
    if invalidos:
        st.error(f"Caracteres inválidos: {set(invalidos)}")
    elif n < 45:
        st.warning(f"{n}/45 respostas (faltam {45 - n})")
    elif n == 45:
        st.success("45/45 respostas")
    else:
        st.error(f"{n}/45 respostas (excedeu)")


def validar_todas_respostas(respostas: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Valida todas as respostas.
    
    Returns:
        Tupla (todas_validas, lista_de_erros)
    """
    erros = []
    
    for area, resp in respostas.items():
        if not resp or resp == "." * 45:
            continue
            
        if len(resp) != 45:
            erros.append(f"{area}: Deve ter 45 respostas (tem {len(resp)})")
        
        invalidos = [c for c in resp if c not in 'ABCDE.']
        if invalidos:
            erros.append(f"{area}: Caracteres inválidos: {set(invalidos)}")
    
    return len(erros) == 0, erros
