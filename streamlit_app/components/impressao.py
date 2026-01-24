# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componente de geração de relatório PDF para o Streamlit.
"""

import streamlit as st
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import tempfile
import os
import sys

# Adicionar path do src para imports
_src_path = Path(__file__).parent.parent.parent / 'src'
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


def _gerar_pdf(resultados: List[Dict], ano: int, tipo_aplicacao: str, cor_prova: str) -> Optional[bytes]:
    """Gera o PDF e retorna bytes."""
    try:
        from tri_enem.relatorios import RelatorioPDF, DadosRelatorio
        from tri_enem.relatorios.base import AreaAnalise, QuestaoAnalise
    except ImportError:
        return None
    
    # Formatar tipo de aplicação
    tipos_extenso = {
        '1a_aplicacao': '1ª Aplicação',
        'digital': 'Digital',
        'reaplicacao': 'Reaplicação',
        'segunda_oportunidade': 'Segunda Oportunidade',
    }
    tipo_extenso = tipos_extenso.get(tipo_aplicacao, tipo_aplicacao)
    
    # Criar dados do relatório
    dados = DadosRelatorio(
        titulo="Resultado do Simulado", 
        ano_prova=ano,
        tipo_aplicacao=tipo_extenso,
        cor_prova=cor_prova.capitalize() if cor_prova else ''
    )
    
    # Converter resultados
    for r in resultados:
        questoes = []
        
        for q in r.get('questoes_acertadas', []):
            questoes.append(QuestaoAnalise(
                posicao=q['posicao'], 
                gabarito=q['gabarito'],
                resposta_dada=q['resposta_dada'], 
                acertou=True,
                param_a=q['param_a'], 
                param_b=q['param_b'], 
                param_c=q['param_c'],
                impacto=q['perda_se_errasse'], 
                co_item=q.get('co_item'),
            ))
        
        for q in r.get('questoes_erradas', []):
            questoes.append(QuestaoAnalise(
                posicao=q['posicao'], 
                gabarito=q['gabarito'],
                resposta_dada=q['resposta_dada'], 
                acertou=False,
                param_a=q['param_a'], 
                param_b=q['param_b'], 
                param_c=q['param_c'],
                impacto=q['ganho_se_acertasse'], 
                co_item=q.get('co_item'),
            ))
        
        area = AreaAnalise(
            sigla=r['sigla'], 
            nome=r.get('nome', r['sigla']), 
            ano=r.get('ano', ano), 
            co_prova=r.get('co_prova', 0),
            nota=r['nota'], 
            theta=r.get('theta', 0), 
            acertos=r['acertos'],
            total_itens=r['total_itens'], 
            questoes=questoes, 
            lingua=r.get('lingua'),
            cor_prova=r.get('cor_prova'),
        )
        dados.areas.append(area)
    
    # Gerar PDF
    try:
        fd, tmp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        relatorio = RelatorioPDF()
        relatorio.gerar(dados, tmp_path)
        
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
        
        os.unlink(tmp_path)
        return pdf_bytes
        
    except Exception:
        return None


def exibir_download_pdf(resultados: List[Dict], ano: int, tipo_aplicacao: str = ""):
    """
    Exibe botão de download do relatório PDF.
    
    Usa session_state para manter o PDF gerado entre reruns.
    """
    # Verificar dependências
    try:
        import reportlab
        import matplotlib
    except ImportError:
        st.info("📄 Relatório PDF não disponível. Instale: `pip install reportlab matplotlib`")
        return
    
    st.markdown("### 📄 Relatório PDF")
    st.caption("Relatório completo com gráficos, tabelas e análise de cada questão")
    
    # Obter cor predominante
    cor_prova = ""
    for r in resultados:
        if r.get('cor_prova'):
            cor_prova = r['cor_prova']
            break
    
    # Gerar PDF apenas uma vez e salvar na session
    if 'pdf_bytes' not in st.session_state or st.session_state.get('pdf_ano') != ano:
        with st.spinner("Gerando PDF..."):
            pdf_bytes = _gerar_pdf(resultados, ano, tipo_aplicacao, cor_prova)
            if pdf_bytes:
                st.session_state['pdf_bytes'] = pdf_bytes
                st.session_state['pdf_ano'] = ano
    
    pdf_bytes = st.session_state.get('pdf_bytes')
    
    if pdf_bytes:
        nome_arquivo = f"resultado_enem_{ano}.pdf"
        
        st.download_button(
            label="📥 Baixar Relatório PDF",
            data=pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf",
            type="secondary",
        )
    else:
        st.error("Não foi possível gerar o PDF.")
