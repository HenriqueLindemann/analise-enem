# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes do Streamlit App.

Módulos disponíveis:
- inputs: Componentes de entrada de dados (respostas, configurações)
- resultados: Exibição de resultados e análises
- graficos: Visualizações Plotly
- impressao: Geração de relatório PDF
- layout: Estrutura e configuração da página
- seo: Otimização para mecanismos de busca
"""

from .inputs import input_respostas, input_configuracoes, validar_todas_respostas
from .resultados import exibir_resumo_geral, exibir_resultado_area
from .impressao import exibir_download_pdf
from .graficos import (
    grafico_notas_barras,
    grafico_impacto,
    grade_questoes,
    grafico_pizza_acertos,
)

__all__ = [
    # Inputs
    'input_respostas',
    'input_configuracoes',
    'validar_todas_respostas',
    # Resultados
    'exibir_resumo_geral',
    'exibir_resultado_area',
    # Impressão
    'exibir_download_pdf',
    # Gráficos
    'grafico_notas_barras',
    'grafico_impacto',
    'grade_questoes',
    'grafico_pizza_acertos',
]
