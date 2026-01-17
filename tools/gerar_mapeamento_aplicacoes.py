"""
Gera mapeamento de provas focando na 1a aplicacao (mais confiavel).

METODOLOGIA:
- 1a Aplicacao: As 4 provas com MAIOR numero de participantes por area/ano
  (correspondem as 4 cores da aplicacao regular)
- Outras: Todas as demais provas (2a aplicacao, PPL, adaptadas, etc)

LIMITACOES:
- Classificacao baseada APENAS em numero de participantes
- Cores podem estar incorretas em anos antigos (pre-2016)
- Requer validacao manual para uso critico

TRABALHOS FUTUROS:
- Validar cores manualmente com cadernos de prova reais
- Identificar padrao de codigos por ano para classificar aplicacoes
- Integrar com dados oficiais do INEP quando disponiveis
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

BASE_PATH = Path(__file__).parent.parent / 'microdados_limpos'
OUTPUT_PATH = Path(__file__).parent.parent / 'src' / 'tri_enem'
DOCS_PATH = Path(__file__).parent.parent / 'docs'


def carregar_dados(ano):
    """Carrega itens e participantes de um ano."""
    itens_path = BASE_PATH / str(ano) / f'ITENS_PROVA_{ano}.csv'
    part_path = BASE_PATH / str(ano) / f'DADOS_ENEM_{ano}.csv'
    
    if not itens_path.exists() or not part_path.exists():
        return None, None
    
    itens = pd.read_csv(itens_path, sep=';', encoding='latin1')
    part = pd.read_csv(part_path, sep=';', encoding='latin1', low_memory=False)
    
    return itens, part


def gerar_mapeamento_ano(ano, itens, part):
    """Gera mapeamento para um ano."""
    resultado = {}
    
    tem_cor = 'TX_COR' in itens.columns
    
    for area in ['MT', 'CN', 'CH', 'LC']:
        col_prova = f'CO_PROVA_{area}'
        if col_prova not in part.columns:
            continue
        
        # Contar participantes por prova
        contagem = part[col_prova].value_counts().reset_index()
        contagem.columns = ['CO_PROVA', 'participantes']
        
        # Pegar cores se disponivel
        if tem_cor:
            cores = itens[itens['SG_AREA'] == area][['CO_PROVA', 'TX_COR']].drop_duplicates()
            contagem = contagem.merge(cores, on='CO_PROVA', how='left')
        else:
            contagem['TX_COR'] = 'COR_DESCONHECIDA'
        
        # Top 4 = 1a aplicacao (as 4 cores principais)
        top4 = contagem.head(4)
        outras = contagem.iloc[4:]
        
        resultado[area] = {
            'primeira_aplicacao': [],
            'outras_aplicacoes': []
        }
        
        for _, row in top4.iterrows():
            cor = str(row['TX_COR']).upper().strip() if pd.notna(row['TX_COR']) else 'COR_DESCONHECIDA'
            resultado[area]['primeira_aplicacao'].append({
                'cor': cor,
                'codigo': int(row['CO_PROVA']),
                'participantes': int(row['participantes'])
            })
        
        for _, row in outras.iterrows():
            cor = str(row['TX_COR']).upper().strip() if pd.notna(row['TX_COR']) else 'COR_DESCONHECIDA'
            resultado[area]['outras_aplicacoes'].append({
                'cor': cor,
                'codigo': int(row['CO_PROVA']),
                'participantes': int(row['participantes'])
            })
    
    return resultado


def gerar_mapeamento_completo():
    """Gera mapeamento para todos os anos."""
    mapeamento = {
        '_metadata': {
            'descricao': 'Mapeamento de provas ENEM por aplicacao e cor',
            'metodologia': 'Top 4 provas por participantes = 1a aplicacao',
            'limitacoes': [
                'Classificacao baseada em numero de participantes (inferencia)',
                'Nao distingue 2a aplicacao de PPL',
                'Cores podem estar incorretas em anos antigos',
                'Requer validacao manual para uso critico'
            ],
            'trabalhos_futuros': [
                'Validar cores com cadernos reais',
                'Mapear padroes de codigo por ano',
                'Integrar dados oficiais INEP'
            ],
            'confiabilidade': {
                'primeira_aplicacao': 'ALTA - Top 4 por participantes',
                'outras_aplicacoes': 'BAIXA - Mistura 2a aplicacao, PPL, adaptadas'
            }
        }
    }
    
    print("Gerando mapeamento de provas...")
    
    for ano in range(2009, 2025):
        print(f"  {ano}...", end=" ")
        itens, part = carregar_dados(ano)
        
        if itens is None:
            print("sem dados")
            continue
        
        mapeamento[str(ano)] = gerar_mapeamento_ano(ano, itens, part)
        print("ok")
    
    return mapeamento


def gerar_guia_estudante(mapeamento):
    """Gera guia simplificado para estudantes."""
    linhas = []
    
    linhas.append("# Guia de Provas do ENEM - Codigos por Cor e Aplicacao")
    linhas.append("")
    linhas.append("## AVISO IMPORTANTE")
    linhas.append("")
    linhas.append("Este mapeamento foi gerado por **inferencia estatistica** baseada no")
    linhas.append("numero de participantes por prova. **NAO foi validado manualmente**.")
    linhas.append("")
    linhas.append("**Limitacoes:**")
    linhas.append("- A classificacao de cores pode estar incorreta")
    linhas.append("- 'Outras aplicacoes' mistura 2a chamada, PPL e provas adaptadas")
    linhas.append("- Anos antigos (pre-2016) tem menos metadados disponiveis")
    linhas.append("")
    linhas.append("**Confiabilidade:**")
    linhas.append("- **1a Aplicacao**: ALTA (top 4 provas por participantes)")
    linhas.append("- **Outras**: BAIXA (requer validacao futura)")
    linhas.append("")
    linhas.append("---")
    linhas.append("")
    linhas.append("## Como usar o calculador")
    linhas.append("")
    linhas.append("O calculador TRI **precisa do codigo correto da prova** para maxima precisao.")
    linhas.append("Se voce nao informar, ele usa a primeira prova disponivel, que pode nao ser a sua.")
    linhas.append("")
    linhas.append("```python")
    linhas.append("from tri_enem import SimuladorNota")
    linhas.append("")
    linhas.append("sim = SimuladorNota()")
    linhas.append("")
    linhas.append("# COM codigo (recomendado se souber)")
    linhas.append("resultado = sim.calcular('MT', 2023, respostas, co_prova=1211)  # Azul")
    linhas.append("")
    linhas.append("# SEM codigo (usa primeira prova - pode nao ser a sua)")
    linhas.append("resultado = sim.calcular('MT', 2023, respostas)")
    linhas.append("```")
    linhas.append("")
    linhas.append("---")
    linhas.append("")
    
    for ano in range(2024, 2008, -1):
        ano_str = str(ano)
        if ano_str not in mapeamento or ano_str == '_metadata':
            continue
        
        dados = mapeamento[ano_str]
        
        linhas.append(f"## ENEM {ano}")
        linhas.append("")
        
        # Tabela resumo 1a aplicacao
        linhas.append("### 1a Aplicacao (Regular)")
        linhas.append("")
        linhas.append("| Area | Cor | Codigo | Participantes |")
        linhas.append("|------|-----|--------|---------------|")
        
        for area in ['MT', 'CN', 'CH', 'LC']:
            if area not in dados:
                continue
            for prova in dados[area]['primeira_aplicacao']:
                linhas.append(f"| {area} | {prova['cor']} | {prova['codigo']} | {prova['participantes']:,} |")
        
        linhas.append("")
        
        # Outras aplicacoes (resumido)
        tem_outras = any(
            len(dados[area]['outras_aplicacoes']) > 0 
            for area in ['MT', 'CN', 'CH', 'LC'] if area in dados
        )
        
        if tem_outras:
            linhas.append("### Outras Aplicacoes (2a chamada, PPL, adaptadas)")
            linhas.append("")
            linhas.append("<details>")
            linhas.append("<summary>Clique para expandir</summary>")
            linhas.append("")
            linhas.append("| Area | Cor/Tipo | Codigo | Participantes |")
            linhas.append("|------|----------|--------|---------------|")
            
            for area in ['MT', 'CN', 'CH', 'LC']:
                if area not in dados:
                    continue
                for prova in dados[area]['outras_aplicacoes'][:10]:  # Limitar a 10
                    linhas.append(f"| {area} | {prova['cor']} | {prova['codigo']} | {prova['participantes']:,} |")
            
            linhas.append("")
            linhas.append("</details>")
            linhas.append("")
        
        linhas.append("---")
        linhas.append("")
    
    linhas.append("## Trabalhos Futuros")
    linhas.append("")
    linhas.append("- [ ] Validar cores com cadernos de prova reais")
    linhas.append("- [ ] Identificar padrao de codigos para cada tipo de aplicacao")
    linhas.append("- [ ] Separar corretamente 2a aplicacao de PPL")
    linhas.append("- [ ] Adicionar provas digitais (2020+)")
    linhas.append("- [ ] Integrar com dados oficiais do INEP")
    linhas.append("")
    linhas.append("---")
    linhas.append("")
    linhas.append("*Gerado automaticamente. Para regenerar: `python tools/gerar_mapeamento_aplicacoes.py`*")
    
    return '\n'.join(linhas)


if __name__ == '__main__':
    mapeamento = gerar_mapeamento_completo()
    
    # Salvar JSON
    json_file = OUTPUT_PATH / 'provas_por_aplicacao.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(mapeamento, f, ensure_ascii=False, indent=2)
    print(f"\nJSON salvo: {json_file}")
    
    # Salvar Guia
    guia = gerar_guia_estudante(mapeamento)
    guia_file = DOCS_PATH / 'GUIA_PROVAS.md'
    with open(guia_file, 'w', encoding='utf-8') as f:
        f.write(guia)
    print(f"Guia salvo: {guia_file}")
