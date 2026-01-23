#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
TRI ENEM - Calculador de Nota Streamlit

Interface web para cálculo de nota TRI do ENEM.
Desenvolvido por Henrique Lindemann - Eng. Computação UFRGS

Execute com: streamlit run streamlit_app/app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Configurar paths
_app_dir = Path(__file__).parent
_root_dir = _app_dir.parent
sys.path.insert(0, str(_root_dir / 'src'))
sys.path.insert(0, str(_app_dir))

from calculador import get_calculador
from components.inputs import input_configuracoes, input_respostas, validar_todas_respostas
from components.resultados import exibir_resumo_geral, exibir_resultado_area

# ============================================================================
#                         CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="TRI ENEM - Calculador de Nota | Calcule sua nota com precisão",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/HenriqueLindemann/analise-enem',
        'Report a bug': 'https://github.com/HenriqueLindemann/analise-enem/issues',
        'About': """
        # TRI ENEM - Calculador de Nota
        
        Calcule sua nota do ENEM usando **Teoria de Resposta ao Item (TRI)** - 
        o mesmo método usado pelo INEP.
        
        Desenvolvido por Henrique Lindemann.
        
        [GitHub](https://github.com/HenriqueLindemann/analise-enem) | 
        [LinkedIn](https://www.linkedin.com/in/henriquelindemann/)
        """
    }
)

# CSS customizado
st.markdown("""
<style>
    /* Estilo geral */
    .main {
        padding-top: 1rem;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Inputs de texto */
    .stTextInput input {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        letter-spacing: 2px;
    }
    
    /* Botão principal */
    .stButton > button[kind="primary"] {
        width: 100%;
        font-size: 1.1rem;
        padding: 0.75rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Esconder elementos Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsividade Mobile */
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
        
        .stTextInput input {
            font-size: 12px;
            letter-spacing: 1px;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3 {
            font-size: 1rem !important;
        }
        
        .stButton > button {
            font-size: 1rem;
            padding: 0.5rem;
        }
        
        .footer {
            font-size: 0.75rem;
            padding: 1rem 0;
        }
    }
    
    /* Touch targets para mobile */
    @media (pointer: coarse) {
        .stSelectbox > div {
            min-height: 44px;
        }
        
        .stButton > button {
            min-height: 48px;
        }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
#                              SIDEBAR
# ============================================================================

def render_sidebar():
    """Renderiza a sidebar com configurações e informações."""
    
    with st.sidebar:
        st.markdown("## ⚙️ Configurações")
        
        # Obter calculador
        calc = get_calculador()
        mapeador = calc.mapeador
        
        # Inputs de configuração
        ano, tipo_aplicacao, lingua, cores = input_configuracoes(mapeador)
        
        st.markdown("---")
        
        # Informações
        with st.expander("Sobre o cálculo", expanded=False):
            st.markdown("""
            O cálculo usa **Teoria de Resposta ao Item (TRI)**, 
            o mesmo método usado pelo INEP.
            
            **Características:**
            - Modelo Logístico de 3 Parâmetros (ML3)
            - Estimação EAP (Expected a Posteriori)
            - Coeficientes de equalização calibrados
            
            **Precisão:**
            - Erro típico < 1 ponto para provas calibradas
            - Pode haver diferenças em provas não calibradas
            """)
        
        st.markdown("---")
        
        st.caption("""
        Desenvolvido por [Henrique Lindemann](https://github.com/HenriqueLindemann)
        
        [GitHub](https://github.com/HenriqueLindemann/analise-enem)
        """)
        
        return ano, tipo_aplicacao, lingua, cores


# ============================================================================
#                            PÁGINA PRINCIPAL
# ============================================================================

def main():
    """Função principal do app."""
    
    # Título
    st.markdown("""
    # TRI ENEM - Calculador de Nota
    
    Digite suas respostas e calcule sua nota usando o método oficial do INEP. Atualmente somente testado para navegadores desktop.
    
    **Primeiro passo:** Na barra lateral ⬅️, selecione o ano, tipo de prova e as cores de cada caderno.
    """)
    
    # Renderizar sidebar e obter configurações
    ano, tipo_aplicacao, lingua, cores = render_sidebar()
    
    # Inputs de respostas
    respostas = input_respostas()
    
    # Validação
    todas_validas, erros_validacao = validar_todas_respostas(respostas)
    
    # Verificar se há alguma resposta preenchida
    tem_respostas = any(r and r != "." * 45 for r in respostas.values())
    
    # Botão de calcular
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        calcular = st.button(
            "CALCULAR NOTA",
            type="primary",
            disabled=not tem_respostas,
            width='stretch'
        )
    
    # Mostrar erros de validação
    if erros_validacao and tem_respostas:
        for erro in erros_validacao:
            st.error(f"❌ {erro}")
    
    # Calcular e exibir resultados
    if calcular and tem_respostas and todas_validas:
        # Container para feedback de loading
        status_container = st.empty()
        progress_bar = st.progress(0, text="Iniciando cálculo...")
        
        try:
            progress_bar.progress(20, text="Carregando parâmetros TRI...")
            calc = get_calculador()
            
            progress_bar.progress(50, text="Calculando notas...")
            resultados, erros_calculo = calc.calcular_todas_areas(
                ano=ano,
                respostas=respostas,
                cores=cores,
                tipo_aplicacao=tipo_aplicacao,
                lingua=lingua
            )
            
            progress_bar.progress(100, text="Concluído!")
            progress_bar.empty()
        except Exception as e:
            progress_bar.empty()
            st.error(f"Erro ao calcular: {e}")
            resultados, erros_calculo = [], []
        
        # Mostrar erros de cálculo
        for erro in erros_calculo:
            st.warning(erro)
        
        if resultados:
            st.markdown("---")
            
            # Resumo geral
            exibir_resumo_geral(resultados)
            
            st.markdown("---")
            st.markdown("## Análise Detalhada por Área")
            st.caption("Clique em uma área para ver a análise completa")
            
            # Detalhes por área em expanders
            for resultado in resultados:
                sigla = resultado['sigla']
                nome = {
                    'LC': 'Linguagens e Códigos',
                    'CH': 'Ciências Humanas',
                    'CN': 'Ciências da Natureza',
                    'MT': 'Matemática'
                }.get(sigla, sigla)
                
                nota = resultado['nota']
                acertos = resultado['acertos']
                total = resultado['total_itens']
                
                with st.expander(f"**{nome}** — {nota:.0f} pts ({acertos}/{total} acertos)", expanded=False):
                    exibir_resultado_area(resultado)
            
            # Salvar resultados na sessão para possível download
            st.session_state['resultados'] = resultados
            st.session_state['ano'] = ano
            st.session_state['tipo_aplicacao'] = tipo_aplicacao
        else:
            st.error("Não foi possível calcular nenhuma nota. Verifique as configurações e respostas.")
    
    elif calcular and not tem_respostas:
        st.warning("Preencha pelo menos uma área para calcular.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>
            <strong>TRI ENEM</strong> - Calculador de Nota | 
            Desenvolvido por <a href="https://www.linkedin.com/in/henriquelindemann/" target="_blank">Henrique Lindemann</a> |
            <a href="https://github.com/HenriqueLindemann/analise-enem" target="_blank">GitHub</a>
        </p>
        <p style="font-size: 0.8rem; color: #888;">
            Cálculo aproximado - erro típico &lt; 1 ponto para provas calibradas
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
