# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Estrutura da página, com controles nativos do Streamlit."""

from pathlib import Path
from typing import Tuple
from urllib.parse import quote
import streamlit as st

from ..config import (
    APP_VERSION, APP_GITHUB_URL, APP_ISSUES_URL,
    APP_VIDEO_SHARE_URL, APP_VIDEO_FILE_URL,
    TEXTO_SOBRE, TEXTO_PRIVACIDADE, TEXTO_FOOTER, TEXTO_ABOUT_MENU,
    TIPOS_APLICACAO, ORDEM_TIPOS, SEO,
)

VIDEO_PATH = Path(__file__).parent.parent / "assets" / "video-nota-tri.mp4"

# Toca só o vídeo do diálogo aberto e pausa o que sair da página, evitando
# áudio sem janela. O ``autoplay`` do st.video não dá essa garantia.
_JS_AUTOPLAY = """<script>
(() => {
  const inicio = Date.now();
  const busca = setInterval(() => {
    const video = document.querySelector('[data-testid="stDialog"] video');
    if (!video) {
      if (Date.now() - inicio > 5000) clearInterval(busca);
      return;
    }
    clearInterval(busca);
    video.addEventListener("play", () => { if (!video.isConnected) video.pause(); });
    const vigia = setInterval(() => {
      if (!video.isConnected) { video.pause(); clearInterval(vigia); }
    }, 250);
    video.play().catch(() => {});
  }, 100);
})();
</script>"""


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
    st.markdown('<h1 style="margin-bottom: 0.5rem;">Calculadora Nota TRI ENEM</h1>',
                unsafe_allow_html=True)
    st.markdown("Estime sua nota por TRI, com precisão conferida em microdados do INEP.")
    st.caption("Peso de cada questão · gráficos · relatório PDF")
    render_botao_video()


@st.dialog("Como a nota TRI é calculada", width="large")
def _dialog_video(autoplay: bool = False) -> None:
    st.video(str(VIDEO_PATH))
    if autoplay:
        st.html(_JS_AUTOPLAY, unsafe_allow_javascript=True)
    st.caption("2 min · Matemática, ENEM 2024 · parâmetros reais publicados pelo INEP")
    texto = f"Entenda em 2 minutos como a nota TRI do ENEM é calculada: {APP_VIDEO_SHARE_URL}"
    with st.container(horizontal=True, gap="small"):
        st.link_button("WhatsApp", f"https://wa.me/?text={quote(texto)}",
                       icon=":material/share:")
        st.link_button("Baixar vídeo", APP_VIDEO_FILE_URL, icon=":material/download:")
    st.code(APP_VIDEO_SHARE_URL, language=None)


def render_botao_video() -> None:
    """Abre o vídeo pelo botão ou uma vez por sessão com ``?video=1`` na URL.

    Só o clique conta como gesto do usuário, que libera autoplay com som.
    """
    if st.button("Entenda o cálculo em 2 min", icon=":material/play_circle:", key="abrir_video"):
        _dialog_video(autoplay=True)
    elif st.query_params.get("video") and not st.session_state.get("video_aberto"):
        st.session_state["video_aberto"] = True
        _dialog_video()


def render_config(mapeador) -> Tuple[int, str]:
    st.subheader("Sua prova")
    col_ano, col_tipo = st.columns(2)
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
    return ano, tipo


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
