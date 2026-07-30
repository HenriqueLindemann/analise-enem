# Exemplos de Uso

Exemplos práticos de como usar o módulo TRI ENEM.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `calcular_nota.py` | Cálculo básico de nota + análise de erros |
| `analise_completa_2024.py` | Exemplo de análise detalhada |

## Uso

Instale o projeto em modo editável e execute os exemplos a partir da raiz:

```bash
python -m pip install -e .
python examples/calcular_nota.py
```

Ou use diretamente o `meu_simulado.py` na raiz (mais fácil!):

```bash
python meu_simulado.py
```

## Exemplo Rápido

```python
from tri_enem import MapeadorProvas, CalculadorTRI

# Inicializar
mapeador = MapeadorProvas()
calc = CalculadorTRI()

# Obter código da prova pela cor
co_prova = mapeador.obter_codigo(2023, 'MT', '1a_aplicacao', 'azul')

# Calcular nota
respostas = 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE'
resultado = calc.calcular_nota(2023, 'MT', co_prova, respostas)

print(f"Nota: {resultado['nota']:.1f}")
```

Ao usar `SimuladorNota`, identifique a prova com `co_prova` ou com a combinação
`cor_prova` + `tipo_aplicacao`. Para LC, informe também `lingua="ingles"` ou
`lingua="espanhol"`.
