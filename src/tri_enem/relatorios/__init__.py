"""
Módulo de Relatórios TRI ENEM

Sistema modular para geração de relatórios em diferentes formatos.

Estrutura:
    - gerador.py: Gerador principal do PDF
    - estilos.py: Cores e estilos de texto
    - graficos.py: Visualizações (barras, grade, impacto)
    - tabelas.py: Tabelas de erros e resumos
    - utils.py: Utilitários (verificação de precisão)
    - base.py: Classes de dados

Uso básico:
    from tri_enem.relatorios import RelatorioPDF, DadosRelatorio
    
    dados = DadosRelatorio(titulo="Meu Simulado", ano_prova=2024)
    # ... adicionar áreas
    
    relatorio = RelatorioPDF()
    relatorio.gerar(dados, './relatorios/resultado.pdf')
"""

from .gerador import RelatorioPDF
from .base import RelatorioBase, DadosRelatorio, AreaAnalise, QuestaoAnalise
from .utils import verificar_precisao_prova

__all__ = [
    'RelatorioPDF',
    'RelatorioBase',
    'DadosRelatorio',
    'AreaAnalise',
    'QuestaoAnalise',
    'verificar_precisao_prova',
]
