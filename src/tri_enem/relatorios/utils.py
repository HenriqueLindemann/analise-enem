# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Utilitários para o relatório PDF.

Funções auxiliares: verificação de precisão, formatação, etc.
"""

import json
from pathlib import Path
from typing import Dict


def verificar_precisao_prova(ano: int, area: str, co_prova: int) -> Dict:
    """
    Verifica a precisão estimada de uma prova.
    
    Retorna:
        dict com 'mae', 'r_squared', 'confiavel', 'aviso'
    """
    # Caminhos dos arquivos
    base_path = Path(__file__).parent.parent
    data_file = base_path / 'coeficientes_data.json'
    problematicas_file = base_path / 'provas_problematicas.json'
    
    resultado = {
        'mae': None,
        'r_squared': None,
        'confiavel': True,
        'aviso': None
    }
    
    # Verificar provas problemáticas primeiro
    if problematicas_file.exists():
        try:
            with open(problematicas_file, 'r') as f:
                problematicas = json.load(f)
            
            for p in problematicas:
                if p['ano'] == ano and p['area'] == area and p['prova'] == co_prova:
                    resultado['mae'] = p['mae']
                    resultado['r_squared'] = p['r_squared']
                    resultado['confiavel'] = False
                    resultado['aviso'] = f"⚠️ Prova com erro alto (MAE={p['mae']:.1f} pts)"
                    return resultado
        except:
            pass
    
    # Verificar coeficientes normais
    if data_file.exists():
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            key = f"{ano},{area},{co_prova}"
            if key in data.get('por_prova', {}):
                info = data['por_prova'][key]
                resultado['mae'] = info.get('mae')
                resultado['r_squared'] = info.get('r_squared')
                
                # Considerar não confiável se MAE > 2 pontos
                if resultado['mae'] and resultado['mae'] > 2:
                    resultado['confiavel'] = False
                    resultado['aviso'] = f"⚠️ Precisão reduzida (erro ~{resultado['mae']:.1f} pts)"
            else:
                resultado['confiavel'] = False
                resultado['aviso'] = "⚠️ Prova não calibrada - usando coeficientes genéricos"
        except:
            pass
    
    return resultado


def formatar_dificuldade(param_b: float) -> str:
    """Formata o parâmetro b de dificuldade."""
    if param_b < -1:
        return f"{param_b:+.1f} (muito fácil)"
    elif param_b < 0:
        return f"{param_b:+.1f} (fácil)"
    elif param_b < 1:
        return f"{param_b:+.1f} (média)"
    elif param_b < 2:
        return f"{param_b:+.1f} (difícil)"
    else:
        return f"{param_b:+.1f} (muito difícil)"
