"""
GraphRAG 集成模块
将 Neo4j 图谱数据与 LLM 结合，实现真正的 RAG 增强模拟
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .neo4j_adapter import get_neo4j_adapter


@dataclass
class GraphContext:
    """图谱上下文"""
    agent_id: str
    agent_name: str
    relationships: List[Dict[str, Any]]  # 关系数据
    related_events: List[Dict[str, Any]]  # 相关事件
    faction_info: Dict[str, Any]  # 阵营信息
    recent_actions: List[Dict[str, Any]]  # 最近动作


class GraphRAGEnhancer:
    """
    GraphRAG 增强器
    
    功能：
    1. 从 Neo4j 查询 Agent 关系网络
    2. 构建上下文增强的提示词
    3. 支持动态关系更新
    """
    
    def __init__(self, graph_id: str = "neo4j_graph"):
        self.graph_id = graph_id
        self.neo4j = get_neo4j_adapter()
        self.enabled = self.neo4j.is_connected()
        
        if not self.enabled:
            print("[GraphRAG] Neo4j 未连接，GraphRAG 功能禁用")
        else:
            print(f"[GraphRAG] 已连接到 {self.graph_id}")
    
    def get_agent_context(self, agent_id: str, agent_name: str) -> GraphContext:
        """
        获取 Agent 的图谱上下文
        
        查询：
        1. 直接关系（盟友、敌对、中立）
        2. 间接关系（共同盟友、共同敌人）
        3. 相关事件
        4. 阵营归属
        """
        if not self.enabled:
            return GraphContext(agent_id, agent_name, [], [], {}, [])
        
        try:
            # 1. 查询直接关系
            relationships = self._query_direct_relationships(agent_name)
            
            # 2. 查询相关事件
            related_events = self._query_related_events(agent_name)
            
            # 3. 查询阵营信息
            faction_info = self._query_faction_info(agent_name)
            
            # 4. 查询最近动作
            recent_actions = self._query_recent_actions(agent_name)
            
            return GraphContext(
                agent_id=agent_id,
                agent_name=agent_name,
                relationships=relationships,
                related_events=related_events,
                faction_info=faction_info,
                recent_actions=recent_actions
            )
            
        except Exception as e:
            print(f"[GraphRAG] 查询失败: {e}")
            return GraphContext(agent_id, agent_name, [], [], {}, [])
    
    def _query_direct_relationships(self, agent_name: str) -> List[Dict]:
        """查询直接关系"""
        query = """
        MATCH (a {name: $name})-[r]->(b)
        WHERE NOT b:Chunk
        RETURN type(r) as relation_type, 
               b.name as target_name, 
               b.type as target_type,
               r.description as description,
               r.trust_level as trust_level
        UNION
        MATCH (b)-[r]->(a {name: $name})
        WHERE NOT b:Chunk
        RETURN type(r) as relation_type, 
               b.name as target_name, 
               b.type as target_type,
               r.description as description,
               r.trust_level as trust_level
        """
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(query, name=agent_name)
                relationships = []
                for record in result:
                    rel = {
                        "type": record["relation_type"],
                        "target": record["target_name"],
                        "target_type": record["target_type"],
                        "description": record.get("description", ""),
                        "trust": record.get("trust_level", 0)
                    }
                    relationships.append(rel)
                return relationships
        except Exception as e:
            print(f"[GraphRAG] 关系查询失败: {e}")
            return []
    
    def _query_related_events(self, agent_name: str) -> List[Dict]:
        """查询与 Agent 相关的事件"""
        query = """
        MATCH (e:Event)-[:INVOLVES]->(a {name: $name})
        RETURN e.name as event_name,
               e.description as description,
               e.severity as severity,
               e.timestamp as timestamp
        ORDER BY e.timestamp DESC
        LIMIT 5
        """
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(query, name=agent_name)
                events = []
                for record in result:
                    event = {
                        "name": record["event_name"],
                        "description": record.get("description", ""),
                        "severity": record.get("severity", "medium"),
                        "timestamp": record.get("timestamp", "")
                    }
                    events.append(event)
                return events
        except Exception as e:
            print(f"[GraphRAG] 事件查询失败: {e}")
            return []
    
    def _query_faction_info(self, agent_name: str) -> Dict:
        """查询阵营信息"""
        query = """
        MATCH (a {name: $name})-[:BELONGS_TO]->(f:Faction)
        RETURN f.name as faction_name,
               f.description as description,
               f.stance as stance
        """
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(query, name=agent_name)
                record = result.single()
                if record:
                    return {
                        "name": record["faction_name"],
                        "description": record.get("description", ""),
                        "stance": record.get("stance", "neutral")
                    }
                return {}
        except Exception as e:
            print(f"[GraphRAG] 阵营查询失败: {e}")
            return {}
    
    def _query_recent_actions(self, agent_name: str) -> List[Dict]:
        """查询 Agent 最近的动作"""
        query = """
        MATCH (a {name: $name})-[:PERFORMED]->(action:Action)
        RETURN action.type as action_type,
               action.description as description,
               action.timestamp as timestamp,
               action.target as target
        ORDER BY action.timestamp DESC
        LIMIT 10
        """
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(query, name=agent_name)
                actions = []
                for record in result:
                    action = {
                        "type": record["action_type"],
                        "description": record.get("description", ""),
                        "timestamp": record.get("timestamp", ""),
                        "target": record.get("target", "")
                    }
                    actions.append(action)
                return actions
        except Exception as e:
            print(f"[GraphRAG] 动作查询失败: {e}")
            return []
    
    def build_enhanced_prompt(self, agent_context: GraphContext, 
                             base_prompt: str,
                             current_situation: str = "") -> str:
        """
        构建增强的提示词
        
        将图谱上下文注入到提示词中
        """
        # 构建关系上下文
        relationship_context = ""
        if agent_context.relationships:
            # 过滤掉 BELONGS_TO 关系（阵营归属）
            filtered_relationships = [r for r in agent_context.relationships 
                                     if r.get("type") != "BELONGS_TO"]
            
            if filtered_relationships:
                relationship_context = "\n\n### 你的关系网络\n"
                for rel in filtered_relationships[:5]:  # 最多5个关系
                    trust = rel.get("trust", 0) or 0  # 处理 None
                    trust_desc = self._trust_level_description(trust)
                    relationship_context += f"- **{rel['target']}** ({rel['target_type']}): {rel['type']}, 信任度: {trust_desc}\n"
                    if rel.get("description"):
                        relationship_context += f"  - {rel['description']}\n"
        
        # 构建阵营上下文
        faction_context = ""
        if agent_context.faction_info:
            faction = agent_context.faction_info
            faction_context = f"\n\n### 你的阵营归属\n"
            faction_context += f"- 阵营: {faction.get('name', '未知')}\n"
            faction_context += f"- 立场: {faction.get('stance', '中立')}\n"
            if faction.get("description"):
                faction_context += f"- 描述: {faction['description']}\n"
        
        # 构建事件上下文
        event_context = ""
        if agent_context.related_events:
            event_context = "\n\n### 相关事件\n"
            for event in agent_context.related_events[:3]:  # 最多3个事件
                event_context += f"- **{event['name']}** (严重度: {event.get('severity', 'medium')})\n"
                if event.get("description"):
                    event_context += f"  - {event['description']}\n"
        
        # 构建最近动作上下文
        action_context = ""
        if agent_context.recent_actions:
            action_context = "\n\n### 你最近的动作\n"
            for action in agent_context.recent_actions[:3]:
                action_context += f"- {action['type']}: {action.get('description', '')[:50]}...\n"
        
        # 组合增强提示词
        enhanced_prompt = f"""{base_prompt}

