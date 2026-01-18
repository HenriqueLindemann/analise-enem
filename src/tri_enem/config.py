"""
Configurações de classificação para análise TRI do ENEM.

Este arquivo centraliza os limiares e configurações usados na análise.
Modifique aqui para ajustar as classificações de dificuldade, cores, etc.
"""

# ==============================================================================
#                    CLASSIFICAÇÃO DE DIFICULDADE
# ==============================================================================

# Limiares do parâmetro B (dificuldade na escala TRI)
# Quanto maior o valor, mais difícil a questão
# Escala típica: -3 a +3, centrada em 0

LIMIARES_DIFICULDADE = {
    'muito_facil': (-float('inf'), -1.0),  # b < -1.0
    'facil': (-1.0, 0.0),                   # -1.0 <= b < 0.0
    'media': (0.0, 1.0),                    # 0.0 <= b < 1.0
    'dificil': (1.0, 2.0),                  # 1.0 <= b < 2.0
    'muito_dificil': (2.0, float('inf')),   # b >= 2.0
}

# Nomes para exibição
NOMES_DIFICULDADE = {
    'muito_facil': 'Muito Fácil',
    'facil': 'Fácil',
    'media': 'Média',
    'dificil': 'Difícil',
    'muito_dificil': 'Muito Difícil',
}

# Cores para cada nível (formato RGB 0-1 para reportlab, ou hex para outros)
CORES_DIFICULDADE = {
    'muito_facil': (0.2, 0.8, 0.2),   # Verde claro
    'facil': (0.4, 0.9, 0.4),          # Verde
    'media': (1.0, 0.8, 0.2),          # Amarelo
    'dificil': (1.0, 0.5, 0.2),        # Laranja
    'muito_dificil': (0.9, 0.2, 0.2),  # Vermelho
}

# Cores hexadecimais (para HTML/Web)
CORES_DIFICULDADE_HEX = {
    'muito_facil': '#4CAF50',
    'facil': '#8BC34A',
    'media': '#FFC107',
    'dificil': '#FF9800',
    'muito_dificil': '#F44336',
}

# ==============================================================================
#                    FUNÇÕES DE CLASSIFICAÇÃO
# ==============================================================================

def classificar_dificuldade(param_b: float) -> str:
    """
    Classifica a dificuldade do item baseado no parâmetro B.
    
    Args:
        param_b: Parâmetro B de dificuldade (escala TRI)
        
    Returns:
        Chave do nível de dificuldade ('muito_facil', 'facil', etc.)
    """
    for nivel, (min_val, max_val) in LIMIARES_DIFICULDADE.items():
        if min_val <= param_b < max_val:
            return nivel
    return 'media'  # fallback


def nome_dificuldade(param_b: float) -> str:
    """Retorna o nome legível da dificuldade."""
    nivel = classificar_dificuldade(param_b)
    return NOMES_DIFICULDADE.get(nivel, 'Média')


def cor_dificuldade(param_b: float) -> tuple:
    """Retorna a cor RGB para o nível de dificuldade."""
    nivel = classificar_dificuldade(param_b)
    return CORES_DIFICULDADE.get(nivel, (0.5, 0.5, 0.5))


# ==============================================================================
#                    CONFIGURAÇÕES DE RELATÓRIO
# ==============================================================================

# Configurações do PDF
PDF_CONFIG = {
    'page_size': 'A4',
    'margin_left': 50,
    'margin_right': 50,
    'margin_top': 50,
    'margin_bottom': 50,
    'font_family': 'Helvetica',
    'font_size_title': 18,
    'font_size_header': 14,
    'font_size_body': 10,
    'font_size_small': 8,
}

# Nomes das áreas
NOMES_AREAS = {
    'MT': 'Matemática e suas Tecnologias',
    'CN': 'Ciências da Natureza e suas Tecnologias',
    'CH': 'Ciências Humanas e suas Tecnologias',
    'LC': 'Linguagens, Códigos e suas Tecnologias',
}

NOMES_AREAS_CURTO = {
    'MT': 'Matemática',
    'CN': 'Ciências da Natureza',
    'CH': 'Ciências Humanas',
    'LC': 'Linguagens',
}