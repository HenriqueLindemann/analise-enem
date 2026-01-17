"""
Simulador de Nota TRI do ENEM

Interface simplificada para calcular notas TRI.
O usuário só precisa fornecer:
- Ano ou código da prova
- 45 respostas (sempre 45, independente do ano)
- Opção de língua estrangeira para LC

Exemplo:
    from tri_enem import SimuladorNota
    
    sim = SimuladorNota()
    
    # Calcular nota de MT
    nota_mt = sim.calcular('MT', 2023, 'ABCDE...' * 9)  # 45 respostas
    
    # Calcular nota de LC (com língua)
    nota_lc = sim.calcular('LC', 2023, 'ABCDE...' * 9, lingua='ingles')
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Union, List
from dataclasses import dataclass

from .calculador import CalculadorTRI, ItemTRI
from .coeficientes import obter_coeficiente
from .tradutor import obter_config_lc, filtrar_itens_lc


@dataclass
class ResultadoNota:
    """Resultado do cálculo de nota."""
    nota: float
    theta: float
    acertos: int
    total_itens: int
    area: str
    ano: int
    co_prova: int
    lingua: Optional[str] = None
    
    def __repr__(self):
        return f"ResultadoNota(nota={self.nota:.1f}, acertos={self.acertos}/{self.total_itens})"


class SimuladorNota:
    """
    Simulador de Nota TRI do ENEM com interface simplificada.
    
    Características:
    - Aceita sempre 45 respostas para qualquer área/ano
    - Trata automaticamente as diferenças de estrutura LC
    - Usa coeficientes calibrados para máxima precisão
    """
    
    def __init__(self, microdados_path: str = None):
        """
        Args:
            microdados_path: Caminho para microdados_limpos (default: auto-detecta)
        """
        self.base_path = Path(microdados_path or "microdados_limpos")
        self._calc = CalculadorTRI(str(self.base_path))
        self._cache_itens_df: Dict[int, pd.DataFrame] = {}
    
    def _carregar_itens_df(self, ano: int) -> pd.DataFrame:
        """Carrega DataFrame de itens com cache."""
        if ano not in self._cache_itens_df:
            path = self.base_path / str(ano) / f"ITENS_PROVA_{ano}.csv"
            self._cache_itens_df[ano] = pd.read_csv(path, sep=';', encoding='latin1')
        return self._cache_itens_df[ano]
    
    def listar_provas(self, ano: int, area: str = None) -> Dict[str, List[int]]:
        """Lista provas disponíveis para um ano."""
        return self._calc.listar_provas(ano, area)
    
    def _descobrir_prova(self, ano: int, area: str) -> int:
        """Descobre o código da prova mais comum para ano/área."""
        provas = self.listar_provas(ano, area)
        if area.upper() in provas:
            return provas[area.upper()][0]  # Primeira prova
        raise ValueError(f"Área {area} não encontrada para {ano}")
    
    def calcular(self, area: str, ano: int, respostas: str,
                 lingua: str = 'ingles', co_prova: int = None) -> ResultadoNota:
        """
        Calcula a nota TRI.
        
        Args:
            area: Área da prova (MT, CN, CH, LC)
            ano: Ano do ENEM (2009-2024)
            respostas: String com 45 respostas (A-E ou .)
            lingua: Para LC: 'ingles' ou 'espanhol'
            co_prova: Código da prova (opcional, usa primeira disponível)
        
        Returns:
            ResultadoNota com nota e detalhes
        """
        area = area.upper()
        
        # Para LC, auto-filtrar de 50 para 45 se necessário
        if area == 'LC':
            from .tradutor import obter_config_lc, filtrar_respostas_lc
            tp_lingua_temp = 0 if lingua.lower() in ['ingles', 'inglês', 'english', '0'] else 1
            config_lc = obter_config_lc(ano)
            respostas = filtrar_respostas_lc(respostas, tp_lingua_temp, config_lc)
        
        # Validar respostas (agora deve ter 45)
        if len(respostas) != 45:
            raise ValueError(f"Respostas deve ter 45 caracteres, tem {len(respostas)}")
        
        # Descobrir prova se não fornecida
        if co_prova is None:
            co_prova = self._descobrir_prova(ano, area)
        
        # Converter lingua para tp_lingua
        tp_lingua = 0 if lingua.lower() in ['ingles', 'inglês', 'english', '0'] else 1
        
        # Carregar itens
        if area == 'LC':
            # Usar tradutor para LC
            df_itens = self._carregar_itens_df(ano)
            config_lc = obter_config_lc(ano)
            df_filtrado = filtrar_itens_lc(df_itens, co_prova, tp_lingua, config_lc)
            
            # Converter para lista de ItemTRI
            itens = self._df_para_itens(df_filtrado)
        else:
            # Outras áreas: usar calculador normal
            itens = self._calc.carregar_itens(ano, area, co_prova, None)
        
        # Converter respostas
        respostas_bin = self._converter_respostas(respostas, itens)
        
        # Calcular theta
        theta = self._calc.estimar_theta_eap(respostas_bin, itens)
        
        # Transformar para escala ENEM
        slope, intercept = obter_coeficiente(ano, area, co_prova)
        nota = slope * theta + intercept
        
        # Contar acertos
        itens_validos = [i for i in itens if not i.abandonado]
        respostas_validas = [r for r, i in zip(respostas_bin, itens) if not i.abandonado]
        
        return ResultadoNota(
            nota=nota,
            theta=theta,
            acertos=sum(respostas_validas),
            total_itens=len(itens_validos),
            area=area,
            ano=ano,
            co_prova=co_prova,
            lingua=lingua if area == 'LC' else None,
        )
    
    def _df_para_itens(self, df: pd.DataFrame) -> List[ItemTRI]:
        """Converte DataFrame para lista de ItemTRI."""
        itens = []
        for _, row in df.iterrows():
            is_abandonado = (
                row.get('IN_ITEM_ABAN') == 1 or
                pd.isna(row['NU_PARAM_A']) or
                pd.isna(row['NU_PARAM_B']) or
                pd.isna(row['NU_PARAM_C']) or
                str(row['TX_GABARITO']).upper() == 'X'
            )
            
            # Handle NaN CO_ITEM gracefully
            co_item = int(row['CO_ITEM']) if pd.notna(row.get('CO_ITEM')) else 0
            
            item = ItemTRI(
                posicao=int(row['CO_POSICAO']),
                gabarito=str(row['TX_GABARITO']),
                param_a=float(row['NU_PARAM_A']) if pd.notna(row['NU_PARAM_A']) else 0.0,
                param_b=float(row['NU_PARAM_B']) if pd.notna(row['NU_PARAM_B']) else 0.0,
                param_c=float(row['NU_PARAM_C']) if pd.notna(row['NU_PARAM_C']) else 0.0,
                co_item=co_item,
                abandonado=is_abandonado,
            )
            itens.append(item)
        
        return sorted(itens, key=lambda x: x.posicao)
    
    def _converter_respostas(self, respostas: str, itens: List[ItemTRI]) -> List[int]:
        """Converte string de 45 respostas em vetor binário."""
        respostas_bin = []
        
        for idx, item in enumerate(itens):
            if idx >= len(respostas):
                respostas_bin.append(0)
                continue
            
            resp = respostas[idx].upper()
            gab = item.gabarito.upper()
            respostas_bin.append(1 if resp == gab else 0)
        
        return respostas_bin
    
    def calcular_todas_areas(self, ano: int, respostas_dict: Dict[str, str],
                             lingua_lc: str = 'ingles') -> Dict[str, ResultadoNota]:
        """
        Calcula nota de todas as áreas de uma vez.
        
        Args:
            ano: Ano do ENEM
            respostas_dict: {'MT': '...', 'CN': '...', 'CH': '...', 'LC': '...'}
            lingua_lc: Língua para LC
        
        Returns:
            Dicionário com ResultadoNota por área
        """
        resultados = {}
        
        for area, respostas in respostas_dict.items():
            try:
                lingua = lingua_lc if area.upper() == 'LC' else 'ingles'
                resultados[area.upper()] = self.calcular(area, ano, respostas, lingua)
            except Exception as e:
                resultados[area.upper()] = {'erro': str(e)}
        
        return resultados
