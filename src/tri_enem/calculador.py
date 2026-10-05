# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Calculadora Nota TRI ENEM - Módulo Principal de Cálculo

Implementa o modelo logístico de 3 parâmetros (ML3) com estimação bayesiana
Expected a Posteriori (EAP), com a quadratura definida por prova no catálogo.

A documentação a seguir registra as decisões que não decorrem do modelo TRI
padrão e que foram estabelecidas empiricamente por comparação com notas
oficiais dos microdados públicos.

Método
------
- Modelo ML3: P(acerto|θ) = c + (1 - c) / (1 + exp(-D·a·(θ - b)))
- Fator de escala D = 1.0 (e não 1.7, como é usual na literatura)
- Prior normal: Gauss-Hermite de 80 pontos ou grade de 41 pontos em [-4, 4]
- Correções de associação, gabarito e exclusão de itens vêm do catálogo
  (``reconstrucao_itens``); os CSVs oficiais não são alterados
- Itens anulados são excluídos da verossimilhança, não contados como erro

Alternativas medidas e descartadas:

    D = 1.7 em vez de 1.0        pior em todos os casos; 2023-MT vai de 0,09 a 8,79
    relação θ->nota quadrática   não garante monotonicidade nem melhora o holdout
    GH com 200 pontos            não corrige a diferença de suporte da prior
    anulados contam como acerto  efeito nulo; os parâmetros são NaN

Transformação para a escala ENEM
--------------------------------
A transformação simples nota = 100·θ + 500 não descreve adequadamente as notas
oficiais observadas. O catálogo pode aplicar uma transformação afim ou
monotônica linear por partes, escolhida sem reutilizar o holdout final. O
baseline (slope, intercept), os nós e as métricas ficam em
coeficientes_data.json.

Toda conversão θ -> nota no motor principal é feita por transformar_escala()
com co_prova informado. Quando não existe um modelo específico, o catálogo
fornece a transformação do ano/área.

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
    2020+      50*                presente    1-45   (pares por idioma)

De 2010 em diante, filtra-se por TP_LINGUA (0=inglês, 1=espanhol) mantendo
os itens comuns (TP_LINGUA nulo), o que reduz 50 para 45 itens. Ver
tradutor.py. *As digitais 691–694 de 2020 têm 90 linhas: duas versões completas
de 45 itens, selecionadas pelo idioma antes do pareamento. Em 2009 não há
coluna de idioma e as 45 posições valem para
todos, inclusive as quatro provas de LC, cujo item anulado sem CO_ITEM precisa
ser preservado para não deslocar o pareamento (ver carregar_itens).

