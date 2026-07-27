# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Calculadora Nota TRI ENEM - Módulo Principal de Cálculo

Implementa o modelo logístico de 3 parâmetros (ML3) com estimação bayesiana
Expected a Posteriori (EAP) sobre quadratura de Gauss-Hermite.

Desenvolvido por engenharia reversa dos microdados do INEP. A documentação a
seguir registra as decisões que não decorrem do modelo TRI padrão e que foram
estabelecidas empiricamente por comparação com notas oficiais.

Método
------
- Modelo ML3: P(acerto|θ) = c + (1 - c) / (1 + exp(-D·a·(θ - b)))
- Fator de escala D = 1.0 (e não 1.7, como é usual na literatura)
- Prior N(0, 1); estimação EAP com 80 pontos de quadratura
- Itens anulados são excluídos da verossimilhança, não contados como erro

Alternativas medidas e descartadas, avaliadas pelo MAE com refit ótimo (que
isola a qualidade do θ). Não vale retestá-las:

    D = 1.7 em vez de 1.0        pior em todos os casos; 2023-MT vai de 0,09 a 8,79
    relação θ->nota quadrática   ganha no máximo 6%, às vezes piora
    200 pontos de quadratura     não altera o resultado
    anulados contam como acerto  efeito nulo; os parâmetros são NaN

Transformação para a escala ENEM
--------------------------------
O INEP não usa nota = 100·θ + 500. Cada prova tem seu próprio par
(slope, intercept), estimado por regressão contra notas oficiais e
armazenado em coeficientes_data.json. Os valores típicos por área são
MT ≈ 129,6 · CN ≈ 113,1 · CH ≈ 112,3 · LC ≈ 108,1, com intercepto próximo
de 500 e variação inferior a 0,1% entre anos.

Toda conversão θ -> nota deve ser feita por transformar_escala() com co_prova
informado. A omissão de co_prova recai no coeficiente médio da área e
introduz desvio de até 1,25 ponto.

Indexação das respostas
-----------------------
CO_POSICAO é a posição global no caderno (MT ocupa 136-180), enquanto
TX_RESPOSTAS_<área> tem 45 caracteres indexados de 0 a 44. O pareamento é
feito pelo índice na lista de itens ordenada por CO_POSICAO, nunca pelo
valor de CO_POSICAO.

Estrutura de LC ao longo dos anos
---------------------------------
    Ano        Itens no arquivo   TP_LINGUA   Posições
    2009       45                 ausente     91-135
    2010-2019  50                 presente    91-135 (pares por idioma)
    2020+      50                 presente    1-45   (pares por idioma)

De 2010 em diante, filtra-se por TP_LINGUA (0=inglês, 1=espanhol) mantendo
os itens comuns (TP_LINGUA nulo), o que reduz 50 para 45 itens. Ver
tradutor.py. Em 2009 não há coluna de idioma e as 45 posições valem para
todos, inclusive as quatro provas de LC, cujo item anulado sem CO_ITEM precisa
ser preservado para não deslocar o pareamento (ver carregar_itens).

