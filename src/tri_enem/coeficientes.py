"""
Coeficientes de Equalização TRI do ENEM

Os coeficientes são carregados automaticamente de coeficientes_data.json
Este arquivo é gerado pela calibração e pode ser atualizado facilmente.

Fórmula: nota = slope * θ + intercept
"""

import json
from pathlib import Path
from typing import Tuple

# Carregar dados de calibração
_data_file = Path(__file__).parent / 'coeficientes_data.json'

if _data_file.exists():
    with open(_data_file, 'r', encoding='utf-8') as f:
        _data = json.load(f)
    
    # Converter chaves de string para tuplas
    COEF_POR_PROVA = {}
    for key_str, value in _data.get('por_prova', {}).items():
        ano, area, prova = key_str.split(',')
        COEF_POR_PROVA[(int(ano), area, int(prova))] = (value['slope'], value['intercept'])
    
    COEF_POR_AREA = {}
    for key_str, value in _data.get('por_area', {}).items():
        ano, area = key_str.split(',')
        COEF_POR_AREA[(int(ano), area)] = (value['slope'], value['intercept'])
    
    # Padrões por área
    COEF_PADRAO = {}
    for area, meta in _data.get('metadata', {}).items():
        COEF_PADRAO[area] = (meta['slope_medio'], meta['intercept_medio'])
else:
    # Fallback caso o arquivo não exista (usar calibração de 2023)
    print("⚠️ Arquivo coeficientes_data.json não encontrado. Usando coeficientes padrão.")
    
    COEF_POR_PROVA = {
        (2023, 'MT', 1211): (129.6216, 500.03),
        (2023, 'MT', 1212): (129.6774, 500.06),
        (2023, 'MT', 1213): (129.6053, 500.02),
        (2023, 'MT', 1214): (129.6043, 500.03),
        (2023, 'CN', 1221): (113.0801, 501.15),
        (2023, 'CN', 1222): (113.1134, 501.16),
        (2023, 'CN', 1223): (113.1357, 501.17),
        (2023, 'CN', 1224): (113.1860, 501.16),
        (2023, 'CH', 1191): (112.2900, 501.52),
        (2023, 'CH', 1192): (112.4399, 501.49),
        (2023, 'CH', 1193): (112.2257, 501.40),
        (2023, 'CH', 1194): (112.3245, 501.45),
        (2023, 'LC', 1201): (108.0987, 499.99),
        (2023, 'LC', 1202): (108.1044, 500.03),
        (2023, 'LC', 1203): (108.0811, 499.95),
        (2023, 'LC', 1204): (108.0377, 499.96),
    }
    
    COEF_POR_AREA = {
        (2023, 'MT'): (129.63, 500.0),
        (2023, 'CN'): (113.13, 501.16),
        (2023, 'CH'): (112.32, 501.47),
        (2023, 'LC'): (108.08, 500.0),
    }
    
    COEF_PADRAO = {
        'MT': (129.63, 500.0),
        'CN': (113.13, 501.16),
        'CH': (112.32, 501.47),
        'LC': (108.08, 500.0),
    }


def obter_coeficiente(ano: int, area: str, co_prova: int = None) -> Tuple[float, float]:
    """
    Obtém o coeficiente de equalização para uma prova.
    
    Ordem de precedência:
    1. Coeficiente específico para (ano, area, prova)
    2. Coeficiente por área para (ano, area)
    3. Coeficiente padrão da área
    
    Args:
        ano: Ano do ENEM
        area: Área (MT, CN, CH, LC)
        co_prova: Código da prova (opcional)
        
    Returns:
        Tupla (slope, intercept)
    """
    area = area.upper()
    
    # 1. Tentar coeficiente específico por prova
    if co_prova is not None:
        key = (ano, area, co_prova)
        if key in COEF_POR_PROVA:
            return COEF_POR_PROVA[key]
    
    # 2. Tentar coeficiente por área/ano
    key = (ano, area)
    if key in COEF_POR_AREA:
        return COEF_POR_AREA[key]
    
    # 3. Usar padrão da área
    return COEF_PADRAO.get(area, (100.0, 500.0))
