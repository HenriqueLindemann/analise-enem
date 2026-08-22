# Exemplos de Uso

Exemplos práticos de uso do pacote `tri_enem` via código Python.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| [`calcular_nota.py`](calcular_nota.py) | Cálculo básico de nota e impacto de erros |
| [`analise_completa_2024.py`](analise_completa_2024.py) | Análise detalhada das 4 áreas com dados reais de 2024 |

## Como Executar

Instale o pacote em modo de desenvolvimento a partir da raiz do repositório:

```bash
pip install -e .
python examples/calcular_nota.py
```

> **Dica:** Para simular respostas preenchendo um gabarito completo, use diretamente [`meu_simulado.py`](../meu_simulado.py).

## Exemplo Rápido

```python
from tri_enem import CalculadorTRI, MapeadorProvas

mapeador = MapeadorProvas()
calc = CalculadorTRI()

# 1. Obter código da prova pela cor
co_prova = mapeador.obter_codigo(2023, 'MT', '1a_aplicacao', 'azul')

# 2. Calcular nota
respostas = 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE'
resultado = calc.calcular_nota(2023, 'MT', co_prova, respostas)

print(f"Nota: {resultado['nota']:.1f}")
```

Ao usar a classe de alto nível `SimuladorNota`, você pode passar diretamente `cor_prova='azul'` e `tipo_aplicacao='1a_aplicacao'` (para LC, passe também `lingua='ingles'` ou `lingua='espanhol'`).
