#!/usr/bin/env python3
"""
运行10轮多智能体政治模拟 - 快速版本（无LLM，规则决策）
用于测试经济系统和博弈论逻辑
"""
import sys
import os
import random

# 添加路径
sys.path.insert(0, '/tmp/mirofish/backend')
sys.path.insert(0, '/tmp/mirofish/backend/app/services')
os.chdir('/tmp/mirofish/backend')

from multi_agent_political_simulation import MultiAgentPoliticalSimulation, DiplomaticAction

class QuickSimulation(MultiAgentPoliticalSimulation):
    """快速版本：使用规则决策替代LLM"""
    
    async def _generate_agent_decision_async(self, agent, scenario, context, round_num):
        """规则决策：绕过LLM，直接返回规则决策"""
        # 直接返回规则决策，不调用LLM
        return self._rule_based_decision(agent)
    
    def _rule_based_decision(self, agent):
        """基于规则的决策"""
        # 国家立场
        country_stances = {
            "usa": {"escalate": 0.4, "deter": 0.2, "cooperate": 0.3, "negotiate": 0.1},
            "china": {"escalate": 0.1, "deter": 0.1, "cooperate": 0.4, "negotiate": 0.4},
            "russia": {"escalate": 0.2, "deter": 0.2, "cooperate": 0.3, "negotiate": 0.3},
            "eu": {"escalate": 0.1, "deter": 0.1, "cooperate": 0.4, "negotiate": 0.4},
            "iran": {"escalate": 0.5, "deter": 0.3, "cooperate": 0.1, "negotiate": 0.1},
            "israel": {"escalate": 0.5, "deter": 0.3, "cooperate": 0.1, "negotiate": 0.1},
            "saudi": {"escalate": 0.2, "deter": 0.3, "cooperate": 0.3, "negotiate": 0.2},
            "india": {"escalate": 0.2, "deter": 0.2, "cooperate": 0.3, "negotiate": 0.3},
            "japan": {"escalate": 0.1, "deter": 0.2, "cooperate": 0.4, "negotiate": 0.3},
            "uk": {"escalate": 0.2, "deter": 0.2, "cooperate": 0.4, "negotiate": 0.2},
            "south_korea": {"escalate": 0.1, "deter": 0.2, "cooperate": 0.4, "negotiate": 0.3},
            "north_korea": {"escalate": 0.3, "deter": 0.3, "cooperate": 0.2, "negotiate": 0.2},
            "turkey": {"escalate": 0.2, "deter": 0.2, "cooperate": 0.3, "negotiate": 0.3},
        }
        
        country = agent.country.lower()
        stances = country_stances.get(country, {"cooperate": 0.5, "negotiate": 0.5})
        
        # 疲劳高时更倾向于合作
        if agent.war_exhaustion > 0.5:
            stances = {"escalate": 0.1, "deter": 0.2, "cooperate": 0.4, "negotiate": 0.3}
        
        # 资源低时更倾向于合作
        if agent.resources < 30:
            stances = {"escalate": 0.1, "deter": 0.1, "cooperate": 0.5, "negotiate": 0.3}
        
        # 随机选择
        r = random.random()
        cumulative = 0
        chosen_action = DiplomaticAction.COOPERATE
        for action, prob in stances.items():
            cumulative += prob
            if r <= cumulative:
                chosen_action = DiplomaticAction(action)
                break
        
        return {
            "agent_id": agent.agent_id,
            "decision": {
                "action": chosen_action,
                "target": "global",
                "reasoning": f"[规则] 国家={country}, 疲劳={agent.war_exhaustion:.2f}, 资源={agent.resources:.1f}"
            }
        }

sim = QuickSimulation()

scenario = '波斯湾战争：伊朗封锁霍尔木兹海峡'
context = '''2026年4月，中东局势急剧恶化。伊朗封锁霍尔木兹海峡。
油价暴涨300%。美国航母部署至波斯湾，以色列空袭伊朗核设施。

初始状态（基于2026年4月真实报告）:
- 伊朗：资源35，疲劳0.65
- 美国：资源85，疲劳0.25
- 以色列：资源70，疲劳0.45
- 中国：资源90，疲劳0.15
- 俄罗斯：资源75，疲劳0.20
- 欧盟：资源60，疲劳0.30
'''

print('='*60)
print('MiroFish 72智能体 × 10轮 快速模拟（规则决策）')
print('='*60)
print(f'场景: {scenario}')
print('='*60)

sim.run_full_simulation(scenario, context, rounds=10)
