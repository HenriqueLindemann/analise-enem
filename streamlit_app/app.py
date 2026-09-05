#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Calculadora Nota TRI ENEM - Interface Web

Interface web para cálculo de nota TRI do ENEM.
Desenvolvido por Henrique Lindemann - Eng. Computação UFRGS
Site: https://notatri.com

Execute com: streamlit run streamlit_app/app.py

Estrutura modular:
- config.py: Configurações centralizadas (SEO, textos, constantes)
- components/layout.py: Estrutura e configuração da página
- components/seo.py: Meta tags e Schema.org JSON-LD
- components/inputs.py: Entradas de dados
- components/resultados.py: Exibição de resultados
- components/graficos.py: Visualizações Plotly
- components/impressao.py: Geração de PDF
"""

import streamlit as st
import sys
from pathlib import Path

# ============================================================================
#                         CONFIGURAR PATHS
# ============================================================================

_app_dir = Path(__file__).parent
_root_dir = _app_dir.parent
sys.path.insert(0, str(_root_dir / 'src'))
sys.path.insert(0, str(_root_dir))

# ============================================================================
#                         IMPORTS LOCAIS
# ============================================================================

from streamlit_app.config import (
    SEO,
    AREAS_ENEM,
)
from tri_enem import MapeadorProvas, normalizar_posicoes_resultados
from tri_enem.formatacao import formatar_numero
from streamlit_app.calculador import get_calculador
from streamlit_app.components.inputs import input_respostas, validar_todas_respostas
from streamlit_app.components.resultados import exibir_resumo_geral, exibir_resultado_area
from streamlit_app.components.impressao import exibir_download_pdf
from streamlit_app.components.layout import (
    configurar_pagina,
    carregar_css,
    render_header,
    render_instrucoes,
    render_config,
    render_botao_calcular,
    render_footer,
)
from streamlit_app.components.seo import (
    gerar_meta_tags,
    gerar_schema_json_ld,
    gerar_noscript_seo,
)

# ============================================================================
#                         CONFIGURAÇÃO INICIAL
# ============================================================================

# IMPORTANTE: set_page_config deve ser a primeira chamada Streamlit
configurar_pagina()

# Carregar estilos CSS
carregar_css()

# ============================================================================
#                         SEO - META TAGS E SCHEMA.ORG
# ============================================================================

def injetar_seo():
    """Injeta meta tags, Schema.org JSON-LD e noscript para SEO."""
    from streamlit_app.config import (
        APP_AUTHOR,
        APP_AUTHOR_URL,
        APP_GITHUB_URL,
        APP_CANONICAL_URL,
    )
    
    # Meta tags HTML
    meta_html = gerar_meta_tags(
        title=SEO.page_title,
        description=SEO.meta_description,
        keywords=SEO.meta_keywords,
        canonical_url=APP_CANONICAL_URL,
        author=APP_AUTHOR,
        og_title=SEO.og_title,
        og_description=SEO.og_description,
        og_type=SEO.og_type,
        og_image=SEO.og_image,
        twitter_card=SEO.twitter_card,
        twitter_title=SEO.twitter_title,
        twitter_description=SEO.twitter_description,
    )
    
    # Schema.org JSON-LD para rich snippets no Google
    schema_html = gerar_schema_json_ld(
        name="Calculadora Nota TRI ENEM",
        description=SEO.meta_description,
        url=APP_CANONICAL_URL,
        author_name=APP_AUTHOR,
        author_url=APP_AUTHOR_URL,
        github_url=APP_GITHUB_URL,
    )
    
    # Conteúdo noscript para crawlers básicos
    noscript_html = gerar_noscript_seo()
    
    # Injetar tudo
    st.markdown(meta_html + schema_html + noscript_html, unsafe_allow_html=True)


# Injetar SEO
injetar_seo()

# ============================================================================
#                            PÁGINA PRINCIPAL
# ============================================================================

def main():
    """Função principal do app - orquestra os componentes."""
    
    # Header com título e descrição (SEO-friendly)
    render_header()
    
    # Instruções de uso
    render_instrucoes()
    
    # Configurações da prova na página principal
    calc = get_calculador()
    ano, tipo_aplicacao, lingua = render_config(calc.mapeador)
    
    # Área principal: inputs de respostas
    respostas, cores = input_respostas(ano, calc.mapeador, tipo_aplicacao)
    
    # Validação das respostas
    todas_validas, _ = validar_todas_respostas(respostas)
    
    tem_respostas = any(r and r != "." * 45 and cores.get(area)
                        for area, r in respostas.items())
    pode_calcular = bool(tem_respostas and todas_validas)
    if not pode_calcular:
        st.caption("Complete 45 respostas em pelo menos uma área disponível. "
                   "Complete ou limpe as demais áreas preenchidas para calcular.")
    calcular = render_botao_calcular(pode_calcular)

    # Reservar a posição evita remontar os expanders após o cálculo.
    status_calculo = st.empty()
    # Processar cálculo
    if calcular and pode_calcular:
        with status_calculo.container():
            _processar_calculo(calc, ano, tipo_aplicacao, lingua, cores, respostas)
    elif calcular and not tem_respostas:
        st.warning("Preencha pelo menos uma área para calcular.")
    
    # Exibir resultados salvos (persiste após reruns)
    _exibir_resultados_salvos(
        ano,
        tipo_aplicacao,
        lingua,
        cores,
        respostas,
    )
    
    # Footer
    render_footer()


def _assinatura_resultado(ano, tipo_aplicacao, lingua, cores, respostas):
    """Identifica a configuração e as respostas usadas em um resultado."""
    areas = ('LC', 'CH', 'CN', 'MT')
    return (
        int(ano),
        str(tipo_aplicacao),
        str(lingua),
        tuple((area, cores.get(area) or '') for area in areas),
        tuple((area, respostas.get(area, '') or '') for area in areas),
    )


def _limpar_resultados_salvos():
    """Remove resultado e PDF quando a configuração deixa de corresponder."""
    for chave in (
        'resultados',
        'resultado_ano',
        'resultado_tipo',
        'resultado_assinatura',
        'pdf_bytes',
        'pdf_chave',
        'pdf_ano',
    ):
        st.session_state.pop(chave, None)


def _processar_calculo(calc, ano, tipo_aplicacao, lingua, cores, respostas):
    """Processa o cálculo das notas com progress bar."""
    _limpar_resultados_salvos()
    progress_bar = st.progress(0, text="Iniciando cálculo...")
    
    try:
        progress_bar.progress(20, text="Carregando parâmetros TRI...")
        
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
            ordem_provas = _obter_ordem_provas(calc, ano)
            resultados_ordenados = _ordenar_resultados_por_prova(resultados, ordem_provas)
            st.session_state['resultados'] = resultados_ordenados
            st.session_state['resultado_ano'] = ano
            st.session_state['resultado_tipo'] = tipo_aplicacao
            st.session_state['resultado_assinatura'] = _assinatura_resultado(
                ano, tipo_aplicacao, lingua, cores, respostas
            )
            # Limpar PDF antigo para gerar novo
            for chave in ('pdf_bytes', 'pdf_chave', 'pdf_ano'):
                st.session_state.pop(chave, None)
        
        # Mostrar erros de cálculo
        for erro in erros_calculo:
            st.warning(erro)
        
        if not resultados:
            st.error("Não foi possível calcular nenhuma nota. Verifique as configurações e respostas.")
            
    except Exception as e:
        progress_bar.empty()
        st.error(f"Erro ao calcular: {e}")


def _exibir_resultados_salvos(
    ano_atual,
    tipo_atual,
    lingua_atual,
    cores_atuais,
    respostas_atuais,
):
    """Exibe resultados salvos na sessão."""
    if 'resultados' not in st.session_state or not st.session_state['resultados']:
        return

    assinatura_atual = _assinatura_resultado(
        ano_atual,
        tipo_atual,
        lingua_atual,
        cores_atuais,
        respostas_atuais,
    )
    if st.session_state.get('resultado_assinatura') != assinatura_atual:
        _limpar_resultados_salvos()
        return
    
    ano_resultado = st.session_state.get('resultado_ano', ano_atual)
    tipo_resultado = st.session_state.get('resultado_tipo', tipo_atual)
    resultados = normalizar_posicoes_resultados(
        st.session_state['resultados'],
        MapeadorProvas().listar_ordem_provas(ano_resultado),
    )
    
    st.markdown("---")
    
    # Resumo geral com métricas
    exibir_resumo_geral(resultados)
    exibir_download_pdf(resultados, ano_resultado, tipo_resultado)
    
    st.markdown("---")
    
    # Seção de análise detalhada (H2 para SEO)
    st.markdown("## Análise Detalhada por Área")
    st.caption("Clique em uma área para ver a análise completa")
    
    # Detalhes por área em expanders
    for resultado in resultados:
        sigla = resultado['sigla']
        nome = AREAS_ENEM.get(sigla, sigla)
        nota = resultado['nota']
        acertos = resultado['acertos']
        total = resultado['total_itens']
        questoes_anuladas = resultado.get('questoes_anuladas') or [
            q['posicao'] for q in resultado.get('anuladas', [])
        ]
        anuladas_txt = ""
        if questoes_anuladas:
            q_list = ", ".join(f"Q{q}" for q in sorted(questoes_anuladas))
            anuladas_txt = f" · {q_list} anulada" if len(questoes_anuladas) == 1 else f" · {q_list} anuladas"
        
        nota_texto = formatar_numero(nota)
        with st.expander(f"**{nome}** — {nota_texto} pts ({acertos}/{total} acertos{anuladas_txt})", expanded=False):
            exibir_resultado_area(resultado)
    


def _obter_ordem_provas(calc, ano):
    """Obtém a ordem das provas via mapeador (com fallback)."""
    try:
        return calc.mapeador.listar_ordem_provas(ano)
    except Exception:
        return ['LC', 'CH', 'CN', 'MT']


def _ordenar_resultados_por_prova(resultados, ordem_provas):
    """Ordena resultados conforme a ordem das provas."""
    index_map = {sigla: idx for idx, sigla in enumerate(ordem_provas)}
    return sorted(
        resultados,
        key=lambda r: index_map.get(r.get('sigla'), 99)
    )


# ============================================================================
#                         EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    with st.container(key="app_content"):
        main()