{relationship_context}
{faction_context}
{event_context}
{action_context}

### 当前局势
{current_situation if current_situation else "无特殊局势"}

### 指令
基于以上背景信息，生成符合你角色和立场的内容。考虑你的关系网络和阵营利益。"""
        
        return enhanced_prompt
    
    def _trust_level_description(self, trust: float) -> str:
        """将信任度转换为描述"""
        if trust >= 0.8:
            return "高度信任"
        elif trust >= 0.5:
            return "友好"
        elif trust >= 0.2:
            return "中立偏友好"
        elif trust >= -0.2:
            return "中立"
        elif trust >= -0.5:
            return "中立偏敌对"
        elif trust >= -0.8:
            return "敌对"
        else:
            return "极度敌对"
    
    def update_relationship(self, agent_a: str, agent_b: str, 
                           action_type: str, content: str):
        """
        更新关系
        
        根据动作类型和内容更新 Neo4j 中的关系
        """
        if not self.enabled:
            return
        
        # 计算信任度变化
        trust_delta = self._calculate_trust_delta(action_type, content)
        
        # 更新 Neo4j
        query = """
        MATCH (a {name: $agent_a})-[r]-(b {name: $agent_b})
        SET r.trust_level = coalesce(r.trust_level, 0) + $trust_delta,
            r.last_interaction = datetime(),
            r.interaction_count = coalesce(r.interaction_count, 0) + 1
        RETURN r.trust_level as new_trust
        """
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(query, 
                                   agent_a=agent_a, 
                                   agent_b=agent_b,
                                   trust_delta=trust_delta)
                record = result.single()
                if record:
                    print(f"[GraphRAG] 更新关系: {agent_a} <-> {agent_b}, "
                          f"信任度变化: {trust_delta:+.2f}, "
                          f"新信任度: {record['new_trust']:.2f}")
        except Exception as e:
            print(f"[GraphRAG] 关系更新失败: {e}")
    
    def _calculate_trust_delta(self, action_type: str, content: str) -> float:
        """计算信任度变化"""
        # 基础变化
        base_delta = {
            "CREATE_POST": 0.0,
            "CREATE_COMMENT": 0.1,
            "LIKE_POST": 0.2,
            "LIKE_COMMENT": 0.15,
            "DISLIKE_POST": -0.2,
            "DISLIKE_COMMENT": -0.15,
            "REPOST": 0.1,
            "FOLLOW": 0.3,
            "UNFOLLOW": -0.3,
        }.get(action_type, 0.0)
        
        # 内容情感分析（简化版）
        content_lower = content.lower()
        
        # 积极词汇
        positive_words = ["支持", "合作", "友好", "感谢", "同意", "帮助", "和平"]
        positive_count = sum(1 for w in positive_words if w in content_lower)
        
        # 消极词汇
        negative_words = ["反对", "攻击", "威胁", "制裁", "谴责", "战争", "敌对"]
        negative_count = sum(1 for w in negative_words if w in content_lower)
        
        # 调整信任度
        sentiment_delta = (positive_count - negative_count) * 0.05
        
        return base_delta + sentiment_delta
    
    def record_action(self, agent_name: str, action_type: str, 
                     description: str, target: str = ""):
        """
        记录动作到图谱
        """
        if not self.enabled:
            return
        
        query = """
        MATCH (a {name: $agent_name})
        CREATE (action:Action {
            type: $action_type,
            description: $description,
            target: $target,
            timestamp: datetime()
        })
        CREATE (a)-[:PERFORMED]->(action)
        RETURN action
        """
        
        try:
            with self.neo4j.driver.session() as session:
                session.run(query,
                          agent_name=agent_name,
                          action_type=action_type,
                          description=description[:200],  # 限制长度
                          target=target)
        except Exception as e:
            print(f"[GraphRAG] 动作记录失败: {e}")


# 便捷函数
def get_graph_rag_enhancer(graph_id: str = "neo4j_graph") -> GraphRAGEnhancer:
    """获取 GraphRAG 增强器实例"""
    return GraphRAGEnhancer(graph_id)


def enhance_agent_prompt(agent_id: str, agent_name: str, 
                        base_prompt: str,
                        graph_id: str = "neo4j_graph",
                        current_situation: str = "") -> str:
    """
    增强 Agent 提示词
    
    便捷函数，一次性获取增强的提示词
    """
    enhancer = get_graph_rag_enhancer(graph_id)
    context = enhancer.get_agent_context(agent_id, agent_name)
    return enhancer.build_enhanced_prompt(context, base_prompt, current_situation)


if __name__ == "__main__":
    # 测试
    enhancer = GraphRAGEnhancer()
    
    if enhancer.enabled:
        context = enhancer.get_agent_context("0", "哈梅内伊")
        print(f"Agent: {context.agent_name}")
        print(f"关系数: {len(context.relationships)}")
        print(f"事件数: {len(context.related_events)}")
        
        base_prompt = "你是一个国家的领导人，请发表关于当前局势的看法。"
        enhanced = enhancer.build_enhanced_prompt(context, base_prompt)
        print(f"\n增强提示词:\n{enhanced[:500]}...")
    else:
        print("GraphRAG 未启用")
