# Exemplos de Uso

Exemplos práticos de como usar o módulo TRI ENEM.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `calcular_nota.py` | Cálculo básico de nota + análise de erros |
| `analise_completa_2024.py` | Análise completa com geração de PDF |

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

from tri_enem import MapeadorProvas, CalculadorTRI

# Inicializar
mapeador = MapeadorProvas()
calc = CalculadorTRI()

# Obter código da prova pela cor
co_prova = mapeador.obter_codigo(2023, 'MT', '1a_aplicacao', 'azul')

# Calcular nota
respostas = 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE'
resultado = calc.calcular_nota_tri(2023, 'MT', co_prova, respostas)

print(f"Nota: {resultado:.1f}")
```
