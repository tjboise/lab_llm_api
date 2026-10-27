#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
set -a
source .env
set +a

SPARK_VLLM_DIR="$HOME/Desktop/spark-vllm-docker"

"$SPARK_VLLM_DIR/launch-cluster.sh" --solo -d -p 8080:8000 exec \
  vllm serve RedHatAI/Llama-4-Scout-17B-16E-Instruct-quantized.w4a16 \
    --served-model-name llama-4-scout \
    --host 0.0.0.0 \
    --port 8000 \
    --api-key "$VLLM_API_KEY" \
    --gpu-memory-utilization 0.70 \
    --max-model-len 16384 \
    --limit-mm-per-prompt '{"image": 4}' \
    --enable-prefix-caching
