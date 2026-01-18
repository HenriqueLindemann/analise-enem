# Relatórios Gerados

Esta pasta contém os relatórios PDF gerados pelo `meu_simulado.py`.

## Como gerar um relatório

1. Edite `meu_simulado.py` com suas respostas
2. Defina `GERAR_PDF = True`
3. Execute: `python meu_simulado.py`
4. O PDF será salvo aqui com nome automático

## Estrutura do relatório

O PDF contém:
- **Resumo das Notas**: tabela com nota, acertos e percentual de cada área
- **Detalhes por Área**: para cada área (MT, CN, CH, LC):
  - Lista de erros ordenada por impacto (quanto ganharia se acertasse)
  - Lista de acertos ordenada por contribuição (quanto perderia se errasse)
  - Parâmetro de dificuldade (b) de cada questão
