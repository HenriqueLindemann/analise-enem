# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Configurações centralizadas do Streamlit App.

Este módulo centraliza todas as constantes, URLs, textos e configurações
do app para facilitar manutenção e SEO.
"""

from dataclasses import dataclass
from typing import Dict, List

# ============================================================================
#                         INFORMAÇÕES DO PROJETO
# ============================================================================

APP_VERSION = "29/07/2026"
APP_AUTHOR = "Henrique Lindemann"
APP_AUTHOR_URL = "https://www.linkedin.com/in/henriquelindemann/"
APP_GITHUB_URL = "https://github.com/HenriqueLindemann/analise-enem"
APP_ISSUES_URL = f"{APP_GITHUB_URL}/issues"
APP_VALIDATION_REPORT_URL = (
    f"{APP_GITHUB_URL}/blob/master/docs/VALIDATION_REPORT.md"
)
APP_CANONICAL_URL = "https://notatri.com"

# ============================================================================
#                         SEO - META TAGS
# ============================================================================

@dataclass
class SEOConfig:
    """Configuração de SEO para meta tags e Schema.org."""
    
    # Título da página (máx 60 caracteres para Google)
    page_title: str = "Calculadora Nota TRI ENEM - Calcule sua Nota Online Grátis"
        
    # Descrição (máx 160 caracteres para Google)
    meta_description: str = (
        "Calculadora Nota TRI ENEM - Calcule sua nota do ENEM online e grátis. "
        "Estimativa TRI validada em microdados oficiais. Gabaritos de 2009 a 2025. "
        "Análise detalhada por área."
    )
    
    # Keywords (separadas por vírgula)
    meta_keywords: str = (
        "calculadora ENEM, nota ENEM, TRI ENEM, calcular nota ENEM, "
        "simulador ENEM, Teoria de Resposta ao Item, gabarito ENEM, "
        "ENEM 2025, ENEM 2024, nota TRI, correção ENEM online, "
        "resultado ENEM, prova ENEM, vestibular, INEP"
    )
    
    # Open Graph (Facebook, LinkedIn, WhatsApp)
    og_title: str = "Calculadora Nota TRI ENEM - Calcule sua Nota Online Grátis"
    og_description: str = (
        "Simule sua nota do ENEM com precisão usando TRI. "
        "Gabaritos oficiais de 2009 a 2025. Gratuito."
    )
    og_type: str = "website"
    og_image: str = ""  # URL da imagem de preview (opcional)
    
    # Twitter Card
    twitter_card: str = "summary_large_image"
    twitter_title: str = "Calculadora Nota TRI ENEM - Nota Online Grátis"
    twitter_description: str = (
        "Calcule sua nota do ENEM usando TRI. "
        "Ferramenta gratuita com gabaritos de 2009 a 2025."
    )


SEO = SEOConfig()


# ============================================================================
#                         ÁREAS DO ENEM
# ============================================================================

AREAS_ENEM: Dict[str, str] = {
    'LC': 'Linguagens e Códigos',
    'CH': 'Ciências Humanas',
    'CN': 'Ciências da Natureza',
    'MT': 'Matemática',
}

ORDEM_AREAS: List[str] = ['LC', 'CH', 'CN', 'MT']

# ============================================================================
#                         TIPOS DE APLICAÇÃO
# ============================================================================

TIPOS_APLICACAO: Dict[str, str] = {
    '1a_aplicacao': '1ª Aplicação',
    'digital': 'Digital',
    'reaplicacao': 'Reaplicação',
    'segunda_oportunidade': 'Segunda Oportunidade',
}

ORDEM_TIPOS: List[str] = ['1a_aplicacao', 'digital', 'reaplicacao', 'segunda_oportunidade']

# ============================================================================
#                         CORES DAS PROVAS
# ============================================================================

ORDEM_CORES: List[str] = ['azul', 'amarela', 'rosa', 'cinza', 'branca', 'verde', 'laranja']

# ============================================================================
#                         TEXTOS DA INTERFACE
# ============================================================================

TEXTO_SOBRE = f"""
O cálculo é uma **estimativa por Teoria de Resposta ao Item (TRI)**,
verificada contra notas oficiais dos microdados do INEP.

**Características:**
- Modelo Logístico de 3 Parâmetros (ML3)
- Estimação EAP (Expected a Posteriori)
- Coeficientes de equalização calibrados

**Validação:**
- Cada prova é conferida em holdout de participantes reais
- A interface mostra erro médio e maior diferença observada

[Consulte o relatório técnico completo, com métricas e erros por prova]({APP_VALIDATION_REPORT_URL})
"""

TEXTO_FOOTER = f"""
<div class="footer">
    <p>
        <strong>Calculadora Nota TRI ENEM</strong> | 
        Desenvolvido por <a href="{APP_AUTHOR_URL}" target="_blank">{APP_AUTHOR}</a> |
        <a href="{APP_GITHUB_URL}" target="_blank">GitHub</a>
    </p>
    <p style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
        Este projeto é <strong>gratuito</strong> e de <strong>uso livre</strong> para estudantes, professores e pesquisadores. Uso comercial requer autorização.
    </p>
    <p style="font-size: 0.8rem; color: #888;">
        Estimativa TRI validada em microdados oficiais; a precisão é informada por prova
    </p>
</div>

<!-- Citação Carl Sagan -->
<hr>
<div style="text-align: center; font-style: italic; color: #666; padding: 1rem; max-width: 800px; margin: 0 auto;">
    <p style="font-size: 0.9rem; line-height: 1.6;">
        "Nós organizamos uma sociedade baseada em ciência e tecnologia, na qual ninguém entende nada de ciência e tecnologia. 
        E essa mistura inflamável de ignorância e poder, mais cedo ou mais tarde, vai explodir na nossa cara. 
        Quem está no comando da ciência e tecnologia em uma democracia se as pessoas não sabem nada sobre isso?"
    </p>
    <p style="font-size: 0.85rem; margin-top: 0.5rem;">
        — <strong>Carl Sagan</strong>
    </p>
</div>
"""

TEXTO_ABOUT_MENU = f"""
# Calculadora Nota TRI ENEM

Estime sua nota do ENEM usando **Teoria de Resposta ao Item (TRI)**,
com precisão verificada por prova em microdados oficiais do INEP.

Ferramenta gratuita para estudantes, professores e pesquisadores.

Acesse: https://notatri.com

Desenvolvido por {APP_AUTHOR} - Engenharia de Computação UFRGS.

[GitHub]({APP_GITHUB_URL}) | 
[LinkedIn]({APP_AUTHOR_URL})
"""
