# Método de cálculo e validação

O pacote `tri_enem` calcula a nota de uma prova do ENEM (2009–2025) a partir
das respostas e da identificação da prova. API, terminal, Streamlit e PDF usam
o mesmo catálogo, `src/tri_enem/coeficientes_data.json`. Os números por prova
estão em [VALIDATION_REPORT.md](VALIDATION_REPORT.md).

## Modelo

```text
P(acerto | θ) = c + (1 − c) / (1 + exp(−a · (θ − b)))
```

- Parâmetros `a`, `b` e `c` dos arquivos `ITENS_PROVA_<ano>.csv` do INEP, sem
  alteração (`src/tri_enem/data/itens/`).
- θ estimado por EAP com prior normal, numa grade de 40 pontos equiespaçados
  em [−4, 4].
- Escala fixa por área, `nota = slope · θ + intercept` (`metadata.escala`),
  ajustada uma vez com 329.020 participantes sorteados. Não há ajuste por prova.
- Itens anulados ficam fora da verossimilhança.
- Quem acerta todos os itens com gabarito A–E recebe a nota oficial desse
  padrão (`nota_gabarito`), quando o INEP atribui a ele a nota de outro caderno.

## Reconstrução dos itens

Em 52 provas, a leitura direta dos CSVs não reproduz as notas oficiais. O
catálogo registra a correção (`reconstrucao_itens`): associação entre curva e
posição, gabarito e itens excluídos. Quase sempre são curvas publicadas
reaproveitadas. Parâmetros ou gabaritos estimados pelo projeto são marcados
como tal. Em 2013/MT/190 (adaptada), um item reestimado levou a diferença
média na amostra de teste de 0,313 para 0,110 ponto.

`CalculadorTRI(reconstrucoes={})` calcula com a leitura direta, para pesquisa.

## Validação

`tools/levantar_censo.py` compara a nota calculada com a oficial de todos os
participantes válidos dos microdados. O resultado (`censo` no catálogo) é a
fonte do que a interface exibe e do status de cada prova.

| Status | Critério |
|---|---|
| `ok` | menos de 5 participantes a mais de 2 pontos |
| `erro_raro` | 5 ou mais participantes a mais de 2 pontos |
| `nao_calibrado` | amostra de teste com menos de 30 participantes ou sem todas as faixas de nota |
| `sem_participantes` | nenhum participante válido |
| `sem_itens` | parâmetros dos itens indisponíveis |

Um ou dois casos isolados, com dezenas ou centenas de pontos de diferença, são
registros corrompidos e não rebaixam a prova. Uma prova `nao_calibrado`
continua assim mesmo com o censo.

Uma amostra de teste com 221.059 participantes, fora de todo ajuste, confirma
o resultado de forma independente. Os validadores em `tests/` recalculam essas
amostras e conferem hashes e métricas.

Registros com respostas de outra prova (CN e CH trocadas, código de prova ou
idioma errado) ficam fora das contas. A evidência de cada um está em
`tests/fixtures/registros_inconsistentes.json` e é reconferida com o motor.

## Limites conhecidos

- **2011:** o INEP anulou itens só para um grupo de participantes, e a API não
  sabe a qual grupo cada um pertence. As 16 provas são `erro_raro`. A
  proporção de casos acima de 2 pontos fica entre 1 em 510 e 1 em 7.000.
- **2012:** cinco provas `erro_raro`. A pior é MT/150, com 682 de 1.013.485
  participantes acima de 2 pontos. As especiais CN/153 e CH/154 têm 233
  participantes, 5 e 7 deles acima de 2 pontos.
- **2010/MT/97:** 761 de 840.825 participantes acima de 2 pontos.
- **2009, provas 81–84** e **2020, ampliadas e superampliadas:** sem
  parâmetros de itens. A API não calcula a nota.

## Reprodução

O fluxo está em [tools/README.md](../tools/README.md), e a verificação offline
em [tests/README.md](../tests/README.md).
