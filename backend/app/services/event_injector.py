"""
Event Injector - 事件注入器
根据世界状态自动注入戏剧性事件
"""

import random
import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

class EventType(Enum):
    PEACE_OFFER = "peace_offer"
    WAR_DECLARED = "war_declared"
    CEASEFIRE = "ceasefire"
    ALLIANCE_FORMED = "alliance_formed"
    BETRAYAL = "betrayal"
    ATTACK = "attack"
    DEFENSE = "defense"
    SURRENDER = "surrender"
    CAPTURE = "capture"
    TRADE_AGREEMENT = "trade_agreement"
    SANCTIONS = "sanctions"
    EMBARGO = "embargo"
    PROTEST = "protest"
    REVOLUTION = "revolution"
    MASSACRE = "massacre"
    DIPLOMATIC_BREAK = "diplomatic_break"
    NEGOTIATION = "negotiation"
    MEDIATION = "mediation"
    ASSASSINATION = "assassination"
    COUP = "coup"
    NATURAL_DISASTER = "natural_disaster"
    PROPAGANDA = "propaganda"
    LEAK = "leak"
    FALSE_FLAG = "false_flag"

@dataclass
class GameEvent:
    event_id: str
    event_type: EventType
    description: str
    affected_agents: List[str]
    trigger_round: int
    duration: int = 1
    severity: float = 0.5
    conditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False

