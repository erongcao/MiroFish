"""
Multi-Agent Political Simulation - 多智能体政治模拟
所有势力都是独立的Agent，互相博弈形成复杂的局势
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

from game_theory_diplomacy import (
    GameTheoryDiplomacy, DiplomaticAction, ConflictLevel,
    AgentDiplomaticState, PayoffMatrix
)
from llm_political_game import LLMClient, FORCE_CHARACTERS
from us_political_forces import US_POLITICAL_FORCES
from china_political_forces import CHINA_POLITICAL_FORCES
from russia_political_forces import RUSSIA_POLITICAL_FORCES
from eu_political_forces import EU_POLITICAL_FORCES

@dataclass
class Agent:
    """智能体"""
    agent_id: str
    name: str
    country: str
    force_type: str  # "government", "military", "financial", "lobby", etc.
    
    # 能力
    power: float = 0.5  # 影响力/国力
    resources: float = 100.0
    credibility: float = 1.0
    
    # 立场
    stance: Dict[str, float] = field(default=dict)  # 对其他国家的立场
    
    # 博弈状态
    reputation: float = 0.0
    war_exhaustion: float = 0.0
    trust: Dict[str, float] = field(default=dict)
    
    # 联盟和敌对
    allies: Set[str] = field(default_factory=set)
    enemies: Set[str] = field(default_factory=set)
    
    # 当前行动
    current_action: DiplomaticAction = DiplomaticAction.COOPERATE
    current_target: str = ""
    
    # 政府内部关系（如果是政府官员）
    government_role: str = ""  # "president", "secretary_of_state", "general", etc.
    faction: str = ""  # " Hawks", "doves", "pragmatists"
    
    def get_alliance_power(self, all_agents: Dict[str, 'Agent']) -> float:
        """计算联盟总力量"""
        total = self.power
        for ally_id in self.allies:
            if ally_id in all_agents:
                total += all_agents[ally_id].power * 0.5
        return total
    
    def get_enemy_threat(self, all_agents: Dict[str, 'Agent']) -> float:
        """计算敌对威胁"""
        total = 0.0
        for enemy_id in self.enemies:
            if enemy_id in all_agents:
                total += all_agents[enemy_id].power
        return total


class MultiAgentPoliticalSimulation:
    """多智能体政治模拟系统"""
    
    def __init__(self, llm_provider: str = "ollama"):
        self.llm = LLMClient(llm_provider)
        
        # 所有智能体
        self.agents: Dict[str, Agent] = {}
        
        # 博弈论引擎
        self.gt_engine = GameTheoryDiplomacy()
        
        # 历史记录
        self.round_history: List[Dict] = []
        
        # 初始化所有势力Agent
        self._initialize_all_agents()
    
    def _initialize_all_agents(self):
        """初始化所有势力Agent"""
        print("\n" + "="*60)
        print("初始化多智能体系统")
        print("="*60)
        
        # 1. 美国势力 (14个)
        for force_id, force in US_POLITICAL_FORCES.items():
            agent = Agent(
                agent_id=f"us_{force_id}",
                name=f"美国{force.name_cn}",
                country="usa",
                force_type=force.force_type,
                power=force.overall_influence * 0.8,
                resources=100.0,
                stance={
                    "china": force.stance_china,
                    "russia": force.stance_russia,
                    "iran": force.stance_middle_east,
                },
            )
            
            # 设置初始盟友/敌对
            if force.party_alignment == "bipartisan":
                agent.allies.add("us_military_industrial")
            if force.force_type == "military_industrial":
                agent.enemies.update(["cn_military_red", "ru_siloviki"])
            
            self.agents[agent.agent_id] = agent
            print(f"  [美国] {agent.name} (power={agent.power:.2f})")
        
        # 2. 中国势力 (10个)
        for force_id, force in CHINA_POLITICAL_FORCES.items():
            agent = Agent(
                agent_id=f"cn_{force_id}",
                name=f"中国{force.name_cn}",
                country="china",
                force_type=getattr(force, 'force_type', force.ideology),  # 使用force_type或ideology
                power=force.overall_influence * 0.8,
                resources=100.0,
                stance={
                    "usa": getattr(force, 'stance_usa', 0),
                    "russia": getattr(force, 'stance_russia', 0),
                    "taiwan": getattr(force, 'stance_taiwan', 0),
                },
            )
            
            self.agents[agent.agent_id] = agent
            print(f"  [中国] {agent.name} (power={agent.power:.2f})")
        
        # 3. 俄罗斯势力 (9个)
        for force_id, force in RUSSIA_POLITICAL_FORCES.items():
            agent = Agent(
                agent_id=f"ru_{force_id}",
                name=f"俄罗斯{force.name_cn}",
                country="russia",
                force_type=getattr(force, 'force_type', 'security'),  # 默认为security
                power=force.overall_influence * 0.8,
                resources=100.0,
                stance={
                    "west": getattr(force, 'stance_west', 0),
                    "china": getattr(force, 'stance_china', 0),
                },
            )
            
            self.agents[agent.agent_id] = agent
            print(f"  [俄罗斯] {agent.name} (power={agent.power:.2f})")
        
        # 4. 欧盟势力 (10个)
        for force_id, force in EU_POLITICAL_FORCES.items():
            agent = Agent(
                agent_id=f"eu_{force_id}",
                name=f"欧盟{force.name_cn}",
                country="eu",
                force_type=getattr(force, 'force_type', 'political'),
                power=force.overall_influence * 0.6,  # 欧盟力量打折
                resources=80.0,
                stance={
                    "usa": getattr(force, 'stance_usa', 0),
                    "china": getattr(force, 'stance_china', 0),
                    "russia": getattr(force, 'stance_russia', 0),
                },
            )
            
            self.agents[agent.agent_id] = agent
            print(f"  [欧盟] {agent.name} (power={agent.power:.2f})")
        
        # 5. 政府内部派系（特殊Agent）
        self._add_government_agents()
        
        print(f"\n[初始化完成] 共 {len(self.agents)} 个智能体")
    
    def _add_government_agents(self):
        """添加政府内部派系Agent"""
        # 特朗普政府内部派系
        government_agents = {
            # 美国政府
            "trump_president": {
                "name": "特朗普(总统)",
                "country": "usa",
                "role": "Commander in Chief",
                "faction": "nationalist",
                "power": 1.0,
                "stances": {"china": -0.7, "russia": 0.3, "iran": -0.6},
            },
            " Pompeo_state": {
                "name": "蓬佩奥(国务卿)",
                "country": "usa",
                "role": "Secretary of State",
                "faction": "hawk",
                "power": 0.8,
                "stances": {"china": -0.9, "russia": -0.8, "iran": -0.9},
            },
            "Mnuchin_treasury": {
                "name": "姆努钦(财长)",
                "country": "usa",
                "role": "Treasury Secretary",
                "faction": "pragmatist",
                "power": 0.7,
                "stances": {"china": -0.4, "russia": -0.3, "iran": -0.5},
            },
            "Esper_defense": {
                "name": "埃斯珀(防长)",
                "country": "usa",
                "role": "Defense Secretary",
                "faction": "military",
                "power": 0.75,
                "stances": {"china": -0.6, "russia": -0.5, "iran": -0.7},
            },
            
            # 中国政府
            "xi_president": {
                "name": "习近平(国家主席)",
                "country": "china",
                "role": "President",
                "faction": "central",
                "power": 1.0,
                "stances": {"usa": -0.5, "russia": 0.6, "taiwan": 0.9},
            },
            "yang_foreign": {
                "name": "杨洁篪(外事委主任)",
                "country": "china",
                "role": "Top Diplomat",
                "faction": "pragmatist",
                "power": 0.7,
                "stances": {"usa": -0.4, "russia": 0.5, "india": -0.3},
            },
            "wei_military": {
                "name": "魏凤和(防长)",
                "country": "china",
                "role": "Defense Minister",
                "faction": "military",
                "power": 0.75,
                "stances": {"usa": -0.8, "taiwan": 0.95},
            },
            
            # 俄罗斯政府
            "putin_president": {
                "name": "普京(总统)",
                "country": "russia",
                "role": "President",
                "faction": "central",
                "power": 1.0,
                "stances": {"usa": -0.8, "china": 0.6, "ukraine": -0.9},
            },
            "shoigu_defense": {
                "name": "绍伊古(防长)",
                "country": "russia",
                "role": "Defense Minister",
                "faction": "military",
                "power": 0.8,
                "stances": {"usa": -0.9, "ukraine": -0.95},
            },
            "lavrov_foreign": {
                "name": "拉夫罗夫(外长)",
                "country": "russia",
                "role": "Foreign Minister",
                "faction": "diplomat",
                "power": 0.7,
                "stances": {"usa": -0.7, "eu": -0.5},
            },
            
            # 欧盟政府
            "macron_france": {
                "name": "马克龙(法国总统)",
                "country": "france",
                "role": "President",
                "faction": "europeanist",
                "power": 0.8,
                "stances": {"usa": 0.4, "russia": -0.3, "china": 0.2},
            },
            "merkel_germany": {
                "name": "默克尔(德国总理)",
                "country": "germany",
                "role": "Chancellor",
                "faction": "pragmatist",
                "power": 0.85,
                "stances": {"usa": 0.5, "russia": -0.2, "china": 0.1},
            },
        }
        
        for agent_id, config in government_agents.items():
            agent = Agent(
                agent_id=agent_id,
                name=config["name"],
                country=config["country"],
                force_type="government",
                power=config["power"],
                resources=100.0,
                stance=config["stances"],
                government_role=config["role"],
                faction=config["faction"],
            )
            
            self.agents[agent_id] = agent
            print(f"  [政府] {agent.name} ({agent.faction})")
    
    def run_round(self, round_num: int, scenario: str, context: str) -> Dict:
        """运行一轮模拟"""
        print(f"\n{'='*60}")
        print(f"第 {round_num} 轮 - {len(self.agents)} 个智能体博弈")
        print(f"{'='*60}")
        
        # 1. LLM决策阶段 - 每个Agent独立决策
        print("\n[阶段1] LLM决策生成")
        decisions = {}
        
        for agent_id, agent in self.agents.items():
            if agent.resources <= 0:
                continue  # 资源耗尽，跳过
            
            decision = self._generate_agent_decision(agent, scenario, context, round_num)
            decisions[agent_id] = decision
            
            time.sleep(0.05)  # 避免API过载
        
        # 2. 博弈论计算 - 所有两两博弈
        print(f"\n[阶段2] 博弈论计算 ({len(self.agents)}个Agent = {len(self.agents)*(len(self.agents)-1)//2}对)")
        payoff_results = self._calculate_all_bilateral_games(decisions)
        
        # 3. 联盟形成
        print("\n[阶段3] 联盟与敌对")
        self._update_alliances_and_enemies(payoff_results)
        
        # 4. 势力格局变化
        print("\n[阶段4] 势力格局分析")
        power_changes = self._analyze_power_shifts()
        
        # 5. 状态更新
        self._update_agent_states(payoff_results)
        
        # 记录历史
        round_data = {
            "round": round_num,
            "decisions": decisions,
            "payoffs": payoff_results,
            "power_changes": power_changes,
        }
        self.round_history.append(round_data)
        
        # 6. 打印报告
        self._print_round_report(round_num, decisions, payoff_results, power_changes)
        
        return round_data
    
    def _generate_agent_decision(self, agent: Agent, scenario: str, 
                                  context: str, round_num: int) -> Dict:
        """让LLM为Agent生成决策"""
        # 获取该Agent相关的其他Agent
        related_agents = []
        for other_id, other in self.agents.items():
            if other_id != agent.agent_id and other.country != agent.country:
                stance = agent.stance.get(other.country, 0.0)
                related_agents.append({
                    "name": other.name,
                    "country": other.country,
                    "stance": stance,
                    "power": other.power,
                })
        
        # 获取盟友和敌对
        allies = [self.agents[a].name for a in agent.allies if a in self.agents]
        enemies = [self.agents[e].name for e in agent.enemies if e in self.agents]
        
        prompt = f"""你是{agent.name}（{agent.country.upper()}）。

