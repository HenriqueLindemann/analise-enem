# Calculadora Nota TRI ENEM

Estime sua nota do ENEM usando **Teoria de Resposta ao Item (TRI)**, com
precisão medida por prova em participantes reais dos microdados oficiais.

Suporta provas de **2009 a 2025** com análise detalhada e relatórios completos.

---

## Interface Web - Sem Instalação

**→ Acesse direto no navegador:** [https://notatri.com/](https://notatri.com/)

---

## Instalação (versão local)

Requer [Python 3.9+](https://www.python.org/downloads/).

1. Clone ou baixe o repositório:
   ```bash
   git clone https://github.com/HenriqueLindemann/analise-enem.git
   cd analise-enem
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

> **Para desenvolvimento:** `pip install -e ".[web,dev]"`

---

## Uso Rápido

Edite o arquivo **`meu_simulado.py`** com suas respostas:

```python
ANO = 2021
TIPO_APLICACAO = '1a_aplicacao'
LINGUA = 'ingles'  # Para LC: ingles ou espanhol

# DIA 1
COR_LC = 'rosa'
RESPOSTAS_LC = 'ACABCD...'  # 45 respostas

COR_CH = 'rosa'
RESPOSTAS_CH = 'EDAAAA...'

# DIA 2
COR_CN = 'rosa'
RESPOSTAS_CN = 'DABCED...'

COR_MT = 'rosa'
RESPOSTAS_MT = 'DCCAEA...'
```

Execute:

```bash
python meu_simulado.py
```

Resultado:

```
============================================================
       CALCULADORA NOTA TRI ENEM - PROVA 2021
============================================================

Aplicação: 1a_aplicacao

------------------------------------------------------------
RESULTADOS
------------------------------------------------------------
Linguagens.........................  677,4 pts (35/43)
Ciências Humanas...................  749,9 pts (39/45)
Ciências da Natureza...............  753,3 pts (37/44)
Matemática.........................  916,3 pts (41/44)
------------------------------------------------------------
MÉDIA..............................  774,2 pts
```

## Funcionalidades

- **Precisão verificável** com erro médio e maior erro observado por prova
- **Relatórios PDF** com análise de cada questão
- **Análise de impacto** — descubra quais erros mais afetaram sua nota
- **Todas as áreas**: MT, CN, CH, LC (inglês/espanhol)
- **Cobertura de 17 anos**: 2009 a 2025

## Uso Avançado

### Via código Python

```python
from tri_enem import MapeadorProvas, CalculadorTRI

mapeador = MapeadorProvas()
calc = CalculadorTRI()

# Obter código da prova pela cor
co_prova = mapeador.obter_codigo(2023, 'MT', '1a_aplicacao', 'azul')

# Calcular nota
respostas = 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE'
resultado = calc.calcular_nota(2023, 'MT', co_prova, respostas)
print(f"Nota: {resultado['nota']:.1f}")
```

### Análise de impacto dos erros

```python
analise = calc.analisar_todas_questoes(2023, 'MT', co_prova, respostas)

print("Erros que mais impactaram sua nota:")
for erro in analise['erros'][:5]:
    numero = erro.get('posicao_caderno', erro['posicao'])
    print(f"  Q{numero}: +{erro['ganho_se_acertasse']:.1f} pts | Gabarito: {erro['gabarito']}")
```

Detalhes técnicos da API e da semântica das posições estão em
[`src/tri_enem/README.md`](src/tri_enem/README.md).

## Relatório PDF

Disponível pelo botão de download na interface web ou com `GERAR_PDF = True` em `meu_simulado.py`. O relatório inclui:

- **Visão geral**: notas estimadas, médias e indicadores de precisão.
- **Gabarito visual**: grade com acertos, erros e questões anuladas.
- **Análise de impacto**: ranking dos erros que mais custaram pontos e ganho estimado por questão.

Veja o [PDF de exemplo](relatorios/EXEMPLO_relatorio.pdf) e a [documentação do gerador](relatorios/README.md).

## Como Funciona

O cálculo usa o **Modelo Logístico de 3 Parâmetros (ML3P)** com estimação EAP:

- **A (Discriminação)**: Quão bem a questão diferencia alunos
- **B (Dificuldade)**: Nível de dificuldade
- **C (Chute)**: Probabilidade de acerto casual

A transformação final pode ser linear ou monotônica linear por partes,
conforme o desempenho em um conjunto independente de validação.

> Os parâmetros dos itens são publicados pelo INEP. As transformações de
> escala são estimadas e validadas pelo projeto contra notas oficiais.

## Precisão e Calibração

Cada prova é validada contra casos reais de participantes dos microdados oficiais:

- **Confirmada (`ok`)**: erro máximo $\le 2$ pontos no conjunto de teste independente (*holdout*).
- **Estimativa / Alerta**: erro baixo na maioria dos casos ou variações maiores; métricas de erro médio (MAE) e erro máximo são sempre exibidas.
- **Incalculável**: provas sem parâmetros de itens publicados pelo INEP.

Consulte os números de cada prova no [Relatório de Validação](docs/VALIDATION_REPORT.md) e os critérios em [`src/tri_enem/precisao.py`](src/tri_enem/precisao.py).

## Desenvolvimento e Testes

### Testes automatizados (offline)

```bash
pytest
python tests/validar_holdout.py
```

A suíte cobre regressão contra notas reais (*golden tests*), validação do *holdout* oficial, coerência entre interfaces (CLI, Web e API), propriedades matemáticas da TRI e tratamento de itens anulados.

### Validação completa (com microdados brutos)

```bash
python tests/run_full_validation.py --microdados-dir /caminho/para/MICRODADOS_ENEM
```

Consulte [`tests/README.md`](tests/README.md) para a matriz detalhada de testes e [`tools/README.md`](tools/README.md) para o fluxo de calibração.

## Estrutura do Projeto

```
analise-enem/
├── meu_simulado.py               # EDITE com suas respostas
├── pyproject.toml                # Empacotamento + config de testes (dev)
├── requirements.txt              # Dependências (fonte de verdade)
├── requirements-dev.txt          # Complemento para testes e empacotamento
├── streamlit_app/                # Interface Web
├── src/tri_enem/
│   ├── calculador.py             # Motor de cálculo TRI
│   ├── simulador.py              # Interface simplificada
│   ├── calibracao_modelos.py     # Ajuste e seleção dos modelos de escala
│   ├── mapeador_provas.py        # API do mapeamento
│   ├── mapeamento_provas.yaml    # Todas as provas 2009-2025
│   ├── coeficientes_data.json    # Modelos + holdout + status (schema v3)
│   ├── data/itens/<ano>/         # Parâmetros oficiais incluídos no pacote
│   ├── precisao.py               # Contrato de validação exibido ao usuário
│   ├── tradutor.py               # LC (inglês/espanhol)
│   └── relatorios/               # Gerador de PDF
├── docs/                         # Documentação (ver docs/README.md)
├── tools/                        # Ferramentas de calibração
├── examples/                     # Exemplos de uso via código
├── tests/
│   ├── test_calculador.py        # Motor TRI: regressão, coerência, modelo
│   ├── test_precisao.py          # Avisos de confiabilidade por prova
│   ├── test_mapeador_provas.py   # Testes unitários (pytest)
│   ├── test_utils.py             # Testes unitários (pytest)
│   └── ...                       # Scripts de validação (ver tests/README.md)
└── relatorios/                   # PDFs gerados
```

Documentação técnica adicional sobre calibração, arquitetura e testes está em [`docs/`](docs/README.md).

## Contribuição

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[PolyForm Noncommercial 1.0.0](LICENSE) - Uso pessoal e educacional permitido.

## Autor

**Henrique Lindemann** - Eng. Computação UFRGS  
[LinkedIn](https://www.linkedin.com/in/henriquelindemann/)
