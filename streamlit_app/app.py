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
from components.impressao import exibir_download_pdf

# ============================================================================
#                         CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Calculadora TRI ENEM - Calcule sua Nota do ENEM Online Grátis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/HenriqueLindemann/analise-enem',
        'Report a bug': 'https://github.com/HenriqueLindemann/analise-enem/issues',
        'About': """
        # Calculadora TRI ENEM - Nota do ENEM Online
        
        Calcule sua nota real do ENEM usando **Teoria de Resposta ao Item (TRI)** - 
        o mesmo método oficial usado pelo INEP/MEC.
        
        Ferramenta gratuita para estudantes, professores e pesquisadores.
        
        Desenvolvido por Henrique Lindemann - Engenharia de Computação UFRGS.
        
        [GitHub](https://github.com/HenriqueLindemann/analise-enem) | 
        [LinkedIn](https://www.linkedin.com/in/henriquelindemann/)
        """
    }
)

# Meta tags para SEO - palavras-chave e descrição
st.markdown("""
<meta name="description" content="Calculadora TRI ENEM - Calcule sua nota real do ENEM online grátis usando a Teoria de Resposta ao Item (TRI). Simulador oficial com gabaritos de 2009 a 2024. Ferramenta gratuita para estudantes.">
<meta name="keywords" content="ENEM, TRI, calculadora ENEM, nota ENEM, simulador ENEM, Teoria de Resposta ao Item, calcular nota ENEM, gabarito ENEM, prova ENEM, INEP, vestibular, nota TRI, simulado ENEM online, ENEM 2024, ENEM 2023, correção ENEM">
<meta name="author" content="Henrique Lindemann">
<meta name="robots" content="index, follow">
<meta property="og:title" content="Calculadora TRI ENEM - Calcule sua Nota Online Grátis">
<meta property="og:description" content="Simule sua nota do ENEM com precisão usando TRI. Gabaritos oficiais de 2009 a 2024. Gratuito para estudantes e pesquisadores.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://calculadoratri.streamlit.app">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Calculadora TRI ENEM - Nota Online Grátis">
<meta name="twitter:description" content="Calcule sua nota do ENEM usando TRI. Ferramenta gratuita com gabaritos de 2009 a 2024.">
""", unsafe_allow_html=True)


def carregar_css():
    """Carrega o CSS externo do arquivo styles.css."""
    css_file = Path(__file__).parent / 'styles.css'
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Carregar estilos
carregar_css()


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
        Desenvolvido por [Henrique Lindemann](https://www.linkedin.com/in/henriquelindemann/)
        
        [GitHub](https://github.com/HenriqueLindemann/analise-enem)
        
        v24.01.2026
        """)
        
        return ano, tipo_aplicacao, lingua, cores


# ============================================================================
#                            PÁGINA PRINCIPAL
# ============================================================================

def main():
    """Função principal do app."""
    
    # Título
    st.title("📊 Calculadora Nota TRI ENEM")
    
    # Descrição otimizada para SEO (search engines favorecem st.header e st.text)
    st.header("Calcule sua nota REAL do ENEM online e grátis. Método TRI oficial do INEP com dados reais de calibração.")
    
    st.markdown("""
    **Nota REAL, não estimativa** — Usamos os parâmetros oficiais de calibração do INEP  
    **Impacto de cada questão** — Veja quanto cada acerto ou erro afetou sua nota final  
    **Matemática, não chutes** — Cálculo TRI com precisão < 1 ponto de erro  
    **Análise completa** — Gráficos e relatório PDF das 4 áreas de conhecimento
    
    ---
    
    ### 👉 Complete as informações na barra lateral
    
    **Passo 1:** Selecione o **ano**, **tipo de aplicação** e **cores** dos cadernos  
    **Passo 2:** Digite suas **respostas** nas caixas abaixo  
    **Passo 3:** Clique em **CALCULAR NOTA** e veja seus resultados!
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
            use_container_width=True
        )
    
    # Mostrar erros de validação
    if erros_validacao and tem_respostas:
        for erro in erros_validacao:
            st.error(f"❌ {erro}")
    
    # Calcular notas quando botão for clicado
    if calcular and tem_respostas and todas_validas:
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
            
            # Salvar resultados na sessão
            if resultados:
                st.session_state['resultados'] = resultados
                st.session_state['resultado_ano'] = ano
                st.session_state['resultado_tipo'] = tipo_aplicacao
                # Limpar PDF antigo para gerar novo
                if 'pdf_bytes' in st.session_state:
                    del st.session_state['pdf_bytes']
            
        except Exception as e:
            progress_bar.empty()
            st.error(f"Erro ao calcular: {e}")
            resultados, erros_calculo = [], []
        
        # Mostrar erros de cálculo
        for erro in erros_calculo:
            st.warning(erro)
        
        if not resultados:
            st.error("Não foi possível calcular nenhuma nota. Verifique as configurações e respostas.")
    
    elif calcular and not tem_respostas:
        st.warning("Preencha pelo menos uma área para calcular.")
    
    # Exibir resultados salvos (após calcular ou após rerun do download)
    if 'resultados' in st.session_state and st.session_state['resultados']:
        resultados = st.session_state['resultados']
        ano_resultado = st.session_state.get('resultado_ano', ano)
        tipo_resultado = st.session_state.get('resultado_tipo', tipo_aplicacao)
        
        st.markdown("---")
        
        # Resumo geral
        exibir_resumo_geral(resultados)
        
        st.markdown("---")
        st.markdown("## Análise Detalhada por Área")
        st.caption("Clique em uma área para ver a análise completa")
        
        # Detalhes por área
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
        
        # Download do relatório PDF
        st.markdown("---")
        exibir_download_pdf(resultados, ano_resultado, tipo_resultado)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>
            <strong>Calculadora TRI ENEM</strong> | 
            Desenvolvido por <a href="https://www.linkedin.com/in/henriquelindemann/" target="_blank">Henrique Lindemann</a> |
            <a href="https://github.com/HenriqueLindemann/analise-enem" target="_blank">GitHub</a>
        </p>
        <p style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
            📚 Este projeto é <strong>gratuito</strong> e de <strong>uso livre</strong> para estudantes, professores e pesquisadores. Uso comercial requer autorização.
        </p>
        <p style="font-size: 0.8rem; color: #888;">
            Cálculo aproximado usando Teoria de Resposta ao Item (TRI) - erro típico &lt; 1 ponto para provas calibradas
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Citação Carl Sagan
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; font-style: italic; color: #666; padding: 1rem; max-width: 800px; margin: 0 auto;">
        <p style="font-size: 0.9rem; line-height: 1.6;">
            "Nós organizamos uma sociedade baseada em ciência e tecnologia, na qual ninguém entende nada de ciência e tecnologia. 
            E essa mistura inflamável de ignorância e poder, mais cedo ou mais tarde, vai explodir na nossa cara. 
            Quem está no comando da ciência e tecnologia em uma democracia se as pessoas não sabem nada sobre isso?"
        </p>
        <p style="font-size: 0.85rem; margin-top: 0.5rem;">
            — <strong>Carl Sagan</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
