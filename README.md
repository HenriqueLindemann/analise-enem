# TRI ENEM - Calculador de Notas do ENEM

Calculador de notas do ENEM usando **Teoria de Resposta ao Item (TRI)** com alta precisão.

Este módulo foi desenvolvido através de engenharia reversa dos microdados oficiais do INEP e permite calcular a nota de qualquer prova do ENEM de **2009 a 2024**.

> **Nota:** Este projeto ainda está em desenvolvimento. Nem todas as provas têm erro baixo calibrado. Futuramente será disponibilizada uma lista de códigos de provas validados.

## Funcionalidades

- **Cálculo de nota TRI** com alta precisão (erro médio < 0.5 pontos para provas calibradas)
- **Análise de impacto de erros** - descubra quais questões mais afetaram sua nota
- **Suporte a todas as áreas**: Matemática, Ciências da Natureza, Ciências Humanas e Linguagens
- **Suporte a Inglês e Espanhol** para Linguagens e Códigos
- **Anos suportados**: 2009 a 2024

## Início Rápido

### Instalação

```bash
git clone https://github.com/HenriqueLindemann/analise-enem.git
cd analise-enem
pip install -r requirements.txt
```

### Uso Rápido

Edite o arquivo `meu_simulado.py` na raiz do projeto com suas respostas e execute:

```bash
python meu_simulado.py
```

### Uso via Código

```python
import sys
sys.path.insert(0, 'src')

from tri_enem import SimuladorNota

# Criar simulador
sim = SimuladorNota()

# Suas 45 respostas (A, B, C, D ou E)
respostas_mt = "CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE"

# Calcular nota de Matemática 2023 (com código da prova)
# Veja docs/GUIA_PROVAS.md para encontrar seu código
resultado = sim.calcular('MT', 2023, respostas_mt, co_prova=1211)

print(f"Nota: {resultado.nota:.1f}")
print(f"Acertos: {resultado.acertos}/{resultado.total_itens}")
print(f"Theta: {resultado.theta:.4f}")
```

### Códigos de Prova - IMPORTANTE!

O ENEM aplica várias versões da prova (cores diferentes). Cada versão tem um **código** (CO_PROVA).

**Por que isso importa?** As mesmas respostas resultam em notas DIFERENTES dependendo da prova, porque cada cor tem as questões em ordem diferente.

Consulte `docs/GUIA_PROVAS.md` para encontrar o código da sua prova.

**Exemplo códigos 2023 - Matemática (1ª aplicação):**
| Cor | Código |
|-----|--------|
| AZUL | 1211 |
| AMARELA | 1212 |
| ROSA | 1213 |
| CINZA | 1214 |

### Calculando Linguagens (com escolha de idioma)

```python
# Para LC, especifique a língua estrangeira e o código da prova
respostas_lc = "ABCDE..." * 9  # 45 respostas

# Inglês - prova Azul 2023
resultado_ing = sim.calcular('LC', 2023, respostas_lc, lingua='ingles', co_prova=1201)

# Espanhol - prova Azul 2023
resultado_esp = sim.calcular('LC', 2023, respostas_lc, lingua='espanhol', co_prova=1201)
```

### Análise de Impacto dos Erros

Descubra quais erros mais impactaram sua nota:

```python
from tri_enem import CalculadorTRI

calc = CalculadorTRI()

# Analisar impacto de cada erro
impactos = calc.analisar_impacto_erros(2023, 'MT', 1211, respostas_mt)

print("Top 5 erros com maior impacto:")
for i, erro in enumerate(impactos[:5], 1):
    print(f"  {i}. Questão {erro['posicao']}: +{erro['ganho_potencial']:.1f} pts se acertasse")
    print(f"     Dificuldade: {erro['param_b']:.2f} | Gabarito: {erro['gabarito']}")
```

## Estrutura do Projeto

```
analise-enem/
├── src/
│   └── tri_enem/           # Módulo principal
│       ├── simulador.py    # Interface simplificada (recomendado)
│       ├── calculador.py   # Motor de cálculo TRI
│       ├── calibrador.py   # Calibração de coeficientes
│       ├── coeficientes.py # Carrega coeficientes
│       └── tradutor.py     # Tratamento especial para LC
│
├── examples/               # Exemplos de uso
├── tests/                  # Testes de validação
├── tools/                  # Ferramentas de desenvolvimento
├── docs/                   # Documentação técnica
├── meu_simulado.py         # EDITE ESTE ARQUIVO com suas respostas
└── README.md
```

