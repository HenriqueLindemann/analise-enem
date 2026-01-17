"""
Script para limpar os microdados do ENEM, removendo colunas não essenciais.
Processa em chunks para evitar erro de memória.

Execute a partir da raiz do projeto:
    python tools/limpar_microdados.py
"""

import pandas as pd
import os
from pathlib import Path

# Colunas essenciais para cálculo de notas e análise
COLUNAS_ESSENCIAIS = [
    'NU_INSCRICAO',
    'TP_PRESENCA_CN',
    'TP_PRESENCA_CH',
    'TP_PRESENCA_LC',
    'TP_PRESENCA_MT',
    'CO_PROVA_CN',
    'CO_PROVA_CH',
    'CO_PROVA_LC',
    'CO_PROVA_MT',
    'NU_NOTA_CN',
    'NU_NOTA_CH',
    'NU_NOTA_LC',
    'NU_NOTA_MT',
    'TX_RESPOSTAS_CN',
    'TX_RESPOSTAS_CH',
    'TX_RESPOSTAS_LC',
    'TX_RESPOSTAS_MT',
    'TP_LINGUA',
    'TP_STATUS_REDACAO',
    'NU_NOTA_COMP1',
    'NU_NOTA_COMP2',
    'NU_NOTA_COMP3',
    'NU_NOTA_COMP4',
    'NU_NOTA_COMP5',
    'NU_NOTA_REDACAO',
]

# Para 2024 - RESULTADOS (usa NU_SEQUENCIAL ao invés de NU_INSCRICAO)
COLUNAS_RESULTADOS_2024 = [
    'NU_SEQUENCIAL',
    'TP_PRESENCA_CN',
    'TP_PRESENCA_CH',
    'TP_PRESENCA_LC',
    'TP_PRESENCA_MT',
    'CO_PROVA_CN',
    'CO_PROVA_CH',
    'CO_PROVA_LC',
    'CO_PROVA_MT',
    'NU_NOTA_CN',
    'NU_NOTA_CH',
    'NU_NOTA_LC',
    'NU_NOTA_MT',
    'TX_RESPOSTAS_CN',
    'TX_RESPOSTAS_CH',
    'TX_RESPOSTAS_LC',
    'TX_RESPOSTAS_MT',
    'TP_LINGUA',
    'TP_STATUS_REDACAO',
    'NU_NOTA_COMP1',
    'NU_NOTA_COMP2',
    'NU_NOTA_COMP3',
    'NU_NOTA_COMP4',
    'NU_NOTA_COMP5',
    'NU_NOTA_REDACAO',
]

CHUNK_SIZE = 100_000  # Processar 100k linhas por vez


def limpar_arquivo_chunked(ano, colunas_lista=None):
    """Limpa arquivo de microdados processando em chunks para evitar OOM"""
    if colunas_lista is None:
        colunas_lista = COLUNAS_ESSENCIAIS
    
    if ano == 2024:
        arquivo_origem = f'microdados/{ano}/RESULTADOS_{ano}.csv'
        arquivo_destino = f'microdados_limpos/{ano}/DADOS_ENEM_{ano}.csv'
    else:
        arquivo_origem = f'microdados/{ano}/MICRODADOS_ENEM_{ano}.csv'
        arquivo_destino = f'microdados_limpos/{ano}/DADOS_ENEM_{ano}.csv'
    
    if not os.path.exists(arquivo_origem):
        print(f"❌ Arquivo não encontrado: {arquivo_origem}")
        return 0, 0
    
    print(f"📁 Processando {ano}...")
    
    tamanho_original = os.path.getsize(arquivo_origem) / (1024 * 1024)
    print(f"   Original: {tamanho_original:.2f} MB")
    
    # Criar diretório de destino
    Path(f'microdados_limpos/{ano}').mkdir(parents=True, exist_ok=True)
    
    # Ler header para descobrir quais colunas existem
    df_header = pd.read_csv(arquivo_origem, encoding='latin1', sep=';', nrows=0)
    colunas_manter = [col for col in colunas_lista if col in df_header.columns]
    
    # Processar em chunks
    primeiro_chunk = True
    total_linhas = 0
    
    for chunk in pd.read_csv(
        arquivo_origem, 
        encoding='latin1', 
        sep=';', 
        usecols=colunas_manter,
        chunksize=CHUNK_SIZE,
        low_memory=False
    ):
        total_linhas += len(chunk)
        
        if primeiro_chunk:
            chunk.to_csv(arquivo_destino, index=False, encoding='utf-8', sep=';', mode='w')
            primeiro_chunk = False
        else:
            chunk.to_csv(arquivo_destino, index=False, encoding='utf-8', sep=';', mode='a', header=False)
        
        print(f"   ... {total_linhas:,} linhas processadas", end='\r')
    
    tamanho_limpo = os.path.getsize(arquivo_destino) / (1024 * 1024)
    reducao = ((tamanho_original - tamanho_limpo) / tamanho_original) * 100
    
    print(f"   Limpo:    {total_linhas:,} linhas, {len(colunas_manter)} colunas, {tamanho_limpo:.2f} MB")
    print(f"   ✅ Redução: {reducao:.1f}% ({tamanho_original - tamanho_limpo:.2f} MB economizados)")
    print()
    
    return tamanho_original, tamanho_limpo


