# Testes e Validação

Scripts para validar a precisão do cálculo TRI contra os microdados reais do ENEM.

## Início Rápido

```bash
# Pipeline completo (requer microdados brutos do INEP)
python tests/run_full_validation.py \
  --microdados-dir /caminho/para/microdados \
  --microdados-limpos microdados_limpos

# Pular geração se os exemplos já existem
python tests/run_full_validation.py --skip-gerar

# Também atualiza o status em coeficientes_data.json (requer ≥3 exemplos por prova)
python tests/run_full_validation.py --atualizar-status

# Só testes unitários (sem microdados)
pytest tests/ -v
```

O `--microdados-dir` aceita tanto a estrutura do projeto (`YYYY/MICRODADOS_ENEM_YYYY.csv`)
quanto a estrutura de download do INEP (`microdados_enem_YYYY/DADOS/RESULTADOS_YYYY.csv`).

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `run_full_validation.py` | Pipeline completo de validação (orquestra os 3 passos abaixo) |
| `gerar_exemplos_microdados.py` | Extrai até N exemplos por CO_PROVA dos microdados brutos |
| `validar_exemplos_microdados.py` | Compara notas calculadas vs oficiais; MAE por prova e global |
| `gerar_provas_problematicas.py` | Gera relatório Markdown de provas com erro acima do limite |
| `validar_todos_anos.py` | Validação por amostragem estratificada (2009-2025, por faixa de nota) |
| `extrair_exemplos_completos.py` | Converte fixtures para formato de estudante completo (Streamlit) |
| `executar_testes_completos.py` | Testa o CalculadorEnem do app Streamlit com dados reais |
| `test_mapeador_provas.py` | Testes unitários do mapeamento de códigos de prova |
| `test_utils.py` | Testes unitários de `_utils.py` |
| `_utils.py` | Funções compartilhadas entre os scripts |
| `conftest.py` | Configuração pytest |

## Pré-requisitos

- Microdados brutos do INEP — arquivos originais por ano (para gerar exemplos)
- `microdados_limpos/` — dados processados por ano (para cálculo TRI)
- `src/tri_enem/mapeamento_provas.yaml` — mapeamento de códigos

Os microdados brutos do INEP estão disponíveis em
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem>.

## Saídas

| Arquivo | Commitado | Descrição |
|---------|-----------|-----------|
| `fixtures/exemplos_microdados.json` | Sim | Exemplos extraídos dos microdados (10 por CO_PROVA) |
| `fixtures/codigos_presentes.json` | Sim | Cache de CO_PROVAs encontrados nos microdados_limpos |
| `fixtures/provas_validacao.md` | Sim | Índice legível de todas as provas (nome + status + MAE) |
| `fixtures/gerar_provas_validacao.py` | Sim | Script que regera `provas_validacao.md` |
| `provas_problematicas.md` | Não | Relatório transitório de provas com erro alto |

Os arquivos commitados em `fixtures/` permitem rodar `pytest` e consultar o
mapeamento de provas sem precisar dos microdados brutos do INEP.

## Pipeline Completo

```
run_full_validation.py
    │
    ├─► gerar_exemplos_microdados.py  ──► fixtures/exemplos_microdados.json
    │        (até 10 exemplos por CO_PROVA; suporta estruturas de download do INEP)
    │
    ├─► validar_exemplos_microdados.py ──► MAE global + MAE por prova no console
    │        (--atualizar-status → atualiza coeficientes_data.json quando diverge)
    │
    └─► gerar_provas_problematicas.py ──► provas_problematicas.md
```

## Como o status em runtime é atualizado

A fonte única de verdade é `src/tri_enem/coeficientes_data.json`, lido por `precisao.py`:

```
tools/calibrar_com_mapeamento.py  → coeficientes_data.json (por_prova + status_provas)
                                         ↑
tests/validar_exemplos_microdados.py  (--atualizar-status, quando validação diverge)
```

## Execução Individual

```bash
# Gerar exemplos (10 por prova)
python tests/gerar_exemplos_microdados.py \
  --microdados-dir /caminho/para/microdados_inep \
  --microdados-limpos microdados_limpos \
  --n-max 10

# Validar e atualizar status
python tests/validar_exemplos_microdados.py \
  --exemplos tests/fixtures/exemplos_microdados.json \
  --atualizar-status

# Gerar relatório de provas problemáticas
python tests/gerar_provas_problematicas.py \
  --exemplos tests/fixtures/exemplos_microdados.json \
  --limite-dif 2.0

# Testes unitários
pytest tests/ -v

# Validação por amostragem (todos os anos, estratificada por faixa de nota)
python tests/validar_todos_anos.py

# Regenerar índice de provas (após novo ciclo de validação)
python tests/fixtures/gerar_provas_validacao.py
```

## Resultados Esperados

| Métrica | Esperado |
|---------|----------|
| MAE global | < 1 ponto |
| R² por prova calibrada | > 0.999 |

Provas da 1ª aplicação (2018+) têm maior precisão. Provas especiais (PPL, Libras,
provas digitais LC 2020) podem ter erros maiores e estão marcadas em `status_provas`.
