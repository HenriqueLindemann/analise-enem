#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibração completa usando mapeamento de provas YAML.

Calibra todas as provas mapeadas e salva:
- Coeficientes por prova em coeficientes_data.json
- Status de calibração (OK, erro alto, falhou) no mesmo arquivo

Execute a partir da raiz do projeto:
    python tools/calibrar_com_mapeamento.py [ano]

Exemplos:
    python tools/calibrar_com_mapeamento.py        # Calibra todos os anos
    python tools/calibrar_com_mapeamento.py 2023   # Calibra só 2023
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import Calibrador, MapeadorProvas


# Limiares de qualidade
LIMIAR_MAE_BOM = 2.0       # MAE <= 2.0: prova OK
LIMIAR_MAE_ACEITAVEL = 5.0  # MAE <= 5.0: aviso leve
LIMIAR_MAE_RUIM = 15.0      # MAE <= 15.0: aviso forte
LIMIAR_R2_MINIMO = 0.90     # R² mínimo aceitável


@dataclass
class StatusCalibracao:
    """Status da calibração de uma prova."""
    codigo: int
    ano: int
    area: str
    tipo_aplicacao: str
    cor: str
    
    # Resultados da calibração
    calibrado: bool = False
    slope: Optional[float] = None
    intercept: Optional[float] = None
    r_squared: Optional[float] = None
    mae: Optional[float] = None
    n_amostras: Optional[int] = None
    
    # Status de qualidade
    status: str = 'nao_calibrado'  # ok, aviso_leve, aviso_forte, erro_alto, falhou, nao_calibrado
    mensagem_aviso: Optional[str] = None
    
    def classificar_qualidade(self):
        """Classifica a qualidade da calibração baseado em MAE e R²."""
        if not self.calibrado or self.mae is None:
            self.status = 'nao_calibrado'
            self.mensagem_aviso = '⚠️ Esta prova não possui calibração específica. Estamos usando parâmetros genéricos da área, o que pode resultar em uma nota menos precisa. Use o resultado como estimativa.'
            return
        
        r2 = self.r_squared or 0
        
        if self.mae <= LIMIAR_MAE_BOM and r2 >= 0.99:
            self.status = 'ok'
            self.mensagem_aviso = None
        elif self.mae <= LIMIAR_MAE_ACEITAVEL and r2 >= 0.95:
            self.status = 'aviso_leve'
            self.mensagem_aviso = f'ℹ️ Esta prova tem boa calibração, mas pode haver uma pequena diferença de até {self.mae:.1f} pontos em relação à nota oficial.'
        elif self.mae <= LIMIAR_MAE_RUIM and r2 >= LIMIAR_R2_MINIMO:
            self.status = 'aviso_forte'
            self.mensagem_aviso = f'⚠️ Atenção: Esta prova tem calibração parcial. O erro médio é de aproximadamente {self.mae:.1f} pontos. Sua nota calculada é uma estimativa e pode diferir da nota oficial.'
        else:
            self.status = 'erro_alto'
            self.mensagem_aviso = f'⚠️ ATENÇÃO: Esta prova não está calibrada corretamente. O erro médio é de {self.mae:.1f} pontos, o que significa que a nota calculada pode variar bastante da nota oficial. Use apenas como estimativa aproximada.'


def carregar_dados_existentes(caminho: Path) -> Dict:
    """Carrega dados de calibração existentes."""
    dados_padrao = {
        'por_prova': {},
        'por_area': {},
        'status_provas': {},
        'metadata': {
            'ultima_calibracao': None,
            'versao': '2.0'
        }
    }
    
    if caminho.exists():
        with open(caminho, 'r', encoding='utf-8') as f:
            dados_existentes = json.load(f)
        
        # Mesclar com estrutura padrão (para garantir todas as chaves)
        for chave in dados_padrao:
            if chave not in dados_existentes:
                dados_existentes[chave] = dados_padrao[chave]
        
        return dados_existentes
    
    return dados_padrao