class EventInjector:
    EVENT_TEMPLATES = {
        EventType.WAR_DECLARED: [
            "{agent_a} 正式向 {agent_b} 宣战！",
            "{agent_a} 宣布对 {agent_b} 发动全面军事行动",
            "{agent_a} 撕毁停火协议，重启对 {agent_b} 的敌对行动"
        ],
        EventType.PEACE_OFFER: [
            "{agent_a} 向 {agent_b} 提出和平谈判",
            "{agent_a} 呼吁与 {agent_b} 停火",
            "{agent_a} 提议与 {agent_b} 签署和平条约"
        ],
        EventType.ALLIANCE_FORMED: [
            "{agent_a} 与 {agent_b} 结成战略同盟",
            "{agent_a} 和 {agent_b} 签署互助协议",
            "{agent_a} 宣布与 {agent_b} 建立全面合作关系"
        ],
        EventType.BETRAYAL: [
            "{agent_a} 背叛了与 {agent_b} 的盟约",
            "{agent_a} 暗中破坏与 {agent_b} 的合作",
            "{agent_a} 公开谴责 {agent_b} 的'背叛行为'"
        ],
        EventType.ATTACK: [
            "{agent_a} 对 {agent_b} 发动突袭",
            "{agent_a} 的军事力量攻击了 {agent_b}",
            "{agent_a} 宣布对 {agent_b} 实施精准打击"
        ],
        EventType.ASSASSINATION: [
            "{agent_a} 的高级将领被暗杀，疑似 {agent_b} 所为",
            "{agent_a} 的领导人遭遇刺杀未遂",
            "{agent_a} 指控 {agent_b} 策划暗杀行动"
        ],
        EventType.PROPAGANDA: [
            "{agent_a} 发起大规模宣传攻势对抗 {agent_b}",
            "{agent_a} 散布关于 {agent_b} 的虚假信息",
            "{agent_a} 的媒体猛烈抨击 {agent_b}"
        ],
        EventType.SANCTIONS: [
            "{agent_a} 对 {agent_b} 实施经济制裁",
            "{agent_a} 宣布冻结 {agent_b} 的资产",
            "{agent_a} 切断与 {agent_b} 的贸易往来"
        ],
        EventType.PROTEST: [
            "{agent_a} 内部爆发反战抗议",
            "{agent_a} 的民众游行要求停止冲突",
            "{agent_a} 面临国内政治压力"
        ],
        EventType.COUP: [
            "{agent_a} 发生军事政变",
            "{agent_a} 的政府被推翻",
            "{agent_a} 陷入政治混乱"
        ]
    }
    
    def __init__(self, simulation_dir: str, base_probability: float = 0.05,
                 min_rounds_between_events: int = 3):
        self.simulation_dir = simulation_dir
        self.base_probability = base_probability
        self.min_rounds_between_events = min_rounds_between_events
        self.last_event_round = 0
        self.active_events: List[GameEvent] = []
        self.event_counter = 0
        
    def should_inject_event(self, current_round: int, global_tension: float) -> bool:
        prob = self.base_probability
        tension_factor = global_tension / 100.0
        prob += tension_factor * 0.15
        
        rounds_since_last = current_round - self.last_event_round
        if rounds_since_last < self.min_rounds_between_events:
            return False
        
        if rounds_since_last > 10:
            prob += 0.1
        
        return random.random() < prob
    
    def select_event_type(self, world_state: Dict) -> Optional[EventType]:
        tension = world_state.get("global_tension", 40.0)
        relationships = world_state.get("relationships", {})
        
        hostile_count = sum(1 for r in relationships.values() 
                          if r.get("state") in ["hostile", "at_war"])
        allied_count = sum(1 for r in relationships.values() 
                         if r.get("state") in ["friendly", "allied"])
        
        candidates = []
        
        if tension > 80:
            candidates.extend([EventType.WAR_DECLARED, EventType.ATTACK, 
                             EventType.ASSASSINATION, EventType.COUP])
        elif tension > 60:
            candidates.extend([EventType.ATTACK, EventType.SANCTIONS, 
                             EventType.PROPAGANDA, EventType.BETRAYAL])
        elif tension > 40:
            candidates.extend([EventType.PROPAGANDA, EventType.SANCTIONS,
                             EventType.PROTEST, EventType.DIPLOMATIC_BREAK])
        else:
            candidates.extend([EventType.PEACE_OFFER, EventType.NEGOTIATION,
                             EventType.ALLIANCE_FORMED, EventType.TRADE_AGREEMENT])
        
        if hostile_count > 0:
            candidates.extend([EventType.ATTACK, EventType.WAR_DECLARED] * 2)
        
        if allied_count > 0 and random.random() < 0.1:
            candidates.append(EventType.BETRAYAL)
        
        return random.choice(candidates) if candidates else None
    
    def generate_event(self, event_type: EventType, world_state: Dict,
                      agent_ids: List[str]) -> Optional[GameEvent]:
        if event_type not in self.EVENT_TEMPLATES:
            return None
        
        if len(agent_ids) < 2:
            return None
        
        agent_a, agent_b = random.sample(agent_ids, 2)
        templates = self.EVENT_TEMPLATES[event_type]
        template = random.choice(templates)
        
        agents = world_state.get("agents", {})
        name_a = agents.get(agent_a, {}).get("name", agent_a)
        name_b = agents.get(agent_b, {}).get("name", agent_b)
        
        description = template.format(agent_a=name_a, agent_b=name_b)
        
        self.event_counter += 1
        return GameEvent(
            event_id=f"evt_{self.event_counter}",
            event_type=event_type,
            description=description,
            affected_agents=[agent_a, agent_b],
            trigger_round=world_state.get("round", 0),
            severity=random.uniform(0.3, 1.0)
        )
    
    def inject_event(self, world_state: Dict, agent_ids: List[str]) -> Optional[GameEvent]:
        current_round = world_state.get("round", 0)
        global_tension = world_state.get("global_tension", 40.0)
        
        if not self.should_inject_event(current_round, global_tension):
            return None
        
        event_type = self.select_event_type(world_state)
        if not event_type:
            return None
        
        event = self.generate_event(event_type, world_state, agent_ids)
        if event:
            self.active_events.append(event)
            self.last_event_round = current_round
            self.save()
        
        return event
    
    def get_active_events(self, current_round: int) -> List[GameEvent]:
        active = []
        for event in self.active_events:
            if not event.resolved:
                if current_round <= event.trigger_round + event.duration:
                    active.append(event)
                else:
                    event.resolved = True
        return active
    
    def save(self):
        events_file = os.path.join(self.simulation_dir, "events_state.json")
        try:
            with open(events_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_event_round": self.last_event_round,
                    "event_counter": self.event_counter,
                    "active_events": [
                        {
                            "event_id": e.event_id,
                            "event_type": e.event_type.value,
                            "description": e.description,
                            "affected_agents": e.affected_agents,
                            "trigger_round": e.trigger_round,
                            "severity": e.severity,
                            "resolved": e.resolved
                        }
                        for e in self.active_events
                    ]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[EventInjector] 保存失败: {e}")
