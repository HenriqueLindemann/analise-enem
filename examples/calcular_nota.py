"""
Exemplo de uso do módulo TRI ENEM

Execute a partir da raiz do projeto:
    python examples/calcular_nota.py
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import CalculadorTRI

# Inicializar calculador (usa microdados_limpos por padrão)
calc = CalculadorTRI()

# Exemplo: calcular nota de Matemática 2023
ano = 2023
area = 'MT'
prova = 1211
respostas = "CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE"

# Calcular
resultado = calc.calcular_nota(ano, area, prova, respostas)

print("=" * 50)
print(f"RESULTADO - {area} {ano}")
print("=" * 50)
print(f"Acertos: {resultado['acertos']}/{resultado['total_itens']}")
print(f"Theta (escala 0,1): {resultado['theta']:.5f}")
print(f"NOTA: {resultado['nota']:.1f}")
print()

# Análise de impacto dos erros
print("Top 5 erros com maior impacto:")
impactos = calc.analisar_impacto_erros(ano, area, prova, respostas)
for i, imp in enumerate(impactos[:5], 1):
    print(f"  {i}. Q{imp['posicao']}: +{imp['ganho_potencial']:.1f} pts se acertasse")
