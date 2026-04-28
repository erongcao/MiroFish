#!/bin/bash
# MiroFish Backend 启动脚本

cd /tmp/mirofish/backend

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3.11 -m venv .venv 2>/dev/null || python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（如果尚未安装）
if ! python3 -c "import flask" 2>/dev/null; then
    echo "安装依赖..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

# 启动后端
echo "启动 MiroFish Backend..."
python3 run.py
