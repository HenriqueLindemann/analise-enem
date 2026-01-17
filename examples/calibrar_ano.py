"""
Exemplo: Calibrar coeficientes para um novo ano

Execute a partir da raiz do projeto:
    python examples/calibrar_ano.py

NOTA: Requer microdados_limpos/ com os dados do INEP
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import Calibrador

# Inicializar calibrador (usa microdados_limpos por padrão)
cal = Calibrador()

# Calibrar uma área
print("Calibrando Matemática 2023...")
resultado = cal.calibrar_area(2023, 'MT', n_amostras=300)

print(f"\nCoeficientes descobertos:")
print(f"  nota = {resultado['slope']:.4f} × θ + {resultado['intercept']:.2f}")
print(f"  R² = {resultado['r_squared']:.6f}")
print(f"  MAE = {resultado['mae']:.2f} pontos")

# Calibrar todas as áreas
print("\n" + "=" * 50)
print("Calibrando todas as áreas...")
resultados = cal.calibrar_todas_areas(2023, n_amostras=200)

print("\n" + "=" * 50)
print("Código para adicionar ao calculador:")
print(cal.gerar_codigo_coeficientes(resultados))
