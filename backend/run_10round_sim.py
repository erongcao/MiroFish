#!/usr/bin/env python3
"""
运行10轮多智能体政治模拟
"""
import sys
import os

# 重要：在导入任何模块之前设置环境变量
os.environ['KIMI_API_KEY'] = 'sk-YRFqC7sQoxGKk90lNeBcBu9OJ9mjckrvVXjuf85Dv7tMxN0c'
os.environ['LLM_MODEL_NAME'] = 'kimi-k2.6'
os.environ.pop('LLM_API_KEY', None)  # 确保不使用Ollama

# 添加路径 - 关键：需要同时添加 backend root 和 app/services
sys.path.insert(0, '/tmp/mirofish/backend')
sys.path.insert(0, '/tmp/mirofish/backend/app/services')
os.chdir('/tmp/mirofish/backend')

from multi_agent_political_simulation import MultiAgentPoliticalSimulation

# 明确使用Kimi provider进行LLM调用
sim = MultiAgentPoliticalSimulation("kimi")

scenario = '波斯湾战争：伊朗封锁霍尔木兹海峡'
context = '''2026年4月，中东局势急剧恶化。伊朗以"抵抗以色列侵略"为由，宣布封锁霍尔木兹海峡。
全球25%的石油供应受到威胁，油价从80美元暴涨至350美元。
美国航母战斗群已部署至波斯湾，以色列对伊朗核设施发动先发制人打击。
欧盟、中国、俄罗斯呼吁各方保持克制。

初始状态（基于2026年4月真实报告）:
- 伊朗：资源35，战争疲劳0.65（GDP的65%被摧毁）
- 美国：资源85，战争疲劳0.25（13人死亡，365人受伤）
- 以色列：资源70，战争疲劳0.45
- 中国：资源90，战争疲劳0.15
- 俄罗斯：资源75，战争疲劳0.20
- 欧盟：资源60，战争疲劳0.30
'''

print('='*60)
print('MiroFish 72智能体 × 10轮 博弈论模拟')
print('='*60)
print(f'场景: {scenario}')
print('='*60)

sim.run_full_simulation(scenario, context, rounds=10)
