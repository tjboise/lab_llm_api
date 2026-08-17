#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
set -a
source .env
set +a

SPARK_VLLM_DIR="$HOME/Desktop/spark-vllm-docker"

"$SPARK_VLLM_DIR/launch-cluster.sh" --solo --name vllm_vl_node -d -p 8081:8000 exec \
  vllm serve Qwen/Qwen3-VL-8B-Instruct \
    --served-model-name qwen3-vl-8b \
    --host 0.0.0.0 \
    --port 8000 \
    --api-key "$VLLM_API_KEY" \
    --gpu-memory-utilization 0.22 \
    --max-model-len 32768 \
    --load-format fastsafetensors \
    --enable-prefix-caching
