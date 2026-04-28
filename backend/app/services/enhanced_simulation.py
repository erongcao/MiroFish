"""
Enhanced Simulation Integration Layer
增强模拟集成层 - 将世界状态、事件注入、跨智能体交互整合到主模拟循环
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# 尝试导入增强模块（避免触发 Flask 导入）
try:
    # 直接导入模块文件，不通过 app 包
    import importlib.util
    import os
    
    services_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 导入 world_state_engine
    spec = importlib.util.spec_from_file_location(
        "world_state_engine", 
        os.path.join(services_dir, "world_state_engine.py")
    )
    wse_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wse_module)
    WorldStateEngine = wse_module.WorldStateEngine
    RelationshipState = wse_module.RelationshipState
    AgentStatus = wse_module.AgentStatus
    
    # 导入 event_injector
    spec = importlib.util.spec_from_file_location(
        "event_injector",
        os.path.join(services_dir, "event_injector.py")
    )
    ei_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ei_module)
    EventInjector = ei_module.EventInjector
    EventType = ei_module.EventType
    GameEvent = ei_module.GameEvent
    
    # 导入 cross_agent_interaction
    spec = importlib.util.spec_from_file_location(
        "cross_agent_interaction",
        os.path.join(services_dir, "cross_agent_interaction.py")
    )
    cai_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cai_module)
    CrossAgentInteraction = cai_module.CrossAgentInteraction
    ActionType = cai_module.ActionType
    
    # 导入 GraphRAG Bridge
    spec = importlib.util.spec_from_file_location(
        "graph_rag_bridge",
        os.path.join(services_dir, "graph_rag_bridge.py")
    )
    grab_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(grab_module)
    GraphRAGWorldBridge = grab_module.GraphRAGWorldBridge
    
    ENHANCED_MODE = True
except Exception as e:
    print(f"[EnhancedSim] 增强模块导入失败: {e}")
    ENHANCED_MODE = False
    WorldStateEngine = None
    EventInjector = None
    CrossAgentInteraction = None
    EventType = None
    GameEvent = None
    ActionType = None
    RelationshipState = None
    AgentStatus = None

@dataclass
class RoundContext:
    round_num: int
    agent_configs: List[Dict]
    all_posts: List[Dict]
    active_events: List[Any] = field(default_factory=list)
    new_events: List[Any] = field(default_factory=list)
    interactions: List[Dict] = field(default_factory=list)

class EnhancedSimulationIntegrator:
    def __init__(self, simulation_dir: str, config: Dict[str, Any]):
        self.simulation_dir = simulation_dir
        self.config = config
        self.enabled = ENHANCED_MODE
        
        if not self.enabled:
            print("[EnhancedSim] 增强模式未启用")
            return
        
        initial_tension = config.get("initial_tension", 40.0)
        self.world_state = WorldStateEngine(simulation_dir, initial_tension)
        
        event_config = config.get("event_injector", {})
        self.event_injector = EventInjector(
            simulation_dir,
            base_probability=event_config.get("base_probability", 0.05),
            min_rounds_between_events=event_config.get("min_rounds_between_events", 3)
        )
        
        cross_config = config.get("cross_agent", {})
        self.cross_agent = CrossAgentInteraction(
            simulation_dir,
            min_comments_per_round=cross_config.get("min_comments_per_round", 1),
            max_posts_in_feed=cross_config.get("max_posts_in_feed", 10)
        )
        
        # 初始化 GraphRAG Bridge
        self.graph_rag_bridge = GraphRAGWorldBridge(simulation_dir, config)
        
        print("[EnhancedSim] 增强模拟集成器已初始化")
    
    def initialize(self, agent_configs: List[Dict]):
        if not self.enabled:
            return
        
        self.world_state.initialize(agent_configs)
        print(f"[EnhancedSim] 已初始化 {len(agent_configs)} 个智能体的世界状态")
    
    def pre_round_processing(self, round_num: int, agent_configs: List[Dict],
                            all_posts: List[Dict]) -> RoundContext:
        context = RoundContext(
            round_num=round_num,
            agent_configs=agent_configs,
            all_posts=all_posts
        )
        
        if not self.enabled:
            return context
        
        world_summary = self.world_state.get_state_summary()
        
        agent_ids = list(self.world_state.agents.keys())
        event = self.event_injector.inject_event(world_summary, agent_ids)
        if event:
            context.new_events.append(event)
            self.world_state.record_event(
                event.event_type.value,
                event.description,
                event.affected_agents
            )
        
        context.active_events = self.event_injector.get_active_events(round_num)
        
        for post in all_posts:
            self._analyze_post_interactions(post, round_num, context)
        
        return context
    
    def _analyze_post_interactions(self, post: Dict, round_num: int, 
                                  context: RoundContext):
        agent_id = str(post.get("agent_id", ""))
        content = post.get("content", "")
        
        if not agent_id or not content:
            return
        
        for other_id, other_agent in self.world_state.agents.items():
            if other_id == agent_id:
                continue
            
            if other_agent.name in content or other_id in content:
                interaction = self.cross_agent.analyze_interaction(
                    agent_id, other_id, content, round_num
                )
                
                self.world_state.update_relationship(
                    agent_id, other_id, interaction.trust_impact,
                    {"type": interaction.action_type.value, 
                     "description": content[:100]}
                )
                
                context.interactions.append({
                    "from": agent_id,
                    "to": other_id,
                    "type": interaction.action_type.value,
                    "impact": interaction.trust_impact
                })
    
    def record_action(self, agent_id: str, action_type: str, 
                     action_args: Dict, round_context: RoundContext):
        if not self.enabled:
            return
        
        if agent_id in self.world_state.agents:
            agent = self.world_state.agents[agent_id]
            agent.actions_count += 1
            
            if action_type == "CREATE_POST":
                agent.posts_count += 1
            elif action_type == "CREATE_COMMENT":
                agent.comments_count += 1
        
        content = action_args.get("content", "")
        target_name = action_args.get("target_name", "")  # 可能的目标
        
        # 记录到 GraphRAG
        if self.graph_rag_bridge.enabled:
            agent_name = self.world_state.agents.get(agent_id, None)
            if agent_name:
                agent_name = agent_name.name
                self.graph_rag_bridge.on_action_performed(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    action_type=action_type,
                    content=content,
                    target_name=target_name
                )
        
        if content:
            for other_id, other_agent in self.world_state.agents.items():
                if other_id == agent_id:
                    continue
                
                if other_agent.name in content or other_id in content:
                    interaction = self.cross_agent.analyze_interaction(
                        agent_id, other_id, content, round_context.round_num
                    )
                    
                    self.world_state.update_relationship(
                        agent_id, other_id, interaction.trust_impact
                    )
    
    def post_round_processing(self, round_context: RoundContext):
        if not self.enabled:
            return
        
        self.world_state.advance_round()
        self.cross_agent.save()
        self.event_injector.save()
        
        summary = self.world_state.get_state_summary()
        print(f"[EnhancedSim] Round {summary['round']}: "
              f"tension={summary['global_tension']:.1f}, "
              f"alive={summary['alive_agents']}/{summary['total_agents']}, "
              f"events={summary['total_events']}")
    
    def get_enhanced_feed(self, agent_id: str, round_num: int,
                         base_feed: List[Dict]) -> List[Dict]:
        if not self.enabled:
            return base_feed
        
        enhanced_feed = base_feed.copy()
        
        active_events = self.event_injector.get_active_events(round_num)
        for event in active_events:
            if agent_id in event.affected_agents:
                enhanced_feed.insert(0, {
                    "type": "event",
                    "event_id": event.event_id,
                    "content": f"[事件] {event.description}",
                    "severity": event.severity,
                    "priority": 10
                })
        
        agent_relationships = {}
        for key, rel in self.world_state.relationships.items():
            if agent_id in [rel.agent_a, rel.agent_b]:
                other = rel.agent_b if agent_id == rel.agent_a else rel.agent_a
                agent_relationships[other] = rel.trust
        
        for post in enhanced_feed:
            post_agent = str(post.get("agent_id", ""))
            if post_agent in agent_relationships:
                trust = agent_relationships[post_agent]
                if trust < -0.5:
                    post["relationship_context"] = "hostile"
                elif trust > 0.3:
                    post["relationship_context"] = "friendly"
        
        return enhanced_feed[:self.config.get("cross_agent", {}).get("max_posts_in_feed", 10)]
    
    def get_agent_status(self, agent_id: str) -> Dict:
        if not self.enabled or agent_id not in self.world_state.agents:
            return {"status": "active", "enhanced": False}
        
        agent = self.world_state.agents[agent_id]
        
        relationships = {}
        for key, rel in self.world_state.relationships.items():
            if agent_id in [rel.agent_a, rel.agent_b]:
                other = rel.agent_b if agent_id == rel.agent_a else rel.agent_a
                relationships[other] = {
                    "trust": rel.trust,
                    "state": rel.state.value,
                    "interactions": rel.interaction_count
                }
        
        return {
            "status": agent.status.value,
            "influence": agent.influence,
            "actions_count": agent.actions_count,
            "posts_count": agent.posts_count,
            "comments_count": agent.comments_count,
            "relationships": relationships,
            "enhanced": True
        }


def classify_action_type(content: str) -> str:
    if not ENHANCED_MODE:
        return "NEUTRAL"
    
    content_lower = content.lower()
    
    attack_words = ["攻击", "打击", "轰炸", "入侵", "消灭", "摧毁", "开战", "宣战", "杀死"]
    if any(w in content_lower for w in attack_words):
        return "ATTACK"
    
    alliance_words = ["盟友", "同盟", "联盟", "合作", "伙伴", "联合", "共同", "互助"]
    if any(w in content_lower for w in alliance_words):
        return "ALLIANCE_OFFER"
    
    peace_words = ["停火", "和平", "谈判", "和解", "妥协", "让步", "条约", "协议"]
    if any(w in content_lower for w in peace_words):
        return "PEACE_OFFER"
    
    hostile_words = ["战争", "敌人", "仇恨", "背叛", "威胁", "制裁", "报复"]
    if any(w in content_lower for w in hostile_words):
        return "HOSTILE"
    
    provocative_words = ["谴责", "抗议", "警告", "不满", "反对", "质疑"]
    if any(w in content_lower for w in provocative_words):
        return "PROVOCATIVE"
    
    supportive_words = ["支持", "帮助", "同意", "理解", "尊重", "感谢", "赞赏"]
    if any(w in content_lower for w in supportive_words):
        return "SUPPORTIVE"
    
    return "NEUTRAL"
