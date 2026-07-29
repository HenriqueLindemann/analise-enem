# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Calibrador de Coeficientes TRI

Ferramenta legada para ajustar um baseline linear empírico por
ano/área/prova através de regressão.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from typing import Dict, List, Optional
from .calculador import CalculadorTRI


class Calibrador:
    """
    Ajusta coeficientes lineares aos pares theta/nota dos microdados.

    O baseline usa:
        nota = slope * theta + intercept
    
    Esta classe encontra (slope, intercept) via regressão nos microdados.
    Suporta calibração por prova individual ou por área (todas as provas).
    """
    
    def __init__(
        self,
        participantes_path: str = None,
        itens_path: str = None,
        **kwargs,
    ):
        """Cria calibrador com fontes de participantes e itens independentes.

        ``microdados_path`` é aceito como alias legado de
        ``participantes_path``. Os parâmetros de itens usam o pacote por padrão.
        """
        legado = kwargs.pop("microdados_path", None)
        if kwargs:
            raise TypeError(f"Argumentos desconhecidos: {sorted(kwargs)}")
        if participantes_path is None:
            participantes_path = legado
        elif legado is not None:
            raise TypeError(
                "Use apenas participantes_path; microdados_path é um alias legado"
            )
        self.calc = CalculadorTRI(itens_path)
        self.base_path = Path(participantes_path or "microdados_limpos")
        self._cache_dados: Dict[tuple, pd.DataFrame] = {}

    def _localizar_arquivo(self, ano: int) -> Path:
        """
        Resolve o arquivo de participantes do ano.

        A amostra de tools/amostrar_microdados_brutos.py tem precedência: cobre
        todas as provas do ano em poucos MB, enquanto DADOS_ENEM_<ano>.csv só
        existe para os anos limpos localmente.
        """
        dir_ano = self.base_path / str(ano)
        for nome in (f"AMOSTRA_CALIBRACAO_{ano}.csv", f"DADOS_ENEM_{ano}.csv"):
            caminho = dir_ano / nome
            if caminho.exists():
                return caminho
        raise FileNotFoundError(
            f"Microdados não encontrados em {dir_ano} "
            f"(esperado AMOSTRA_CALIBRACAO_{ano}.csv ou DADOS_ENEM_{ano}.csv)"
        )

    def _carregar_dados(self, ano: int, area: str) -> pd.DataFrame:
        """
        Participantes de uma área, filtrados por presença e nota válida.

        Cache por (ano, área): reler o arquivo a cada prova dominava o tempo.
        """
        if (ano, area) in self._cache_dados:
            return self._cache_dados[(ano, area)]

        microdados_file = self._localizar_arquivo(ano)

        # Colunas necessárias
        pres_col = f'TP_PRESENCA_{area}'
        prova_col = f'CO_PROVA_{area}'
        nota_col = f'NU_NOTA_{area}'
        resp_col = f'TX_RESPOSTAS_{area}'

        usecols = [pres_col, prova_col, nota_col, resp_col]
        if area == 'LC':
            usecols.append('TP_LINGUA')

        # Verificar colunas existentes
        df_header = pd.read_csv(microdados_file, encoding='latin1', sep=';', nrows=0)
        usecols = [c for c in usecols if c in df_header.columns]

        df = pd.read_csv(microdados_file, encoding='latin1', sep=';',
                        usecols=usecols, low_memory=False)

        # Filtrar presentes com nota válida
        df = df[(df[pres_col] == 1) & (df[nota_col] > 0)]
        df = df.dropna(subset=[nota_col, resp_col, prova_col])

        self._cache_dados[(ano, area)] = df
        return df

    def calibrar_prova(self, ano: int, area: str, co_prova: int, 
                       n_amostras: int = 200, verbose: bool = True,
                       estratificado: bool = True) -> Dict:
        """
        Calibra coeficientes para uma prova específica.
        
        Args:
            estratificado: Se True, amostra de forma estratificada incluindo notas altas
        
        Returns:
            Dicionário com slope, intercept, r_squared, mae, n_amostras
        """
        area = area.upper()
        prova_col = f'CO_PROVA_{area}'
        nota_col = f'NU_NOTA_{area}'
        resp_col = f'TX_RESPOSTAS_{area}'
        
        df = self._carregar_dados(ano, area)
        df_prova = df[df[prova_col] == co_prova].copy()  # Explicit copy to avoid warning

        if len(df_prova) < 10:
            return {'erro': f'Poucos participantes: {len(df_prova)}'}

        # Amostragem estratificada por faixa de nota
        if estratificado and len(df_prova) >= n_amostras:
            # Dividir em faixas de nota
            bins = [0, 500, 600, 700, 800, 1000]
            df_prova['faixa'] = pd.cut(df_prova[nota_col], bins=bins, labels=False)
            
            # Amostrar proporcionalmente de cada faixa, garantindo representação de notas altas
            amostras_por_faixa = max(10, n_amostras // 5)  # Pelo menos 10 por faixa
            
            samples = []
            for faixa in df_prova['faixa'].unique():
                if pd.notna(faixa):  # Somente se faixa for válida
                    faixa_df = df_prova[df_prova['faixa'] == faixa]
                    if len(faixa_df) > 0:  # Somente se tiver dados nesta faixa
                        n_sample = min(len(faixa_df), amostras_por_faixa)
                        samples.append(faixa_df.sample(n=n_sample, random_state=42))
            
            # Fallback: se não conseguiu amostras estratificadas, usar todas disponíveis
            if samples:
                df_prova = pd.concat(samples).drop('faixa', axis=1)
            else:
                df_prova = df_prova.drop('faixa', axis=1).head(n_amostras)
        else:
            df_prova = df_prova.head(n_amostras)
        
        df_amostra = df_prova
        
        if verbose:
            print(f"Prova {co_prova}: {len(df_amostra)} participantes", end='')
        
        dados = []

        for _, row in df_amostra.iterrows():
            # Identificar língua para LC
            tp_lingua = None
            if area == 'LC' and 'TP_LINGUA' in row.index and pd.notna(row['TP_LINGUA']):
                try:
                    tp_lingua = int(row['TP_LINGUA'])
                except ValueError:
                    tp_lingua = None

            try:
                # Mesmo ponto de entrada de calcular_nota. Calibrar por outro
                # caminho ajustaria o coeficiente contra um theta que o usuário
                # nunca obtém.
                itens, respostas_bin, _ = self.calc._preparar_calculo(
                    ano, area, co_prova, row[resp_col], tp_lingua
                )
                theta = self.calc.estimar_theta_eap(respostas_bin, itens)
                dados.append({'theta': theta, 'nota': row[nota_col]})
            except Exception:
                if verbose and len(dados) == 0:
                     import traceback
                     print(f"Erro row: {traceback.format_exc()}")
                continue

        if len(dados) < 10:
            return {'erro': 'Poucos cálculos válidos'}
        
        df_cal = pd.DataFrame(dados)
        slope, intercept, r, _, std_err = stats.linregress(df_cal['theta'], df_cal['nota'])
        
        pred = slope * df_cal['theta'] + intercept
        mae = (df_cal['nota'] - pred).abs().mean()
        
        if verbose:
            print(f" -> slope={slope:.2f}, intercept={intercept:.2f}, R²={r**2:.4f}, MAE={mae:.2f}")
        
        return {
            'ano': ano,
            'area': area,
            'prova': co_prova,
            'n_amostras': len(df_cal),
            'slope': slope,
            'intercept': intercept,
            'r_squared': r ** 2,
            'mae': mae,
            'std_err': std_err,
        }
    
    def calibrar_area_todas_provas(self, ano: int, area: str, 
                                    n_amostras_por_prova: int = 100,
                                    verbose: bool = True) -> List[Dict]:
        """
        Calibra todas as provas de uma área em um ano.
        
        Returns:
            Lista de resultados de calibração por prova
        """
        area = area.upper()
        provas = self.calc.listar_provas(ano, area)
        
        if area not in provas:
            return [{'erro': f'Área {area} não encontrada'}]
        
        resultados = []
        resultados = []
        for co_prova in provas[area]:
            # Verificar quantidade de itens antes de calibrar (exceto LC que pode ter 50 ou 45)
            # CN/MT/CH devem ter max 45 itens. Se tiver 90+, é prova duplicada/irregular.
            try:
                # Carregar apenas para verificar contagem 
                itens_check = self.calc.carregar_itens(ano, area, co_prova, None)
                if len(itens_check) > 55 and area != 'LC': 
                    if verbose:
                        print(f"  Prova {co_prova} pulada: {len(itens_check)} itens")
                    continue
            except Exception:
                pass

            if verbose:
                print(f"  ", end='')
            res = self.calibrar_prova(ano, area, co_prova, n_amostras_por_prova, verbose)
            resultados.append(res)
        
        return resultados
    
    def calibrar_ano_completo(self, ano: int, n_amostras_por_prova: int = 100,
                               verbose: bool = True) -> Dict[str, List[Dict]]:
        """
        Calibra todas as áreas e provas de um ano.
        
        Returns:
            Dicionário {área: [resultados por prova]}
        """
        resultados = {}
        
        for area in ['MT', 'CN', 'CH', 'LC']:
            if verbose:
                print(f"\n{'='*60}")
                print(f"{area} - Ano {ano}")
                print('='*60)
            
            resultados[area] = self.calibrar_area_todas_provas(
                ano, area, n_amostras_por_prova, verbose
            )
        
        return resultados
    
    def gerar_coeficientes_dict(self, resultados: Dict[str, List[Dict]]) -> Dict:
        """
        Gera dicionário de coeficientes para usar no CalculadorTRI.
        
        Formato: {(ano, area, prova): (slope, intercept)}
        """
        coefs = {}
        for area, lista in resultados.items():
            for r in lista:
                if 'erro' not in r and r.get('r_squared', 0) > 0.9:
                    key = (r['ano'], r['area'], r['prova'])
                    coefs[key] = (r['slope'], r['intercept'])
        return coefs
    
    def gerar_codigo_python(self, resultados: Dict[str, List[Dict]]) -> str:
        """Gera código Python com os coeficientes descobertos."""
        linhas = ["# Coeficientes descobertos via calibração"]
        linhas.append("# Formato: (ano, area, prova): (slope, intercept)")
        linhas.append("COEF_EQUALIZACAO = {")
        
        for area, lista in resultados.items():
            linhas.append(f"    # {area}")
            for r in lista:
                if 'erro' not in r and r.get('r_squared', 0) > 0.9:
                    linhas.append(
                        f"    ({r['ano']}, '{r['area']}', {r['prova']}): "
                        f"({r['slope']:.4f}, {r['intercept']:.2f}),  # R²={r['r_squared']:.4f}"
                    )
        
        linhas.append("}")
        return "\n".join(linhas)
    
    def resumo_calibracao(self, resultados: Dict[str, List[Dict]]) -> str:
        """Gera resumo estatístico da calibração."""
        linhas = []
        
        for area, lista in resultados.items():
            validos = [r for r in lista if 'erro' not in r]
            if not validos:
                linhas.append(f"{area}: Sem resultados válidos")
                continue
            
            slopes = [r['slope'] for r in validos]
            intercepts = [r['intercept'] for r in validos]
            maes = [r['mae'] for r in validos]
            
            linhas.append(f"\n{area} ({len(validos)} provas):")
            linhas.append(f"  Slope:     {np.mean(slopes):.2f} ± {np.std(slopes):.2f}")
            linhas.append(f"  Intercept: {np.mean(intercepts):.2f} ± {np.std(intercepts):.2f}")
            linhas.append(f"  MAE médio: {np.mean(maes):.2f}")
        
        return "\n".join(linhas)