def copiar_itens_prova():
    """Copia os arquivos ITENS_PROVA (já são pequenos)"""
    print("📋 Copiando arquivos ITENS_PROVA...")
    total = 0
    for ano in range(2009, 2025):
        arquivo_origem = f'microdados/{ano}/ITENS_PROVA_{ano}.csv'
        arquivo_destino = f'microdados_limpos/{ano}/ITENS_PROVA_{ano}.csv'
        
        if os.path.exists(arquivo_origem):
            Path(f'microdados_limpos/{ano}').mkdir(parents=True, exist_ok=True)
            df = pd.read_csv(arquivo_origem, encoding='latin1', sep=';')
            df.to_csv(arquivo_destino, index=False, encoding='utf-8', sep=';')
            total += os.path.getsize(arquivo_destino) / (1024 * 1024)
    print(f"✅ Arquivos ITENS_PROVA copiados ({total:.2f} MB total)\n")
    return total


def main():
    print("=" * 70)
    print("LIMPEZA DE MICRODADOS DO ENEM")
    print("=" * 70)
    print()
    
    total_original = 0
    total_limpo = 0
    
    # Processar anos 2009-2023
    for ano in range(2009, 2024):
        orig, limpo = limpar_arquivo_chunked(ano, COLUNAS_ESSENCIAIS)
        total_original += orig
        total_limpo += limpo
    
    # Processar 2024 (arquitetura diferente)
    orig, limpo = limpar_arquivo_chunked(2024, COLUNAS_RESULTADOS_2024)
    total_original += orig
    total_limpo += limpo
    
    # Copiar ITENS_PROVA
    itens_total = copiar_itens_prova()
    total_limpo += itens_total
    
    print("=" * 70)
    print("✅ LIMPEZA CONCLUÍDA!")
    print("=" * 70)
    print()
    
    import glob
    tamanho_total = sum(os.path.getsize(f) for f in glob.glob('microdados_limpos/**/*.csv', recursive=True))
    tamanho_total_mb = tamanho_total / (1024 * 1024)
    tamanho_total_gb = tamanho_total / (1024 * 1024 * 1024)
    
    print(f"📊 Tamanho original total: {total_original:.2f} MB ({total_original/1024:.2f} GB)")
    print(f"📊 Tamanho limpo total:    {tamanho_total_mb:.2f} MB ({tamanho_total_gb:.2f} GB)")
    print(f"📊 Economia total:         {total_original - tamanho_total_mb:.2f} MB")
    print()
    
    if tamanho_total_gb < 5:
        print("✅ Os arquivos cabem no limite do GitHub Pro Student (5GB)")
    else:
        print("⚠️  Os arquivos ainda excedem 5GB. Considere compressão adicional.")


if __name__ == "__main__":
    main()
