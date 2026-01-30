# Testes e Validação

Scripts para validar a precisão do cálculo TRI contra os microdados reais do ENEM.

## Início Rápido

```bash
# Validação completa (gera exemplos + valida + relatório)
python tests/run_full_validation.py

# Pular geração se já tiver exemplos
python tests/run_full_validation.py --skip-gerar
```

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `run_full_validation.py` | Pipeline completo de validação |
| `gerar_exemplos_microdados.py` | Extrai exemplos (respostas + notas) dos microdados |
| `validar_exemplos_microdados.py` | Compara notas calculadas vs oficiais |
| `gerar_provas_problematicas.py` | Identifica provas com erros acima do limite |
| `validar_todos_anos.py` | Validação por amostragem 2009-2024 |
| `validar_completo.py` | Validação detalhada por área/ano |
| `test_mapeador_provas.py` | Testes unitários do mapeamento |
| `test_utils.py` | Testes das funções utilitárias |
| `_utils.py` | Funções compartilhadas |
| `conftest.py` | Configuração pytest |

## Pré-requisitos

- `microdados/` - Arquivos originais por ano
- `microdados_limpos/` - Dados processados por ano
- `src/tri_enem/mapeamento_provas.yaml` - Mapeamento de códigos

## Saídas

- `fixtures/exemplos_microdados.json` - Exemplos extraídos
- `fixtures/codigos_presentes.json` - Cache de códigos
- `provas_problematicas.md` - Relatório de erros

## Execução Individual

```bash
# Gerar exemplos
python tests/gerar_exemplos_microdados.py \
  --microdados-dir microdados \
  --microdados-limpos microdados_limpos

# Validar
python tests/validar_exemplos_microdados.py \
  --exemplos tests/fixtures/exemplos_microdados.json

# Gerar relatório
python tests/gerar_provas_problematicas.py \
  --exemplos tests/fixtures/exemplos_microdados.json \
  --limite-dif 2.0

# Testes unitários
pytest tests/ -v
```

## Resultados Esperados

| Métrica | Esperado |
|---------|----------|
| MAE | < 1 ponto |
| R² | > 0.999 |

Provas da 1ª aplicação (2018+) têm maior precisão. Provas especiais (PPL, Libras) podem ter calibrações diferentes.
