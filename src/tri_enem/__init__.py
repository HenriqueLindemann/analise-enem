# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
TRI ENEM - Módulo de Cálculo de Notas por Teoria de Resposta ao Item

Interface simplificada (recomendada):
    from tri_enem import SimuladorNota
    
    sim = SimuladorNota()
    
    # Calcular nota (sempre 45 respostas, qualquer ano)
    resultado = sim.calcular('MT', 2023, 'ABCDEABCDE...')  # 45 chars
    print(f"Nota: {resultado.nota:.1f}")
    
    # Para LC, especificar língua
    resultado = sim.calcular('LC', 2023, respostas, lingua='inglês')

Interface avançada:
    from tri_enem import CalculadorTRI, Calibrador
    
    calc = CalculadorTRI("microdados_limpos")
    nota = calc.calcular_nota(2023, 'MT', 1211, respostas)
"""

from .simulador import SimuladorNota, ResultadoNota
from .calculador import CalculadorTRI, ItemTRI
from .calibrador import Calibrador
from .coeficientes import obter_coeficiente, COEF_POR_PROVA, COEF_POR_AREA, COEF_PADRAO
from .tradutor import obter_config_lc, filtrar_itens_lc, ConfiguracaoLC
from .mapeador_provas import MapeadorProvas, InfoProva
from .precisao import verificar_precisao_prova

__all__ = [
    # Interface simplificada (recomendada)
    'SimuladorNota',
    'ResultadoNota',
    # Interface avançada
    'CalculadorTRI',
    'ItemTRI',
    'Calibrador',
    # Coeficientes
    'obter_coeficiente',
    'COEF_POR_PROVA',
    'COEF_POR_AREA',
    'COEF_PADRAO',
    # Tradutor LC
    'obter_config_lc',
    'filtrar_itens_lc',
    'ConfiguracaoLC',
    # Mapeador de códigos
    'MapeadorProvas',
    'InfoProva',
    # Verificação de precisão
    'verificar_precisao_prova',
]
__version__ = '3.0.0'

