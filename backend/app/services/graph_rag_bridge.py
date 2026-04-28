"""
GraphRAG World State Bridge - GraphRAG 与 WorldStateEngine 的连接器
将模拟过程中的Agent互动同步到Neo4j图谱
"""

import os
import sys
from typing import Dict, List, Optional, Any

class GraphRAGWorldBridge:
    """GraphRAG 与 WorldStateEngine 之间的桥接器"""
    
    def __init__(self, simulation_dir: str, config: Dict[str, Any]):
        self.simulation_dir = simulation_dir
        self.config = config
        self.enabled = False
        
        # 尝试导入 GraphRAG
        try:
            sys.path.insert(0, os.path.join(simulation_dir, '..', '..', 'app', 'services'))
            from graph_rag import GraphRAGEnhancer
            self.graph_rag = GraphRAGEnhancer()
            self.enabled = self.graph_rag.enabled
            print(f"[GraphRAG-Bridge] 初始化完成 (enabled={self.enabled})")
        except Exception as e:
            print(f"[GraphRAG-Bridge] GraphRAG 导入失败: {e}")
            self.graph_rag = None
    
    def on_action_performed(self, agent_id: str, agent_name: str, action_type: str, 
                           content: str, target_name: Optional[str] = None):
        """
        当Agent执行动作时调用 - 记录到Neo4j
        """
        if not self.enabled:
            return
        
        try:
            # 记录动作
            self.graph_rag.record_action(
                agent_name=agent_name,
                action_type=action_type,
                description=content[:200],  # 截断
                target=target_name or ""
            )
            
            # 如果有目标，更新关系
            if target_name:
                trust_delta = self._calculate_trust(action_type, content)
                self.graph_rag.update_relationship(
                    agent_a=agent_name,
                    agent_b=target_name,
                    action_type=action_type,
                    content=content
                )
        except Exception as e:
            print(f"[GraphRAG-Bridge] 记录动作失败: {e}")
    
    def _calculate_trust(self, action_type: str, content: str) -> float:
        """根据动作类型和内容计算信任度变化"""
        # 基础信任变化
        action_delta = {
            "CREATE_POST": 0.01,
            "CREATE_COMMENT": 0.03,
            "LIKE_POST": 0.02,
            "LIKE_COMMENT": 0.02,
            "QUOTE_POST": 0.05,
            "REPOST": 0.03,
            "DISLIKE_POST": -0.02,
            "REPLY": 0.03,
        }.get(action_type, 0.0)
        
        # 内容情感分析
        positive_words = ["和平", "合作", "对话", "支持", "友好", "共赢", "稳定"]
        negative_words = ["反对", "威胁", "制裁", "战争", "敌人", "敌对", "打击"]
        
        content_lower = content.lower()
        positive_count = sum(1 for w in positive_words if w in content_lower)
        negative_count = sum(1 for w in negative_words if w in content_lower)
        
        sentiment_delta = (positive_count - negative_count) * 0.01
        
        return action_delta + sentiment_delta
    
    def get_agent_context(self, agent_id: str, agent_name: str) -> Optional[Dict]:
        """获取Agent的图谱上下文"""
        if not self.enabled:
            return None
        
        try:
            context = self.graph_rag.get_agent_context(agent_id, agent_name)
            return {
                "relationships": context.relationships,
                "faction_info": context.faction_info,
                "related_events": context.related_events,
                "recent_actions": context.recent_actions
            }
        except Exception as e:
            print(f"[GraphRAG-Bridge] 获取上下文失败: {e}")
            return None
    
    def on_event_occurred(self, event_name: str, event_type: str, 
                          affected_agents: List[str], severity: str = "medium"):
        """
        当事件发生时调用 - 更新图谱中的事件节点
        """
        if not self.enabled:
            return
        
        try:
            # 在Neo4j中创建事件节点（如果不存在）
            with self.graph_rag.neo4j.driver.session() as session:
                session.run("""
                    MERGE (e:Event {name: $name})
                    SET e.description = $description,
                        e.severity = $severity,
                        e.type = $type
                """, name=event_name, 
                    description=f"{event_type}事件",
                    severity=severity,
                    type=event_type)
                
                # 关联受影响的Agent
                for agent_name in affected_agents:
                    session.run("""
                        MATCH (a:Agent {name: $name})
                        MATCH (e:Event {name: $event_name})
                        MERGE (e)-[:INVOLVES]->(a)
                    """, name=agent_name, event_name=event_name)
        except Exception as e:
            print(f"[GraphRAG-Bridge] 记录事件失败: {e}")
