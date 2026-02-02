# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Verificação de precisão de provas.

Módulo leve para verificar se uma prova tem calibração confiável,
sem dependências de bibliotecas de geração de PDF.
"""

import json
from pathlib import Path
from typing import Dict


def verificar_precisao_prova(ano: int, area: str, co_prova: int) -> Dict:
    """
    Verifica a precisão estimada de uma prova.
    
    Args:
        ano: Ano da prova (2009-2024)
        area: Área (LC, CH, CN, MT)
        co_prova: Código da prova
    
    Returns:
        dict com:
            - 'mae': Mean Absolute Error (erro médio em pontos)
            - 'r_squared': Coeficiente de determinação R²
            - 'confiavel': True se a prova é confiável
            - 'aviso': Mensagem de aviso (ou None)
            - 'status': 'ok', 'aviso_leve', 'aviso_forte', 'erro_alto', 'nao_calibrado'
    """
    # Caminhos dos arquivos
    base_path = Path(__file__).parent
    data_file = base_path / 'coeficientes_data.json'
    problematicas_file = base_path / 'provas_problematicas.json'
    
    resultado = {
        'mae': None,
        'r_squared': None,
        'confiavel': True,
        'aviso': None,
        'status': 'desconhecido'
    }
    
    key = f"{ano},{area},{co_prova}"
    
    # Verificar provas_problematicas.json primeiro (formato antigo - prioridade para erro alto)
    if problematicas_file.exists():
        try:
            with open(problematicas_file, 'r') as f:
                problematicas = json.load(f)
            
            for p in problematicas:
                if p['ano'] == ano and p['area'] == area and p['prova'] == co_prova:
                    resultado['mae'] = p['mae']
                    resultado['r_squared'] = p['r_squared']
                    resultado['confiavel'] = False
                    resultado['aviso'] = f"⚠️ ATENÇÃO: Esta prova teve erros em sua calibração. O erro médio é de {p['mae']:.1f} pontos, o que significa que sua nota calculada pode variar bastante da nota oficial. Use apenas como estimativa aproximada."
                    resultado['status'] = 'erro_alto'
                    return resultado
        except Exception:
            pass
    
    # Verificar coeficientes_data.json (formato novo com status_provas)
    if data_file.exists():
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Verificar status_provas (novo formato)
            if key in data.get('status_provas', {}):
                status_info = data['status_provas'][key]
                resultado['status'] = status_info.get('status', 'desconhecido')
                mensagem_raw = status_info.get('mensagem')
                
                # Transformar mensagens técnicas em mensagens amigáveis
                if mensagem_raw and 'Poucos participantes' in mensagem_raw:
                    resultado['aviso'] = (
                        "⚠️ Esta prova não possui participantes nos microdados públicos do INEP. "
                        "Estamos usando calibração genérica da área, o que pode resultar em uma "
                        "nota menos precisa. Use como estimativa."
                    )
                else:
                    resultado['aviso'] = mensagem_raw
                
                if resultado['status'] in ('erro_alto', 'falhou', 'nao_calibrado'):
                    resultado['confiavel'] = False
                elif resultado['status'] in ('aviso_leve', 'aviso_forte'):
                    resultado['confiavel'] = True  # Ainda usável, mas com aviso
            
            # Pegar MAE e R² dos coeficientes
            if key in data.get('por_prova', {}):
                info = data['por_prova'][key]
                resultado['mae'] = info.get('mae')
                resultado['r_squared'] = info.get('r_squared')
                
                # Fallback: classificar por MAE se não tiver status
                if resultado['status'] == 'desconhecido':
                    if resultado['mae'] and resultado['mae'] > 2:
                        resultado['confiavel'] = False
                        resultado['aviso'] = f"⚠️ Atenção: Esta prova tem calibração parcial. O erro médio é de aproximadamente {resultado['mae']:.1f} pontos. Sua nota calculada é uma estimativa e pode diferir da nota oficial."
                        resultado['status'] = 'aviso_forte'
                    else:
                        resultado['status'] = 'ok'
            elif resultado['status'] == 'desconhecido':
                resultado['confiavel'] = False
                resultado['aviso'] = "⚠️ Esta prova não possui calibração específica. Estamos usando parâmetros genéricos da área, o que pode resultar em uma nota menos precisa. Use o resultado como estimativa."
                resultado['status'] = 'nao_calibrado'
                
        except Exception:
            pass
    
    return resultado
