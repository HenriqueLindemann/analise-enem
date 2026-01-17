#!/bin/bash

# Script de Automação da Análise do ENEM 2021
# Executa o fluxo completo: Limpeza -> Análise Geral -> Visualizações -> Análise TRI

set -e  # Para o script se houver erro

echo "============================================================"
echo "🚀 INICIANDO FLUXO DE ANÁLISE AUTOMATIZADA"
echo "============================================================"

# 1. Limpeza dos resultados anteriores
echo -n "[1/4] Limpando resultados anteriores... "
rm -rf graficos/*.png
rm -rf graficos_tri/*.png
echo "Concluído!"

# 2. Análise Geral (Estatísticas e Percentis)
echo "[2/4] Executando Análise Geral (analise_participante.py)..."
python3 analise_participante.py
echo ""

# 3. Geração de Visualizações Gerais
echo "[3/4] Gerando Visualizações Gerais (visualizacoes_analise.py)..."
python3 visualizacoes_analise.py
echo ""

# 4. Análise TRI Detalhada
echo "[4/4] Executando Análise TRI (analise_tri_final.py)..."
python3 analise_tri_final.py
echo ""

echo "============================================================"
echo "✅ ANÁLISE COMPLETA CONCLUÍDA COM SUCESSO!"
echo "============================================================"
echo "📂 Resultados disponíveis em:"
echo "   - Relatórios gerais: Ver output acima"
echo "   - Gráficos gerais:   graficos/"
echo "   - Gráficos TRI:      graficos_tri/"
