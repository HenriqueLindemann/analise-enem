# Exemplos de Uso

Exemplos praticos de como usar o modulo TRI ENEM.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `calcular_nota.py` | Cálculo básico de nota + análise de erros |
| `calibrar_ano.py` | Como calibrar coeficientes para um novo ano |

## Uso

Execute da raiz do projeto:

```bash
python examples/calcular_nota.py
```

## Exemplo Rápido

```python
import sys
sys.path.insert(0, 'src')

from tri_enem import SimuladorNota

sim = SimuladorNota()

# Matemática 2023
resultado = sim.calcular('MT', 2023, 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE')

print(f"Nota: {resultado.nota:.1f}")
print(f"Acertos: {resultado.acertos}/{resultado.total_itens}")
```
