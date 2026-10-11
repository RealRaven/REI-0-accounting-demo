#!/usr/bin/env bash
set -euo pipefail
MODEL="${LLM_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
exec vllm serve "$MODEL" --port 8001 --max-model-len 8192 --gpu-memory-utilization 0.90