角色：{agent.government_role or agent.force_type}
派系：{agent.faction or 'N/A'}
影响力：{agent.power:.2f}
当前资源：{agent.resources:.1f}
战争疲劳：{agent.war_exhaustion:.2f}

立场：
{json.dumps(agent.stance, ensure_ascii=False, indent=2)}

盟友：{', '.join(allies) if allies else '无'}
敌对：{', '.join(enemies) if enemies else '无'}

当前场景：{scenario}
当前局势：{context}

作为{agent.name}，基于你的立场和利益，选择行动：
- cooperate: 合作
- defect: 背叛（利用对方）
- deter: 威慑
- escalate: 升级冲突
- negotiate: 谈判
- sanction: 制裁
- appeasse: 绥靖

回复JSON：
{{
    "action": "行动",
    "target": "目标国家/势力",
    "reasoning": "决策理由（博弈论分析）",
    "allies_involved": ["盟友列表，如果有的话"],
    "expected_payoff": "预期收益"
}}"""
        
        messages = [
            {"role": "system", "content": "你是一个地缘政治博弈专家。"},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat(messages, temperature=0.8, max_tokens=300)
        
        if response:
            try:
                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                
                data = json.loads(content)
                action_str = data.get("action", "cooperate")
                
                action_map = {
                    "cooperate": DiplomaticAction.COOPERATE,
                    "defect": DiplomaticAction.DEFECT,
                    "deter": DiplomaticAction.DETER,
                    "escalate": DiplomaticAction.ESCALATE,
                    "negotiate": DiplomaticAction.NEGOTIATE,
                    "sanction": DiplomaticAction.SANCTION,
                    "appease": DiplomaticAction.APPEASE,
                    "ignore": DiplomaticAction.IGNORE,
                }
                
                return {
                    "action": action_map.get(action_str, DiplomaticAction.COOPERATE),
                    "target": data.get("target", "none"),
                    "reasoning": data.get("reasoning", ""),
                    "expected_payoff": data.get("expected_payoff", ""),
                }
            except:
                pass
        
        return {"action": DiplomaticAction.COOPERATE, "target": "none", "reasoning": "fallback"}
    
    def _calculate_all_bilateral_games(self, decisions: Dict) -> Dict:
        """计算所有两两博弈"""
        results = {}
        agent_ids = list(self.agents.keys())
        
        for i, agent_a_id in enumerate(agent_ids):
            for agent_b_id in agent_ids[i+1:]:
                agent_a = self.agents[agent_a_id]
                agent_b = self.agents[agent_b_id]
                
                # 获取决策
                decision_a = decisions.get(agent_a_id, {})
                decision_b = decisions.get(agent_b_id, {})
                
                action_a = decision_a.get("action", DiplomaticAction.COOPERATE)
                action_b = decision_b.get("action", DiplomaticAction.COOPERATE)
                
                # 博弈论计算
                result = self.gt_engine.calculate_diplomatic_outcome(
                    agent_a_id, agent_b_id, action_a, action_b
                )
                
                results[f"{agent_a_id}|{agent_b_id}"] = result
        
        return results
    
    def _update_alliances_and_enemies(self, payoff_results: Dict):
        """更新联盟和敌对关系"""
        # 基于博弈结果更新
        for key, result in payoff_results.items():
            agent_a_id, agent_b_id = key.split("|")
            
            payoff_a = result["payoff_a"]
            payoff_b = result["payoff_b"]
            
            # 高收益 -> 可能结盟
            if payoff_a > 2 and payoff_b > 2:
                self.agents[agent_a_id].allies.add(agent_b_id)
                self.agents[agent_b_id].allies.add(agent_a_id)
            # 低收益/背叛 -> 敌对
            elif result.get("betrayal_by_a") or result.get("betrayal_by_b"):
                self.agents[agent_a_id].enemies.add(agent_b_id)
                self.agents[agent_b_id].enemies.add(agent_a_id)
    
    def _analyze_power_shifts(self) -> Dict:
        """分析势力格局变化"""
        power_by_country = defaultdict(float)
        power_by_force = defaultdict(float)
        
        for agent in self.agents.values():
            power_by_country[agent.country] += agent.power
            power_by_force[agent.force_type] += agent.power
        
        return {
            "by_country": dict(power_by_country),
            "by_force_type": dict(power_by_force),
        }
    
    def _update_agent_states(self, payoff_results: Dict):
        """更新Agent状态"""
        for key, result in payoff_results.items():
            agent_a_id, agent_b_id = key.split("|")
            
            # 更新资源
            self.agents[agent_a_id].resources -= abs(result["payoff_a"]) * 0.5
            self.agents[agent_b_id].resources -= abs(result["payoff_b"]) * 0.5
            
            # 更新战争疲劳
            if result.get("conflict_level") in ["limited_war", "total_war"]:
                self.agents[agent_a_id].war_exhaustion += 0.1
                self.agents[agent_b_id].war_exhaustion += 0.1
    
    def _print_round_report(self, round_num: int, decisions: Dict,
                           payoff_results: Dict, power_changes: Dict):
        """打印轮次报告"""
        print(f"\n{'='*60}")
        print(f"第 {round_num} 轮报告 - {len(self.agents)} 个智能体")
        print(f"{'='*60}")
        
        # 按国家分组统计
        print("\n[行动统计 - 按国家]")
        for country in ["usa", "china", "russia", "eu"]:
            country_agents = [a for a in self.agents.values() if a.country == country]
            actions = [decisions.get(a.agent_id, {}).get("action", DiplomaticAction.COOPERATE) 
                      for a in country_agents]
            
            action_counts = {}
            for action in actions:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1
            
            print(f"  {country.upper()}: {action_counts}")
        
        # 关键博弈
        print("\n[关键博弈结果]")
        significant_games = [(k, v) for k, v in payoff_results.items() 
                             if abs(v["payoff_a"]) > 3 or abs(v["payoff_b"]) > 3]
        
        for key, result in significant_games[:5]:
            a_id, b_id = key.split("|")
            agent_a = self.agents.get(a_id)
            agent_b = self.agents.get(b_id)
            
            if agent_a and agent_b:
                print(f"  {agent_a.name} vs {agent_b.name}:")
                print(f"    收益: ({result['payoff_a']:+.1f}, {result['payoff_b']:+.1f})")
                print(f"    冲突: {result['conflict_level']}")
        
        # 势力格局
        print("\n[势力格局]")
        for country, power in sorted(power_changes["by_country"].items(), 
                                     key=lambda x: x[1], reverse=True):
            print(f"  {country.upper()}: {power:.2f}")
        
        # 联盟网络
        print("\n[主要联盟]")
        alliance_count = defaultdict(int)
        for agent in self.agents.values():
            if agent.allies:
                for ally in agent.allies:
                    key = tuple(sorted([agent.country, self.agents[ally].country]))
                    alliance_count[key] += 1
        
        for (c1, c2), count in sorted(alliance_count.items(), 
                                     key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {c1.upper()}-{c2.upper()}: {count}个联盟")
        
        # 资源状态
        print("\n[资源状态 - 前10名]")
        resource_ranking = [(a.agent_id, a.resources, a.war_exhaustion) 
                          for a in self.agents.values()]
        resource_ranking.sort(key=lambda x: x[1], reverse=True)
        
        for i, (aid, res, fatigue) in enumerate(resource_ranking[:10], 1):
            agent = self.agents[aid]
            print(f"  {i}. {agent.name}: 资源={res:.1f}, 疲劳={fatigue:.2f}")
    
    def run_full_simulation(self, scenario: str, context: str, rounds: int = 3):
        """运行完整模拟"""
        print(f"\n{'='*60}")
        print(f"多智能体政治模拟系统")
        print(f"{'='*60}")
        print(f"智能体数量: {len(self.agents)}")
        print(f"博弈对数: {len(self.agents)*(len(self.agents)-1)//2}")
        print(f"模拟轮数: {rounds}")
        print(f"LLM: {self.llm.provider}/{self.llm.model}")
        print(f"{'='*60}")
        
        for round_num in range(1, rounds + 1):
            self.run_round(round_num, scenario, context)
        
        # 最终报告
        self._print_final_report()
    
    def _print_final_report(self):
        """打印最终报告"""
        print(f"\n{'='*60}")
        print("模拟结束 - 最终报告")
        print(f"{'='*60}")
        
        # 胜者排名
        print("\n[势力排名 - 综合国力]")
        final_ranking = []
        for agent in self.agents.values():
            # 综合分数 = 资源 * (1 - 战争疲劳)
            score = agent.resources * max(0.1, 1 - agent.war_exhaustion)
            final_ranking.append((agent.name, agent.country, score, agent.reputation))
        
        final_ranking.sort(key=lambda x: x[2], reverse=True)
        for i, (name, country, score, rep) in enumerate(final_ranking[:15], 1):
            print(f"  {i}. {name} ({country.upper()}): {score:.1f}分")
        
        # 联盟网络
        print("\n[最终联盟网络]")
        alliance_groups = self._identify_alliance_blocks()
        for i, group in enumerate(alliance_groups, 1):
            countries = [self.agents[a].country.upper() for a in group]
            print(f"  阵营{i}: {', '.join(set(countries))}")
        
        # 战争疲劳排名
        print("\n[战争疲劳 - 前5]")
        fatigue_ranking = [(a.name, a.war_exhaustion) for a in self.agents.values()]
        fatigue_ranking.sort(key=lambda x: x[1], reverse=True)
        for name, fatigue in fatigue_ranking[:5]:
            print(f"  {name}: {fatigue:.2f}")
    
    def _identify_alliance_blocks(self) -> List[Set[str]]:
        """识别联盟集团"""
        # 简化：按国家分组
        country_agents = defaultdict(set)
        for agent in self.agents.values():
            country_agents[agent.country].add(agent.agent_id)
        
        return list(country_agents.values())


# 全局实例
multi_agent_sim = MultiAgentPoliticalSimulation()

if __name__ == "__main__":
    print("=== 多智能体政治模拟系统 ===\n")
    
    sim = MultiAgentPoliticalSimulation()
    
    scenario = "波斯湾战争：伊朗封锁霍尔木兹海峡"
    context = "油价暴涨300%，全球能源危机"
    
    sim.run_full_simulation(scenario, context, rounds=2)
