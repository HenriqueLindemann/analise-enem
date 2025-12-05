# Análise de Dados do ENEM 2021 (Protótipo / Prova de Conceito)

> ⚠️ **Aviso:** Este projeto é uma **versão inicial (Proof of Concept)**. Ele foi desenvolvido para validar a viabilidade de cruzar dados de desempenho individual com os microdados públicos do INEP.

O software realiza uma análise estatística detalhada e pedagógica (TRI) de um participante, mas possui limitações de escopo intencionais neste estágio.

## 🚧 Limitações Atuais

Como trata-se de um protótipo muito inicial, considere os seguintes pontos:

1.  **Foco Exclusivo no ENEM 2021**: O código está hardcoded para a estrutura de arquivos e dicionários de dados de 2021. Não suporta outros anos.
2.  **Seleção de Língua Estrangeira**: O script detecta automaticamente a língua escolhida (Inglês ou Espanhol) baseada nos dados do participante, mas não oferece interface para simulação ou troca manual.
3.  **Escalabilidade**: Projetado para analisar um único participante por vez através de arquivo de configuração.

## 📋 Pré-requisitos

- Python 3.8+
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

## 🚀 Fluxo de Análise Automatizado

Simplificamos todo o processo em um único fluxo.

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
> **Importante:** As notas devem corresponder **exatamente** a um participante existente nos Microdados para que a análise TRI (Item Response Theory) consiga recuperar o gabarito e as respostas individuais.

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

## 📂 Estrutura do Projeto

- `run_analysis.sh`: Script orquestrador da automação.
- `config.py`: Configuração das notas do participante.
- `analise_participante.py`: Cálculos estatísticos de população.
- `visualizacoes_analise.py`: Motor de geração de gráficos gerais.
- `analise_tri_final.py`: Motor de análise pedagógica TRI.
- `DADOS/`: Diretório para os CSVs do INEP (não versionado).
- `graficos/` e `graficos_tri/`: Diretórios de saída (não versionados).