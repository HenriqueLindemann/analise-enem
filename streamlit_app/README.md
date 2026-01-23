# TRI ENEM - Calculador de Nota (Streamlit)

Interface web para cálculo de nota TRI do ENEM.

## 🚀 Início Rápido

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
- ✅ Design responsivo (mobile-friendly)
- ✅ Cache para performance
- ✅ Progress bar durante cálculo

## 🌐 Deploy no Streamlit Cloud (Gratuito)

### Passo a passo

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com GitHub
3. Clique em **"New app"**
4. Configure:
   - **Repository:** `HenriqueLindemann/analise-enem`
   - **Branch:** `master`
   - **Main file path:** `streamlit_app/app.py`
   - **Python version:** 3.10 ou superior
5. Clique em **Deploy!**

### Configurações avançadas (opcional)

Se precisar de variáveis de ambiente ou configurações:

```toml
# .streamlit/secrets.toml (não commitar!)
[general]
DEBUG = false
```

## 🔧 Configuração de Produção

O arquivo `.streamlit/config.toml` já está configurado para:

- ✅ Modo headless (sem browser local)
- ✅ XSRF protection ativada
- ✅ Tema personalizado
- ✅ Toolbar minimalista
- ✅ Erros de usuário ocultos

## 📱 Responsividade

O app é otimizado para:
- Desktop (layout wide)
- Tablet (layout adaptativo)
- Mobile (sidebar colapsável, fontes menores)

## 📝 Personalização

### Adicionar logo

Coloque um arquivo `logo.png` na pasta `streamlit_app/` e atualize o código no `app.py`.

### Cores e estilos

Edite as constantes no arquivo `components/graficos.py`.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

PolyForm Noncommercial License 1.0.0 - Uso não comercial apenas.
