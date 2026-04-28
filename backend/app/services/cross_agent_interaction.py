"""
Cross-Agent Interaction - 跨智能体交互
分析智能体间的互动，更新关系状态
"""

import json
import os
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class ActionType(Enum):
    NEUTRAL = "neutral"
    SUPPORTIVE = "supportive"
    PROVOCATIVE = "provocative"
    HOSTILE = "hostile"
    ATTACK = "attack"
    ALLIANCE_OFFER = "alliance_offer"
    PEACE_OFFER = "peace_offer"
    IGNORE = "ignore"

@dataclass
class Interaction:
    from_agent: str
    to_agent: str
    action_type: ActionType
    content: str
    round: int
    sentiment: float = 0.0
    trust_impact: float = 0.0

class CrossAgentInteraction:
    POSITIVE_WORDS = [
        "和平", "合作", "友好", "支持", "帮助", "同意", "理解", "尊重",
        "感谢", "赞赏", "信任", "团结", "协商", "谈判", "停火", "和解"
    ]
    
    NEGATIVE_WORDS = [
        "战争", "攻击", "消灭", "摧毁", "杀死", "死亡", "仇恨", "敌人",
        "背叛", "欺骗", "威胁", "制裁", "入侵", "轰炸", "屠杀", "报复"
    ]
    
    ALLIANCE_WORDS = [
        "盟友", "同盟", "联盟", "合作", "伙伴", "联合", "共同", "互助"
    ]
    
    ATTACK_WORDS = [
        "攻击", "打击", "轰炸", "入侵", "消灭", "摧毁", "开战", "宣战"
    ]
    
    PEACE_WORDS = [
        "停火", "和平", "谈判", "和解", "妥协", "让步", "条约", "协议"
    ]
    
    def __init__(self, simulation_dir: str, min_comments_per_round: int = 1,
                 max_posts_in_feed: int = 10):
        self.simulation_dir = simulation_dir
        self.min_comments_per_round = min_comments_per_round
        self.max_posts_in_feed = max_posts_in_feed
        self.interactions: List[Interaction] = []
        self.agent_interaction_counts: Dict[str, int] = defaultdict(int)
        self.comment_threads: Dict[str, List[Dict]] = defaultdict(list)
        
    def classify_content(self, content: str) -> Tuple[ActionType, float]:
        content_lower = content.lower()
        
        positive_count = sum(1 for w in self.POSITIVE_WORDS if w in content_lower)
        negative_count = sum(1 for w in self.NEGATIVE_WORDS if w in content_lower)
        
        sentiment = (positive_count - negative_count) / max(len(content) / 10, 1)
        sentiment = max(-1.0, min(1.0, sentiment))
        
        if any(w in content_lower for w in self.ATTACK_WORDS):
            return ActionType.ATTACK, sentiment
        elif any(w in content_lower for w in self.ALLIANCE_WORDS):
            return ActionType.ALLIANCE_OFFER, sentiment
        elif any(w in content_lower for w in self.PEACE_WORDS):
            return ActionType.PEACE_OFFER, sentiment
        elif negative_count > positive_count * 2:
            return ActionType.HOSTILE, sentiment
        elif negative_count > positive_count:
            return ActionType.PROVOCATIVE, sentiment
        elif positive_count > negative_count:
            return ActionType.SUPPORTIVE, sentiment
        else:
            return ActionType.NEUTRAL, sentiment
    
    def analyze_interaction(self, from_agent: str, to_agent: str,
                         content: str, round_num: int) -> Interaction:
        action_type, sentiment = self.classify_content(content)
        
        trust_impact = self._calculate_trust_impact(action_type, sentiment, content)
        
        interaction = Interaction(
            from_agent=from_agent,
            to_agent=to_agent,
            action_type=action_type,
            content=content[:200],
            round=round_num,
            sentiment=sentiment,
            trust_impact=trust_impact
        )
        
        self.interactions.append(interaction)
        self.agent_interaction_counts[from_agent] += 1
        
        return interaction
    
    def _calculate_trust_impact(self, action_type: ActionType, 
                               sentiment: float, content: str) -> float:
        base_impact = {
            ActionType.ATTACK: -0.40,
            ActionType.HOSTILE: -0.20,
            ActionType.PROVOCATIVE: -0.10,
            ActionType.NEUTRAL: 0.0,
            ActionType.SUPPORTIVE: 0.10,
            ActionType.PEACE_OFFER: 0.15,
            ActionType.ALLIANCE_OFFER: 0.20,
            ActionType.IGNORE: 0.0
        }
        
        impact = base_impact.get(action_type, 0.0)
        impact += sentiment * 0.1
        
        if len(content) < 50:
            impact *= 0.5
        
        return max(-0.5, min(0.5, impact))
    
    def get_agent_interactions(self, agent_id: str, 
                            round_num: Optional[int] = None) -> List[Interaction]:
        interactions = [i for i in self.interactions 
                       if i.from_agent == agent_id or i.to_agent == agent_id]
        if round_num is not None:
            interactions = [i for i in interactions if i.round == round_num]
        return interactions
    
    def get_relationship_summary(self, agent_a: str, agent_b: str) -> Dict:
        interactions = [i for i in self.interactions
                       if (i.from_agent == agent_a and i.to_agent == agent_b) or
                          (i.from_agent == agent_b and i.to_agent == agent_a)]
        
        if not interactions:
            return {"status": "neutral", "trust": 0.0, "interactions": 0}
        
        avg_sentiment = sum(i.sentiment for i in interactions) / len(interactions)
        total_trust_impact = sum(i.trust_impact for i in interactions)
        
        if total_trust_impact <= -0.5:
            status = "hostile"
        elif total_trust_impact <= -0.2:
            status = "tense"
        elif total_trust_impact >= 0.3:
            status = "friendly"
        elif total_trust_impact >= 0.1:
            status = "cooperative"
        else:
            status = "neutral"
        
        return {
            "status": status,
            "trust": total_trust_impact,
            "interactions": len(interactions),
            "avg_sentiment": avg_sentiment,
            "recent_interactions": [
                {
                    "round": i.round,
                    "type": i.action_type.value,
                    "sentiment": i.sentiment,
                    "impact": i.trust_impact
                }
                for i in interactions[-5:]
            ]
        }
    
    def save(self):
        state_file = os.path.join(self.simulation_dir, "cross_agent_state.json")
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "interactions": [
                        {
                            "from_agent": i.from_agent,
                            "to_agent": i.to_agent,
                            "action_type": i.action_type.value,
                            "sentiment": i.sentiment,
                            "trust_impact": i.trust_impact,
                            "round": i.round
                        }
                        for i in self.interactions[-100:]
                    ],
                    "interaction_counts": dict(self.agent_interaction_counts),
                    "comment_threads": {
                        k: v[-20:]
                        for k, v in self.comment_threads.items()
                    }
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CrossAgent] 保存失败: {e}")
