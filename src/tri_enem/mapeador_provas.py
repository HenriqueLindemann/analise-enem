# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Mapeador de Códigos de Prova ENEM

Este módulo traduz especificações legíveis (área, tipo, cor) em códigos
numéricos de prova, lidando com variações de nomenclatura entre anos.

Exemplo de uso:
    from tri_enem import MapeadorProvas
    
    mapeador = MapeadorProvas()
    codigo = mapeador.obter_codigo(
        ano=2021,
        area="CN",
        tipo_aplicacao="digital",
        cor="azul"
    )
    # Retorna: 1011
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class InfoProva:
    """Informações completas de uma prova."""
    codigo: int
    ano: int
    area: str
    tipo_aplicacao: str
    cor: str
    eh_especial: bool = False
    descricao_especial: Optional[str] = None


class MapeadorProvas:
    """
    Mapeador de códigos de prova ENEM.
    
    Permite buscar códigos por:
    - Ano, área, tipo de aplicação e cor
    - Suporta aliases e normalização de nomenclaturas
    - Lida com provas especiais (Braille, Ledor, Libras, etc.)
    
    Exemplos:
        >>> mapeador = MapeadorProvas()
        >>> 
        >>> # Busca básica
        >>> codigo = mapeador.obter_codigo(2021, "CN", "digital", "azul")
        >>> print(codigo)  # 1011
        >>> 
        >>> # Com normalização automática
        >>> codigo = mapeador.obter_codigo(2021, "CN", "1ª aplicação", "AZUL")
        >>> print(codigo)  # 912
        >>> 
        >>> # Listar opções disponíveis
        >>> cores = mapeador.listar_cores_disponiveis(2021, "CN", "digital")
        >>> print(cores)  # ['azul', 'amarela', 'rosa', 'cinza']
    """
    
    def __init__(self, arquivo_mapeamento: Optional[Path] = None):
        """
        Inicializa o mapeador.
        
        Args:
            arquivo_mapeamento: Caminho para mapeamento_provas.yaml
                               Se None, usa o arquivo padrão do módulo.
        """
        if arquivo_mapeamento is None:
            arquivo_mapeamento = Path(__file__).parent / 'mapeamento_provas.yaml'
        
        with open(arquivo_mapeamento, 'r', encoding='utf-8') as f:
            self.dados = yaml.safe_load(f)
        
        self.metadata = self.dados.get('_metadata', {})
        self.aliases_tipo = self.metadata.get('aliases_tipo_aplicacao', {})
        self.aliases_cor = self.metadata.get('aliases_cores', {})
    
    def normalizar_tipo_aplicacao(self, tipo: str) -> str:
        """
        Normaliza nome do tipo de aplicação.
        
        Aceita variações como:
        - "1ª aplicação" → "1a_aplicacao"
        - "regular" → "1a_aplicacao"
        - "Reaplicação" → "reaplicacao"
        - "ENEM Digital" → "digital"
        
        Args:
            tipo: Nome do tipo (pode ter acentos, maiúsculas, etc.)
            
        Returns:
            Nome normalizado do tipo
        """
        tipo_lower = tipo.lower().strip()
        tipo_normalizado = tipo_lower.replace('ª', 'a').replace('ç', 'c').replace('ã', 'a').replace(' ', '_')
        
        # Buscar em aliases
        for tipo_padrao, aliases in self.aliases_tipo.items():
            if tipo_normalizado in aliases or tipo_normalizado == tipo_padrao:
                return tipo_padrao
        
        # Se não encontrou, retornar normalizado
        return tipo_normalizado
    
    def normalizar_cor(self, cor: str) -> str:
        """
        Normaliza nome da cor.
        
        Aceita variações como:
        - "Azul" → "azul"
        - "AMARELA" → "amarela"
        - "Blue" → "azul"
        
        Args:
            cor: Nome da cor
            
        Returns:
            Nome normalizado da cor
        """
        cor_lower = cor.lower().strip()
        
        # Buscar em aliases
        for cor_padrao, aliases in self.aliases_cor.items():
            if cor_lower in aliases or cor_lower == cor_padrao:
                return cor_padrao
        
        return cor_lower
    
    def normalizar_area(self, area: str) -> str:
        """
        Normaliza sigla da área.
        
        Aceita variações como:
        - "cn" → "CN"
        - "Matemática" → "MT"
        - "Ciências da Natureza" → "CN"
        
        Args:
            area: Sigla ou nome da área
            
        Returns:
            Sigla normalizada (MT, CN, CH, LC)
        """
        area_upper = area.upper().strip()
        
        # Se já é uma sigla válida
        if area_upper in ['MT', 'CN', 'CH', 'LC']:
            return area_upper
        
        # Mapear nomes completos
        mapa_nomes = {
            'MATEMATICA': 'MT',
            'MATEMÁTICA': 'MT',
            'MAT': 'MT',
            'CIENCIAS DA NATUREZA': 'CN',
            'CIÊNCIAS DA NATUREZA': 'CN',
            'NATUREZA': 'CN',
            'CIENCIAS HUMANAS': 'CH',
            'CIÊNCIAS HUMANAS': 'CH',
            'HUMANAS': 'CH',
            'LINGUAGENS': 'LC',
            'LINGUAGENS E CODIGOS': 'LC',
            'LINGUAGENS E CÓDIGOS': 'LC',
            'CÓDIGOS': 'LC',
        }
        
        return mapa_nomes.get(area_upper, area_upper)
    
    def obter_codigo(
        self,
        ano: int,
        area: str,
        tipo_aplicacao: str,
        cor: str,
        permitir_fallback: bool = True
    ) -> int:
        """
        Obtém código numérico da prova.
        
        Args:
            ano: Ano do ENEM (ex: 2021)
            area: Área da prova (MT, CN, CH, LC ou nome completo)
            tipo_aplicacao: Tipo (1a aplicacao, digital, reaplicacao, etc.)
            cor: Cor da prova (azul, rosa, etc.)
            permitir_fallback: Se True, tenta 1a aplicação como fallback
            
        Returns:
            Código numérico da prova
            
        Raises:
            KeyError: Se a combinação não for encontrada
            
        Exemplos:
            >>> mapeador = MapeadorProvas()
            >>> mapeador.obter_codigo(2021, "CN", "digital", "azul")
            1011
            >>> mapeador.obter_codigo(2021, "CN", "1ª aplicação", "ROSA")
            912
        """
        # Normalizar inputs
        area_norm = self.normalizar_area(area)
        tipo_norm = self.normalizar_tipo_aplicacao(tipo_aplicacao)
        cor_norm = self.normalizar_cor(cor)
        
        # Verificar se ano existe (pode estar como int ou str no YAML)
        ano_key = ano if ano in self.dados else str(ano)
        if ano_key not in self.dados:
            raise KeyError(
                f"Ano {ano} não encontrado no mapeamento. "
                f"Anos disponíveis: {self.listar_anos_disponiveis()}"
            )
        
        # Verificar se área existe
        if area_norm not in self.dados[ano_key]:
            raise KeyError(
                f"Área {area_norm} não encontrada para ano {ano}. "
                f"Áreas disponíveis: {list(self.dados[ano_key].keys())}"
            )
        
        dados_area = self.dados[ano_key][area_norm]
        
        # Tentar encontrar no tipo especificado
        if tipo_norm in dados_area:
            if cor_norm in dados_area[tipo_norm]:
                return dados_area[tipo_norm][cor_norm]
            else:
                cores_disponiveis = list(dados_area[tipo_norm].keys())
                raise KeyError(
                    f"Cor '{cor}' não encontrada para {area_norm} {ano} {tipo_aplicacao}. "
                    f"Cores disponíveis: {cores_disponiveis}"
                )
        
        # Fallback: tentar em 1a_aplicacao se permitido
        if permitir_fallback and tipo_norm != '1a_aplicacao' and '1a_aplicacao' in dados_area:
            if cor_norm in dados_area['1a_aplicacao']:
                return dados_area['1a_aplicacao'][cor_norm]
        
        tipos_disponiveis = [k for k in dados_area.keys() if k != 'especiais']
        raise KeyError(
            f"Tipo de aplicação '{tipo_aplicacao}' não encontrado para {area_norm} {ano}. "
            f"Tipos disponíveis: {tipos_disponiveis}"
        )

    
    def listar_anos_disponiveis(self) -> List[int]:
        """
        Lista todos os anos disponíveis no mapeamento.
        
        Returns:
            Lista de anos (ordenada)
        """
        anos = [int(k) for k in self.dados.keys() if not str(k).startswith('_')]
        return sorted(anos)
    
    def listar_tipos_disponiveis(self, ano: int, area: str) -> List[str]:
        """
        Lista tipos de aplicação disponíveis para ano/área.
        
        Args:
            ano: Ano do ENEM
            area: Área (MT, CN, CH, LC)
            
        Returns:
            Lista de tipos disponíveis
            
        Exemplo:
            >>> mapeador.listar_tipos_disponiveis(2021, "CN")
            ['1a_aplicacao', 'digital']
        """
        area_norm = self.normalizar_area(area)
        ano_key = ano if ano in self.dados else str(ano)
        
        if ano_key not in self.dados or area_norm not in self.dados[ano_key]:
            return []
        
        return [k for k in self.dados[ano_key][area_norm].keys() if k != 'especiais']
    
    def listar_cores_disponiveis(
        self, 
        ano: int, 
        area: str, 
        tipo_aplicacao: str
    ) -> List[str]:
        """
        Lista cores disponíveis para ano/área/tipo.
        
        Args:
            ano: Ano do ENEM
            area: Área (MT, CN, CH, LC)
            tipo_aplicacao: Tipo de aplicação
            
        Returns:
            Lista de cores disponíveis
            
        Exemplo:
            >>> mapeador.listar_cores_disponiveis(2021, "CN", "digital")
            ['azul', 'amarela', 'rosa', 'cinza']
        """
        area_norm = self.normalizar_area(area)
        tipo_norm = self.normalizar_tipo_aplicacao(tipo_aplicacao)
        ano_key = ano if ano in self.dados else str(ano)
        
        try:
            return list(self.dados[ano_key][area_norm][tipo_norm].keys())
        except KeyError:
            return []
    
    def obter_info_completa(
        self,
        ano: int,
        area: str,
        tipo_aplicacao: str,
        cor: str
    ) -> InfoProva:
        """
        Retorna informações completas da prova.
        
        Args:
            ano: Ano do ENEM
            area: Área
            tipo_aplicacao: Tipo de aplicação
            cor: Cor da prova
            
        Returns:
            Objeto InfoProva com todas as informações
        """
        codigo = self.obter_codigo(ano, area, tipo_aplicacao, cor)
        
        return InfoProva(
            codigo=codigo,
            ano=ano,
            area=self.normalizar_area(area),
            tipo_aplicacao=self.normalizar_tipo_aplicacao(tipo_aplicacao),
            cor=self.normalizar_cor(cor)
        )
    
    def descobrir_prova_por_codigo(self, codigo: int) -> Optional[InfoProva]:
        """
        Busca reversa: descobre informações da prova pelo código.
        
        Útil para validação ou debugging.
        
        Args:
            codigo: Código numérico da prova
            
        Returns:
            InfoProva se encontrado, None caso contrário
            
        Exemplo:
            >>> info = mapeador.descobrir_prova_por_codigo(1011)
            >>> print(f"{info.ano} {info.area} {info.tipo_aplicacao} {info.cor}")
            2021 CN digital azul
        """
        for ano_key, dados_ano in self.dados.items():
            if str(ano_key).startswith('_'):
                continue
            
            for area, dados_area in dados_ano.items():
                for tipo, cores in dados_area.items():
                    if tipo == 'especiais':
                        continue
                    
                    if not isinstance(cores, dict):
                        continue
                    
                    for cor, cod in cores.items():
                        if cod == codigo:
                            return InfoProva(
                                codigo=codigo,
                                ano=int(ano_key),
                                area=area,
                                tipo_aplicacao=tipo,
                                cor=cor
                            )
        
        return None
    
    def validar_mapeamento(self) -> List[str]:
        """
        Valida a estrutura do arquivo de mapeamento.
        
        Verifica:
        - Códigos duplicados
        - Estrutura correta
        - Tipos válidos
        
        Returns:
            Lista de avisos/erros encontrados (vazia se tudo OK)
        """
        avisos = []
        codigos_vistos = {}
        
        for ano_key, dados_ano in self.dados.items():
            if str(ano_key).startswith('_'):
                continue
            
            for area, dados_area in dados_ano.items():
                if area not in ['MT', 'CN', 'CH', 'LC']:
                    avisos.append(f"Área inválida: {area} em ano {ano_key}")
                    continue
                
                for tipo, cores in dados_area.items():
                    if not isinstance(cores, dict):
                        avisos.append(f"Estrutura inválida em {ano_key}/{area}/{tipo}")
                        continue
                    
                    for cor, codigo in cores.items():
                        # Verificar duplicatas
                        chave = f"{ano_key}-{area}-{tipo}-{cor}"
                        if codigo in codigos_vistos:
                            avisos.append(
                                f"Código {codigo} duplicado: "
                                f"{codigos_vistos[codigo]} e {chave}"
                            )
                        else:
                            codigos_vistos[codigo] = chave
        
        return avisos

    def listar_todas_provas(self, ano: int = None) -> List[InfoProva]:
        """
        Lista todas as provas cadastradas.
        
        Args:
            ano: Se especificado, filtra apenas provas deste ano.
                 Se None, retorna todas as provas de todos os anos.
            
        Returns:
            Lista de InfoProva com todas as provas
            
        Exemplo:
            >>> provas_2023 = mapeador.listar_todas_provas(2023)
            >>> for p in provas_2023:
            ...     print(f"{p.area} {p.tipo_aplicacao} {p.cor} = {p.codigo}")
        """
        provas = []
        
        for ano_key, dados_ano in self.dados.items():
            if str(ano_key).startswith('_'):
                continue
            
            ano_int = int(ano_key)
            if ano is not None and ano_int != ano:
                continue
            
            for area, dados_area in dados_ano.items():
                if area not in ['MT', 'CN', 'CH', 'LC']:
                    continue
                
                for tipo, cores in dados_area.items():
                    if tipo == 'especiais' or not isinstance(cores, dict):
                        continue
                    
                    for cor, codigo in cores.items():
                        provas.append(InfoProva(
                            codigo=codigo,
                            ano=ano_int,
                            area=area,
                            tipo_aplicacao=tipo,
                            cor=cor
                        ))
        
        return provas
    
    def listar_codigos_por_area(self, ano: int, area: str) -> List[int]:
        """
        Lista todos os códigos de prova de uma área em um ano.
        
        Args:
            ano: Ano do ENEM
            area: Área (MT, CN, CH, LC)
            
        Returns:
            Lista de códigos numéricos
        """
        area_norm = self.normalizar_area(area)
        codigos = []
        
        for prova in self.listar_todas_provas(ano):
            if prova.area == area_norm:
                codigos.append(prova.codigo)
        
        return codigos
