#!/bin/bash
# 运行10轮多智能体模拟 - 使用Kimi k2.6 API

export KIMI_API_KEY="sk-YRFqC7sQoxGKk90lNeBcBu9OJ9mjckrvVXjuf85Dv7tMxN0c"
export LLM_MODEL_NAME="kimi-k2.6"

# 重要：确保LLM_API_KEY未设置或为空，否则会优先使用Ollama
unset LLM_API_KEY

cd /tmp/mirofish/backend
source .venv/bin/activate
PYTHONUNBUFFERED=1 python run_10round_sim.py 2>&1
