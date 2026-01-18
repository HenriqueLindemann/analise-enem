# Exemplos de Uso

Exemplos práticos de como usar o módulo TRI ENEM.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `calcular_nota.py` | Cálculo básico de nota + análise de erros |
| `analise_completa_2024.py` | Análise completa com geração de PDF |
| `calibrar_ano.py` | Como calibrar coeficientes para um novo ano |

## Uso

Execute da raiz do projeto:

```bash
python examples/calcular_nota.py
```

Ou use diretamente o `meu_simulado.py` na raiz (mais fácil!):

```bash
python meu_simulado.py
```

## Exemplo Rápido

```python
import sys
sys.path.insert(0, 'src')

from tri_enem import SimuladorNota

sim = SimuladorNota()

# Matemática 2023 - Prova Azul (código 1211)
resultado = sim.calcular('MT', 2023, 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE', co_prova=1211)

print(f"Nota: {resultado.nota:.1f}")
print(f"Acertos: {resultado.acertos}/{resultado.total_itens}")
```

## Códigos de Prova

**IMPORTANTE**: Consulte `docs/GUIA_PROVAS.md` para encontrar o código correto da sua prova!
