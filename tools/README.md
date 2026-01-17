# Ferramentas de Desenvolvimento

Scripts para manutencao e calibracao do modulo.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `limpar_microdados.py` | Reduz CSVs do INEP para apenas colunas essenciais |
| `calibrar_todos_anos.py` | Recalibra coeficientes para todos os anos |

## Uso

Estes scripts requerem os microdados do INEP. Execute da raiz do projeto:

```bash
# Limpar microdados (reduz de ~1.5GB para ~100MB)
python tools/limpar_microdados.py

# Recalibrar coeficientes
python tools/calibrar_todos_anos.py
```

## Microdados

Baixe em: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

Estrutura esperada:
```
microdados/
├── 2023/
│   ├── MICRODADOS_ENEM_2023.csv
│   └── ITENS_PROVA_2023.csv
└── ...
```
