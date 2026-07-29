# Testes e Validação

Scripts para validar a precisão do cálculo TRI contra os microdados reais do ENEM.

## Início Rápido

```bash
# Pipeline completo (requer microdados brutos do INEP)
python tests/run_full_validation.py \
  --microdados-dir /caminho/para/MICRODADOS_ENEM

# Revalidar catálogo/holdout já publicados sem reler 47 GB
python tests/run_full_validation.py \
  --microdados-dir /caminho/para/MICRODADOS_ENEM \
  --somente-validar

# Catálogo v3 e holdout estratificado (fluxo de publicação)
python tools/recalibrar_validacao.py \
  --microdados-dir /caminho/para/MICRODADOS_ENEM

# Só testes unitários (sem microdados)
pytest tests/ -v
```

O `--microdados-dir` aceita tanto a estrutura do projeto (`YYYY/MICRODADOS_ENEM_YYYY.csv`)
quanto a estrutura de download do INEP (`microdados_enem_YYYY/DADOS/RESULTADOS_YYYY.csv`).

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `run_full_validation.py` | Pipeline canônico: itens, recalibração, holdout e pytest |
| `gerar_exemplos_microdados.py` | Extrai até N exemplos por CO_PROVA dos microdados brutos |
| `validar_exemplos_microdados.py` | Compara notas calculadas vs oficiais; MAE por prova e global |
| `gerar_provas_problematicas.py` | Gera relatório Markdown de provas com erro acima do limite |
| `validar_todos_anos.py` | Validação por amostragem estratificada (2009-2025, por faixa de nota) |
| `extrair_exemplos_completos.py` | Converte fixtures para formato de estudante completo (Streamlit) |
| `executar_testes_completos.py` | Testa o CalculadorEnem do app Streamlit com dados reais |
| `test_calculador.py` | Motor TRI: regressão (golden), coerência CLI × web e propriedades do modelo |
| `test_precisao.py` | Classificação de confiabilidade e invariantes dos avisos |
| `test_mapeador_provas.py` | Testes unitários do mapeamento de códigos de prova |
| `test_utils.py` | Testes unitários de `_utils.py` |
| `_utils.py` | Funções compartilhadas entre os scripts |
| `conftest.py` | Configuração pytest |

## Pré-requisitos

- Microdados brutos do INEP — arquivos originais por ano (para gerar exemplos)
- `src/tri_enem/data/itens/` — parâmetros de itens usados no cálculo e no wheel
- `microdados_limpos/` — amostras locais de participantes para ferramentas legadas
- `src/tri_enem/mapeamento_provas.yaml` — mapeamento de códigos

Os microdados brutos do INEP estão disponíveis em
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem>.

## Saídas

| Arquivo | Commitado | Descrição |
|---------|-----------|-----------|
| `fixtures/exemplos_microdados.json` | Sim | Exemplos extraídos dos microdados (10 por CO_PROVA) |
| `fixtures/validation_holdout.jsonl.gz` | Sim | Holdout estratificado sem identificadores pessoais |
| `fixtures/validation_manifest.json` | Sim | Origem, hashes, cobertura e versão da amostragem |
| `fixtures/golden_notas.json` | Sim | Valores de referência de nota e theta usados na regressão |
| `fixtures/codigos_presentes.json` | Sim | Cache legado de CO_PROVAs presentes nos dados de participantes |
| `../docs/VALIDATION_REPORT.md` | Sim | Relatório gerado do mesmo catálogo e manifesto do holdout |
| `provas_problematicas.md` | Não | Relatório transitório de provas com erro alto |

Os arquivos commitados em `fixtures/` permitem rodar `pytest` e consultar o
mapeamento de provas sem precisar dos microdados brutos do INEP.

## Pipeline Completo

O pipeline de publicação é `tools/recalibrar_validacao.py`. Ele substitui os
artefatos de forma atômica e deve ser seguido por:

```bash
python tests/validar_holdout.py
pytest -q
```

```text
tools/recalibrar_validacao.py
    ├─► src/tri_enem/coeficientes_data.json
    ├─► tests/fixtures/validation_holdout.jsonl.gz
    ├─► tests/fixtures/validation_manifest.json
    └─► docs/VALIDATION_REPORT.md
```

## Como o status em runtime é atualizado

A fonte única de verdade é a entrada de cada prova em
`src/tri_enem/coeficientes_data.json` (schema v3), lida por `precisao.py`.
Modelo, métricas e status são publicados juntos; não existe `status_provas`
paralelo. `tests/validar_holdout.py` recalcula as métricas sem modificar o
catálogo.

## Execução Individual

```bash
# Gerar exemplos (10 por prova)
python tests/gerar_exemplos_microdados.py \
  --microdados-dir /caminho/para/microdados_inep \
  --microdados-limpos microdados_limpos \
  --n-max 10

# Validar exemplos auxiliares (somente leitura no schema v3)
python tests/validar_exemplos_microdados.py \
  --exemplos tests/fixtures/exemplos_microdados.json

# Gerar relatório de provas problemáticas
python tests/gerar_provas_problematicas.py \
  --exemplos tests/fixtures/exemplos_microdados.json \
  --limite-dif 2.0

# Testes unitários
pytest tests/ -v

# Validação por amostragem (todos os anos, estratificada por faixa de nota)
python tests/validar_todos_anos.py

# Recalcular o holdout publicado
python tests/validar_holdout.py
```

## Resultados Esperados

| Métrica | Esperado |
|---------|----------|
| Prova `ok` | erro máximo individual ≤ 2 pontos |
| Cobertura | todas as provas mapeadas catalogadas |
| Integridade | nenhum caso pulado sem motivo explícito |
| Apresentação | confirmação positiva, perfil intermediário ou cautela forte |

O status de cada prova é derivado do maior erro absoluto do holdout e aparece
na própria entrada da prova no catálogo v3. O perfil intermediário descreve o
desempenho típico sem alterar o status estrito nem promover a prova a
`confiavel=True`.
