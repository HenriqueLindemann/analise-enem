# Ferramentas de Desenvolvimento

Scripts para manutenção e calibração do módulo.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `amostrar_microdados_brutos.py` | Reduz cada ano do INEP a uma amostra por prova, própria para calibrar |
| `calibrar_com_mapeamento.py` | Calibra coeficientes usando mapeamento YAML |
| `limpar_microdados.py` | Reduz CSVs do INEP para apenas colunas essenciais |
| `calibrar_todos_anos.py` | Recalibra coeficientes para todos os anos |

## Uso

Estes scripts requerem os microdados do INEP. Execute da raiz do projeto:

```bash
# Amostrar os brutos: ~50 GB -> ~150 MB, cerca de 1500 participantes por prova
python tools/amostrar_microdados_brutos.py --brutos <dir com microdados_enem_YYYY/>

# Recalibrar todas as provas a partir das amostras
python tools/calibrar_com_mapeamento.py

# Ou apenas um ano
python tools/calibrar_com_mapeamento.py 2023
```

Prefira a amostragem. `limpar_microdados.py` preserva todos os participantes e
produz dezenas de GB; a calibração satura com algumas centenas por prova, já que
a relação θ → nota tem R² acima de 0,9999.

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
1. Carrega a amostra do ano (`microdados_limpos/<ano>/AMOSTRA_CALIBRACAO_<ano>.csv`)
2. Para cada prova, calcula θ pelo mesmo ponto de entrada do cálculo entregue ao
   usuário (`CalculadorTRI._preparar_calculo`)
3. Ajusta regressão linear: `nota = slope × θ + intercept`
4. Salva coeficientes e métricas de qualidade em `coeficientes_data.json`

O passo 2 importa: calibrar por outro caminho faria o coeficiente absorver
defeitos de pareamento, escondendo o erro dentro dos coeficientes.
