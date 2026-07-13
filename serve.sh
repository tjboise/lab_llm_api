#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
set -a
source .env
set +a

SPARK_VLLM_DIR="$HOME/Desktop/spark-vllm-docker"

"$SPARK_VLLM_DIR/launch-cluster.sh" --solo -d -p 8000:8000 exec \
  vllm serve Qwen/Qwen3-32B \
    --served-model-name qwen3-32b \
    --host 0.0.0.0 \
    --port 8000 \
    --api-key "$VLLM_API_KEY" \
    --gpu-memory-utilization 0.85 \
    --max-model-len 32768 \
    --load-format fastsafetensors \
    --enable-prefix-caching \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --reasoning-parser qwen3
