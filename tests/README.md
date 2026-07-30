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

# Catálogo v3 e holdout estratificado (publica artefatos)
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
| `validar_holdout.py` | Recalcula o holdout e confere catálogo, manifesto e relatório |
| `test_calculador.py` | Motor TRI: regressão (golden), coerência CLI × web e propriedades do modelo |
| `test_calibracao.py` | Ajuste monotônico, amostragem estratificada e geração do relatório |
| `test_e2e_usuario.py` | Coerência ponta a ponta das três interfaces em 2009-2025 |
| `test_streamlit_interface.py` | App Streamlit, gráficos, entrada e PDF |
| `test_itens_empacotados.py` | Integridade dos 17 CSVs incluídos no pacote |
| `test_precisao.py` | Classificação de confiabilidade e invariantes dos avisos |
| `test_mapeador_provas.py` | Testes unitários do mapeamento de códigos de prova |
| `test_simulador.py` | Seleção explícita da prova na interface simplificada |
| `test_validadores_cli.py` | Códigos de saída e falha fechada dos validadores |
| `test_utils.py` | Testes unitários de `_utils.py` |
| `smoke_instalacao.py` | Testa o wheel instalado fora do repositório |
| `_utils.py` | Funções compartilhadas entre os scripts |
| `conftest.py` | Configuração pytest |

## Pré-requisitos

- Microdados brutos do INEP — arquivos originais por ano (para gerar exemplos)
- `src/tri_enem/data/itens/` — parâmetros de itens usados no cálculo e no wheel
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
| `../docs/VALIDATION_REPORT.md` | Sim | Relatório gerado do mesmo catálogo e manifesto do holdout |

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
Modelo, métricas e status são publicados juntos.
`tests/validar_holdout.py` recalcula as métricas sem modificar o catálogo.

## Execução Individual

```bash
# Gerar exemplos (10 por prova)
python tests/gerar_exemplos_microdados.py \
  --microdados-dir /caminho/para/microdados_inep \
  --n-max 10

# Validar exemplos auxiliares (somente leitura no schema v3)
python tests/validar_exemplos_microdados.py \
  --exemplos tests/fixtures/exemplos_microdados.json

# Testes unitários
pytest tests/ -v

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
