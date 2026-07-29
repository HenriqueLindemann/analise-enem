# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
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
    nota_mt = sim.calcular(
        'MT', 2023, 'ABCDE...' * 9, co_prova=1211
    )
    
    # Calcular nota de LC (com língua)
    nota_lc = sim.calcular(
        'LC', 2023, 'ABCDE...' * 9, lingua='ingles', co_prova=1201
    )
"""

from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass

from .calculador import CalculadorTRI


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

    É apenas uma fachada de conveniência: resolve o código da prova (por cor e
    tipo de aplicação) e delega o cálculo a CalculadorTRI, o mesmo motor usado
    pela interface web. Não reimplementa nada do cálculo.
    """
    
    def __init__(self, microdados_path: str = None):
        """
        Args:
            microdados_path: Caminho externo opcional para os itens. Quando
                omitido, usa os CSVs incluídos no pacote.
        """
        self.base_path = Path(microdados_path) if microdados_path else None
        self._calc = CalculadorTRI(microdados_path)

    def listar_provas(self, ano: int, area: str = None) -> Dict[str, List[int]]:
        """Lista provas disponíveis para um ano."""
        return self._calc.listar_provas(ano, area)
    
    def _descobrir_prova(self, ano: int, area: str) -> int:
        """Resolve automaticamente somente quando não existe ambiguidade."""
        provas = self.listar_provas(ano, area)
        codigos = provas.get(area.upper(), [])
        if len(codigos) == 1:
            return codigos[0]
        if len(codigos) > 1:
            raise ValueError(
                f"{ano}/{area.upper()} possui {len(codigos)} provas. Informe "
                "co_prova ou cor_prova + tipo_aplicacao."
            )
        raise ValueError(f"Área {area} não encontrada para {ano}")
    
    def calcular(
        self, 
        area: str, 
        ano: int, 
        respostas: str,
        lingua: str = None,
        co_prova: int = None,
        cor_prova: str = None,
        tipo_aplicacao: str = None,
    ) -> ResultadoNota:
        """
        Calcula a nota TRI.
        
        Modos de especificação da prova (ordem de precedência):
        1. co_prova: Código numérico direto (retrocompatibilidade)
        2. cor_prova + tipo_aplicacao: Busca no mapeamento
        3. Auto-descoberta somente se existir uma única prova possível
        
        Args:
            area: Área da prova (MT, CN, CH, LC)
            ano: Ano do ENEM (2009-2025)
            respostas: String com 45 respostas (A-E ou .)
            lingua: Para LC: 'ingles' ou 'espanhol' (obrigatório)
            co_prova: Código numérico da prova (opcional)
            cor_prova: Cor da prova (ex: 'azul', 'ROSA') - alternativa ao co_prova
            tipo_aplicacao: Tipo (ex: '1a_aplicacao', 'digital',
                'reaplicacao'); obrigatório quando ``cor_prova`` é usada
        
        Returns:
            ResultadoNota com nota e detalhes
            
        Exemplos:
            # Modo 1: Código direto (retrocompatibilidade)
            sim.calcular('CN', 2021, respostas, co_prova=1011)
            
            # Modo 2: Por cor e tipo
            sim.calcular('CN', 2021, respostas, cor_prova='azul', tipo_aplicacao='digital')
        """
        area = area.upper()

        # Resolver código da prova
        if co_prova is None and cor_prova is not None:
            if tipo_aplicacao is None:
                raise ValueError(
                    "Ao usar cor_prova, informe também tipo_aplicacao."
                )
            # Usar mapeador para descobrir código
            from .mapeador_provas import MapeadorProvas
            mapeador = MapeadorProvas()
            co_prova = mapeador.obter_codigo(ano, area, tipo_aplicacao, cor_prova)
        elif co_prova is None:
            # Auto-descoberta
            co_prova = self._descobrir_prova(ano, area)

        if area == "LC":
            if lingua is None:
                raise ValueError("Para LC, informe lingua='ingles' ou 'espanhol'")
            lingua_norm = str(lingua).strip().lower()
            ingles = {"ingles", "inglês", "english", "0"}
            espanhol = {"espanhol", "español", "spanish", "1"}
            if lingua_norm in ingles:
                tp_lingua = 0
            elif lingua_norm in espanhol:
                tp_lingua = 1
            else:
                raise ValueError(
                    f"Língua inválida: {lingua!r}. Use 'ingles' ou 'espanhol'."
                )
        else:
            tp_lingua = None

        # Todo o cálculo é delegado ao CalculadorTRI, inclusive a redução da
        # string de LC de 50 para 45 posições e a filtragem de itens por idioma.
        # Manter aqui um segundo caminho, com filtragem própria, foi o que
        # produziu notas de LC divergentes entre este simulador e a interface
        # web por oito anos de prova.
        resultado = self._calc.calcular_nota(
            ano, area, co_prova, respostas,
            tp_lingua,
        )

        return ResultadoNota(
            nota=resultado['nota'],
            theta=resultado['theta'],
            acertos=resultado['acertos'],
            total_itens=resultado['total_itens'],
            area=area,
            ano=ano,
            co_prova=co_prova,
            lingua=lingua if area == 'LC' else None,
        )


    def calcular_todas_areas(
        self,
        ano: int,
        respostas_dict: Dict[str, str],
        lingua_lc: str = 'ingles',
        co_provas: Optional[Dict[str, int]] = None,
        cores_prova: Optional[Dict[str, str]] = None,
        tipo_aplicacao: str = None,
    ) -> Dict[str, ResultadoNota]:
        """
        Calcula nota de todas as áreas de uma vez.
        
        Args:
            ano: Ano do ENEM
            respostas_dict: {'MT': '...', 'CN': '...', 'CH': '...', 'LC': '...'}
            lingua_lc: Língua para LC
            co_provas: Código explícito por área
            cores_prova: Cor por área, alternativa a ``co_provas``
            tipo_aplicacao: Aplicação obrigatória quando ``cores_prova`` é usado
        
        Returns:
            Dicionário com ResultadoNota por área
        """
        resultados = {}
        co_provas = {k.upper(): v for k, v in (co_provas or {}).items()}
        cores_prova = {k.upper(): v for k, v in (cores_prova or {}).items()}
        
        for area, respostas in respostas_dict.items():
            try:
                area_norm = area.upper()
                lingua = lingua_lc if area_norm == 'LC' else None
                resultados[area_norm] = self.calcular(
                    area_norm,
                    ano,
                    respostas,
                    lingua,
                    co_prova=co_provas.get(area_norm),
                    cor_prova=cores_prova.get(area_norm),
                    tipo_aplicacao=tipo_aplicacao,
                )
            except Exception as e:
                resultados[area.upper()] = {'erro': str(e)}
        
        return resultados
