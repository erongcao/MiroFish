"""
Game Theory Neo4j Simulation - 博弈论+Neo4j整合模拟
整合博弈论机制（收益矩阵、声誉、信任、冲突升级）到图数据库模拟中
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# 导入博弈论模块
from game_theory_diplomacy import (
    GameTheoryDiplomacy, DiplomaticAction, ConflictLevel,
    AgentDiplomaticState, PayoffMatrix
)
from neo4j_political_simulation import Neo4jPoliticalSimulation
from llm_political_game import LLMClient, FORCE_CHARACTERS

@dataclass
class GameTheoryRoundResult:
    """博弈论轮次结果"""
    round_num: int
    
    # 博弈论指标
    payoff_matrix: Dict[str, Tuple[float, float]]
    nash_equilibria: List[Tuple[str, str, str, str]]  # (a, b, action_a, action_b)
    
    # 声誉变化
    reputation_changes: Dict[str, float]
    
    # 信任网络
    trust_network: Dict[str, Dict[str, float]]
    
    # 冲突级别
    conflict_levels: Dict[str, str]
    
    # 资源消耗
    resource_consumption: Dict[str, float]
    
    # 战争疲劳
    war_exhaustion: Dict[str, float]

class GameTheoryNeo4jSimulation:
    """博弈论+Neo4j整合模拟系统"""
    
    def __init__(self, llm_provider: str = "ollama"):
        self.llm = LLMClient(llm_provider)
        self.characters = FORCE_CHARACTERS
        
        # 博弈论引擎
        self.gt_engine = GameTheoryDiplomacy()
        
        # Neo4j模拟
        self.neo4j_sim = Neo4jPoliticalSimulation(llm_provider)
        
        # 历史记录
        self.gt_history: List[GameTheoryRoundResult] = []
    
    def initialize_simulation(self, force_ids: List[str], scenario: str):
        """初始化模拟"""
        print(f"\n{'='*60}")
        print("博弈论+Neo4j整合模拟系统")
        print(f"{'='*60}")
        
        # 1. 初始化Neo4j图
        self.neo4j_sim.initialize_graph(force_ids, scenario)
        
        # 2. 初始化博弈论Agent
        agent_configs = []
        for fid in force_ids:
            char = self.characters.get(fid, {})
            
            # 根据势力特性设置立场
            stance = "neutral"
            if "military" in fid or "security" in fid:
                stance = "opposing"
            elif "wall_street" in fid or "reformists" in fid or "oligarchs" in fid:
                stance = "supportive"
            
            agent_configs.append({
                "agent_id": fid,
                "stance": stance,
                "sentiment_bias": char.get("stance_usa", 0.0) if "cn_" in fid else 0.0,
            })
        
        self.gt_engine.initialize_agents(agent_configs)
        
        print(f"\n[初始化完成]")
        print(f"  图数据库: {len(force_ids)}个节点")
        print(f"  博弈论: {len(agent_configs)}个Agent")
    
    def run_game_theory_round(self, round_num: int, force_ids: List[str],
                             scenario: str, context: str) -> GameTheoryRoundResult:
        """运行博弈论轮次"""
        print(f"\n{'='*60}")
        print(f"第 {round_num} 轮 - 博弈论分析")
        print(f"{'='*60}")
        
        # 1. LLM生成决策（作为博弈行动）
        print("\n[阶段1] LLM决策 → 博弈行动映射")
        actions = {}
        
        for fid in force_ids:
            char = self.characters.get(fid, {})
            name = char.get("name", fid)
            
            # 获取LLM决策
            relations = self.neo4j_sim._get_force_relations(fid)
            
            prompt = f"""{char.get('identity', '')}

当前场景：{scenario}
当前局势：{context}

你的关系网络：
{json.dumps(relations, ensure_ascii=False, indent=2)}

基于博弈论，选择你的行动：
- cooperate: 合作（投入资源，期望双赢）
- defect: 背叛（利用对方合作，获取最大收益）
- deter: 威慑（展示武力，阻止对方攻击）
- escalate: 升级（军事行动，高风险高成本）
- negotiate: 谈判（寻求外交解决）
- sanction: 制裁（经济施压）
- appease: 绥靖（让步求和）
- ignore: 无视（不采取行动）

