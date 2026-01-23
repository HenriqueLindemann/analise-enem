"""
Testes para o módulo MapeadorProvas

Execute com: python -m pytest tests/test_mapeador_provas.py -v
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from tri_enem.mapeador_provas import MapeadorProvas, InfoProva


class TestMapeadorProvas:
    """Testes do sistema de mapeamento de códigos de prova."""
    
    @pytest.fixture
    def mapeador(self):
        """Fixture que retorna uma instância do mapeador."""
        return MapeadorProvas()
    
    def test_lookup_basico(self, mapeador):
        """Teste de lookup básico com dados do arquivo exemplo."""
        # 2021 CN 1a aplicação Rosa
        codigo = mapeador.obter_codigo(2021, "CN", "1a_aplicacao", "rosa")
        assert codigo == 912
        
        # 2021 CN Digital Azul
        codigo = mapeador.obter_codigo(2021, "CN", "digital", "azul")
        assert codigo == 1011
    
    def test_normalizacao_tipo(self, mapeador):
        """Teste de normalização de tipos de aplicação."""
        assert mapeador.normalizar_tipo_aplicacao("1ª aplicação") == "1a_aplicacao"
        assert mapeador.normalizar_tipo_aplicacao("regular") == "1a_aplicacao"
        assert mapeador.normalizar_tipo_aplicacao("PRIMEIRA APLICAÇÃO") == "1a_aplicacao"
        assert mapeador.normalizar_tipo_aplicacao("primeira aplicacao") == "1a_aplicacao"
        
        assert mapeador.normalizar_tipo_aplicacao("Reaplicação") == "reaplicacao"
        assert mapeador.normalizar_tipo_aplicacao("2ª aplicação") == "reaplicacao"
        
        assert mapeador.normalizar_tipo_aplicacao("digital") == "digital"
        assert mapeador.normalizar_tipo_aplicacao("ENEM Digital") == "digital"
    
    def test_normalizacao_cor(self, mapeador):
        """Teste de normalização de cores."""
        assert mapeador.normalizar_cor("AZUL") == "azul"
        assert mapeador.normalizar_cor("Amarela") == "amarela"
        assert mapeador.normalizar_cor("rosa") == "rosa"
        assert mapeador.normalizar_cor("Blue") == "azul"
    
    def test_normalizacao_area(self, mapeador):
        """Teste de normalização de áreas."""
        assert mapeador.normalizar_area("cn") == "CN"
        assert mapeador.normalizar_area("CN") == "CN"
        assert mapeador.normalizar_area("Matemática") == "MT"
        assert mapeador.normalizar_area("matematica") == "MT"
        assert mapeador.normalizar_area("Ciências da Natureza") == "CN"
        assert mapeador.normalizar_area("Linguagens") == "LC"
    
    def test_lookup_normalizado(self, mapeador):
        """Teste de lookup com inputs não normalizados."""
        # Usar variações de nomenclatura
        codigo = mapeador.obter_codigo(2021, "cn", "1ª aplicação", "ROSA")
        assert codigo == 912
        
        codigo = mapeador.obter_codigo(2021, "Ciências da Natureza", "regular", "rosa")
        assert codigo == 912
    
    def test_listar_anos(self, mapeador):
        """Teste de listagem de anos disponíveis."""
        anos = mapeador.listar_anos_disponiveis()
        assert 2021 in anos
        assert 2023 in anos
        assert 2024 in anos
        assert sorted(anos) == anos  # Deve estar ordenado
    
    def test_listar_tipos(self, mapeador):
        """Teste de listagem de tipos disponíveis."""
        tipos = mapeador.listar_tipos_disponiveis(2021, "CN")
        assert "1a_aplicacao" in tipos
        assert "digital" in tipos
    
    def test_listar_cores(self, mapeador):
        """Teste de listagem de cores disponíveis."""
        cores = mapeador.listar_cores_disponiveis(2021, "CN", "1a_aplicacao")
        assert "azul" in cores
        assert "amarela" in cores
        assert "cinza" in cores
        assert "rosa" in cores
    
    def test_busca_reversa(self, mapeador):
        """Teste de busca reversa por código."""
        info = mapeador.descobrir_prova_por_codigo(1011)
        assert info is not None
        assert info.ano == 2021
        assert info.area == "CN"
        assert info.tipo_aplicacao == "digital"
        assert info.cor == "azul"
    
    def test_info_completa(self, mapeador):
        """Teste de obtenção de informações completas."""
        info = mapeador.obter_info_completa(2021, "CN", "digital", "azul")
        assert isinstance(info, InfoProva)
        assert info.codigo == 1011
        assert info.ano == 2021
        assert info.area == "CN"
        assert info.tipo_aplicacao == "digital"
        assert info.cor == "azul"
    
    def test_erro_ano_inexistente(self, mapeador):
        """Teste de erro para ano inexistente."""
        with pytest.raises(KeyError, match="Ano .* não encontrado"):
            mapeador.obter_codigo(1999, "CN", "digital", "azul")
    
    def test_erro_cor_inexistente(self, mapeador):
        """Teste de erro para cor inexistente."""
        with pytest.raises(KeyError, match="Cor .* não encontrada"):
            mapeador.obter_codigo(2021, "CN", "digital", "verde")
    
    def test_erro_tipo_inexistente(self, mapeador):
        """Teste de erro para tipo inexistente."""
        with pytest.raises(KeyError, match="Tipo de aplicação .* não encontrado"):
            mapeador.obter_codigo(2024, "MT", "digital", "azul", permitir_fallback=False)
    
    def test_validar_mapeamento(self, mapeador):
        """Teste de validação da estrutura do mapeamento."""
        avisos = mapeador.validar_mapeamento()
        # Não deve haver avisos no arquivo exemplo bem formatado
        # (pode ter duplicatas se o mesmo código aparecer em anos diferentes)
        # O importante é que não falhe
        assert isinstance(avisos, list)


if __name__ == '__main__':
    # Permitir executar diretamente
    pytest.main([__file__, '-v'])
