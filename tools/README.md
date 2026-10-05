# Ferramentas de desenvolvimento

Os scripts desta pasta preparam dados e pesquisam a calibração; a API e a
interface usam somente o catálogo incluído no pacote. O
[método](../docs/SCORE_RECALCULATION.md) descreve o modelo, a evidência e os
limites conhecidos.

Instale as dependências de desenvolvimento (inclui SciPy). Os microdados
originais são apenas lidos. Defina `OPENBLAS_NUM_THREADS=1` ao usar
`--workers`, para não multiplicar threads entre processos.

## Itens e recalibração

O gerador de itens exige 2009–2025, valida os dados e publica os CSVs
normalizados com um manifesto SHA-256:

```bash
python tools/gerar_dados_itens.py --microdados-dir /caminho/MICRODADOS_ENEM
```

Para reajustar as escalas mantendo as reconstruções e âncoras do catálogo:

```bash
OPENBLAS_NUM_THREADS=1 python tools/recalibrar_validacao.py \
  --microdados-dir /caminho/MICRODADOS_ENEM --workers 3
```

O comando cobre as provas mapeadas, separa treino, seleção e holdout,
escolhe pelo MAE ponderado e só publica catálogo, fixture primária, manifesto
e `docs/VALIDATION_REPORT.md` depois de validar as invariantes.
`--nao-publicar` permite inspecionar os candidatos.

Para pesquisar também associações de itens, gabaritos e quadratura:

```bash
OPENBLAS_NUM_THREADS=1 python tools/fechar_gap_validacao.py \
  --microdados-dir /caminho/MICRODADOS_ENEM --workers 3 --nao-publicar
```

Depois de mudar modelos, regenere `tests/fixtures/golden_notas.json` e
reavalie as confirmações (veja [tests/README.md](../tests/README.md)).
Atualizar apenas hashes não valida um cálculo novo.

## Mudanças de modelo

Um modelo novo é escolhido em treino/seleção e congelado antes de ser
avaliado. A confirmação usa casos novos, amostrados depois de excluir todos
os anteriores (`amostrar_microdados(..., excluir_case_ids=...)`); uma amostra
já examinada é apenas exploratória. Ao incorporar, as métricas são
recalculadas nos mesmos casos, sem reajuste, e a nova fixture passa a ser
conferida por um validador em `tests/`.

`gerar_imagem_readme.py` gera a imagem de exemplo do README.

Caches e resultados de pesquisa ficam em `resultados/investigacao/`, ignorado
pelo Git. A documentação versionada fica restrita ao método e ao relatório
gerado.
