# TRI ENEM - Calculador de Nota (Streamlit)

Interface web para cálculo de nota TRI do ENEM.

## 🌐 Acesse Online

**👉 [https://calculadoratri.streamlit.app/](https://calculadoratri.streamlit.app/)**

Calcule sua nota do ENEM direto no navegador, sem instalar nada!

---

## 🚀 Rodando Localmente

### 1. Instale as dependências

```bash
# Na pasta raiz do projeto
pip install -r requirements.txt
pip install -r streamlit_app/requirements.txt
```

### 2. Execute o app

```bash
streamlit run streamlit_app/app.py
```

### 3. Acesse no navegador

O app abrirá automaticamente em `http://localhost:8501`

## 📦 Estrutura

```
streamlit_app/
├── app.py              # Aplicação principal
├── calculador.py       # Wrapper do módulo tri_enem
├── requirements.txt    # Dependências específicas
├── .streamlit/
│   └── config.toml     # Configurações de deploy
├── components/
│   ├── __init__.py
│   ├── inputs.py       # Componentes de entrada
│   ├── resultados.py   # Componentes de resultado
│   └── graficos.py     # Visualizações Plotly
└── README.md
```

## ✨ Funcionalidades

- ✅ Seleção de ano (2009-2024)
- ✅ Seleção de tipo de aplicação (1ª, Digital, Reaplicação)
- ✅ Seleção de cor por área
- ✅ Input de 45 respostas por área
- ✅ Cálculo TRI preciso
- ✅ Visualização de notas por área
- ✅ Grade visual de acertos/erros
- ✅ Gráfico de impacto das questões
- ✅ Análise detalhada por área
- ✅ Tabela de erros e acertos
- ✅ Cache para performance
- ✅ Progress bar durante cálculo

## 📄 Licença

PolyForm Noncommercial License 1.0.0 - Uso não comercial apenas.
