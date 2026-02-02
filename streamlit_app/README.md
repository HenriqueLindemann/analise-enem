# TRI ENEM - Calculador de Nota (Streamlit)

Interface web para cálculo de nota TRI do ENEM.

## 🌐 Acesse Online

**👉 [https://notatri.com/](https://notatri.com/)**

Calcule sua nota do ENEM direto no navegador, sem instalar nada!

---

## Rodando Localmente

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

## Estrutura Modular

```
streamlit_app/
├── app.py              # Aplicação principal (orquestrador)
├── config.py           # Configurações centralizadas (SEO, textos, constantes)
├── calculador.py       # Wrapper do módulo tri_enem
├── styles.css          # Estilos CSS externos
├── requirements.txt    # Dependências específicas
├── .streamlit/
│   └── config.toml     # Configurações de deploy
├── static/
│   ├── robots.txt      # Instruções para crawlers
│   └── sitemap.xml     # Mapa do site para SEO
├── components/
│   ├── __init__.py     # Exports do módulo
│   ├── inputs.py       # Componentes de entrada (respostas, configs)
│   ├── resultados.py   # Exibição de resultados
│   ├── graficos.py     # Visualizações Plotly
│   ├── impressao.py    # Geração de PDF
│   ├── layout.py       # Estrutura da página (header, sidebar, footer)
│   └── seo.py          # Meta tags, Schema.org JSON-LD
└── README.md
```

## SEO 

O app inclui otimizações para ranqueamento no Google:

### Meta Tags
- Title otimizado com keywords (max 60 caracteres)
- Meta description com limite de 160 caracteres
- Meta keywords com termos relevantes
- Canonical URL para evitar conteúdo duplicado

### Open Graph (Redes Sociais)
- Tags og:title, og:description, og:type, og:url
- Suporte a Facebook, LinkedIn, WhatsApp

### Twitter Card
- Tags twitter:card, twitter:title, twitter:description

### Schema.org JSON-LD
- WebApplication schema para rich snippets
- FAQPage schema com perguntas frequentes
- Dados estruturados para Google

### Arquivos Estáticos
- robots.txt para instruir crawlers
- sitemap.xml para indexação

## Funcionalidades

- ✅ Seleção de ano (2009-2024)
- ✅ Seleção de tipo de aplicação (1ª, Digital, Reaplicação)
- ✅ Seleção de cor por área
- ✅ Input de 45 respostas por área
- ✅ Cálculo TRI preciso
- ✅ Visualização de notas por área
- ✅ Grade visual de acertos/erros
- ✅ Gráfico de impacto das questões
- ✅ Análise detalhada por área
- ✅ Download de relatório PDF
- ✅ Cache para performance
- ✅ Progress bar durante cálculo

## Licença

PolyForm Noncommercial License 1.0.0 - Uso não comercial apenas.
