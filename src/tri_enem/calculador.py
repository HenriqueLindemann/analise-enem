"""
Calculador de Nota TRI do ENEM

Implementa o modelo logístico de 3 parâmetros (ML3) com estimação
bayesiana Expected a Posteriori (EAP) usando quadratura gaussiana.

Este módulo foi desenvolvido via engenharia reversa dos microdados do INEP.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass

from .coeficientes import obter_coeficiente


@dataclass
class ItemTRI:
    """Representa um item da prova com seus parâmetros TRI na escala (0,1)"""
    posicao: int
    gabarito: str
    param_a: float  # Discriminação
    param_b: float  # Dificuldade
    param_c: float  # Acerto casual (probabilidade)
    co_item: int
    abandonado: bool = False
    tp_lingua: Optional[float] = None  # 0=inglês, 1=espanhol, NaN=comum


class CalculadorTRI:
    """
    Calculador de proficiência TRI usando modelo ML3 + EAP.
    
    Conforme documentação INEP:
    - Modelo Logístico de 3 Parâmetros (ML3)
    - Estimação EAP com pontos de quadratura gaussiana
    - Prior: N(0, 1) - Normal padrão
    
    DESCOBERTA via engenharia reversa:
    O INEP NÃO usa exatamente nota = 100*θ + 500
    Cada área tem seu próprio coeficiente de equalização.
    
    LC (Linguagens 2023+): 
    - 50 itens no arquivo (posições 1-45)
    - Posições 1-5: existem versões inglês (TP_LINGUA=0) E espanhol (TP_LINGUA=1)
    - Posições 6-45: questões comuns (TP_LINGUA=NaN)
    - Filtrar pelo TP_LINGUA do participante para obter 45 itens totais
    """
    
    D = 1.0  # Fator de escala
    N_QUADRATURA = 80  # 80 pontos melhora precisão para notas altas
    
    # Coeficientes carregados de coeficientes.py
    # Ver coeficientes.py para adicionar novos coeficientes
    
    def __init__(self, microdados_path: str = None):
        """
        Args:
            microdados_path: Caminho para pasta com arquivos de dados
                            (padrão: microdados_limpos)
        """
        self.base_path = Path(microdados_path or "microdados_limpos")
        self._cache_itens: Dict[str, List[ItemTRI]] = {}
        self._cache_df_itens: Dict[str, pd.DataFrame] = {}
        self._pontos_quad, self._pesos_quad = self._calcular_quadratura()
    
    def _calcular_quadratura(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula pontos e pesos para quadratura Gauss-Hermite sobre N(0,1)"""
        pontos_h, pesos_h = np.polynomial.hermite.hermgauss(self.N_QUADRATURA)
        pontos = pontos_h * np.sqrt(2)
        pesos = pesos_h / np.sqrt(np.pi)
        return pontos, pesos
    
    def _carregar_df_itens(self, ano: int) -> pd.DataFrame:
        """Carrega DataFrame de itens de um ano (com cache)."""
        if ano in self._cache_df_itens:
            return self._cache_df_itens[ano]
        
        itens_path = self.base_path / str(ano) / f"ITENS_PROVA_{ano}.csv"
        
        if not itens_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {itens_path}")
        
        df = pd.read_csv(itens_path, encoding='latin1', sep=';')
        self._cache_df_itens[ano] = df
        return df
    
    def listar_provas(self, ano: int, area: str = None) -> Dict[str, List[int]]:
        """Lista todas as provas disponíveis para um ano."""
        df = self._carregar_df_itens(ano)
        
        if area:
            df = df[df['SG_AREA'] == area.upper()]
            return {area.upper(): sorted(df['CO_PROVA'].unique().tolist())}
        else:
            resultado = {}
            for a in df['SG_AREA'].unique():
                resultado[a] = sorted(df[df['SG_AREA'] == a]['CO_PROVA'].unique().tolist())
            return resultado
    
    def carregar_itens(self, ano: int, area: str, co_prova: int, 
                       tp_lingua: Optional[int] = None) -> List[ItemTRI]:
        """
        Carrega os itens de uma prova específica.
        
        Args:
            ano: Ano do ENEM
            area: Área (CN, CH, LC, MT)
            co_prova: Código da prova
            tp_lingua: Para LC: 0=inglês, 1=espanhol. Filtra questões de idioma.
                       Se None para LC, usa inglês (0) como padrão.
        """
        # Para LC, sempre definir tp_lingua
        if area.upper() == 'LC' and tp_lingua is None:
            tp_lingua = 0
        
        cache_key = f"{ano}_{area}_{co_prova}_{tp_lingua}"
        
        if cache_key in self._cache_itens:
            return self._cache_itens[cache_key]
        
        df = self._carregar_df_itens(ano)
        df_prova = df[(df['SG_AREA'] == area.upper()) & (df['CO_PROVA'] == co_prova)].copy()
        
        if df_prova.empty:
            raise ValueError(f"Prova não encontrada: {ano}/{area}/{co_prova}")
        
        # Para LC: filtrar por tp_lingua
        # - Manter itens com TP_LINGUA == tp_lingua (questões de idioma)
        # - Manter itens com TP_LINGUA == NaN (questões comuns)
        if area.upper() == 'LC' and 'TP_LINGUA' in df_prova.columns:
            df_prova = df_prova[
                (pd.isna(df_prova['TP_LINGUA'])) | 
                (df_prova['TP_LINGUA'] == tp_lingua)
            ].copy()
        
        # Deduplicar itens (preferência por versão impressa = 0)
        # df_prova já está filtrado por CO_PROVA, então a linha `df = df[df['CO_PROVA'] == co_prova]`
        # da instrução é redundante e incorreta aqui.
        if 'TP_VERSAO_DIGITAL' in df_prova.columns:
            df_prova.sort_values(by=['CO_POSICAO', 'TP_VERSAO_DIGITAL'], na_position='first', inplace=True)
            df_prova.drop_duplicates(subset=['CO_POSICAO'], keep='first', inplace=True)
        else:
             if 'CO_POSICAO' in df_prova.columns:
                  df_prova.drop_duplicates(subset=['CO_POSICAO'], keep='first', inplace=True)

        itens = []
        for _, row in df_prova.iterrows():
            # item_id = str(int(row['CO_ITEM'])) if pd.notna(row['CO_ITEM']) else str(len(itens_list)) # This line is from the instruction but not used.
            
            # Verificar se foi anulada
            is_abandonado = (
                row.get('IN_ITEM_ABAN') == 1
            ) or (
                pd.isna(row['NU_PARAM_A']) or 
                pd.isna(row['NU_PARAM_B']) or 
                pd.isna(row['NU_PARAM_C'])
            ) or (
                str(row['TX_GABARITO']).upper() == 'X'
            ) or ( # Added from instruction
                pd.isna(row['TX_GABARITO']) or 
                str(row['TX_GABARITO']) == '.' or 
                str(row['TX_GABARITO']) == '*'
            )
            
            try:
                co_item_val = int(row['CO_ITEM'])
            except (ValueError, TypeError):
                # Se CO_ITEM não puder ser convertido para int, pular este item
                continue
                    
            item = ItemTRI(
                posicao=int(row['CO_POSICAO']),
                gabarito=str(row['TX_GABARITO']),
                param_a=float(row['NU_PARAM_A']) if pd.notna(row['NU_PARAM_A']) else 0.0,
                param_b=float(row['NU_PARAM_B']) if pd.notna(row['NU_PARAM_B']) else 0.0,
                param_c=float(row['NU_PARAM_C']) if pd.notna(row['NU_PARAM_C']) else 0.0,
                co_item=co_item_val,
                abandonado=is_abandonado,
                tp_lingua=row.get('TP_LINGUA'),
            )
            itens.append(item)
        
        itens.sort(key=lambda x: x.posicao)
        self._cache_itens[cache_key] = itens
        return itens
    
    def probabilidade_acerto(self, theta: float, item: ItemTRI) -> float:
        """Calcula P(u=1|θ) usando modelo ML3."""
        a, b, c = item.param_a, item.param_b, item.param_c
        exp_arg = self.D * a * (theta - b)
        
        if exp_arg > 700:
            return 1.0
        elif exp_arg < -700:
            return c
        
        return c + (1 - c) / (1 + np.exp(-exp_arg))
    
    def log_verossimilhanca(self, theta: float, respostas: List[int], 
                           itens: List[ItemTRI]) -> float:
        """Calcula log da verossimilhança L(x|η,θ)."""
        log_L = 0.0
        
        for u, item in zip(respostas, itens):
            if item.abandonado:
                continue
            
            p = self.probabilidade_acerto(theta, item)
            p = np.clip(p, 1e-15, 1 - 1e-15)
            
            log_L += np.log(p) if u == 1 else np.log(1 - p)
        
        return log_L
    
    def estimar_theta_eap(self, respostas: List[int], itens: List[ItemTRI]) -> float:
        """
        Estima θ usando Expected a Posteriori (EAP).
        
        θ_EAP = Σ(X_k * L_k * W_k) / Σ(L_k * W_k)
        """
        log_L = np.array([
            self.log_verossimilhanca(theta_k, respostas, itens) 
            for theta_k in self._pontos_quad
        ])
        
        log_L_max = np.max(log_L)
        L = np.exp(log_L - log_L_max)
        
        numerador = np.sum(self._pontos_quad * L * self._pesos_quad)
        denominador = np.sum(L * self._pesos_quad)
        
        return numerador / denominador if denominador > 0 else 0.0
    
    def converter_respostas(self, respostas_str: str, itens: List[ItemTRI]) -> List[int]:
        """
        Converte string de respostas em vetor binário (1=acerto, 0=erro).
        
        A string TX_RESPOSTAS tem caracteres na ordem dos itens (já ordenados por posição).
        Cada item corresponde a um índice na string baseado em sua ordem na lista.
        
        Nota: CO_POSICAO representa posição global na prova (ex: MT vai de 136-180),
        mas TX_RESPOSTAS_MT tem 45 caracteres indexados de 0-44.
        """
        respostas = []
        
        for idx, item in enumerate(itens):
            if idx >= len(respostas_str):
                respostas.append(0)
                continue
            
            resposta = respostas_str[idx].upper()
            gabarito = item.gabarito.upper()
            respostas.append(1 if resposta == gabarito else 0)
        
        return respostas
    
    def transformar_escala(self, theta: float, ano: int = None, area: str = None,
                          co_prova: int = None) -> float:
        """
        Transforma θ da escala (0,1) para escala ENEM.
        
        Usa coeficientes de equalização do módulo coeficientes.py
        """
        slope, intercept = obter_coeficiente(ano or 2023, area or 'MT', co_prova)
        return slope * theta + intercept
    
    def calcular_nota(self, ano: int, area: str, co_prova: int, 
                     respostas_str: str, tp_lingua: Optional[int] = None) -> Dict:
        """
        Calcula a nota TRI completa.
        
        Args:
            ano: Ano do ENEM
            area: Área (CN, CH, LC, MT)
            co_prova: Código da prova
            respostas_str: String com as respostas
            tp_lingua: Para LC: 0=inglês, 1=espanhol
            
        Returns:
            Dicionário com resultado completo
        """
        itens = self.carregar_itens(ano, area, co_prova, tp_lingua)
        respostas_bin = self.converter_respostas(respostas_str, itens)
        
        itens_validos = [i for i in itens if not i.abandonado]
        respostas_validas = [r for r, i in zip(respostas_bin, itens) if not i.abandonado]
        
        theta = self.estimar_theta_eap(respostas_bin, itens)
        nota = self.transformar_escala(theta, ano, area, co_prova)
        
        return {
            'ano': ano,
            'area': area,
            'co_prova': co_prova,
            'total_itens': len(itens_validos),
            'acertos': sum(respostas_validas),
            'theta': theta,
            'nota': nota,
            'tp_lingua': tp_lingua,
        }
    
    def atualizar_coeficientes(self, coef_dict: Dict):
        """Atualiza os coeficientes de equalização."""
        self.COEF_EQUALIZACAO.update(coef_dict)
    
    def analisar_impacto_erros(self, ano: int, area: str, co_prova: int,
                               respostas_str: str, tp_lingua: Optional[int] = None) -> List[Dict]:
        """
        Analisa o impacto de cada erro na nota final.
        Retorna lista ordenada por ganho potencial (maior primeiro).
        """
        itens = self.carregar_itens(ano, area, co_prova, tp_lingua)
        respostas_bin = self.converter_respostas(respostas_str, itens)
        
        theta_original = self.estimar_theta_eap(respostas_bin, itens)
        nota_original = self.transformar_escala(theta_original, ano, area)
        
        impactos = []
        
        # Mapear índice na string para o item correspondente
        for idx, (resp, item) in enumerate(zip(respostas_bin, itens)):
            if resp == 0 and not item.abandonado:
                respostas_mod = respostas_bin.copy()
                respostas_mod[idx] = 1
                
                theta_mod = self.estimar_theta_eap(respostas_mod, itens)
                nota_mod = self.transformar_escala(theta_mod, ano, area)
                
                # idx é o índice na lista de itens, que corresponde ao índice na string de respostas
                resposta_dada = respostas_str[idx] if idx < len(respostas_str) else '?'
                
                impactos.append({
                    'posicao': item.posicao,
                    'gabarito': item.gabarito,
                    'resposta_dada': resposta_dada,
                    'param_a': item.param_a,
                    'param_b': item.param_b,
                    'param_c': item.param_c,
                    'ganho_potencial': nota_mod - nota_original,
                })
        
        impactos.sort(key=lambda x: x['ganho_potencial'], reverse=True)
        return impactos
    
    def analisar_todas_questoes(self, ano: int, area: str, co_prova: int,
                                 respostas_str: str, tp_lingua: Optional[int] = None) -> Dict:
        """
        Analisa TODAS as questões da prova (acertos e erros).
        
        Para cada questão retorna:
        - Status (acerto/erro)
        - Ganho potencial (se errasse) ou ganho obtido (se acertou)
        - Dificuldade relativa
        - Parâmetros TRI
        
        Returns:
            Dict com 'nota', 'theta', 'acertos', 'erros' e listas detalhadas
        """
        itens = self.carregar_itens(ano, area, co_prova, tp_lingua)
        respostas_bin = self.converter_respostas(respostas_str, itens)
        
        theta_original = self.estimar_theta_eap(respostas_bin, itens)
        nota_original = self.transformar_escala(theta_original, ano, area)
        
        acertos = []
        erros = []
        
        for idx, (resp, item) in enumerate(zip(respostas_bin, itens)):
            if item.abandonado:
                continue
                
            resposta_dada = respostas_str[idx] if idx < len(respostas_str) else '?'
            
            # Simular o cenário oposto
            respostas_mod = respostas_bin.copy()
            respostas_mod[idx] = 1 - resp  # Inverter acerto/erro
            theta_mod = self.estimar_theta_eap(respostas_mod, itens)
            nota_mod = self.transformar_escala(theta_mod, ano, area)
            
            questao = {
                'posicao': item.posicao,
                'gabarito': item.gabarito,
                'resposta_dada': resposta_dada,
                'param_a': item.param_a,
                'param_b': item.param_b,
                'param_c': item.param_c,
                'co_item': item.co_item,
            }
            
            if resp == 1:  # Acerto
                questao['perda_se_errasse'] = nota_original - nota_mod
                acertos.append(questao)
            else:  # Erro
                questao['ganho_se_acertasse'] = nota_mod - nota_original
                erros.append(questao)
        
        # Ordenar acertos por perda potencial (mais valiosos primeiro)
        acertos.sort(key=lambda x: x['perda_se_errasse'], reverse=True)
        # Ordenar erros por ganho potencial (maior primeiro)
        erros.sort(key=lambda x: x['ganho_se_acertasse'], reverse=True)
        
        return {
            'nota': nota_original,
            'theta': theta_original,
            'total_acertos': len(acertos),
            'total_erros': len(erros),
            'total_itens': len(acertos) + len(erros),
            'acertos': acertos,
            'erros': erros,
        }
        return impactos
