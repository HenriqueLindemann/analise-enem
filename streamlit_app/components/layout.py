# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de layout e estrutura do app.

Separa a estrutura visual da lógica de negócio.
"""

import streamlit as st
from pathlib import Path
from typing import Tuple, Dict, Optional
import sys

# Adicionar path para imports
_app_dir = Path(__file__).parent.parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

from config import (
    APP_VERSION,
    APP_AUTHOR,
    APP_AUTHOR_URL,
    APP_GITHUB_URL,
    APP_ISSUES_URL,
    TEXTO_SOBRE,
    TEXTO_FOOTER,
    TEXTO_ABOUT_MENU,
    TIPOS_APLICACAO,
    ORDEM_TIPOS,
    ORDEM_CORES,
    SEO,
)


def configurar_pagina() -> None:
    """
    Configura a página do Streamlit com SEO otimizado.
    
    Deve ser chamado PRIMEIRO, antes de qualquer outro st.*.
    """
    st.set_page_config(
        page_title=SEO.page_title,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': APP_GITHUB_URL,
            'Report a bug': APP_ISSUES_URL,
            'About': TEXTO_ABOUT_MENU
        }
    )


def carregar_css() -> None:
    """Carrega o CSS externo do arquivo styles.css."""
    css_file = Path(__file__).parent.parent / 'styles.css'
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def render_header() -> None:
    """
    Renderiza o header da página com título e descrição SEO-friendly.
    
    """
    # H1 - Título principal (único por página)
    st.markdown(
        '<h1 style="margin-bottom: 0.5rem;">📊 Calculadora Nota TRI ENEM</h1>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        'Calcule sua nota <strong>REAL</strong> do ENEM online e grátis usando o método TRI oficial do INEP',
        unsafe_allow_html=True
    )
    
    # Destaques (SEO-friendly com keywords)
    st.markdown("""
<div class="highlights" style="margin: 1rem 0;">
    <p><strong>Nota REAL, não estimativa</strong> — Usamos os parâmetros oficiais disponibilizados pelo INEP</p>
    <p><strong>Impacto de cada questão</strong> — Veja quanto cada acerto ou erro afetou sua nota final</p>
    <p><strong>Análise completa</strong> — Gráficos e relatório PDF das 4 áreas de conhecimento</p>
</div>
    """, unsafe_allow_html=True)


def render_instrucoes() -> None:
    """Renderiza as instruções de uso."""
    st.markdown("""
---

### 👈 Complete as informações na barra lateral

**Passo 1:** Selecione o **ano**, **tipo de aplicação** e **cores** dos cadernos  
**Passo 2:** Digite suas **respostas** nas caixas abaixo  
**Passo 3:** Clique em **CALCULAR NOTA** e veja seus resultados!
    """)


def render_sidebar_config(mapeador) -> Tuple[int, str, str, Dict[str, str]]:
    """
    Renderiza a sidebar com configurações.
    
    Args:
        mapeador: Instância do MapeadorProvas
        
    Returns:
        Tupla (ano, tipo_aplicacao, lingua, cores_por_area)
    """
    with st.sidebar:
        st.markdown("## ⚙️ Configurações")
        
        # Anos disponíveis
        anos = mapeador.listar_anos_disponiveis()
        
        # Ano
        ano = st.selectbox(
            "Ano da prova",
            options=sorted(anos, reverse=True),
            index=0,
            help="Selecione o ano do ENEM"
        )
        
        # Tipos de aplicação disponíveis
        tipos_possiveis = set()
        for area in ['LC', 'CH', 'CN', 'MT']:
            tipos = mapeador.listar_tipos_disponiveis(ano, area)
            tipos_possiveis.update(tipos)
        
        tipos_disponiveis = [t for t in ORDEM_TIPOS if t in tipos_possiveis]
        
        tipo_aplicacao = st.selectbox(
            "Tipo de aplicação",
            options=tipos_disponiveis,
            format_func=lambda x: TIPOS_APLICACAO.get(x, x),
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
        cores_por_area = _render_cores_provas(mapeador, ano, tipo_aplicacao)
        
        st.markdown("---")
        
        # Informações sobre o cálculo
        with st.expander("Sobre o cálculo", expanded=False):
            st.markdown(TEXTO_SOBRE)
        
        st.markdown("---")
        
        # Créditos
        st.caption(f"""
Desenvolvido por [{APP_AUTHOR}]({APP_AUTHOR_URL})

[GitHub]({APP_GITHUB_URL})

v{APP_VERSION}
        """)
        
        return ano, tipo_aplicacao, lingua, cores_por_area


def _render_cores_provas(mapeador, ano: int, tipo_aplicacao: str) -> Dict[str, str]:
    """Renderiza seletor de cores das provas."""
    with st.expander("Cores das provas", expanded=True):
        st.caption("A cor da prova está na capa do caderno de questões.")
        
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
                    key=lambda c: ORDEM_CORES.index(c) if c in ORDEM_CORES else 99
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
        
        return cores_por_area


def render_botao_calcular(tem_respostas: bool) -> bool:
    """
    Renderiza o botão de calcular centralizado.
    
    Args:
        tem_respostas: Se há respostas preenchidas
        
    Returns:
        True se o botão foi clicado
    """
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        return st.button(
            "CALCULAR NOTA",
            type="primary",
            disabled=not tem_respostas,
            use_container_width=True
        )


def render_footer() -> None:
    """Renderiza o footer da página."""
    st.markdown("---")
    st.markdown(TEXTO_FOOTER, unsafe_allow_html=True)
