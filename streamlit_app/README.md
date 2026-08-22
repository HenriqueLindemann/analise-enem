# Calculadora Nota TRI ENEM - Interface Web

Interface web para estimativa da nota TRI do ENEM.

## Acesse Online

**→ [https://notatri.com/](https://notatri.com/)**

Estime sua nota do ENEM direto no navegador, sem instalar nada.

---

## Rodando Localmente

```bash
# Na raiz do repositório:
pip install -e ".[web]"
# ou: pip install -r requirements.txt -r streamlit_app/requirements.txt

streamlit run streamlit_app/app.py
```

O app abrirá automaticamente em `http://localhost:8501`.

## Estrutura Modular

```
streamlit_app/
├── app.py              # Aplicação principal (orquestrador)
├── config.py           # Configurações centralizadas (SEO, textos, constantes)
├── calculador.py       # Wrapper do módulo tri_enem
├── styles.css          # Estilos CSS externos
├── requirements.txt    # Dependências específicas da web
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

## SEO e Metadados

O aplicativo inclui otimizações completas para motores de busca e compartilhamento social:

- **Metatags dinâmicas**: títulos e descrições otimizados com URLs canônicas.
- **Open Graph & Twitter Cards**: suporte a prévias no WhatsApp, Facebook, Twitter e LinkedIn.
- **Dados estruturados (JSON-LD)**: schemas `WebApplication` e `FAQPage` para rich snippets.
- **Indexação**: `robots.txt` e `sitemap.xml` para rastreamento.

## Funcionalidades

- Cobertura de todas as edições de **2009 a 2025** (todas as áreas e aplicações).
- **Estimativa TRI instantânea** com status de validação transparente por prova.
- **Grade visual de acertos/erros** e ranking de impacto das questões.
- **Download de relatório PDF** com detalhamento vetorial completo.

## Licença

[PolyForm Noncommercial 1.0.0](../LICENSE) - Uso pessoal e educacional permitido.
