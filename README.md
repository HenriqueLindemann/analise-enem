# Calculadora Nota TRI ENEM

Estime sua nota do ENEM usando **Teoria de Resposta ao Item (TRI)**, com
precisão medida por prova em participantes reais dos microdados oficiais.

Suporta provas de **2009 a 2025** com análise detalhada e relatórios completos.

---

## Interface Web - Sem Instalação

**→ Acesse direto no navegador:** [https://notatri.com/](https://notatri.com/)

---

## Instalação (apenas versão local)

### Para quem nunca programou

**Este programa produz uma estimativa TRI e informa a validação da prova.** Você precisa:

1. **Baixar este projeto** (botão verde "Code" → Download ZIP)
2. **Instalar Python**: https://www.python.org/downloads/
3. **Instalar as bibliotecas necessárias**: abra o terminal/prompt na pasta do projeto e digite:
   ```bash
   pip install -r requirements.txt
   ```
4. **Abrir o arquivo `meu_simulado.py`** com Bloco de Notas
5. **Trocar as alternativas** pelas suas respostas da prova
6. **Executar o simulador** no terminal:
   ```bash
   python meu_simulado.py
   ```

**Pronto!** Sua nota aparece na tela e, com `GERAR_PDF = True`, um PDF é criado
na pasta `relatorios/`.

**Precisa de ajuda?** Pergunte para sua IA favorita como instalar e rodar um programa Python no seu sistema operacional.

### Para desenvolvedores

```bash
git clone https://github.com/HenriqueLindemann/analise-enem.git
cd analise-enem
pip install -e ".[web,dev]"
```

---

## Uso Rápido

Edite o arquivo **`meu_simulado.py`** com suas respostas:

```python
ANO = 2023
TIPO_APLICACAO = '1a_aplicacao'
LINGUA = 'ingles'  # Para LC: ingles ou espanhol

# DIA 1
COR_LC = 'azul'
RESPOSTAS_LC = 'ACABC...'  # 45 respostas

COR_CH = 'azul'
RESPOSTAS_CH = 'BDCEA...'

# DIA 2
COR_CN = 'azul'
RESPOSTAS_CN = 'ACDAE...'

COR_MT = 'azul'
RESPOSTAS_MT = 'CEAEA...'
```

Execute:

```bash
python meu_simulado.py
```

Resultado:

```
============================================================
       CALCULADORA NOTA TRI ENEM - PROVA 2023
============================================================

Aplicação: 1a_aplicacao

------------------------------------------------------------
RESULTADOS
------------------------------------------------------------
Linguagens..........................   654.2 pts (33/45)
Ciências Humanas....................   712.4 pts (38/45)
Ciências da Natureza................   695.1 pts (35/45)
Matemática..........................   782.3 pts (40/45)
------------------------------------------------------------
MÉDIA...............................   711.0 pts
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
    print(f"  Q{erro['posicao']}: +{erro['ganho_se_acertasse']:.1f} pts | Gabarito: {erro['gabarito']}")
```

## Relatório PDF

Defina `GERAR_PDF = True` em `meu_simulado.py` e um relatório será salvo em `relatorios/` com:
- Notas de cada área
- Erros ordenados por impacto
- Parâmetros TRI de cada questão
- **Mensagem de validação** positiva, intermediária ou de cautela por prova

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

A precisão varia conforme a prova. Cada transformação é ajustada sem usar o
holdout final. Uma prova só recebe `ok` quando todos os casos desse holdout
ficam a até 2 pontos da nota oficial e a cobertura mínima é satisfeita.

Provas que não atingem o limite continuam disponíveis como estimativa e
mostram MAE, erro máximo observado e quantidade de casos. Provas sem parâmetros
de itens são explicitamente marcadas como incalculáveis.

Na interface, uma prova `ok` recebe uma confirmação verde. Quando o desempenho
é consistente na maioria dos casos, mas poucas exceções impedem a garantia
estrita, a mensagem intermediária comunica esse resultado sem tratar toda a
calibração como ruim. Diferenças sistemáticas continuam recebendo alerta forte.
Os critérios e números exatos permanecem no relatório técnico.

Os números atuais são gerados automaticamente em
[docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md); os critérios executáveis
estão em [`src/tri_enem/precisao.py`](src/tri_enem/precisao.py).

## Desenvolvimento e Testes

O projeto possui uma suíte de testes abrangente para garantir a precisão dos
cálculos e a integridade do mapeamento de questões ao longo dos anos.

### Testes automatizados (offline)

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
python tests/validar_holdout.py
```

Rodam também na integração contínua (`.github/workflows/testes.yml`), a cada
push e pull request. Utilizam os dados versionados no repositório e cobrem:

- **Regressão (golden)** — fixa nota e theta de 136 casos reais abrangendo
  todo ano × área. Qualquer alteração no motor que modifique um resultado é
  detectada. Regenerado por `tests/fixtures/gerar_golden_notas.py`.
- **Holdout oficial estratificado** — cobre todas as provas calculáveis e faz
  o CI falhar se uma prova `ok` tiver qualquer erro acima de 2 pontos.
- **Percurso do usuário ponta a ponta** — as 45 letras digitadas produzem a
  mesma nota nas três interfaces (web, `analisar_todas_questoes` e
  `SimuladorNota`), e os casos elegíveis são comparados à nota oficial.
- **Propriedades do modelo** — monotonicidade da curva ML3, limites do EAP e
  ausência de efeito de itens anulados sobre a nota.
- **Mensagens de precisão** — verifica a confirmação positiva das provas
  `ok`, o aviso intermediário para exceções concentradas e o invariante de que
  prova não confiável nunca é apresentada sem aviso.

### Validação e publicação

O pipeline que recalibra os modelos exige os microdados brutos do INEP. Ele
separa calibração, seleção e holdout e publica os artefatos de forma atômica:

```bash
python tests/run_full_validation.py \
  --microdados-dir /caminho/para/MICRODADOS_ENEM
```

Os testes normais não dependem desses arquivos grandes: os parâmetros dos
itens, casos de regressão e holdout já estão versionados. Veja
[`tests/README.md`](tests/README.md) para a matriz de testes e
[`tools/README.md`](tools/README.md) para o fluxo de recalibração.

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

Os arquivos `ITENS_PROVA_<ano>.csv` têm uma única fonte versionada:
`src/tri_enem/data/itens/<ano>/`. Eles são gerados por
`tools/gerar_dados_itens.py`, que valida o esquema e grava
`src/tri_enem/data/itens/manifest.json` com os hashes das fontes oficiais e dos
arquivos normalizados. Eles são incluídos no wheel por `pyproject.toml` e
carregados com `importlib.resources`.

As decisões de implementação validadas contra os microdados ficam nos
docstrings dos módulos correspondentes (`calculador.py`, `precisao.py`,
`tradutor.py`). Documentação adicional em [docs/](docs/README.md).

## Para Estudantes

1. **Faça um simulado** com uma prova antiga
2. **Anote suas 45 respostas** de cada área
3. **Preencha `meu_simulado.py`** com ano, cor e respostas
4. **Execute e analise** - foque nos erros de questões fáceis!

## Contribuição

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[PolyForm Noncommercial 1.0.0](LICENSE) - Uso pessoal e educacional permitido.

## Autor

**Henrique Lindemann** - Eng. Computação UFRGS  
[LinkedIn](https://www.linkedin.com/in/henriquelindemann/)