## Como Funciona

O cálculo usa o **Modelo Logístico de 3 Parâmetros (ML3)** com estimação **EAP** (Expected a Posteriori):

1. **Parâmetro A (Discriminação)**: Quão bem a questão diferencia alunos
2. **Parâmetro B (Dificuldade)**: Nível de dificuldade da questão
3. **Parâmetro C (Chute)**: Probabilidade de acerto casual

A nota final é calculada como:
```
nota = slope × theta + intercept
```

Onde `theta` é a proficiência estimada e os coeficientes (`slope`, `intercept`) foram descobertos via engenharia reversa dos microdados oficiais.

## Precisão

| Métrica | Valor |
|---------|-------|
| Erro Médio Absoluto (MAE) | < 0.5 pontos (provas calibradas) |
| R² | ~0.9999 |
| Anos disponíveis | 2009-2024 |

**Atenção:** Algumas provas ainda não foram validadas. A precisão pode variar.

## Para Estudantes

### Nunca usou Python? Sem problemas!

1. **Instale o Python**: Baixe em [python.org](https://www.python.org/downloads/) (versão 3.8 ou superior)
2. **Baixe este projeto**: Clique em "Code" > "Download ZIP" no GitHub e extraia
3. **Abra o terminal na pasta do projeto**:
   - Windows: Clique com botão direito na pasta > "Abrir no Terminal"
   - Mac/Linux: Abra o Terminal e use `cd caminho/para/pasta`
4. **Instale as dependências**: Digite `pip install -r requirements.txt` e pressione Enter
5. **Edite o arquivo `meu_simulado.py`** com suas respostas (pode usar o Bloco de Notas)
6. **Execute**: Digite `python meu_simulado.py` e pressione Enter

### Como encontrar o código da sua prova

O código da prova é essencial para um cálculo preciso!

1. Abra o arquivo `docs/GUIA_PROVAS.md`
2. Encontre o ano da sua prova
3. Veja a tabela de códigos por cor (Azul, Amarela, Rosa, etc.)
4. Anote os códigos das 4 áreas

**Dica**: Se você não lembra a cor da prova, tente com cada código e veja qual dá mais acertos.

### Como usar para estudar

1. Faça um simulado com uma prova antiga do ENEM
2. Anote suas 45 respostas de cada área
3. Descubra o código da sua prova em `docs/GUIA_PROVAS.md`
4. Edite o arquivo `meu_simulado.py` com suas respostas e códigos
5. Execute e veja sua nota estimada
6. Analise seus erros por impacto e dificuldade
7. Foque nos erros de questões fáceis/médias (maior retorno)

### Entendendo a análise de erros

- **Questões fáceis que você errou**: Prioridade máxima de estudo!
- **Ganho potencial alto**: Essas questões mais "pesam" na sua nota
- **Questões difíceis que você errou**: Normal, não se preocupe tanto

## Documentação Adicional

- [Guia de Provas](docs/GUIA_PROVAS.md) - **IMPORTANTE**: Encontre o código da sua prova aqui
- [Descobertas da Engenharia Reversa](docs/DESCOBERTAS.md) - Detalhes técnicos de como o cálculo foi descoberto

## Observações Importantes

- Os **microdados do INEP** não estão incluídos (são muito grandes)
- Para calibração ou validação, baixe em: [Portal INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)
- O módulo já vem com **coeficientes pré-calibrados** de 2009-2024
- Nem todas as provas foram validadas - a precisão pode variar

## Contribuição

Contribuições são bem-vindas! Especialmente:
- Validação de novas provas
- Melhorias na análise de erros
- Novas visualizações
- Documentação
- Testes

## Licença

**Uso livre para fins educacionais e não-comerciais.**

Uso comercial é restrito. Ao utilizar este projeto em outros trabalhos sem fins lucrativos, 
por favor mantenha a referência à fonte original.

## Autor

Desenvolvido por **Henrique Lindemann**  
Estudante de Engenharia de Computação - UFRGS

LinkedIn: [linkedin.com/in/henriquelindemann](https://www.linkedin.com/in/henriquelindemann/)
