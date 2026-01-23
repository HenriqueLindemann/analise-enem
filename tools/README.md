# Ferramentas de Desenvolvimento

Scripts para manutenção e calibração do módulo.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `limpar_microdados.py` | Reduz CSVs do INEP para apenas colunas essenciais |
| `calibrar_com_mapeamento.py` | Calibra coeficientes usando mapeamento YAML |
| `calibrar_todos_anos.py` | Recalibra coeficientes para todos os anos |

## Uso

Estes scripts requerem os microdados do INEP. Execute da raiz do projeto:

```bash
# Limpar microdados (reduz de ~1.5GB para ~100MB)
python tools/limpar_microdados.py

# Calibrar um ano específico usando mapeamento
python tools/calibrar_com_mapeamento.py

# Recalibrar todos os anos
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

## Calibração

O processo de calibração:
1. Carrega microdados limpos
2. Para cada prova, calcula θ (habilidade) usando ML3P
3. Ajusta regressão linear: `nota = slope × θ + intercept`
4. Salva coeficientes e métricas de qualidade em `coeficientes_data.json`