def salvar_dados(dados: Dict, caminho: Path):
    """Salva dados de calibração."""
    dados['metadata']['ultima_calibracao'] = datetime.now().isoformat()
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def calibrar_prova_completa(cal: Calibrador, prova, n_amostras: int = 200, verbose: bool = True) -> StatusCalibracao:
    """
    Calibra uma prova e retorna status completo.
    
    Args:
        cal: Calibrador configurado
        prova: InfoProva do mapeador
        n_amostras: Número de amostras por prova
        verbose: Se True, imprime progresso
    
    Returns:
        StatusCalibracao com resultados
    """
    status = StatusCalibracao(
        codigo=prova.codigo,
        ano=prova.ano,
        area=prova.area,
        tipo_aplicacao=prova.tipo_aplicacao,
        cor=prova.cor
    )
    
    if verbose:
        print(f"  {prova.area} {prova.tipo_aplicacao} {prova.cor} ({prova.codigo}): ", end='', flush=True)
    
    try:
        resultado = cal.calibrar_prova(
            prova.ano, prova.area, prova.codigo,
            n_amostras=n_amostras, verbose=False
        )
        
        if 'erro' in resultado:
            status.status = 'falhou'
            status.mensagem_aviso = f"Falha: {resultado['erro']}"
            if verbose:
                print(f"❌ {resultado['erro']}")
            return status
        
        # Preencher resultados
        status.calibrado = True
        status.slope = resultado['slope']
        status.intercept = resultado['intercept']
        status.r_squared = resultado['r_squared']
        status.mae = resultado['mae']
        status.n_amostras = resultado['n_amostras']
        
        # Classificar qualidade
        status.classificar_qualidade()
        
        if verbose:
            emoji = {'ok': '✅', 'aviso_leve': '⚠️', 'aviso_forte': '⚠️', 'erro_alto': '❌'}
            print(f"{emoji.get(status.status, '❓')} MAE={status.mae:.2f} R²={status.r_squared:.4f}")
        
        return status
        
    except Exception as e:
        status.status = 'falhou'
        status.mensagem_aviso = f"Erro: {str(e)}"
        if verbose:
            print(f"❌ Erro: {e}")
        return status


def calibrar_ano(mapeador: MapeadorProvas, cal: Calibrador, ano: int, 
                 dados: Dict, n_amostras: int = 200, verbose: bool = True) -> Dict[str, List[StatusCalibracao]]:
    """
    Calibra todas as provas de um ano.
    
    Returns:
        Dicionário {area: [StatusCalibracao]}
    """
    provas = mapeador.listar_todas_provas(ano)
    
    if not provas:
        print(f"  Nenhuma prova encontrada para {ano}")
        return {}
    
    resultados = {}
    
    # Agrupar por área
    for area in ['LC', 'CH', 'CN', 'MT']:
        provas_area = [p for p in provas if p.area == area]
        
        if not provas_area:
            continue
        
        if verbose:
            print(f"\n  {area} ({len(provas_area)} provas)")
            print(f"  {'-' * 50}")
        
        resultados[area] = []
        slopes_area = []
        intercepts_area = []
        
        for prova in provas_area:
            status = calibrar_prova_completa(cal, prova, n_amostras, verbose)
            resultados[area].append(status)
            
            # Salvar no dicionário de dados
            key = f"{prova.ano},{prova.area},{prova.codigo}"
            
            if status.calibrado and status.status != 'erro_alto':
                dados['por_prova'][key] = {
                    'slope': status.slope,
                    'intercept': status.intercept,
                    'r_squared': status.r_squared,
                    'mae': status.mae,
                    'n_amostras': status.n_amostras
                }
                slopes_area.append(status.slope)
                intercepts_area.append(status.intercept)
            
            # Salvar status da prova
            dados['status_provas'][key] = {
                'status': status.status,
                'mensagem': status.mensagem_aviso,
                'tipo_aplicacao': status.tipo_aplicacao,
                'cor': status.cor
            }
        
        # Média da área
        if slopes_area:
            import numpy as np
            key_area = f"{ano},{area}"
            dados['por_area'][key_area] = {
                'slope': float(np.mean(slopes_area)),
                'intercept': float(np.mean(intercepts_area)),
                'n_provas': len(slopes_area)
            }
    
    return resultados


