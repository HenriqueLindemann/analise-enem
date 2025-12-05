# Análise de Dados do ENEM 2021 (Protótipo / Prova de Conceito)

Este projeto realiza uma análise estatística detalhada do desempenho de um participante no ENEM 2021, utilizando os Microdados oficiais. Ele oferece tanto uma comparação geral com a população (percentis, histogramas) quanto uma análise pedagógica usando a Teoria de Resposta ao Item (TRI).

> ⚠️ **Aviso:** Este projeto é uma **versão inicial (Proof of Concept)**. Ele foi desenvolvido para validar a viabilidade de cruzar dados de desempenho individual com os microdados públicos do INEP.

- Bibliotecas Python: `pandas`, `numpy`, `matplotlib`, `seaborn`

```bash
pip install pandas numpy matplotlib seaborn
```

- **Microdados do ENEM 2021**:
  - Os dados são volumosos e não estão incluídos neste repositório.
  - Acesse o [Portal do INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
  - Baixe os **Microdados do ENEM 2021**.
  - Crie uma pasta chamada `DADOS/` na raiz deste projeto (caso não exista).
  - Extraia os arquivos `MICRODADOS_ENEM_2021.csv` e `ITENS_PROVA_2021.csv` para dentro da pasta `DADOS/`.

## Como Usar

### 1. Configurar as Notas
Abra o arquivo `config.py` e insira as 5 notas do participante que você deseja analisar.

```python
# config.py
NOTAS_PARTICIPANTE = {
    'NU_NOTA_LC': 677.5,
    'NU_NOTA_CH': 749.9,
    # ... insira as outras notas aqui
}
```
> **Importante:** As notas de exemplo em `config.py` são de um participante real. Para que a análise TRI funcione corretamente, as notas inseridas devem corresponder exatamente a um participante existente nos Microdados, caso contrário, as buscas não encontrarão um "match".

### 2. Executar a Automação
Utilize o script de automação que limpa resultados anteriores, realiza os cálculos e gera todos os gráficos de uma só vez.

```bash
chmod +x run_analysis.sh
./run_analysis.sh
```

### O que o script faz?
1.  **Limpeza**: Remove gráficos de execuções anteriores.
2.  **Análise Geral (`analise_participante.py`)**: Calcula percentis comparando com a população total (agora otimizado para comparar por presença em cada área).
3.  **Visualizações Gerais (`visualizacoes_analise.py`)**: Gera histogramas, boxplots e radar charts na pasta `graficos/`.
4.  **Análise TRI (`analise_tri_final.py`)**: Busca o participante, recupera as respostas questão a questão e cruza com a dificuldade (Parâmetro B) dos itens, gerando diagnósticos pedagógicos na pasta `graficos_tri/`.

## Estrutura do Projeto

- `run_analysis.sh`: Script orquestrador da automação.
- `config.py`: Configuração das notas do participante.
- `analise_participante.py`: Cálculos estatísticos de população.
- `visualizacoes_analise.py`: Motor de geração de gráficos gerais.
- `analise_tri_final.py`: Motor de análise pedagógica TRI.
- `DADOS/`: Diretório para os CSVs do INEP (não versionado).
- `graficos/` e `graficos_tri/`: Diretórios de saída (não versionados).
