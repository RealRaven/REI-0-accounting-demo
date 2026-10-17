#!/usr/bin/env bash
set -euo pipefail
MODEL="${LLM_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
python -c "from huggingface_hub import snapshot_download; snapshot_download('$MODEL')"