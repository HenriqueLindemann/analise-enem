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
        dict com 'mae', 'r_squared', 'confiavel', 'aviso', 'status'
    """
    # Caminhos dos arquivos
    base_path = Path(__file__).parent.parent
    data_file = base_path / 'coeficientes_data.json'
    problematicas_file = base_path / 'provas_problematicas.json'
    
    # DEBUG
    print(f"[DEBUG verificar_precisao] Verificando {ano} {area} {co_prova}")
    print(f"[DEBUG verificar_precisao] Base path: {base_path}")
    print(f"[DEBUG verificar_precisao] Arquivo problematicas existe: {problematicas_file.exists()}")
    
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
            
            print(f"[DEBUG verificar_precisao] Total provas problematicas: {len(problematicas)}")
            
            for p in problematicas:
                if p['ano'] == ano and p['area'] == area and p['prova'] == co_prova:
                    print(f"[DEBUG verificar_precisao] ENCONTRADA! MAE={p['mae']}")
                    resultado['mae'] = p['mae']
                    resultado['r_squared'] = p['r_squared']
                    resultado['confiavel'] = False
                    resultado['aviso'] = f"⚠️ ATENÇÃO: Erro muito alto (MAE={p['mae']:.1f} pts) - resultado pode não ser confiável"
                    resultado['status'] = 'erro_alto'
                    return resultado
        except Exception as e:
            print(f"[DEBUG verificar_precisao] Erro ao ler problematicas: {e}")
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
                resultado['aviso'] = status_info.get('mensagem')
                
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
                        resultado['aviso'] = f"⚠️ Precisão reduzida (erro ~{resultado['mae']:.1f} pts)"
                        resultado['status'] = 'aviso_forte'
                    else:
                        resultado['status'] = 'ok'
            elif resultado['status'] == 'desconhecido':
                resultado['confiavel'] = False
                resultado['aviso'] = "⚠️ Prova não calibrada - usando coeficientes genéricos"
                resultado['status'] = 'nao_calibrado'
                
        except Exception:
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
