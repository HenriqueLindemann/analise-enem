# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componente de geração de relatório PDF para o Streamlit.
"""

from __future__ import annotations

import streamlit as st
from typing import List, Dict, Optional
from pathlib import Path
import tempfile
import os
import sys
import hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TEXTO_DOWNLOAD_PDF = (
    "Baixe uma versão acessível e organizada dos resultados para salvar, "
    "imprimir ou compartilhar."
)

TZ_BRASILIA = timezone(timedelta(hours=-3))


def _data_geracao_no_fuso_usuario(
    nome_fuso: str | None,
    deslocamento_minutos: int | None,
    agora_utc: datetime | None = None,
) -> datetime:
    """Retorna o horário do navegador; usa Brasília quando ele não o informa."""

    agora_utc = agora_utc or datetime.now(timezone.utc)
    if nome_fuso:
        try:
            return agora_utc.astimezone(ZoneInfo(nome_fuso))
        except (ZoneInfoNotFoundError, ValueError):
            pass
    if deslocamento_minutos is not None:
        try:
            fuso = timezone(-timedelta(minutes=int(deslocamento_minutos)))
            return agora_utc.astimezone(fuso)
        except (OverflowError, TypeError, ValueError):
            pass
    return agora_utc.astimezone(TZ_BRASILIA)


def _data_geracao_usuario() -> datetime:
    contexto = getattr(st, "context", None)
    return _data_geracao_no_fuso_usuario(
        getattr(contexto, "timezone", None),
        getattr(contexto, "timezone_offset", None),
    )

# Adicionar path do src para imports
_src_path = Path(__file__).parent.parent.parent / 'src'
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


def _gerar_pdf(resultados: List[Dict], ano: int, tipo_aplicacao: str, cor_prova: str) -> Optional[bytes]:
    """Gera o PDF e retorna bytes."""
    if not resultados:
        return None
    try:
        from tri_enem.relatorios import (
            RelatorioPDF,
            adaptar_resultados_para_relatorio,
        )
    except ImportError:
        return None
    dados = adaptar_resultados_para_relatorio(
        resultados,
        ano,
        titulo="Desempenho no Simulado ENEM",
        tipo_aplicacao=tipo_aplicacao,
        cor_prova=cor_prova,
        data_geracao=_data_geracao_usuario(),
    )
    
    # Gerar PDF. Exceções são propagadas para que a interface mostre a causa.
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        relatorio = RelatorioPDF()
        relatorio.gerar(dados, tmp_path)
        
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
        return pdf_bytes
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def exibir_download_pdf(resultados: List[Dict], ano: int, tipo_aplicacao: str = ""):
    """
    Exibe botão de download do relatório PDF.
    
    Usa session_state para manter o PDF gerado entre reruns.
    """
    st.markdown("### Relatório PDF")
    st.caption(TEXTO_DOWNLOAD_PDF)
    
    # Obter cor predominante
    cor_prova = ""
    for r in resultados:
        if r.get('cor_prova'):
            cor_prova = r['cor_prova']
            break
    
    cor_prova = cor_prova or ''
    pdf_chave = hashlib.sha256(
        repr((ano, tipo_aplicacao, cor_prova, resultados)).encode('utf-8')
    ).hexdigest()

    # Gerar PDF apenas uma vez e salvar na session
    if st.session_state.get('pdf_chave') != pdf_chave:
        st.session_state.pop('pdf_bytes', None)
        with st.spinner("Gerando PDF..."):
            try:
                pdf_bytes = _gerar_pdf(
                    resultados, ano, tipo_aplicacao, cor_prova
                )
            except Exception as exc:
                st.error(f"Não foi possível gerar o PDF: {exc}")
                return
            if pdf_bytes:
                st.session_state['pdf_bytes'] = pdf_bytes
                st.session_state['pdf_chave'] = pdf_chave
    
    pdf_bytes = st.session_state.get('pdf_bytes')
    
    if pdf_bytes:
        nome_arquivo = f"resultado_enem_{ano}.pdf"
        
        st.download_button(
            label="Baixar Relatório PDF",
            data=pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf",
            type="secondary",
            on_click="ignore",
            width="stretch",
        )
    else:
        st.error("Não foi possível gerar o PDF.")
