#!/usr/bin/env python3
"""
运行多智能体政治模拟 - 集成Neo4j图数据库
每轮结束后自动将Agent关系和博弈结果持久化到Neo4j
"""
import sys
import os

# 设置环境变量
os.environ['DASHSCOPE_API_KEY'] = 'sk-00a5136c6276471fa72db5928c613e1a'
os.environ['DASHSCOPE_MODEL'] = 'qwen-plus'
os.environ.pop('LLM_API_KEY', None)
os.environ.pop('KIMI_API_KEY', None)

# 添加路径
sys.path.insert(0, '/tmp/mirofish/backend')
sys.path.insert(0, '/tmp/mirofish/backend/app/services')
os.chdir('/tmp/mirofish/backend')

from multi_agent_political_simulation import MultiAgentPoliticalSimulation

# 使用DashScope + Neo4j
sim = MultiAgentPoliticalSimulation("dashscope")

scenario = '波斯湾战争：伊朗封锁霍尔木兹海峡'
context = '''2026年4月，中东地区紧张局势持续。伊朗与美国的对峙导致霍尔木兹海峡通行受阻。
全球能源供应受到关注，油价从80美元上涨至350美元。
美国在中东保持军事存在，以色列对伊朗核计划表示关切。
欧盟、中国、俄罗斯呼吁各方通过外交途径解决分歧。

初始状态:
- 伊朗：资源35
- 美国：资源85
- 以色列：资源70
- 中国：资源90
- 俄罗斯：资源75
- 欧盟：资源60'''

print('='*60)
print('MiroFish 72智能体 × 博弈论模拟 + Neo4j持久化')
print('='*60)
print(f'场景: {scenario}')
print(f'LLM: DashScope qwen-plus')
print(f'图数据库: Neo4j (bolt://localhost:7687)')
print('='*60)

sim.run_full_simulation(scenario, context, rounds=5)
