# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Análise das notas oficiais de 2009 a 2025 agrupadas pelo número de acertos."""

import json
from pathlib import Path
from typing import Dict, Optional

import plotly.graph_objects as go
import streamlit as st

from ..config import AREAS_ENEM, ORDEM_AREAS

ARQUIVO = Path(__file__).parent.parent / "assets" / "notas_por_acertos.json"
COR_LINHA = "#2471a3"
COR_BORDA = "#a9c7df"
COR_FAIXA = "rgba(36, 113, 163, 0.12)"


@st.cache_resource(show_spinner=False)
def carregar_notas_por_acertos() -> Dict:
    return json.loads(ARQUIVO.read_text(encoding="utf-8"))


def _inteiro(valor: float) -> str:
    return f"{round(valor):,}".replace(",", ".")


def resumo_acertos(dados: Dict, area: str, acertos: int) -> Optional[Dict]:
    """Participantes de todos os anos juntos e cada ano, para quem teve ``acertos``."""
    geral = dados["geral"][area].get(str(acertos))
    if geral is None:
        return None
    _, p10, p50, p90 = geral
    edicoes = {}
    for ano, prova in dados["edicoes"][area].items():
        baixo, mediana, alto, modelo = prova["acertos"][str(acertos)]
        edicoes[int(ano)] = {
            "de": baixo, "mediana": mediana, "ate": alto, "modelo": bool(modelo),
            "validas": prova["itens_validos"] if acertos > prova["itens_validos"] else None,
        }
    return {"mediana": p50, "de": p10, "ate": p90, "edicoes": dict(sorted(edicoes.items()))}


def _texto_hover(ano: int, v: Dict) -> str:
    rotulo = '<br><span style="color:#596777">{}</span>  <b>{}</b>'
    nota = '<br><span style="color:#596777;font-size:12px">{}</span>'
    texto = f'<b style="font-size:15px">{ano}</b>'
    if round(v["de"]) == round(v["ate"]):
        texto += rotulo.format("Nota", _inteiro(v["mediana"]))
    else:
        texto += rotulo.format("Mediana", _inteiro(v["mediana"]))
        texto += rotulo.format("80% entre", f'{_inteiro(v["de"])}</b> e <b>{_inteiro(v["ate"])}')
    if v["validas"]:
        texto += nota.format(f'{v["validas"]} questões válidas: todas certas')
    if v["modelo"]:
        texto += nota.format("Poucos participantes: estimado pelo modelo TRI")
    return texto


def grafico_acertos(resumo: Dict) -> go.Figure:
    """Por ano: linha da mediana sobre a faixa onde ficaram 80% dos participantes."""
    anos = list(resumo["edicoes"])
    valores = list(resumo["edicoes"].values())
    baixo, mediana, alto = ([v[c] for v in valores] for c in ("de", "mediana", "ate"))
    modelo = [v["modelo"] for v in valores]
    borda = dict(color=COR_BORDA, width=1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=anos, y=baixo, mode="lines", line=borda, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=anos, y=alto, mode="lines", line=borda, hoverinfo="skip",
                             fill="tonexty", fillcolor=COR_FAIXA))
    fig.add_trace(go.Scatter(
        x=anos, y=mediana, mode="lines+markers",
        line=dict(color=COR_LINHA, width=2.5),
        # Vazado: ano estimado pelo modelo.
        marker=dict(size=[9 if m else 7 for m in modelo],
                    color=["white" if m else COR_LINHA for m in modelo],
                    line=dict(width=[2 if m else 1.5 for m in modelo],
                              color=[COR_LINHA if m else "white" for m in modelo])),
        hovertext=[_texto_hover(a, v) for a, v in zip(anos, valores)], hoverinfo="text",
    ))
    menor, maior = min(baixo), max(alto)
    folga = max(10.0, (maior - menor) * 0.08)
    fig.update_layout(
        height=300,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="white", plot_bgcolor="white",
        showlegend=False, dragmode=False,
        hoverlabel=dict(bgcolor="white", bordercolor="#d6dbe1", align="left",
                        font=dict(size=13, color="#2c3e50")),
        xaxis=dict(
            tickmode="array", tickvals=list(range(2009, 2026, 4)),
            range=[2008.6, 2025.4], showgrid=False, fixedrange=True,
            tickfont=dict(size=12, color="#596777"),
        ),
        yaxis=dict(
            range=[max(0.0, menor - folga), maior + folga],
            gridcolor="#e8ebef", zeroline=False, fixedrange=True,
            tickfont=dict(size=12, color="#596777"), nticks=6,
        ),
    )
    return fig


def _texto_resumo(resumo: Dict) -> str:
    return (
        '<div class="acertos-resumo">'
        f'<p><span>Mediana</span><strong>{_inteiro(resumo["mediana"])}</strong></p>'
        f'<p><span>80% ficaram entre</span><strong>{_inteiro(resumo["de"])} e '
        f'{_inteiro(resumo["ate"])}</strong></p></div>'
    )


@st.dialog("Notas por número de acertos", width="large")
def _dialog_acertos() -> None:
    st.markdown(
        "Notas oficiais de quem teve o mesmo número de acertos nas provas de 2009 a 2025 "
        "(1ª aplicação). **Use como análise histórica, não previsão!**"
    )
    col_area, col_acertos = st.columns(2)
    with col_area:
        area = st.selectbox("Área", ORDEM_AREAS, key="acertos_area",
                            format_func=AREAS_ENEM.get)
    with col_acertos:
        acertos = st.number_input("Acertos", min_value=0, max_value=45, value=None,
                                  step=1, placeholder="0 a 45", key="acertos")
    if acertos is None:
        return
    acertos = int(acertos)
    resumo = resumo_acertos(carregar_notas_por_acertos(), area, acertos)
    if resumo is None:
        return
    st.markdown(_texto_resumo(resumo), unsafe_allow_html=True)
    st.plotly_chart(grafico_acertos(resumo), key="grafico_acertos",
                    config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})
    st.caption("Linha: mediana (metade ficou acima, metade abaixo). "
               "Faixa: onde ficaram 80% dos participantes.")


def render_botao_acertos() -> None:
    if st.button("Mas e analisando só pela quantidade de acertos?",
                 icon=":material/bar_chart:", key="abrir_acertos"):
        _dialog_acertos()
