# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Módulo de Relatórios TRI ENEM

Sistema modular para geração de relatórios em diferentes formatos.

Estrutura:
    - gerador.py: Gerador principal do PDF
    - estilos.py: Cores e estilos de texto
    - graficos.py: Visualizações (barras, grade, impacto)
    - tabelas.py: Tabelas de erros e resumos
    - utils.py: Formatação da dificuldade dos itens
    - base.py: Classes de dados
    - adaptador.py: Conversão única de resultados para relatórios

Uso básico:
    from tri_enem.relatorios import RelatorioPDF, DadosRelatorio
    
    dados = DadosRelatorio(titulo="Meu Simulado", ano_prova=2024)
    # ... adicionar áreas
    
    relatorio = RelatorioPDF()
    relatorio.gerar(dados, './relatorios/resultado.pdf')
"""

from .base import RelatorioBase, DadosRelatorio, AreaAnalise, QuestaoAnalise
from .adaptador import adaptar_resultados_para_relatorio

try:
    from .gerador import RelatorioPDF
except ImportError:
    # Permite usar as estruturas e o adaptador sem a dependência opcional de PDF.
    pass

__all__ = [
    'RelatorioBase',
    'DadosRelatorio',
    'AreaAnalise',
    'QuestaoAnalise',
    'adaptar_resultados_para_relatorio',
]

if 'RelatorioPDF' in globals():
    __all__.insert(0, 'RelatorioPDF')
