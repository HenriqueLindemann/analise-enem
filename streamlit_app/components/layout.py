# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Estrutura da página, com controles nativos do Streamlit."""

from pathlib import Path
from typing import Tuple
from urllib.parse import quote
import streamlit as st

from ..config import (
    APP_VERSION, APP_GITHUB_URL, APP_ISSUES_URL,
    APP_VIDEO_SHARE_URL, APP_VIDEO_FILE_URL,
    ANO_EM_BREVE, TEXTO_ENEM_2026,
    TEXTO_SOBRE, TEXTO_PRIVACIDADE, TEXTO_FOOTER, TEXTO_ABOUT_MENU,
    TIPOS_APLICACAO, ORDEM_TIPOS, SEO,
)
from .acertos import render_botao_acertos

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
    st.markdown("**No ENEM, importa não só quantas questões você acerta, mas quais.**")
    st.caption("Estimativa pela TRI, o mesmo modelo do INEP, com os parâmetros oficiais "
               "da prova. Veja o que mais pesou na sua nota.")
    render_botao_video()


@st.dialog("Como a nota TRI é calculada", width="large")
def _dialog_video(autoplay: bool = False) -> None:
    st.video(str(VIDEO_PATH))
    if autoplay:
        st.html(_JS_AUTOPLAY, unsafe_allow_javascript=True)
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


def render_config(mapeador) -> Tuple[int, str | None]:
    st.subheader("Sua prova")
    anos_calculaveis = sorted(mapeador.listar_anos_disponiveis(), reverse=True)
    anos_opcoes = sorted(set(anos_calculaveis) | {ANO_EM_BREVE}, reverse=True)
    index_padrao = anos_opcoes.index(anos_calculaveis[0]) if anos_calculaveis else 0
    col_ano, col_tipo = st.columns(2)
    with col_ano:
        ano = st.selectbox("Ano da prova", anos_opcoes, index=index_padrao, key="ano_prova")
    tipos = set()
    for area in ("LC", "CH", "CN", "MT"):
        tipos.update(mapeador.listar_tipos_disponiveis(ano, area))
    disponiveis = [tipo for tipo in ORDEM_TIPOS if tipo in tipos]
    if not disponiveis:
        return ano, None
    if st.session_state.get("tipo_prova") not in disponiveis:
        tipo_salvo = st.session_state.get("tipo_prova_salvo")
        st.session_state["tipo_prova"] = tipo_salvo if tipo_salvo in disponiveis else disponiveis[0]
    with col_tipo:
        tipo = st.selectbox("Tipo de aplicação", disponiveis, key="tipo_prova",
                            format_func=lambda t: TIPOS_APLICACAO.get(t, t))
    st.session_state["tipo_prova_salvo"] = tipo
    return ano, tipo


def render_aviso_ano_em_breve() -> None:
    with st.container(border=True, key="aviso_ano_em_breve"):
        st.markdown(TEXTO_ENEM_2026)
        render_botao_acertos()


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
