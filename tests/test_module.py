"""
Teste rápido do módulo tri_enem

Execute a partir da raiz do projeto:
    python tests/test_module.py
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import CalculadorTRI

c = CalculadorTRI('microdados_limpos')
r = c.calcular_nota(2023, 'MT', 1211, 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE')
print(f"Teste OK: nota={r['nota']:.1f}, acertos={r['acertos']}")
