#!/usr/bin/env bash
# Gera o vídeo Nota TRI ENEM: dados do motor → trilha → verificação → quadros → MP4 → stills.
# Uso: ./video/build.sh [site|reels ...]   (PUBLICAR=1 atualiza os arquivos versionados do app/README)
set -euo pipefail

VIDEO="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$VIDEO/.." && pwd)"
PY_RENDER="${PY_RENDER:-python3}"
PY_DATA="${PY_DATA:-$REPO/.venv/bin/python}"
PARTS="${PARTS:-8}"
JOBS="${JOBS:-4}"
FORMATOS=("${@:-site}")

cd "$VIDEO"

echo '[dados] Extraindo dados do motor TRI'
"$PY_DATA" -m filme dados

for FMT in "${FORMATOS[@]}"; do
    PASTA="$VIDEO/saida/$FMT"
    mkdir -p "$PASTA/parts" "$PASTA/stills"
    rm -f "$PASTA/parts"/p*.mp4 "$PASTA/stills"/f_*.png "$PASTA/stills-safe"/f_*.png

    echo "[$FMT 1/5] Trilha sincronizada e masterização"
    "$PY_RENDER" -m filme --formato "$FMT" trilha

    echo "[$FMT 2/5] Verificação de conteúdo, continuidade e sincronia"
    "$PY_RENDER" -m filme --formato "$FMT" verificar

    echo "[$FMT 3/5] Renderização dos quadros ($PARTS partes, $JOBS processos)"
    TOTAL=$("$PY_RENDER" -m filme --formato "$FMT" quadros)
    STEP=$(( (TOTAL + PARTS - 1) / PARTS ))
    for ((i=0; i<PARTS; i++)); do
        start=$(( i * STEP ))
        end=$(( start + STEP < TOTAL ? start + STEP : TOTAL ))
        echo "  parte $((i+1))/$PARTS: quadros $start..$end"
        nice -n 10 "$PY_RENDER" -m filme --formato "$FMT" quadros "$start" "$end" "$PASTA/parts/p$i.mp4" &
        while (( $(jobs -rp | wc -l) >= JOBS )); do wait -n; done
    done
    wait

    echo "[$FMT 4/5] Montagem e validação do MP4"
    "$PY_RENDER" -m filme --formato "$FMT" montar

    echo "[$FMT 5/5] Stills de revisão"
    "$PY_RENDER" -m filme --formato "$FMT" stills

    if [[ "${PUBLICAR:-0}" == "1" ]]; then
        echo "[$FMT] Publicando arquivos versionados"
        "$PY_RENDER" -m filme --formato "$FMT" publicar
    fi

    rm -rf "$PASTA/parts" "$PASTA/trilha.wav"
    printf 'Concluído: %s/nota-tri-%s.mp4\n' "$PASTA" "$FMT"
done