Limitações conhecidas estão documentadas em precisao.py, que classifica cada
prova por erro medido contra notas oficiais.
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
        
        # Traduzir códigos BAM2 (Segunda Oportunidade) de 2025 para códigos PPL equivalentes
        # que possuem itens definidos no ITENS_PROVA_2025.csv
        co_prova_busca = co_prova
        if ano == 2025:
            TRADUCAO_BAM2 = {
                # Matemática
                1607: 1502, 1608: 1503, 1609: 1504, 1610: 1505, 1611: 1506, 1633: 1537,
                # Ciências da Natureza
                1619: 1511, 1620: 1512, 1621: 1514, 1622: 1513, 1623: 1515, 1634: 1538,
                # Ciências Humanas
                1583: 1520, 1584: 1521, 1585: 1522, 1586: 1523, 1587: 1524, 1631: 1535,
                # Linguagens e Códigos
                1595: 1529, 1596: 1530, 1597: 1531, 1598: 1532, 1599: 1533, 1632: 1499,
            }
            if co_prova in TRADUCAO_BAM2:
                co_prova_busca = TRADUCAO_BAM2[co_prova]

        from .tradutor import (
            obter_config_lc, filtrar_itens_lc, deduplicar_itens_por_posicao,
        )

        df = self._carregar_df_itens(ano)

        if area.upper() == 'LC':
            # Filtro de idioma e dedup vivem em tradutor.py, um só lugar.
            df_prova = filtrar_itens_lc(
                df, co_prova_busca, tp_lingua, obter_config_lc(ano)
            )
        else:
            df_prova = deduplicar_itens_por_posicao(
                df[(df['SG_AREA'] == area.upper()) & (df['CO_PROVA'] == co_prova_busca)]
            )

        if df_prova.empty:
            raise ValueError(f"Prova não encontrada: {ano}/{area}/{co_prova}")

        itens = []
        for _, row in df_prova.iterrows():
            # Item anulado: excluído da verossimilhança (ver estimar_theta_eap).
            # A sinalização varia conforme o ano, daí as quatro condições: flag
            # explícita, parâmetros TRI ausentes ou gabarito marcado como
            # anulado ('X', '.', '*' ou vazio).
            is_abandonado = (
                row.get('IN_ITEM_ABAN') == 1
            ) or (
                pd.isna(row['NU_PARAM_A']) or
                pd.isna(row['NU_PARAM_B']) or
                pd.isna(row['NU_PARAM_C'])
            ) or (
                str(row['TX_GABARITO']).upper() == 'X'
            ) or (
                pd.isna(row['TX_GABARITO']) or
                str(row['TX_GABARITO']) == '.' or
                str(row['TX_GABARITO']) == '*'
            )

            # CO_ITEM é só identificador e falta em itens anulados (LC 2009
            # tem um por prova). Descartar a linha desalinharia todas as
            # posições seguintes.
            try:
                co_item_val = int(row['CO_ITEM'])
            except (ValueError, TypeError):
                co_item_val = 0

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
    
    def normalizar_respostas(self, respostas_str: str, area: str, ano: int,
                             tp_lingua: Optional[int] = None) -> str:
        """
        Reduz a string de respostas às 45 posições canônicas.

        LC de 2014 a 2021 vem com 50 caracteres nos microdados: cinco posições
        por idioma, com '99999' no não escolhido. Sem reduzir, a nota sai
        deslocada em até 168 pontos. Entradas de 45 passam inalteradas.
        """
        if area.upper() == 'LC':
            from .tradutor import obter_config_lc, filtrar_respostas_lc
            respostas_str = filtrar_respostas_lc(
                respostas_str, tp_lingua if tp_lingua is not None else 0,
                obter_config_lc(ano),
            )
        return respostas_str

    def _preparar_calculo(self, ano: int, area: str, co_prova: int,
                          respostas_str: str, tp_lingua: Optional[int] = None):
        """
        Ponto único de entrada: carrega itens, normaliza respostas e pareia.

        CLI, web e PDF passam por aqui, para não divergirem no tratamento da
        entrada.

        Returns:
            (itens, respostas_bin, respostas_norm)
        """
        itens = self.carregar_itens(ano, area, co_prova, tp_lingua)
        respostas_norm = self.normalizar_respostas(respostas_str, area, ano, tp_lingua)

        if len(respostas_norm) != len(itens):
            raise ValueError(
                f"{ano}/{area}/{co_prova}: a prova tem {len(itens)} itens, mas "
                f"foram fornecidas {len(respostas_norm)} respostas"
            )

        return itens, self.converter_respostas(respostas_norm, itens), respostas_norm

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
        itens, respostas_bin, _ = self._preparar_calculo(
            ano, area, co_prova, respostas_str, tp_lingua
        )

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
    
    def analisar_impacto_erros(self, ano: int, area: str, co_prova: int,
                               respostas_str: str, tp_lingua: Optional[int] = None) -> List[Dict]:
        """
        Analisa o impacto de cada erro na nota final.
        Retorna lista ordenada por ganho potencial (maior primeiro).

        Recorte de `analisar_todas_questoes` restrito aos erros, mantido pela
        API pública. Evita um segundo laço de reestimação.
        """
        analise = self.analisar_todas_questoes(
            ano, area, co_prova, respostas_str, tp_lingua
        )
        return [
            {
                'posicao': q['posicao'],
                'gabarito': q['gabarito'],
                'resposta_dada': q['resposta_dada'],
                'param_a': q['param_a'],
                'param_b': q['param_b'],
                'param_c': q['param_c'],
                'ganho_potencial': q['ganho_se_acertasse'],
            }
            for q in analise['erros']
        ]

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
        itens, respostas_bin, respostas_norm = self._preparar_calculo(
            ano, area, co_prova, respostas_str, tp_lingua
        )

        theta_original = self.estimar_theta_eap(respostas_bin, itens)
        nota_original = self.transformar_escala(theta_original, ano, area, co_prova)

        acertos = []
        erros = []

        for idx, (resp, item) in enumerate(zip(respostas_bin, itens)):
            if item.abandonado:
                continue

            resposta_dada = respostas_norm[idx] if idx < len(respostas_norm) else '?'

            # Simular o cenário oposto
            respostas_mod = respostas_bin.copy()
            respostas_mod[idx] = 1 - resp  # Inverter acerto/erro
            theta_mod = self.estimar_theta_eap(respostas_mod, itens)
            nota_mod = self.transformar_escala(theta_mod, ano, area, co_prova)
            
            questao = {
                'posicao': item.posicao,  # Posição original no microdado
                'idx_area': idx,          # Posição relativa na área (0 a 44)
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
