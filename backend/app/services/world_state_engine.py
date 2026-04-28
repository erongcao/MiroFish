"""
World State Engine - 世界状态引擎
跟踪全局状态、智能体关系、事件历史
"""

import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

class RelationshipState(Enum):
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ALLIED = "allied"
    HOSTILE = "hostile"
    AT_WAR = "at_war"
    DEAD = "dead"

class AgentStatus(Enum):
    ACTIVE = "active"
    INJURED = "injured"
    CAPTURED = "captured"
    DEAD = "dead"
    INACTIVE = "inactive"

@dataclass
class Relationship:
    agent_a: str
    agent_b: str
    trust: float = 0.0
    state: RelationshipState = RelationshipState.NEUTRAL
    interaction_count: int = 0
    last_interaction_round: int = 0
    events: List[Dict] = field(default_factory=list)

@dataclass
class AgentState:
    agent_id: str
    name: str
    status: AgentStatus = AgentStatus.ACTIVE
    influence: float = 1.0
    sentiment: float = 0.0
    actions_count: int = 0
    posts_count: int = 0
    comments_count: int = 0
    events_triggered: List[str] = field(default_factory=list)

class WorldStateEngine:
    def __init__(self, simulation_dir: str, initial_tension: float = 40.0):
        self.simulation_dir = simulation_dir
        self.round = 0
        self.global_tension = initial_tension
        self.max_tension = 100.0
        self.min_tension = 0.0
        self.agents: Dict[str, AgentState] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.events_history: List[Dict] = []
        self.alive_agents: set = set()
        self.total_events = 0
        
    def initialize(self, agent_configs: List[Dict]):
        for config in agent_configs:
            agent_id = str(config.get("agent_id", ""))
            name = config.get("name", f"Agent_{agent_id}")
            self.agents[agent_id] = AgentState(agent_id=agent_id, name=name)
            self.alive_agents.add(agent_id)
        
        agent_ids = list(self.agents.keys())
        for i, a in enumerate(agent_ids):
            for b in agent_ids[i+1:]:
                key = f"{a}|{b}"
                self.relationships[key] = Relationship(agent_a=a, agent_b=b)
        
        self.save()
    
    def get_relationship_key(self, agent_a: str, agent_b: str) -> str:
        return f"{min(agent_a, agent_b)}|{max(agent_a, agent_b)}"
    
    def update_relationship(self, agent_a: str, agent_b: str, 
                           trust_delta: float, event: Optional[Dict] = None):
        key = self.get_relationship_key(agent_a, agent_b)
        if key not in self.relationships:
            self.relationships[key] = Relationship(agent_a=agent_a, agent_b=agent_b)
        
        rel = self.relationships[key]
        rel.trust = max(-1.0, min(1.0, rel.trust + trust_delta))
        rel.interaction_count += 1
        rel.last_interaction_round = self.round
        
        if event:
            rel.events.append({
                "round": self.round,
                "type": event.get("type", "unknown"),
                "description": event.get("description", ""),
                "trust_delta": trust_delta
            })
        
        if rel.trust <= -0.85:
            rel.state = RelationshipState.AT_WAR
        elif rel.trust <= -0.5:
            rel.state = RelationshipState.HOSTILE
        elif rel.trust >= 0.7:
            rel.state = RelationshipState.ALLIED
        elif rel.trust >= 0.3:
            rel.state = RelationshipState.FRIENDLY
        else:
            rel.state = RelationshipState.NEUTRAL
        
        if rel.state == RelationshipState.AT_WAR:
            self.global_tension = min(self.max_tension, self.global_tension + 5.0)
    
    def advance_round(self):
        self.round += 1
        self.global_tension = max(self.min_tension, self.global_tension - 0.5)
        self.save()
    
    def record_event(self, event_type: str, description: str, 
                    affected_agents: List[str] = None):
        self.total_events += 1
        event = {
            "id": f"evt_{self.total_events}",
            "round": self.round,
            "type": event_type,
            "description": description,
            "affected_agents": affected_agents or [],
        }
        self.events_history.append(event)
        
        if event_type in ["WAR_DECLARED", "AGENT_KILLED", "CRISIS"]:
            self.global_tension = min(self.max_tension, self.global_tension + 10.0)
        
        self.save()
        return event
    
    def update_agent_status(self, agent_id: str, status: AgentStatus):
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            if status == AgentStatus.DEAD:
                self.alive_agents.discard(agent_id)
            self.save()
    
    def get_state_summary(self) -> Dict:
        return {
            "round": self.round,
            "global_tension": self.global_tension,
            "alive_agents": len(self.alive_agents),
            "total_agents": len(self.agents),
            "total_events": self.total_events,
            "relationships": {
                k: {"trust": v.trust, "state": v.state.value, "interactions": v.interaction_count}
                for k, v in self.relationships.items()
            }
        }
    
    def save(self):
        state_file = os.path.join(self.simulation_dir, "world_state.json")
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "round": self.round,
                    "global_tension": self.global_tension,
                    "agents": {
                        k: {"agent_id": v.agent_id, "name": v.name, "status": v.status.value,
                            "influence": v.influence, "actions_count": v.actions_count}
                        for k, v in self.agents.items()
                    },
                    "relationships": {
                        k: {"agent_a": v.agent_a, "agent_b": v.agent_b, "trust": v.trust,
                            "state": v.state.value, "interaction_count": v.interaction_count}
                        for k, v in self.relationships.items()
                    },
                    "events_history": self.events_history[-50:],
                    "alive_agents": list(self.alive_agents),
                    "total_events": self.total_events
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WorldState] 保存失败: {e}")
    
    def load(self):
        state_file = os.path.join(self.simulation_dir, "world_state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.round = data.get("round", 0)
                    self.global_tension = data.get("global_tension", 40.0)
                    self.total_events = data.get("total_events", 0)
                    self.alive_agents = set(data.get("alive_agents", []))
            except Exception as e:
                print(f"[WorldState] 加载失败: {e}")
