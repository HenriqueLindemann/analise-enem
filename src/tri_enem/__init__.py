# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Calculadora Nota TRI ENEM - Módulo de Cálculo por Teoria de Resposta ao Item

Interface simplificada (recomendada):
    from tri_enem import SimuladorNota
    
    sim = SimuladorNota()
    
    # Calcular nota (sempre 45 respostas, qualquer ano)
    resultado = sim.calcular(
        'MT', 2023, respostas, co_prova=1211
    )
    print(f"Nota: {resultado.nota:.1f}")
    
    # Para LC, especificar língua
    resultado = sim.calcular(
        'LC', 2023, respostas, lingua='inglês', co_prova=1201
    )

Interface avançada:
    from tri_enem import CalculadorTRI
    
    calc = CalculadorTRI()
    nota = calc.calcular_nota(2023, 'MT', 1211, respostas)
"""

from .simulador import SimuladorNota, ResultadoNota, ResultadoErro
from .calculador import CalculadorTRI, ItemTRI
from .coeficientes import (
    aplicar_transformacao,
    obter_transformacao,
)
from .tradutor import obter_config_lc, filtrar_itens_lc, ConfiguracaoLC
from .mapeador_provas import MapeadorProvas, InfoProva
from .precisao import formatar_aviso_curto, formatar_resumo_validacao, verificar_precisao_prova
from .posicoes import normalizar_posicoes_resultados, posicao_caderno

__all__ = [
    # Interface simplificada (recomendada)
    'SimuladorNota',
    'ResultadoNota',
    'ResultadoErro',
    # Interface avançada
    'CalculadorTRI',
    'ItemTRI',
    # Transformações de escala
    'obter_transformacao',
    'aplicar_transformacao',
    # Tradutor LC
    'obter_config_lc',
    'filtrar_itens_lc',
    'ConfiguracaoLC',
    # Mapeador de códigos
    'MapeadorProvas',
    'InfoProva',
    # Verificação de precisão
    'verificar_precisao_prova',
    'formatar_resumo_validacao',
    'formatar_aviso_curto',
    # Numeração de questões para exibição
    'normalizar_posicoes_resultados',
    'posicao_caderno',
]
__version__ = '5.0.0'
