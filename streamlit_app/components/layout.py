# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Estrutura da página, com controles nativos do Streamlit."""

from pathlib import Path
from typing import Tuple
import streamlit as st

from ..config import (
    APP_VERSION, APP_GITHUB_URL, APP_ISSUES_URL,
    TEXTO_SOBRE, TEXTO_PRIVACIDADE, TEXTO_FOOTER, TEXTO_ABOUT_MENU,
    TIPOS_APLICACAO, ORDEM_TIPOS, SEO,
)


def configurar_pagina() -> None:
    st.set_page_config(
        page_title=SEO.page_title, page_icon="📊", layout="wide",
        menu_items={"Get Help": APP_GITHUB_URL, "Report a bug": APP_ISSUES_URL,
                    "About": TEXTO_ABOUT_MENU},
    )


def carregar_css() -> None:
    css_file = Path(__file__).parent.parent / "styles.css"
    st.html(f"<style>{css_file.read_text(encoding='utf-8')}</style>")


def render_header() -> None:
    """
    Renderiza o header da página com título e descrição SEO-friendly.
    
    """
    # H1 - Título principal (único por página)
    st.markdown(
        '<h1 style="margin-bottom: 0.5rem;">Calculadora Nota TRI ENEM</h1>',
        unsafe_allow_html=True
    )

    st.markdown(
        'Estime sua nota do ENEM com TRI e validação em microdados oficiais do '
        'INEP. **Agora com mais precisão!**',
        unsafe_allow_html=True
    )
    
    # Destaques (SEO-friendly com keywords)
    st.markdown("""
<div class="highlights" style="margin: 1rem 0;">
    <p><strong>Impacto de cada questão</strong> · Veja quanto cada acerto ou erro afetou sua nota final</p>
    <p><strong>Análise completa</strong> · Gráficos e relatório PDF das 4 áreas de conhecimento</p>
</div>
    """, unsafe_allow_html=True)


def render_instrucoes() -> None:
    """Renderiza as instruções de uso."""
    st.markdown("""
---

### Complete as informações da prova abaixo

**Passo 1:** Selecione o **ano**, **tipo de aplicação** e **cores** dos cadernos  
**Passo 2:** Digite suas **respostas** nas caixas abaixo  
**Passo 3:** Clique em **CALCULAR NOTA** e veja seus resultados!
    """)


def render_config(mapeador) -> Tuple[int, str, str]:
    st.subheader("Sua prova")
    col_ano, col_tipo, col_lingua = st.columns(3)
    with col_ano:
        ano = st.selectbox("Ano da prova", sorted(mapeador.listar_anos_disponiveis(), reverse=True), key="ano_prova")
    tipos = set()
    for area in ("LC", "CH", "CN", "MT"):
        tipos.update(mapeador.listar_tipos_disponiveis(ano, area))
    disponiveis = [tipo for tipo in ORDEM_TIPOS if tipo in tipos]
    if st.session_state.get("tipo_prova") not in disponiveis:
        st.session_state["tipo_prova"] = disponiveis[0]
    with col_tipo:
        tipo = st.selectbox("Tipo de aplicação", disponiveis, key="tipo_prova",
                            format_func=lambda t: TIPOS_APLICACAO.get(t, t))
    with col_lingua:
        lingua = st.selectbox("Língua estrangeira", ["ingles", "espanhol"],
                               key="lingua_prova", help="Para a prova de Linguagens",
                               format_func=lambda l: "Inglês" if l == "ingles" else "Espanhol")
    return ano, tipo, lingua


def render_botao_calcular(pode_calcular: bool) -> bool:
    return st.button("Calcular nota", type="primary", disabled=not pode_calcular,
                     width="stretch", key="calcular")


def render_footer() -> None:
    st.markdown("---")
    with st.container(horizontal=True, horizontal_alignment="left", gap="small"):
        with st.popover("Sobre o cálculo"):
            st.markdown(TEXTO_SOBRE)
            st.caption(f"v{APP_VERSION}")
        with st.popover("Microdados ENEM e privacidade"):
            st.markdown(TEXTO_PRIVACIDADE)
    st.markdown(TEXTO_FOOTER, unsafe_allow_html=True)
