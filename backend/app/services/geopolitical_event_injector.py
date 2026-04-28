"""
Geopolitical Event Injector - 地缘政治事件注入器
生成模拟真实局势进展的事件
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import json

class EventType(Enum):
    # 外交事件
    DIPLOMATIC_MEETING = "diplomatic_meeting"  # 外交会议
    CEASEFIRE_PROPOSAL = "ceasefire_proposal"  # 停火提议
    SANCTIONS = "sanctions"  # 制裁
    SANCTIONS_LIFTED = "sanctions_lifted"  # 解除制裁
    
    # 军事事件
    MILITARY_EXERCISE = "military_exercise"  # 军事演习
    CEASEFIRE_VIOLATION = "ceasefire_violation"  # 停火违反
    ATTACK = "attack"  # 攻击
    DEFENSE = "defense"  # 防御
    
    # 经济事件
    OIL_PRICE_SHOCK = "oil_price_shock"  # 油价冲击
    TRADE_DEAL = "trade_deal"  # 贸易协议
    
    # 国际事件
    UN_RESOLUTION = "un_resolution"  # 联合国决议
    SUMMIT = "summit"  # 峰会

@dataclass
class GeopoliticalEvent:
    event_type: EventType
    name: str
    description: str
    affected_agents: List[str]
    tension_impact: float  # 对紧张度的影响 (+=升级, -=降级)
    round_duration: int  # 事件持续轮数
    probability: float  # 基础触发概率
    phase: str  # 模拟阶段: "early", "middle", "late"

class GeopoliticalEventInjector:
    """
    地缘政治事件注入器 - 推动局势进展
    """
    
    def __init__(self, simulation_dir: str, config: Dict[str, Any]):
        self.simulation_dir = simulation_dir
        self.config = config
        self.current_round = 0
        self.active_events: List[GeopoliticalEvent] = []
        self.event_history: List[Dict] = []
        self.last_event_round = 0
        
        # 配置
        self.base_probability = config.get("base_probability", 0.08)
        self.min_rounds_between_events = config.get("min_rounds_between_events", 2)
        self.max_active_events = config.get("max_active_events", 3)
        
        # 阶段定义
        self.phases = {
            "early": 1,      # 1-3轮: 初始阶段
            "middle": 4,     # 4-7轮: 发展阶段
            "late": 8        # 8-10轮: 收尾阶段
        }
    
    def get_current_phase(self, round_num: int) -> str:
        """获取当前模拟阶段"""
        if round_num <= 3:
            return "early"
        elif round_num <= 7:
            return "middle"
        else:
            return "late"
    
    def inject_event(self, world_summary: Dict, round_num: int) -> Optional[GeopoliticalEvent]:
        """
        注入新事件（基于当前状态和历史）
        """
        self.current_round = round_num
        current_phase = self.get_current_phase(round_num)
        global_tension = world_summary.get("global_tension", 40.0)
        
        # 检查冷却期
        rounds_since_last = round_num - self.last_event_round
        if rounds_since_last < self.min_rounds_between_events:
            return None
        
        # 活跃事件已达上限
        if len(self.active_events) >= self.max_active_events:
            return None
        
        # 根据阶段选择可能的事件
        candidates = self._get_candidate_events(current_phase, global_tension)
        
        # 按概率排序并选择
        selected = None
        for event in candidates:
            if random.random() < event.probability:
                selected = event
                break
        
        if selected:
            self.active_events.append(selected)
            self.last_event_round = round_num
            self.event_history.append({
                "round": round_num,
                "event": selected.name,
                "type": selected.event_type.value,
                "tension_impact": selected.tension_impact
            })
            return selected
        
        return None
    
    def _get_candidate_events(self, phase: str, global_tension: float) -> List[GeopoliticalEvent]:
        """获取候选事件"""
        candidates = []
        
        # 停火提议事件（中期更可能出现）
        if phase in ["middle", "late"] and global_tension > 50:
            candidates.append(GeopoliticalEvent(
                event_type=EventType.CEASEFIRE_PROPOSAL,
                name="停火协议谈判",
                description="伊朗和美国开始就停火协议进行谈判",
                affected_agents=["哈梅内伊", "特朗普", "伊朗总统", "伊朗外交部长"],
                tension_impact=-15.0,
                round_duration=3,
                probability=0.15,
                phase=phase
            ))
        
        # 制裁事件
        if global_tension < 60:
            candidates.append(GeopoliticalEvent(
                event_type=EventType.SANCTIONS,
                name="新制裁宣布",
                description="美国宣布对伊朗实施新制裁",
                affected_agents=["特朗普", "伊朗总统", "伊朗革命卫队", "卢比奥"],
                tension_impact=10.0,
                round_duration=2,
                probability=0.12,
                phase=phase
            ))
        
        # 军事演习
        if global_tension > 40:
            candidates.append(GeopoliticalEvent(
                event_type=EventType.MILITARY_EXERCISE,
                name="美军海湾演习",
                description="美国在波斯湾举行军事演习",
                affected_agents=["特朗普", "伊朗革命卫队", "伊朗总统", "以色列"],
                tension_impact=8.0,
                round_duration=2,
                probability=0.10,
                phase=phase
            ))
        
        # 停火违反
        if global_tension > 60 and random.random() < 0.3:
            candidates.append(GeopoliticalEvent(
                event_type=EventType.CEASEFIRE_VIOLATION,
                name="停火协议破裂",
                description="某方违反停火协议，冲突升级",
                affected_agents=["以色列", "哈梅内伊", "真主党", "伊朗革命卫队"],
                tension_impact=15.0,
                round_duration=2,
                probability=0.20,
                phase=phase
            ))
        
        # 外交会议
        candidates.append(GeopoliticalEvent(
            event_type=EventType.DIPLOMATIC_MEETING,
            name="多方外交磋商",
            description="欧盟、中国主持多方外交会议",
            affected_agents=["伊朗外交部长", "欧盟", "中国", "特朗普"],
            tension_impact=-5.0,
            round_duration=2,
            probability=0.18,
            phase=phase
        ))
        
        # 油价冲击
        if random.random() < 0.15:
            candidates.append(GeopoliticalEvent(
                event_type=EventType.OIL_PRICE_SHOCK,
                name="霍尔木兹紧张局势",
                description="霍尔木兹海峡局势紧张，油价波动",
                affected_agents=["伊朗革命卫队", "特朗普", "欧盟", "中国"],
                tension_impact=12.0,
                round_duration=1,
                probability=0.12,
                phase=phase
            ))
        
        # 制裁解除
        if phase == "late" and global_tension < 40:
            candidates.append(GeopoliticalEvent(
                event_type=EventType.SANCTIONS_LIFTED,
                name="部分制裁解除",
                description="作为和平协议的一部分，部分制裁被解除",
                affected_agents=["伊朗总统", "伊朗外交部长", "特朗普", "欧盟"],
                tension_impact=-10.0,
                round_duration=3,
                probability=0.10,
                phase=phase
            ))
        
        return candidates
    
    def get_active_events(self, round_num: int) -> List[GeopoliticalEvent]:
        """获取当前活跃事件"""
        return [e for e in self.active_events if e.round_duration > 0]
    
    def tick_active_events(self):
        """活跃事件轮次递减"""
        for event in self.active_events:
            event.round_duration -= 1
        self.active_events = [e for e in self.active_events if e.round_duration > 0]
    
    def get_event_summary(self) -> str:
        """获取事件摘要文本"""
        if not self.active_events:
            return "当前无活跃事件"
        
        summary = "当前活跃事件:\n"
        for event in self.active_events:
            summary += f"- {event.name}: {event.description}\n"
        return summary
