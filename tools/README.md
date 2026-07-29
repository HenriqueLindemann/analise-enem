# Ferramentas de desenvolvimento

## Fonte dos itens de prova

Os parâmetros versionados têm uma única localização:

```text
src/tri_enem/data/itens/<ano>/ITENS_PROVA_<ano>.csv
```

O gerador reproduzível lê diretamente a estrutura oficial extraída do INEP:

```bash
python tools/gerar_dados_itens.py \
  --microdados-dir /caminho/MICRODADOS_ENEM
```

Ele exige os 17 anos, valida colunas e áreas, normaliza os CSVs para UTF-8 com
separador `;` e publica tudo somente após validar o conjunto completo. O
`manifest.json` gerado registra caminho relativo, contagens e hashes SHA-256
da fonte e da saída. `tools/limpar_microdados.py` delega essa etapa ao mesmo
gerador; os participantes reduzidos continuam locais em `microdados_limpos/`
e não entram no pacote.

Para também criar esses extratos locais de participantes:

```bash
python tools/limpar_microdados.py \
  --microdados-dir /caminho/MICRODADOS_ENEM
```

O script reconhece os mesmos layouts oficiais, exige as colunas essenciais e
substitui cada extrato somente depois de terminar a escrita do respectivo ano.

## Recalibração oficial

O fluxo v4 recomendado lê diretamente a estrutura de download do INEP:

```bash
python tools/recalibrar_validacao.py \
  --microdados-dir /caminho/MICRODADOS_ENEM \
  --workers 3
```

Ele:

1. cobre cada prova mapeada e cada idioma disponível;
2. amostra deterministicamente todas as faixas, inclusive notas acima de 1000;
3. separa calibração, seleção e holdout;
4. compara modelos lineares e monotônicos;
5. publica catálogo, fixture, manifesto e relatório somente após validar todas
   as invariantes.

Saídas:

```text
src/tri_enem/coeficientes_data.json
tests/fixtures/validation_holdout.jsonl.gz
tests/fixtures/validation_manifest.json
docs/VALIDATION_REPORT.md
```

Use `python tests/validar_holdout.py` para recalcular a fixture publicada.

## Atalhos e ferramentas legadas

`calibrar_com_mapeamento.py` delega ao calibrador v4 em modo diagnóstico e
nunca publica artefatos. `calibrar_todos_anos.py` é um atalho compatível para a
recalibração v4 completa; não existe mais um segundo formato de coeficientes.

`amostrar_microdados_brutos.py` continua disponível apenas para investigações
com amostras reduzidas em `microdados_limpos/`. Essas amostras não são usadas
para publicar o catálogo nem o holdout de precisão.
