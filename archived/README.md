# Arquivos Arquivados

Esta pasta contem analises que dependem dos microdados completos do INEP.

Eles podem ser úteis como referência, mas requerem os microdados para funcionar.

## Conteúdo

| Arquivo | Descrição |
|---------|-----------|
| `analise_participante.py` | Busca participante nos microdados e calcula percentis |
| `analise_tri_final.py` | Análise TRI com gráficos de dificuldade |
| `visualizacoes_analise.py` | Geração de histogramas, boxplots, radar charts |

## Requisitos

- Microdados completos do INEP (~1.5GB por ano)
- matplotlib, seaborn (além das dependências padrão)

## Como usar

Estes scripts foram desenvolvidos para o ENEM 2021. Para usá-los:

1. Baixe os microdados do INEP
2. Coloque em `DADOS/MICRODADOS_ENEM_2021.csv`
3. Ajuste os caminhos nos scripts