Limitações conhecidas estão documentadas em precisao.py, que classifica cada
prova por erro medido contra notas oficiais.
"""

import numpy as np
import pandas as pd
from collections import OrderedDict
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Iterable, Tuple, List, Dict
from dataclasses import dataclass
from threading import Lock

from .coeficientes import (
    aplicar_transformacao, obter_transformacao, obter_reconstrucoes_itens,
)
from .posicoes import posicao_caderno as calcular_posicao_caderno


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
    tp_lingua: float | None = None  # 0=inglês, 1=espanhol, NaN=comum
    metodo_quadratura: str = "gauss_hermite_80"


class CalculadorTRI:
    """
    Calculador de proficiência TRI usando modelo ML3 + EAP.
    
    Implementação:
    - Modelo Logístico de 3 Parâmetros (ML3)
    - Estimação EAP com quadratura registrada no catálogo
    - Prior: N(0, 1) - Normal padrão
    - Transformação de escala calibrada por prova contra notas oficiais
    
    LC (Linguagens 2023+): 
    - 50 itens no arquivo (posições 1-45)
    - Posições 1-5: existem versões inglês (TP_LINGUA=0) E espanhol (TP_LINGUA=1)
    - Posições 6-45: questões comuns (TP_LINGUA=NaN)
    - Filtrar pelo TP_LINGUA do participante para obter 45 itens totais
    """
    
    D = 1.0  # Fator de escala
    N_QUADRATURA = 80  # Gauss-Hermite padrão; a grade alternativa tem 41 pontos.
    MAX_CACHE_QUADRATURA = 128
    
    # Coeficientes carregados de coeficientes.py
    # Ver coeficientes.py para adicionar novos coeficientes
    
    def __init__(self, itens_path: str = None, reconstrucoes: Dict | None = None):
        """
        Args:
            itens_path: Caminho externo opcional para a pasta de itens.
                Quando omitido, usa os parâmetros empacotados com ``tri_enem``.
            reconstrucoes: Ajustes explícitos por ano/área/prova. None usa o
                catálogo empacotado; {} carrega somente os CSVs originais.
                Fontes externas não recebem ajustes do pacote implicitamente.
        """
        self._packaged_base = Path(
            str(files("tri_enem").joinpath("data", "itens"))
        )
        if itens_path is None:
            self.base_path = self._packaged_base
        else:
            self.base_path = Path(itens_path)
        self._cache_itens: Dict[str, List[ItemTRI]] = {}
        self._cache_df_itens: Dict[str, pd.DataFrame] = {}
        # Só parâmetros públicos da prova, nunca respostas dos participantes.
        self._cache_logs_quadratura = OrderedDict()
        self._lock_logs_quadratura = Lock()
        self._mapeador: object | None = None  # Criado sob demanda; ver _ordem_provas.
        self._pontos_quad, self._pesos_quad = self._calcular_quadratura()
        self.reconstrucoes = (
            deepcopy(reconstrucoes) if reconstrucoes is not None
            else obter_reconstrucoes_itens() if itens_path is None else {}
        )
        self._usar_ancoras_catalogo = reconstrucoes is None and itens_path is None
        pontos_grade = np.linspace(-4.0, 4.0, 41)
        self._quadratura_grade = (pontos_grade, np.exp(-pontos_grade ** 2 / 2))

    def _quadratura_itens(self, itens: List[ItemTRI]):
        metodos = {item.metodo_quadratura for item in itens}
        if len(metodos) > 1:
            raise ValueError("Os itens devem usar o mesmo método de quadratura")
        if metodos == {"grade_41"}:
            return self._quadratura_grade
        if metodos - {"gauss_hermite_80"}:
            raise ValueError(f"Quadratura desconhecida: {metodos}")
        return self._pontos_quad, self._pesos_quad
    
    def _ordem_provas(self, ano: int) -> List[str]:
        """Ordem das áreas no caderno, com um único mapeador por instância."""
        if self._mapeador is None:
            from .mapeador_provas import MapeadorProvas

            self._mapeador = MapeadorProvas()
        return self._mapeador.listar_ordem_provas(ano)
    
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

        # O gerador do pacote normaliza para UTF-8. Caminhos externos podem
        # apontar aos CSVs oficiais antigos em Latin-1, por isso o fallback de
        # codificação é explícito e não muda a origem solicitada.
        try:
            df = pd.read_csv(itens_path, encoding="utf-8", sep=";")
        except UnicodeDecodeError:
            df = pd.read_csv(itens_path, encoding="latin1", sep=";")
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
                       tp_lingua: int | None = None) -> List[ItemTRI]:
        """
        Carrega os itens de uma prova específica.
        
        Args:
            ano: Ano do ENEM
            area: Área (CN, CH, LC, MT)
            co_prova: Código da prova
            tp_lingua: Para LC: 0=inglês, 1=espanhol. É obrigatório nas
                provas que registram idioma.
        """
        ano = int(ano)
        area = area.upper()
        co_prova = int(co_prova)

        from .tradutor import (
            obter_config_lc, filtrar_itens_lc, deduplicar_itens_por_posicao,
        )

        config_lc = None
        if area == "LC":
            config_lc = obter_config_lc(ano)
            if config_lc.tem_tp_lingua_itens and tp_lingua not in (0, 1):
                raise ValueError(
                    f"{ano}/LC/{co_prova}: informe tp_lingua=0 (inglês) "
                    "ou tp_lingua=1 (espanhol)"
                )
        elif tp_lingua is not None:
            tp_lingua = None
        
        cache_key = f"{ano}_{area}_{co_prova}_{tp_lingua}"
        
        if cache_key in self._cache_itens:
            return self._cache_itens[cache_key]
        
        # Traduzir códigos BAM2 (Segunda Oportunidade) de 2025 para códigos PPL equivalentes
        # que possuem itens definidos no ITENS_PROVA_2025.csv
        co_prova_busca = co_prova
        reconstrucao = self.reconstrucoes.get(f"{ano},{area},{co_prova}", {})
        if "por_idioma" in reconstrucao:
            reconstrucao = reconstrucao["por_idioma"].get(str(tp_lingua), {})
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

        co_prova_busca = int(reconstrucao.get("codigo_base", co_prova_busca))

        df = self._carregar_df_itens(ano)

        if area == 'LC':
            # Filtro de idioma e dedup vivem em tradutor.py, um só lugar.
            df_prova = filtrar_itens_lc(
                df, co_prova_busca, tp_lingua, config_lc
            )
        else:
            df_prova = deduplicar_itens_por_posicao(
                df[(df['SG_AREA'] == area.upper()) & (df['CO_PROVA'] == co_prova_busca)]
            )

        if df_prova.empty:
            raise ValueError(f"Prova não encontrada: {ano}/{area}/{co_prova}")

        itens = []
        # Evitar construir uma Series por questão ao carregar os cadernos.
        for row in df_prova.itertuples(index=False):
            # Item anulado: excluído da verossimilhança (ver estimar_theta_eap).
            # A sinalização varia conforme o ano, daí as quatro condições: flag
            # explícita, parâmetros TRI ausentes ou gabarito marcado como
            # anulado ('X', '.', '*' ou vazio).
            is_abandonado = (
                getattr(row, 'IN_ITEM_ABAN', None) == 1
            ) or (
                pd.isna(row.NU_PARAM_A) or
                pd.isna(row.NU_PARAM_B) or
                pd.isna(row.NU_PARAM_C)
            ) or (
                str(row.TX_GABARITO).upper() == 'X'
            ) or (
                pd.isna(row.TX_GABARITO) or
                str(row.TX_GABARITO) == '.' or
                str(row.TX_GABARITO) == '*'
            )

            # CO_ITEM é só identificador e falta em itens anulados (LC 2009
            # tem um por prova). Descartar a linha desalinharia todas as
            # posições seguintes.
            try:
                co_item_val = int(row.CO_ITEM)
            except (ValueError, TypeError):
                co_item_val = 0

            item = ItemTRI(
                posicao=int(row.CO_POSICAO),
                gabarito=str(row.TX_GABARITO),
                param_a=float(row.NU_PARAM_A) if pd.notna(row.NU_PARAM_A) else 0.0,
                param_b=float(row.NU_PARAM_B) if pd.notna(row.NU_PARAM_B) else 0.0,
                param_c=float(row.NU_PARAM_C) if pd.notna(row.NU_PARAM_C) else 0.0,
                co_item=co_item_val,
                abandonado=is_abandonado,
                tp_lingua=getattr(row, 'TP_LINGUA', None),
            )
            itens.append(item)
        
        itens.sort(key=lambda x: x.posicao)
        ajustes = reconstrucao.get("itens")
        if ajustes is not None:
            if len(ajustes) != len(itens):
                raise ValueError(f"{cache_key}: reconstrução com número de itens inválido")
            for item, ajuste in zip(itens, ajustes):
                item.param_a = float(ajuste["a"])
                item.param_b = float(ajuste["b"])
                item.param_c = float(ajuste["c"])
                item.abandonado = bool(ajuste["abandonado"])
                item.gabarito = ajuste.get("gabarito", item.gabarito)
                item.co_item = int(ajuste.get("co_item", item.co_item))
                parametros = (item.param_a, item.param_b, item.param_c)
                if (not np.all(np.isfinite(parametros)) or item.param_a < 0
                        or not 0 <= item.param_c <= 1):
                    raise ValueError(f"{cache_key}: parâmetros reconstruídos inválidos")
                if not item.abandonado and item.gabarito not in set("ABCDE"):
                    raise ValueError(f"{cache_key}: gabarito reconstruído inválido")
        metodo = reconstrucao.get("quadratura", "gauss_hermite_80")
        for item in itens:
            item.metodo_quadratura = metodo
        self._quadratura_itens(itens)
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

    def _logs_quadratura(self, pontos, itens):
        """Reutiliza log(P) e log(1-P), com limite de memória por calculador.

        A chave acompanha mudanças nos parâmetros, no fator D e nos pontos.
        Os arrays publicados são imutáveis e o LRU é protegido entre sessões.
        A construção mantém a rotina escalar e a disposição usada no batch.
        """
        ativos = [item for item in itens if not item.abandonado]
        chave = (
            self.D, tuple(pontos),
            tuple((item.param_a, item.param_b, item.param_c) for item in ativos),
        )
        with self._lock_logs_quadratura:
            salvo = self._cache_logs_quadratura.get(chave)
            if salvo is not None:
                self._cache_logs_quadratura.move_to_end(chave)
                return salvo

        probabilidades = np.asarray([
            [self.probabilidade_acerto(theta, item) for item in ativos]
            for theta in pontos
        ]).reshape(len(pontos), len(ativos))
        probabilidades = np.clip(probabilidades, 1e-15, 1 - 1e-15)
        log_p = np.log(probabilidades)
        log_q = np.log(1 - probabilidades)
        log_p.setflags(write=False)
        log_q.setflags(write=False)
        with self._lock_logs_quadratura:
            self._cache_logs_quadratura[chave] = (log_p, log_q)
            self._cache_logs_quadratura.move_to_end(chave)
            while len(self._cache_logs_quadratura) > self.MAX_CACHE_QUADRATURA:
                self._cache_logs_quadratura.popitem(last=False)
        return log_p, log_q
    
    def estimar_theta_eap(self, respostas: List[int], itens: List[ItemTRI]) -> float:
        """
        Estima θ usando Expected a Posteriori (EAP).
        
        θ_EAP = Σ(X_k * L_k * W_k) / Σ(L_k * W_k)
        """
        pontos, pesos = self._quadratura_itens(itens)
        log_p, log_q = self._logs_quadratura(pontos, itens)
        # Preservar a ordem das somas do caminho escalar de referência.
        log_L = np.zeros(len(pontos), dtype=float)
        coluna = 0
        for u, item in zip(respostas, itens):
            if item.abandonado:
                continue
            log_L += log_p[:, coluna] if u == 1 else log_q[:, coluna]
            coluna += 1
        
        log_L_max = np.max(log_L)
        L = np.exp(log_L - log_L_max)
        
        numerador = np.sum(pontos * L * pesos)
        denominador = np.sum(L * pesos)
        
        return numerador / denominador if denominador > 0 else 0.0

    def estimar_theta_eap_batch(
        self,
        respostas: Iterable[Iterable[int]],
        itens: List[ItemTRI],
        batch_size: int = 4096,
    ) -> np.ndarray:
        """Estima EAP em lotes pelo mesmo modelo do caminho escalar.

        A matriz de respostas deve ter uma coluna por item. Itens anulados são
        retirados antes da multiplicação matricial. O processamento em blocos
        limita memória sem alterar o resultado matemático.
        """
        matriz = np.asarray(respostas, dtype=float)
        if matriz.ndim != 2 or matriz.shape[1] != len(itens):
            raise ValueError(
                "A matriz de respostas deve ser bidimensional e ter "
                f"{len(itens)} colunas"
            )
        if not np.all((matriz == 0) | (matriz == 1)):
            raise ValueError("Respostas binárias devem conter somente 0 ou 1")
        if batch_size <= 0:
            raise ValueError("batch_size deve ser positivo")

        pontos, pesos = self._quadratura_itens(itens)
        ativos = np.asarray([not item.abandonado for item in itens])
        matriz = matriz[:, ativos]
        itens_ativos = [item for item in itens if not item.abandonado]
        if not itens_ativos:
            return np.zeros(matriz.shape[0], dtype=float)

        log_p, log_q = self._logs_quadratura(pontos, itens)

        resultado = np.empty(matriz.shape[0], dtype=float)
        for inicio in range(0, matriz.shape[0], batch_size):
            fim = min(inicio + batch_size, matriz.shape[0])
            bloco = matriz[inicio:fim]
            log_l = bloco @ log_p.T + (1 - bloco) @ log_q.T
            log_l -= np.max(log_l, axis=1, keepdims=True)
            posterior = np.exp(log_l) * pesos
            denominador = posterior.sum(axis=1)
            numerador = posterior @ pontos
            resultado[inicio:fim] = np.divide(
                numerador,
                denominador,
                out=np.zeros_like(numerador),
                where=denominador > 0,
            )
        return resultado
    
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
                             tp_lingua: int | None = None) -> str:
        """
        Reduz a string de respostas às 45 posições canônicas.

        LC de 2014 a 2021 vem com 50 caracteres nos microdados: cinco posições
        por idioma, com '99999' no não escolhido. Sem reduzir, a nota sai
        deslocada em até 168 pontos. Entradas de 45 passam inalteradas.
        """
        if not isinstance(respostas_str, str):
            raise TypeError("respostas_str deve ser uma string")

        if area.upper() == 'LC':
            from .tradutor import obter_config_lc, filtrar_respostas_lc
            config = obter_config_lc(ano)
            if config.tem_tp_lingua_dados and tp_lingua not in (0, 1):
                raise ValueError(
                    f"{ano}/LC: informe tp_lingua=0 (inglês) ou "
                    "tp_lingua=1 (espanhol)"
                )
            respostas_str = filtrar_respostas_lc(
                respostas_str, tp_lingua if tp_lingua is not None else 0, config,
            )
        return respostas_str

    def _preparar_calculo(self, ano: int, area: str, co_prova: int,
                          respostas_str: str, tp_lingua: int | None = None):
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

        invalidos = sorted(set(respostas_norm.upper()) - set("ABCDE.*"))
        if invalidos:
            raise ValueError(
                f"{ano}/{area}/{co_prova}: respostas contêm caracteres inválidos: "
                f"{', '.join(repr(c) for c in invalidos)}"
            )

        return itens, self.converter_respostas(respostas_norm, itens), respostas_norm

    def preparar_respostas_batch(
        self,
        ano: int,
        area: str,
        co_prova: int,
        respostas: Iterable[str],
        tp_lingua: int | None = None,
    ) -> Tuple[List[ItemTRI], np.ndarray]:
        """Normaliza e converte um lote de respostas da mesma prova/idioma."""
        itens = self.carregar_itens(ano, area, co_prova, tp_lingua)
        binarias = []
        for resposta in respostas:
            _, vetor, _ = self._preparar_calculo(
                ano, area, co_prova, resposta, tp_lingua
            )
            binarias.append(vetor)
        return itens, np.asarray(binarias, dtype=np.int8)

    def transformar_escala(self, theta: float, ano: int = None, area: str = None,
                          co_prova: int = None) -> float:
        """
        Transforma θ da escala (0,1) para escala ENEM.
        
        Usa a transformação validada por prova, com fallback por área.
        """
        transformacao = obter_transformacao(ano or 2023, area or 'MT', co_prova)
        return aplicar_transformacao(theta, transformacao)
    
    def calcular_nota(self, ano: int, area: str, co_prova: int, 
                     respostas_str: str, tp_lingua: int | None = None) -> Dict:
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
        itens_anulados = [i for i in itens if i.abandonado]
        respostas_validas = [r for r, i in zip(respostas_bin, itens) if not i.abandonado]

        ordem_provas = self._ordem_provas(ano)
        questoes_anuladas_brutas = [i.posicao for i in itens_anulados]
        questoes_anuladas_caderno = [
            calcular_posicao_caderno(
                area,
                indice,
                ordem_provas,
            )
            for indice, item in enumerate(itens)
            if item.abandonado
        ]

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
            'total_anulados': len(itens_anulados),
            # ``questoes_anuladas`` é a numeração pública do caderno. O motor
            # detalhado continua expondo ``posicao`` como CO_POSICAO bruto.
            'questoes_anuladas': questoes_anuladas_caderno,
            'questoes_anuladas_caderno': questoes_anuladas_caderno,
            'questoes_anuladas_brutas': questoes_anuladas_brutas,
        }
    
    def analisar_impacto_erros(self, ano: int, area: str, co_prova: int,
                               respostas_str: str, tp_lingua: int | None = None) -> List[Dict]:
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
                                 respostas_str: str, tp_lingua: int | None = None) -> Dict:
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

        ordem_provas = self._ordem_provas(ano)

        acertos = []
        erros = []
        anuladas = []

        itens_validos_indices = [idx for idx, item in enumerate(itens) if not item.abandonado]
        if itens_validos_indices:
            matriz_mod = []
            for idx in itens_validos_indices:
                mod = list(respostas_bin)
                mod[idx] = 1 - mod[idx]
                matriz_mod.append(mod)
            thetas_mod = self.estimar_theta_eap_batch(matriz_mod, itens)
            mapa_thetas_mod = dict(zip(itens_validos_indices, thetas_mod))
        else:
            mapa_thetas_mod = {}

        for idx, (resp, item) in enumerate(zip(respostas_bin, itens)):
            resposta_dada = respostas_norm[idx] if idx < len(respostas_norm) else '?'

            if item.abandonado:
                questao_anulada = {
                    'posicao': item.posicao,
                    'posicao_caderno': calcular_posicao_caderno(
                        area, idx, ordem_provas
                    ),
                    'idx_area': idx,
                    'gabarito': item.gabarito,
                    'resposta_dada': resposta_dada,
                    'param_a': item.param_a,
                    'param_b': item.param_b,
                    'param_c': item.param_c,
                    'co_item': item.co_item,
                    'anulada': True,
                }
                anuladas.append(questao_anulada)
                continue

            # Simular o cenário oposto (obtido via batch vetorizado)
            theta_mod = float(mapa_thetas_mod[idx])
            nota_mod = self.transformar_escala(theta_mod, ano, area, co_prova)
            
            questao = {
                'posicao': item.posicao,  # Posição original no microdado
                'posicao_caderno': calcular_posicao_caderno(
                    area, idx, ordem_provas
                ),
                'idx_area': idx,          # Posição relativa na área (0 a 44)
                'gabarito': item.gabarito,
                'resposta_dada': resposta_dada,
                'param_a': item.param_a,
                'param_b': item.param_b,
                'param_c': item.param_c,
                'co_item': item.co_item,
                'anulada': False,
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
            'area': area,
            'nota': nota_original,
            'theta': theta_original,
            'total_acertos': len(acertos),
            'total_erros': len(erros),
            'total_anulados': len(anuladas),
            'total_itens': len(acertos) + len(erros),
            'acertos': acertos,
            'erros': erros,
            'anuladas': anuladas,
            # A lista sem sufixo mantém a semântica bruta desta API avançada.
            'questoes_anuladas': [q['posicao'] for q in anuladas],
            'questoes_anuladas_caderno': [
                q['posicao_caderno'] for q in anuladas
            ],
        }