def gerar_resumo(resultados_todos: Dict[int, Dict[str, List[StatusCalibracao]]]) -> str:
    """Gera resumo da calibração."""
    linhas = ["\n" + "=" * 70, "RESUMO DA CALIBRAÇÃO", "=" * 70]
    
    total_ok = 0
    total_aviso = 0
    total_erro = 0
    total_falhou = 0
    
    for ano, resultados in sorted(resultados_todos.items()):
        linhas.append(f"\n{ano}:")
        
        for area, lista in resultados.items():
            ok = sum(1 for s in lista if s.status == 'ok')
            aviso = sum(1 for s in lista if s.status in ('aviso_leve', 'aviso_forte'))
            erro = sum(1 for s in lista if s.status == 'erro_alto')
            falhou = sum(1 for s in lista if s.status in ('falhou', 'nao_calibrado'))
            
            total_ok += ok
            total_aviso += aviso
            total_erro += erro
            total_falhou += falhou
            
            linhas.append(f"  {area}: ✅{ok} ⚠️{aviso} ❌{erro} ❓{falhou}")
    
    linhas.append(f"\n{'=' * 70}")
    linhas.append(f"TOTAL: ✅ {total_ok} OK | ⚠️ {total_aviso} avisos | ❌ {total_erro} erro alto | ❓ {total_falhou} falhou")
    
    return "\n".join(linhas)


def main():
    """Função principal."""
    print("=" * 70)
    print("CALIBRAÇÃO COM MAPEAMENTO YAML")
    print("=" * 70)
    
    # Parsear argumentos
    ano_especifico = None
    if len(sys.argv) > 1:
        try:
            ano_especifico = int(sys.argv[1])
            print(f"Calibrando apenas ano: {ano_especifico}")
        except ValueError:
            print(f"Argumento inválido: {sys.argv[1]}")
            return
    
    # Inicializar
    mapeador = MapeadorProvas()
    cal = Calibrador("microdados_limpos")
    
    # Caminho dos dados
    caminho_dados = Path('src/tri_enem/coeficientes_data.json')
    dados = carregar_dados_existentes(caminho_dados)
    
    # Definir anos a calibrar
    if ano_especifico:
        anos = [ano_especifico]
    else:
        anos = mapeador.listar_anos_disponiveis()
    
    print(f"\nAnos a calibrar: {anos}")
    print(f"Coeficientes existentes: {len(dados['por_prova'])}")
    
    resultados_todos = {}
    
    for ano in anos:
        print(f"\n{'=' * 70}")
        print(f"ANO {ano}")
        print("=" * 70)
        
        try:
            resultados = calibrar_ano(mapeador, cal, ano, dados, n_amostras=200)
            resultados_todos[ano] = resultados
            
            # Salvar progresso
            salvar_dados(dados, caminho_dados)
            print(f"\n  💾 Dados salvos ({len(dados['por_prova'])} provas)")
            
        except Exception as e:
            print(f"\n  ❌ Erro ao calibrar {ano}: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumo final
    print(gerar_resumo(resultados_todos))
    
    print(f"\n{'=' * 70}")
    print("CALIBRAÇÃO COMPLETA!")
    print(f"{'=' * 70}")
    print(f"Arquivo salvo: {caminho_dados}")
    print(f"  Por prova: {len(dados['por_prova'])}")
    print(f"  Por área: {len(dados['por_area'])}")
    print(f"  Status: {len(dados['status_provas'])}")


if __name__ == '__main__':
    main()
