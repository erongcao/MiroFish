"""
Neo4j Political Simulation - 基于图数据库的真实地缘政治模拟
每一轮都更新Neo4j图数据库，使用图算法计算影响力传播
"""

import json
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# 导入Neo4j适配器
try:
    from neo4j_adapter import Neo4jGraphAdapter
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("[警告] Neo4j适配器未找到")

from llm_political_game import LLMClient, FORCE_CHARACTERS

@dataclass
class SimulationState:
    """模拟状态"""
    round_num: int
    force_states: Dict[str, Dict]
    relation_weights: Dict[str, float]
    global_metrics: Dict[str, float]

class Neo4jPoliticalSimulation:
    """基于Neo4j的真实地缘政治模拟"""
    
    def __init__(self, llm_provider: str = "ollama"):
        self.llm = LLMClient(llm_provider)
        self.characters = FORCE_CHARACTERS
        
        # 初始化Neo4j
        self.neo4j = None
        if NEO4J_AVAILABLE:
            try:
                self.neo4j = Neo4jGraphAdapter()
                if self.neo4j.connected:
                    print("[Neo4j] 已连接，启用图数据库模拟")
                else:
                    print("[Neo4j] 连接失败，使用内存模式")
                    self.neo4j = None
            except Exception as e:
                print(f"[Neo4j] 初始化失败: {e}")
                self.neo4j = None
        
        # 内存备用
        self.memory_graph = {
            "nodes": {},
            "edges": {},
        }
        
        self.simulation_history: List[SimulationState] = []
    
    def initialize_graph(self, force_ids: List[str], scenario: str):
        """初始化图数据库"""
        print(f"\n{'='*60}")
        print("初始化地缘政治关系网络")
        print(f"{'='*60}")
        
        # 清除旧数据
        if self.neo4j and self.neo4j.connected:
            with self.neo4j.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                print("[Neo4j] 清除旧数据")
        
        # 创建势力节点
        for fid in force_ids:
            char = self.characters.get(fid, {})
            name = char.get("name", fid)
            country = char.get("country", "")
            
            # 节点属性
            properties = {
                "id": fid,
                "name": name,
                "country": country,
                "influence": char.get("influence", 0.5),
                "resource": 1.0,
                "trust_avg": 0.5,
            }
            
            if self.neo4j and self.neo4j.connected:
                with self.neo4j.driver.session() as session:
                    session.run("""
                        CREATE (f:Force {
                            id: $id,
                            name: $name,
                            country: $country,
                            influence: $influence,
                            resource: $resource,
                            trust_avg: $trust_avg
                        })
                    """, **properties)
            
            self.memory_graph["nodes"][fid] = properties
            print(f"  [节点] {name} ({country})")
        
        # 创建关系边
        relations = [
            ("us_military_industrial", "us_pro_israel_lobby", "alliance", 0.8),
            ("us_military_industrial", "us_wall_street", "conflict", -0.3),
            ("us_wall_street", "cn_private_capital", "trade", 0.6),
            ("cn_military_red", "cn_security", "alliance", 0.9),
            ("cn_military_red", "cn_reformists", "conflict", -0.4),
            ("ru_siloviki", "ru_oligarchs", "conflict", -0.2),
            ("us_military_industrial", "cn_military_red", "hostility", -0.8),
            ("eu_franco_german", "us_wall_street", "trade", 0.5),
            ("eu_atlanticists", "us_military_industrial", "alliance", 0.7),
            ("cn_reformists", "us_wall_street", "cooperation", 0.4),
            ("ru_siloviki", "us_military_industrial", "hostility", -0.7),
            ("cn_security", "us_pro_israel_lobby", "hostility", -0.6),
        ]
        
        for from_id, to_id, rel_type, weight in relations:
            if from_id in force_ids and to_id in force_ids:
                self._create_relation(from_id, to_id, rel_type, weight)
        
        print(f"\n[初始化完成] {len(force_ids)}个节点, {len(relations)}条边")
    
    def _create_relation(self, from_id: str, to_id: str, 
                        rel_type: str, weight: float):
        """创建关系边"""
        if self.neo4j and self.neo4j.connected:
            with self.neo4j.driver.session() as session:
                session.run("""
                    MATCH (a:Force {id: $from_id}), (b:Force {id: $to_id})
                    CREATE (a)-[r:RELATION {
                        type: $rel_type,
                        weight: $weight,
                        round: 0
                    }]->(b)
                """, from_id=from_id, to_id=to_id, 
                    rel_type=rel_type, weight=weight)
        
        edge_key = f"{from_id}->{to_id}"
        self.memory_graph["edges"][edge_key] = {
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            "weight": weight,
            "round": 0,
        }
    
    def run_simulation_round(self, round_num: int, force_ids: List[str],
                            scenario: str, context: str) -> SimulationState:
        """运行一轮模拟"""
        print(f"\n{'='*60}")
        print(f"第 {round_num} 轮模拟")
        print(f"{'='*60}")
        
        # 1. LLM决策阶段
        print("\n[阶段1] LLM决策生成")
        decisions = {}
        for fid in force_ids:
            char = self.characters.get(fid, {})
            name = char.get("name", fid)
            
            # 构建包含图关系的prompt
            relations = self._get_force_relations(fid)
            
            prompt = f"""{char.get('identity', '')}

当前场景：{scenario}
当前局势：{context}

你的关系网络：
{json.dumps(relations, ensure_ascii=False, indent=2)}

基于你的关系和利益，做出决策。
回复JSON格式：
{{
    "action": "cooperate/confront/deescalate/neutral/escalate",
    "target": "目标势力",
    "reasoning": "决策理由",
    "risk_level": 0.0-1.0,
    "resource_commitment": 0.0-1.0
}}"""
            
            messages = [
                {"role": "system", "content": "你是一个地缘政治决策者。"},
                {"role": "user", "content": prompt},
            ]
            
            response = self.llm.chat(messages, temperature=0.8, max_tokens=300)
            
            if response:
                try:
                    content = response.content.strip()
                    if content.startswith("```"):
                        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                    
                    data = json.loads(content)
                    decisions[fid] = data
                    print(f"  {name}: {data.get('action', 'neutral')} -> {data.get('target', 'none')}")
                except:
                    decisions[fid] = {"action": "neutral", "target": "none", "reasoning": "解析失败"}
            else:
                decisions[fid] = {"action": "neutral", "target": "none", "reasoning": "LLM失败"}
            
            time.sleep(0.2)
        
        # 2. 更新图数据库
        print("\n[阶段2] 更新关系网络")
        self._update_graph_based_on_decisions(decisions, round_num)
        
        # 3. 图算法分析
        print("\n[阶段3] 图算法分析")
        metrics = self._run_graph_algorithms(force_ids)
        
        # 4. 计算影响力传播
        print("\n[阶段4] 影响力传播计算")
        influence_changes = self._calculate_influence_propagation(force_ids)
        
        # 5. 生成状态报告
        state = SimulationState(
            round_num=round_num,
            force_states={fid: {
                "decision": decisions[fid],
                "influence": metrics.get(fid, {}).get("pagerank", 0.5),
                "resource": self.memory_graph["nodes"][fid]["resource"],
            } for fid in force_ids},
            relation_weights=self._get_all_relation_weights(),
            global_metrics={
                "avg_trust": metrics.get("avg_trust", 0.5),
                "polarization": metrics.get("polarization", 0.0),
                "conflict_intensity": self._calculate_conflict_intensity(decisions),
            },
        )
        
        self.simulation_history.append(state)
        
        # 6. 打印详细报告
        self._print_round_report(state, force_ids)
        
        return state
    
    def _get_force_relations(self, force_id: str) -> List[Dict]:
        """获取势力的关系"""
        relations = []
        for edge_key, edge in self.memory_graph["edges"].items():
            if edge["from"] == force_id:
                char = self.characters.get(edge["to"], {})
                relations.append({
                    "target": char.get("name", edge["to"]),
                    "type": edge["type"],
                    "weight": edge["weight"],
                })
        return relations
    
    def _update_graph_based_on_decisions(self, decisions: Dict, round_num: int):
        """根据决策更新图"""
        for fid, decision in decisions.items():
            action = decision.get("action", "neutral")
            target = decision.get("target", "none")
            
            # 更新节点资源
            resource_cost = decision.get("resource_commitment", 0.5) * 0.1
            self.memory_graph["nodes"][fid]["resource"] -= resource_cost
            
            # 更新关系权重
            for edge_key, edge in self.memory_graph["edges"].items():
                if edge["from"] == fid:
                    # 根据行动类型调整关系
                    if action == "confront" or action == "escalate":
                        edge["weight"] -= 0.1
                    elif action == "cooperate" or action == "deescalate":
                        edge["weight"] += 0.05
                    
                    # 限制范围
                    edge["weight"] = max(-1.0, min(1.0, edge["weight"]))
                    edge["round"] = round_num
                    
                    # 更新Neo4j
                    if self.neo4j and self.neo4j.connected:
                        with self.neo4j.driver.session() as session:
                            session.run("""
                                MATCH (a:Force {id: $from_id})-[r:RELATION]->(b:Force {id: $to_id})
                                SET r.weight = $weight, r.round = $round
                            """, from_id=edge["from"], to_id=edge["to"],
                                weight=edge["weight"], round=round_num)
        
        print(f"  关系网络已更新（第{round_num}轮）")
    
    def _run_graph_algorithms(self, force_ids: List[str]) -> Dict:
        """运行图算法"""
        metrics = {}
        
        # 简化的PageRank计算
        pagerank = {fid: 1.0 for fid in force_ids}
        
        for _ in range(10):  # 10次迭代
            new_pagerank = {}
            for fid in force_ids:
                rank = 0.15  # 阻尼因子
                
                # 收集入边
                for edge_key, edge in self.memory_graph["edges"].items():
                    if edge["to"] == fid and edge["weight"] > 0:
                        from_id = edge["from"]
                        out_edges = sum(1 for e in self.memory_graph["edges"].values()
                                      if e["from"] == from_id and e["weight"] > 0)
                        if out_edges > 0:
                            rank += 0.85 * pagerank[from_id] / out_edges
                
                new_pagerank[fid] = rank
            
            pagerank = new_pagerank
        
        # 归一化
        max_rank = max(pagerank.values()) if pagerank else 1.0
        for fid in force_ids:
            metrics[fid] = {"pagerank": pagerank[fid] / max_rank}
        
        # 计算平均信任度
        trust_values = [edge["weight"] for edge in self.memory_graph["edges"].values()
                       if edge["type"] in ["alliance", "trade", "cooperation"]]
        metrics["avg_trust"] = sum(trust_values) / len(trust_values) if trust_values else 0.5
        
        # 计算极化程度
        hostility_values = [abs(edge["weight"]) for edge in self.memory_graph["edges"].values()
                          if edge["type"] in ["hostility", "conflict"]]
        metrics["polarization"] = sum(hostility_values) / len(hostility_values) if hostility_values else 0.0
        
        return metrics
    
    def _calculate_influence_propagation(self, force_ids: List[str]) -> Dict:
        """计算影响力传播"""
        changes = {}
        
        for fid in force_ids:
            # 基于PageRank的变化
            node = self.memory_graph["nodes"][fid]
            old_influence = node.get("influence", 0.5)
            
            # 计算邻居影响
            neighbor_effect = 0.0
            for edge_key, edge in self.memory_graph["edges"].items():
                if edge["to"] == fid:
                    neighbor_effect += edge["weight"] * 0.1
            
            new_influence = old_influence + neighbor_effect
            new_influence = max(0.1, min(1.0, new_influence))
            
            node["influence"] = new_influence
            changes[fid] = new_influence - old_influence
            
            # 更新Neo4j
            if self.neo4j and self.neo4j.connected:
                with self.neo4j.driver.session() as session:
                    session.run("""
                        MATCH (f:Force {id: $id})
                        SET f.influence = $influence
                    """, id=fid, influence=new_influence)
        
        return changes
    
    def _get_all_relation_weights(self) -> Dict[str, float]:
        """获取所有关系权重"""
        return {
            edge_key: edge["weight"]
            for edge_key, edge in self.memory_graph["edges"].items()
        }
    
    def _calculate_conflict_intensity(self, decisions: Dict) -> float:
        """计算冲突强度"""
        confront_count = sum(1 for d in decisions.values()
                          if d.get("action") in ["confront", "escalate"])
        return confront_count / len(decisions) if decisions else 0.0
    
    def _print_round_report(self, state: SimulationState, force_ids: List[str]):
        """打印轮次报告"""
        print(f"\n{'='*60}")
        print(f"第 {state.round_num} 轮报告")
        print(f"{'='*60}")
        
        print("\n[势力状态]")
        for fid in force_ids:
            char = self.characters.get(fid, {})
            name = char.get("name", fid)
            force_state = state.force_states[fid]
            decision = force_state["decision"]
            
            print(f"  {name}:")
            print(f"    行动: {decision.get('action', 'neutral')}")
            print(f"    目标: {decision.get('target', 'none')}")
            print(f"    影响力: {force_state['influence']:.2f}")
            print(f"    资源: {force_state['resource']:.2f}")
            print(f"    风险: {decision.get('risk_level', 0.0):.1f}")
        
        print("\n[全局指标]")
        for metric, value in state.global_metrics.items():
            print(f"  {metric}: {value:.2f}")
        
        print("\n[关系网络变化]")
        for edge_key, weight in state.relation_weights.items():
            edge = self.memory_graph["edges"][edge_key]
            from_name = self.characters.get(edge["from"], {}).get("name", edge["from"])
            to_name = self.characters.get(edge["to"], {}).get("name", edge["to"])
            print(f"  {from_name} -> {to_name}: {edge['type']} = {weight:+.2f}")
    
    def export_graph_data(self) -> Dict:
        """导出图数据"""
        return {
            "nodes": self.memory_graph["nodes"],
            "edges": self.memory_graph["edges"],
            "history": [
                {
                    "round": s.round_num,
                    "metrics": s.global_metrics,
                }
                for s in self.simulation_history
            ],
        }
    
    def run_full_simulation(self, scenario_id: str, force_ids: List[str],
                           scenario: str, context: str, rounds: int = 3):
        """运行完整模拟"""
        print(f"\n{'='*60}")
        print(f"Neo4j地缘政治模拟系统")
        print(f"{'='*60}")
        print(f"场景: {scenario_id}")
        print(f"势力: {len(force_ids)}个")
        print(f"轮数: {rounds}")
        print(f"图数据库: {'Neo4j' if self.neo4j and self.neo4j.connected else '内存模式'}")
        print(f"LLM: {self.llm.provider}/{self.llm.model}")
        print(f"{'='*60}")
        
        # 初始化
        self.initialize_graph(force_ids, scenario)
        
        # 运行多轮
        for round_num in range(1, rounds + 1):
            self.run_simulation_round(round_num, force_ids, scenario, context)
        
        # 最终报告
        self._print_final_report(force_ids)
    
    def _print_final_report(self, force_ids: List[str]):
        """打印最终报告"""
        print(f"\n{'='*60}")
        print("模拟结束 - 最终报告")
        print(f"{'='*60}")
        
        print("\n[势力排名 - 最终影响力]")
        rankings = []
        for fid in force_ids:
            char = self.characters.get(fid, {})
            name = char.get("name", fid)
            influence = self.memory_graph["nodes"][fid].get("influence", 0.5)
            resource = self.memory_graph["nodes"][fid].get("resource", 1.0)
            rankings.append((name, influence, resource))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        for i, (name, influence, resource) in enumerate(rankings, 1):
            print(f"  {i}. {name}: 影响力={influence:.2f}, 资源={resource:.2f}")
        
        print("\n[关系网络 - 最终状态]")
        for edge_key, edge in self.memory_graph["edges"].items():
            from_name = self.characters.get(edge["from"], {}).get("name", edge["from"])
            to_name = self.characters.get(edge["to"], {}).get("name", edge["to"])
            status = "友好" if edge["weight"] > 0.3 else "敌对" if edge["weight"] < -0.3 else "中立"
            print(f"  {from_name} -> {to_name}: {edge['weight']:+.2f} ({status})")
        
        print("\n[模拟历史]")
        for state in self.simulation_history:
            print(f"  第{state.round_num}轮: 冲突强度={state.global_metrics.get('conflict_intensity', 0):.2f}, "
                  f"极化={state.global_metrics.get('polarization', 0):.2f}")


# 全局实例
neo4j_sim = Neo4jPoliticalSimulation()

if __name__ == "__main__":
    print("=== Neo4j地缘政治模拟 ===\n")
    
    sim = Neo4jPoliticalSimulation()
    
    scenario = "波斯湾战争：伊朗封锁霍尔木兹海峡，全球石油危机"
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
    
    sim.run_full_simulation('persian_gulf', forces, scenario, context, rounds=2)
    
    # 导出数据
    data = sim.export_graph_data()
    print(f"\n导出数据: {len(data['nodes'])}个节点, {len(data['edges'])}条边")