回复JSON：
{{
    "action": "行动类型",
    "target": "目标势力",
    "reasoning": "博弈论分析（为什么这个行动是最优的）",
    "expected_payoff": "预期收益"
}}"""
            
            messages = [
                {"role": "system", "content": "你是一个博弈论专家，用博弈论分析最优策略。"},
                {"role": "user", "content": prompt},
            ]
            
            response = self.llm.chat(messages, temperature=0.8, max_tokens=400)
            
            if response:
                try:
                    content = response.content.strip()
                    if content.startswith("```"):
                        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                    
                    data = json.loads(content)
                    action_str = data.get("action", "cooperate")
                    
                    # 映射到博弈论行动
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
                    
                    actions[fid] = {
                        "action": action_map.get(action_str, DiplomaticAction.COOPERATE),
                        "target": data.get("target", "none"),
                        "reasoning": data.get("reasoning", ""),
                    }
                    
                    print(f"  {name}: {action_str} -> {actions[fid]['target']}")
                    print(f"    推理: {actions[fid]['reasoning'][:60]}...")
                except:
                    actions[fid] = {
                        "action": DiplomaticAction.COOPERATE,
                        "target": "none",
                        "reasoning": "解析失败",
                    }
            else:
                actions[fid] = {
                    "action": DiplomaticAction.COOPERATE,
                    "target": "none",
                    "reasoning": "LLM失败",
                }
            
            time.sleep(0.2)
        
        # 2. 博弈论计算（两两博弈）
        print("\n[阶段2] 博弈论计算（收益矩阵）")
        
        payoff_results = {}
        nash_equilibria = []
        
        for i, fid_a in enumerate(force_ids):
            for fid_b in force_ids[i+1:]:
                action_a = actions[fid_a]["action"]
                action_b = actions[fid_b]["action"]
                
                # 计算博弈结果
                result = self.gt_engine.calculate_diplomatic_outcome(
                    fid_a, fid_b, action_a, action_b
                )
                
                payoff_results[f"{fid_a}|{fid_b}"] = result
                
                # 检查纳什均衡
                if self._is_nash_equilibrium(fid_a, fid_b, action_a, action_b):
                    nash_equilibria.append((fid_a, fid_b, action_a.value, action_b.value))
                
                # 打印关键博弈
                char_a = self.characters.get(fid_a, {})
                char_b = self.characters.get(fid_b, {})
                name_a = char_a.get("name", fid_a)
                name_b = char_b.get("name", fid_b)
                
                print(f"\n  {name_a} vs {name_b}:")
                print(f"    行动: {action_a.value} vs {action_b.value}")
                print(f"    收益: A={result['payoff_a']:+.1f}, B={result['payoff_b']:+.1f}")
                print(f"    信任变化: {result['trust_delta']:+.2f}")
                print(f"    冲突级别: {result['conflict_level']}")
                if result['betrayal_by_a']:
                    print(f"    ⚠️ {name_a} 背叛了 {name_b}!")
                if result['betrayal_by_b']:
                    print(f"    ⚠️ {name_b} 背叛了 {name_a}!")
        
        # 3. 收集状态变化
        print("\n[阶段3] 状态变化统计")
        
        reputation_changes = {}
        trust_network = {}
        conflict_levels = {}
        resource_consumption = {}
        war_exhaustion = {}
        
        for fid in force_ids:
            agent = self.gt_engine.agents[fid]
            char = self.characters.get(fid, {})
            name = char.get("name", fid)
            
            reputation_changes[fid] = agent.reputation
            trust_network[fid] = dict(agent.trust_memory)
            resource_consumption[fid] = 100.0 - agent.resources
            war_exhaustion[fid] = agent.war_exhaustion
            
            print(f"  {name}:")
            print(f"    声誉: {agent.reputation:+.2f}")
            print(f"    资源消耗: {resource_consumption[fid]:.1f}")
            print(f"    战争疲劳: {war_exhaustion[fid]:.2f}")
        
        # 冲突级别
        for key, level in self.gt_engine.conflict_levels.items():
            conflict_levels[key] = level.value
        
        # 4. 更新Neo4j图
        print("\n[阶段4] 更新图数据库")
        self._update_neo4j_with_gt_results(force_ids, actions, payoff_results)
        
        # 5. 创建结果
        result = GameTheoryRoundResult(
            round_num=round_num,
            payoff_matrix={
                key: (res["payoff_a"], res["payoff_b"])
                for key, res in payoff_results.items()
            },
            nash_equilibria=nash_equilibria,
            reputation_changes=reputation_changes,
            trust_network=trust_network,
            conflict_levels=conflict_levels,
            resource_consumption=resource_consumption,
            war_exhaustion=war_exhaustion,
        )
        
        self.gt_history.append(result)
        
        return result
    
    def _is_nash_equilibrium(self, agent_a: str, agent_b: str,
                            action_a: DiplomaticAction, 
                            action_b: DiplomaticAction) -> bool:
        """检查是否为纳什均衡"""
        # 简化的纳什均衡检查
        # 如果双方都没有单方面改变策略的动机
        
        # 获取当前收益
        result = self.gt_engine.calculate_diplomatic_outcome(
            agent_a, agent_b, action_a, action_b
        )
        current_payoff_a = result["payoff_a"]
        current_payoff_b = result["payoff_b"]
        
        # 检查A是否有更好的选择
        better_for_a = False
        for alt_action in DiplomaticAction:
            if alt_action != action_a:
                alt_result = self.gt_engine.calculate_diplomatic_outcome(
                    agent_a, agent_b, alt_action, action_b
                )
                if alt_result["payoff_a"] > current_payoff_a + 0.5:
                    better_for_a = True
                    break
        
        # 检查B是否有更好的选择
        better_for_b = False
        for alt_action in DiplomaticAction:
            if alt_action != action_b:
                alt_result = self.gt_engine.calculate_diplomatic_outcome(
                    agent_a, agent_b, action_a, alt_action
                )
                if alt_result["payoff_b"] > current_payoff_b + 0.5:
                    better_for_b = True
                    break
        
        # 纳什均衡：双方都没有更好选择
        return not better_for_a and not better_for_b
    
    def _update_neo4j_with_gt_results(self, force_ids: List[str],
                                     actions: Dict, 
                                     payoff_results: Dict):
        """用博弈论结果更新Neo4j"""
        # 更新节点属性
        for fid in force_ids:
            agent = self.gt_engine.agents[fid]
            
            if self.neo4j_sim.neo4j and self.neo4j_sim.neo4j.connected:
                with self.neo4j_sim.neo4j.driver.session() as session:
                    session.run("""
                        MATCH (f:Force {id: $id})
                        SET f.reputation = $reputation,
                            f.resources = $resources,
                            f.war_exhaustion = $war_exhaustion
                    """, id=fid, reputation=agent.reputation,
                        resources=agent.resources,
                        war_exhaustion=agent.war_exhaustion)
            
            # 更新内存图
            if fid in self.neo4j_sim.memory_graph["nodes"]:
                self.neo4j_sim.memory_graph["nodes"][fid]["reputation"] = agent.reputation
                self.neo4j_sim.memory_graph["nodes"][fid]["resource"] = agent.resources
                self.neo4j_sim.memory_graph["nodes"][fid]["war_exhaustion"] = agent.war_exhaustion
        
        # 更新关系权重（基于信任度）
        for key, result in payoff_results.items():
            fid_a, fid_b = key.split("|")
            
            agent_a = self.gt_engine.agents[fid_a]
            trust = agent_a.get_trust(fid_b)
            
            # 更新边权重
            edge_key = f"{fid_a}->{fid_b}"
            if edge_key in self.neo4j_sim.memory_graph["edges"]:
                self.neo4j_sim.memory_graph["edges"][edge_key]["weight"] = trust
                
                if self.neo4j_sim.neo4j and self.neo4j_sim.neo4j.connected:
                    with self.neo4j_sim.neo4j.driver.session() as session:
                        session.run("""
                            MATCH (a:Force {id: $from_id})-[r:RELATION]->(b:Force {id: $to_id})
                            SET r.weight = $weight, r.trust = $trust
                        """, from_id=fid_a, to_id=fid_b, 
                            weight=trust, trust=trust)
    
    def print_game_theory_report(self, result: GameTheoryRoundResult,
                                 force_ids: List[str]):
        """打印博弈论报告"""
        print(f"\n{'='*60}")
        print(f"第 {result.round_num} 轮博弈论报告")
        print(f"{'='*60}")
        
        # 纳什均衡
        if result.nash_equilibria:
            print("\n[纳什均衡]")
            for a, b, action_a, action_b in result.nash_equilibria:
                name_a = self.characters.get(a, {}).get("name", a)
                name_b = self.characters.get(b, {}).get("name", b)
                print(f"  {name_a}({action_a}) vs {name_b}({action_b})")
        
        # 收益矩阵
        print("\n[收益矩阵 - 关键博弈]")
        for key, (payoff_a, payoff_b) in result.payoff_matrix.items():
            if abs(payoff_a) > 2 or abs(payoff_b) > 2:  # 只显示显著博弈
                fid_a, fid_b = key.split("|")
                name_a = self.characters.get(fid_a, {}).get("name", fid_a)
                name_b = self.characters.get(fid_b, {}).get("name", fid_b)
                print(f"  {name_a} vs {name_b}: ({payoff_a:+.1f}, {payoff_b:+.1f})")
        
        # 冲突级别
        print("\n[冲突级别]")
        hostile_pairs = []
        for key, level in result.conflict_levels.items():
            if level not in ["peace", "tension"]:
                fid_a, fid_b = key.split("|")
                name_a = self.characters.get(fid_a, {}).get("name", fid_a)
                name_b = self.characters.get(fid_b, {}).get("name", fid_b)
                hostile_pairs.append((name_a, name_b, level))
        
        if hostile_pairs:
            for a, b, level in hostile_pairs:
                print(f"  {a} vs {b}: {level}")
        else:
            print("  无严重冲突")
        
        # 战争疲劳
        print("\n[战争疲劳]")
        for fid, fatigue in result.war_exhaustion.items():
            if fatigue > 0.3:
                name = self.characters.get(fid, {}).get("name", fid)
                print(f"  {name}: {fatigue:.2f} (高)")
    
    def run_full_simulation(self, scenario_id: str, force_ids: List[str],
                           scenario: str, context: str, rounds: int = 3):
        """运行完整模拟"""
        # 初始化
        self.initialize_simulation(force_ids, scenario)
        
        # 运行多轮
        for round_num in range(1, rounds + 1):
            result = self.run_game_theory_round(round_num, force_ids, scenario, context)
            self.print_game_theory_report(result, force_ids)
        
        # 最终报告
        self._print_final_gt_report(force_ids)
    
    def _print_final_gt_report(self, force_ids: List[str]):
        """打印最终博弈论报告"""
        print(f"\n{'='*60}")
        print("博弈论模拟结束 - 最终报告")
        print(f"{'='*60}")
        
        # 总收益排名
        print("\n[总收益排名]")
        total_payoffs = {}
        for fid in force_ids:
            agent = self.gt_engine.agents[fid]
            total = sum(h.payoff for h in agent.history)
            total_payoffs[fid] = total
        
        rankings = sorted(total_payoffs.items(), key=lambda x: x[1], reverse=True)
        for i, (fid, payoff) in enumerate(rankings, 1):
            name = self.characters.get(fid, {}).get("name", fid)
            print(f"  {i}. {name}: {payoff:+.1f}")
        
        # 背叛统计
        print("\n[背叛统计]")
        betrayals = {}
        for fid in force_ids:
            agent = self.gt_engine.agents[fid]
            count = sum(1 for h in agent.history if h.betrayal)
            if count > 0:
                name = self.characters.get(fid, {}).get("name", fid)
                betrayals[fid] = count
        
        if betrayals:
            for fid, count in sorted(betrayals.items(), key=lambda x: x[1], reverse=True):
                name = self.characters.get(fid, {}).get("name", fid)
                print(f"  {name}: {count}次")
        else:
            print("  无背叛行为")
        
        # 冲突演变
        print("\n[冲突演变]")
        for key, level in self.gt_engine.conflict_levels.items():
            if level != ConflictLevel.PEACE:
                fid_a, fid_b = key.split("|")
                name_a = self.characters.get(fid_a, {}).get("name", fid_a)
                name_b = self.characters.get(fid_b, {}).get("name", fid_b)
                print(f"  {name_a} vs {name_b}: {level.value}")


# 全局实例
gt_neo4j_sim = GameTheoryNeo4jSimulation()

if __name__ == "__main__":
    print("=== 博弈论+Neo4j整合模拟 ===\n")
    
    sim = GameTheoryNeo4jSimulation()
    
    scenario = "波斯湾战争：伊朗封锁霍尔木兹海峡"
    forces = [
        'us_military_industrial',
        'us_wall_street',
        'cn_military_red',
        'cn_reformists',
        'ru_siloviki',
        'ru_oligarchs',
        'eu_franco_german',
        'eu_atlanticists',
    ]
    
    context = "油价暴涨300%，美国海军第五舰队在巴林待命"
    
    sim.run_full_simulation('persian_gulf_gt', forces, scenario, context, rounds=2)
