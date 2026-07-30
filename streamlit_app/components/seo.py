# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Componentes de SEO para otimização em mecanismos de busca.

Este módulo gera:
- Meta tags padrão (description, keywords, author)
- Open Graph tags (Facebook, LinkedIn, WhatsApp)
- Twitter Card tags
- Schema.org JSON-LD structured data
- Canonical URL
"""

import json
from datetime import datetime
from typing import Optional


def gerar_meta_tags(
    title: str,
    description: str,
    keywords: str,
    canonical_url: str,
    author: str,
    og_title: Optional[str] = None,
    og_description: Optional[str] = None,
    og_type: str = "website",
    og_image: Optional[str] = None,
    twitter_card: str = "summary",
    twitter_title: Optional[str] = None,
    twitter_description: Optional[str] = None,
) -> str:
    """
    Gera HTML com meta tags para SEO.
    
    Args:
        title: Título da página
        description: Descrição (max 160 chars)
        keywords: Palavras-chave separadas por vírgula
        canonical_url: URL canônica da página
        author: Nome do autor
        og_*: Open Graph tags
        twitter_*: Twitter Card tags
    
    Returns:
        String HTML com meta tags
    """
    og_title = og_title or title
    og_description = og_description or description
    twitter_title = twitter_title or title
    twitter_description = twitter_description or description
    
    tags = f'''
<!-- SEO Meta Tags -->
<meta name="google-site-verification" content="Rp7Rf0XvmzPBy1A7XAbeYTEJdMVeX789OMw3D2HBgOs" />
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<meta name="author" content="{author}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical_url}">

<!-- Open Graph / Facebook / LinkedIn / WhatsApp -->
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_description}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical_url}">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Calculadora Nota TRI ENEM">
'''
    
    if og_image:
        tags += f'<meta property="og:image" content="{og_image}">\n'
    
    tags += f'''
<!-- Twitter Card -->
<meta name="twitter:card" content="{twitter_card}">
<meta name="twitter:title" content="{twitter_title}">
<meta name="twitter:description" content="{twitter_description}">
'''
    
    return tags


def gerar_schema_json_ld(
    name: str,
    description: str,
    url: str,
    author_name: str,
    author_url: str,
    github_url: str,
) -> str:
    """
    Gera Schema.org JSON-LD para rich snippets no Google.
    
    Implementa:
    - WebApplication schema
    - FAQPage schema
    
    Args:
        name: Nome do app
        description: Descrição
        url: URL do app
        author_name: Nome do autor
        author_url: URL do autor (LinkedIn)
        github_url: URL do repositório
        
    Returns:
        Script HTML com JSON-LD
    """
    # Schema principal: WebApplication
    web_app_schema = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": name,
        "description": description,
        "url": url,
        "codeRepository": github_url,
        "applicationCategory": "EducationalApplication",
        "operatingSystem": "All",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "BRL"
        },
        "author": {
            "@type": "Person",
            "name": author_name,
            "url": author_url
        },
        "provider": {
            "@type": "Person",
            "name": author_name,
            "url": author_url
        },
        "datePublished": "2024-01-01",
        "dateModified": datetime.now().strftime("%Y-%m-%d"),
        "inLanguage": "pt-BR",
        "isAccessibleForFree": True,
        "keywords": [
            "ENEM", "TRI", "calculadora", "nota ENEM", 
            "Teoria de Resposta ao Item", "vestibular", "educação"
        ],
    }
    
    # FAQ Schema para perguntas frequentes
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "Como calcular minha nota do ENEM usando TRI?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Selecione o ano e a prova, digite suas 45 respostas e clique em Calcular. A estimativa TRI informa a precisão medida em microdados oficiais."
                }
            },
            {
                "@type": "Question",
                "name": "O que é TRI - Teoria de Resposta ao Item?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "A TRI modela a probabilidade de acerto a partir dos parâmetros dos itens. Esta calculadora produz uma estimativa e publica sua validação contra notas oficiais."
                }
            },
            {
                "@type": "Question",
                "name": "A calculadora é gratuita?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Sim! A calculadora é 100% gratuita para estudantes, professores e pesquisadores. O código é aberto e disponível no GitHub."
                }
            },
            {
                "@type": "Question",
                "name": "Quais anos do ENEM estão disponíveis?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "A calculadora suporta provas do ENEM de 2009 até 2025, incluindo 1ª aplicação, prova digital e reaplicações."
                }
            },
        ]
    }
    
    # Combinar schemas
    return f'''
<!-- Schema.org JSON-LD Structured Data -->
<script type="application/ld+json">
{json.dumps(web_app_schema, ensure_ascii=False, indent=2)}
</script>
<script type="application/ld+json">
{json.dumps(faq_schema, ensure_ascii=False, indent=2)}
</script>
'''


def gerar_noscript_seo() -> str:
    """
    Gera conteúdo <noscript> para crawlers que não executam JS.
    
    Alguns crawlers básicos não renderizam JavaScript.
    Este conteúdo fornece informações essenciais para eles.
    
    Returns:
        String HTML com conteúdo noscript
    """
    return '''
<noscript>
    <div style="padding: 20px; font-family: Arial, sans-serif;">
        <h1>Calculadora Nota TRI ENEM - Estime sua Nota Online Grátis</h1>
        <p>
            Esta calculadora gratuita produz uma estimativa da nota do ENEM
            usando Teoria de Resposta ao Item (TRI), com validação por prova
            em microdados oficiais.
        </p>
        <h2>Funcionalidades:</h2>
        <ul>
            <li>Suporte a provas de 2009 a 2025</li>
            <li>Precisão informada com erro médio e maior diferença por prova</li>
            <li>Análise detalhada de cada questão</li>
            <li>Gráficos de impacto por questão</li>
            <li>Relatório PDF para download</li>
        </ul>
        <h2>Como usar:</h2>
        <ol>
            <li>Selecione o ano e cor da prova</li>
            <li>Digite suas 45 respostas para cada área</li>
            <li>Clique em Calcular e veja seu resultado</li>
        </ol>
        <p>
            Desenvolvido por Henrique Lindemann - Engenharia de Computação UFRGS.
            Código aberto disponível no GitHub.
        </p>
    </div>
</noscript>
'''
