# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componente de geração de relatório PDF para o Streamlit.

Usa link HTML com data URI para abrir PDF em nova aba,
evitando rerun do Streamlit que perde o contexto.
"""

import streamlit as st
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import tempfile
import base64
import os
import sys

# Adicionar path do src para imports
_src_path = Path(__file__).parent.parent.parent / 'src'
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


@st.cache_data(show_spinner="Gerando PDF...")
def _gerar_pdf_cached(resultados_json: str, ano: int, tipo_aplicacao: str, cor_prova: str) -> Optional[bytes]:
    """
    Gera PDF com cache para evitar regeneração.
    
    Recebe JSON string para ser hashável pelo cache.
    """
    import json
    resultados = json.loads(resultados_json)
    return _gerar_pdf_interno(resultados, ano, tipo_aplicacao, cor_prova)


def _gerar_pdf_interno(resultados: List[Dict], ano: int, tipo_aplicacao: str, cor_prova: str) -> Optional[bytes]:
    """Lógica interna de geração do PDF."""
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
    Exibe link para abrir/baixar o relatório PDF em nova aba.
    
    Usa link HTML com data URI - não causa rerun do Streamlit.
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
    
    # Converter para JSON para cache
    import json
    resultados_json = json.dumps(resultados, ensure_ascii=False)
    
    # Gerar PDF (com cache - só gera uma vez)
    pdf_bytes = _gerar_pdf_cached(resultados_json, ano, tipo_aplicacao, cor_prova)
    
    if pdf_bytes:
        # Converter para base64
        b64 = base64.b64encode(pdf_bytes).decode()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"resultado_enem_{ano}_{timestamp}.pdf"
        
        # Link HTML que abre em nova aba - NÃO causa rerun
        href = f'data:application/pdf;base64,{b64}'
        st.markdown(
            f'''
            <a href="{href}" download="{nome_arquivo}" target="_blank" 
               style="display: inline-block; padding: 0.5rem 1rem; 
                      background-color: #3498DB; color: white; 
                      text-decoration: none; border-radius: 0.5rem;
                      font-weight: 600; font-size: 1rem;">
                📥 Baixar Relatório PDF
            </a>
            <p style="margin-top: 0.5rem; font-size: 0.85rem; color: #888;">
                Clique para baixar ou abrir em nova aba
            </p>
            ''',
            unsafe_allow_html=True
        )
    else:
        st.error("Não foi possível gerar o PDF. Verifique se reportlab e matplotlib estão instalados.")
