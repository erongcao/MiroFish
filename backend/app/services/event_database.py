"""
Geopolitical Event Database - 地缘政治事件数据库
记录和查询真实世界地缘政治事件
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class GeopoliticalEvent:
    """地缘政治事件"""
    event_id: str
    date: str                    # YYYY-MM-DD
    event_type: str              # 事件类型
    actors: List[str]            # 参与方
    description: str             # 描述
    impact_score: float = 0.0    # 影响分数 (-1到1)
    region: str = ""             # 地区
    
    # 具体影响
    trust_impact: Dict[str, float] = field(default_factory=dict)  # 对信任的影响
    economic_impact: Dict[str, float] = field(default_factory=dict)  # 经济影响
    military_impact: Dict[str, float] = field(default_factory=dict)  # 军事影响

# 2020-2024 重大地缘政治事件数据库
EVENT_DATABASE = [
    # 2020
    GeopoliticalEvent(
        event_id="covid19_start",
        date="2020-01-01",
        event_type="pandemic",
        actors=["china", "usa", "eu"],
        description="COVID-19疫情全球爆发",
        impact_score=-0.3,
        region="global",
        trust_impact={"usa-china": -0.2, "china-eu": -0.1},
        economic_impact={"global": -0.05},
    ),
    GeopoliticalEvent(
        event_id="us_china_trade_war",
        date="2020-01-15",
        event_type="trade",
        actors=["usa", "china"],
        description="中美签署第一阶段贸易协议",
        impact_score=0.2,
        region="asia_pacific",
        trust_impact={"usa-china": 0.1},
    ),
    # 2021
    GeopoliticalEvent(
        event_id="us_taliban_deal",
        date="2021-08-15",
        event_type="military",
        actors=["usa", "afghanistan"],
        description="美军撤离阿富汗，塔利班掌权",
        impact_score=-0.4,
        region="middle_east",
        trust_impact={"usa-eu": -0.1},
        military_impact={"usa": -0.05},
    ),
    GeopoliticalEvent(
        event_id="aukus",
        date="2021-09-15",
        event_type="alliance",
        actors=["usa", "uk", "australia"],
        description="AUKUS同盟成立，向澳洲提供核潜艇",
        impact_score=-0.3,
        region="asia_pacific",
        trust_impact={"usa-china": -0.3, "china-australia": -0.4, "france-australia": -0.5},
    ),
    # 2022
    GeopoliticalEvent(
        event_id="russia_ukraine_war",
        date="2022-02-24",
        event_type="war",
        actors=["russia", "ukraine"],
        description="俄罗斯入侵乌克兰",
        impact_score=-0.9,
        region="europe",
        trust_impact={"russia-eu": -0.8, "russia-usa": -0.7, "russia-nato": -0.9},
        economic_impact={"russia": -0.15, "eu": -0.05, "global": -0.03},
        military_impact={"russia": 0.1, "nato": 0.05},
    ),
    GeopoliticalEvent(
        event_id="china_taiwan_tension",
        date="2022-08-02",
        event_type="crisis",
        actors=["china", "usa", "taiwan"],
        description="佩洛西访台，台海危机升级",
        impact_score=-0.5,
        region="asia_pacific",
        trust_impact={"usa-china": -0.4, "china-taiwan": -0.6},
        military_impact={"china": 0.05, "usa": 0.03},
    ),
    # 2023
    GeopoliticalEvent(
        event_id="china_brokered_saudi_iran",
        date="2023-03-10",
        event_type="diplomacy",
        actors=["china", "saudi_arabia", "iran"],
        description="中国斡旋沙特伊朗复交",
        impact_score=0.4,
        region="middle_east",
        trust_impact={"china-saudi_arabia": 0.3, "china-iran": 0.2, "saudi_arabia-iran": 0.5},
    ),
    GeopoliticalEvent(
        event_id="nato_expansion",
        date="2023-04-04",
        event_type="alliance",
        actors=["nato", "finland"],
        description="芬兰加入北约",
        impact_score=-0.3,
        region="europe",
        trust_impact={"russia-nato": -0.5, "russia-finland": -0.6},
        military_impact={"nato": 0.05},
    ),
    GeopoliticalEvent(
        event_id="israel_hamas_war",
        date="2023-10-07",
        event_type="war",
        actors=["israel", "hamas"],
        description="哈马斯袭击以色列，加沙战争爆发",
        impact_score=-0.7,
        region="middle_east",
        trust_impact={"israel-iran": -0.5, "usa-israel": 0.2},
        economic_impact={"middle_east": -0.05},
    ),
    # 2024
    GeopoliticalEvent(
        event_id="china_philippines_tension",
        date="2024-03-01",
        event_type="crisis",
        actors=["china", "philippines"],
        description="中菲南海冲突升级",
        impact_score=-0.4,
        region="asia_pacific",
        trust_impact={"china-philippines": -0.5, "usa-philippines": 0.3},
        military_impact={"china": 0.03, "usa": 0.02},
    ),
    GeopoliticalEvent(
        event_id="iran_israel_escalation",
        date="2024-04-13",
        event_type="military",
        actors=["iran", "israel"],
        description="伊朗首次直接攻击以色列",
        impact_score=-0.6,
        region="middle_east",
        trust_impact={"iran-israel": -0.8, "usa-israel": 0.1},
        military_impact={"iran": 0.05, "israel": 0.05},
    ),
]


class EventDatabase:
    """地缘政治事件数据库"""
    
    def __init__(self):
        self.events = EVENT_DATABASE
        self.event_index = {e.event_id: e for e in self.events}
    
    def get_events_by_date_range(self, start_date: str, end_date: str) -> List[GeopoliticalEvent]:
        """获取日期范围内的事件"""
        return [e for e in self.events if start_date <= e.date <= end_date]
    
    def get_events_by_actors(self, actors: List[str]) -> List[GeopoliticalEvent]:
        """获取涉及特定参与方的事件"""
        return [e for e in self.events if any(a in e.actors for a in actors)]
    
    def get_events_by_type(self, event_type: str) -> List[GeopoliticalEvent]:
        """获取特定类型的事件"""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_by_region(self, region: str) -> List[GeopoliticalEvent]:
        """获取特定地区的事件"""
        return [e for e in self.events if e.region == region]
    
    def calculate_cumulative_impact(self, 
                                   actors: List[str],
                                   start_date: str = "2020-01-01",
                                   end_date: str = "2024-12-31") -> Dict[str, float]:
        """计算特定参与方在时间段内的累积影响"""
        events = self.get_events_by_date_range(start_date, end_date)
        
        impact = {
            "trust": 0.0,
            "economic": 0.0,
            "military": 0.0,
            "overall": 0.0,
        }
        
        for event in events:
            if any(a in event.actors for a in actors):
                impact["overall"] += event.impact_score
                
                # 累加具体影响
                for actor in actors:
                    if actor in event.trust_impact:
                        impact["trust"] += event.trust_impact[actor]
                    if actor in event.economic_impact:
                        impact["economic"] += event.economic_impact[actor]
                    if actor in event.military_impact:
                        impact["military"] += event.military_impact[actor]
        
        return impact
    
    def get_recent_major_events(self, n: int = 5) -> List[GeopoliticalEvent]:
        """获取最近的n个重大事件"""
        sorted_events = sorted(self.events, key=lambda e: e.date, reverse=True)
        return sorted_events[:n]
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "total_events": len(self.events),
            "events": [
                {
                    "event_id": e.event_id,
                    "date": e.date,
                    "type": e.event_type,
                    "actors": e.actors,
                    "description": e.description,
                    "impact": e.impact_score,
                    "region": e.region,
                }
                for e in self.events
            ]
        }


# 全局实例
event_db = EventDatabase()

if __name__ == "__main__":
    # 测试
    db = EventDatabase()
    
    print("=== 地缘政治事件数据库测试 ===\n")
    
    print("2022年重大事件:")
    events_2022 = db.get_events_by_date_range("2022-01-01", "2022-12-31")
    for e in events_2022:
        print(f"  {e.date}: {e.description} (影响: {e.impact_score})")
    
    print("\n涉及俄罗斯的事件:")
    russia_events = db.get_events_by_actors(["russia"])
    for e in russia_events:
        print(f"  {e.date}: {e.description}")
    
    print("\n战争类事件:")
    war_events = db.get_events_by_type("war")
    for e in war_events:
        print(f"  {e.date}: {e.description}")
    
    print("\n最近5个重大事件:")
    recent = db.get_recent_major_events(5)
    for e in recent:
        print(f"  {e.date}: {e.description}")
    
    print("\n俄罗斯2020-2024累积影响:")
    impact = db.calculate_cumulative_impact(["russia"])
    print(f"  总体: {impact['overall']:.2f}")
    print(f"  信任: {impact['trust']:.2f}")
    print(f"  经济: {impact['economic']:.2f}")
    print(f"  军事: {impact['military']:.2f}")

# ===== 2025-2026 重大地缘政治事件 =====
GeopoliticalEvent(
    event_id="us_china_tariff_2025",
    date="2025-02-01",
    event_type="trade",
    actors=["usa", "china"],
    description="美国对华加征关税至60%，中国反制",
    impact_score=-0.4,
    region="asia_pacific",
    trust_impact={"usa-china": -0.3},
    economic_impact={"china": -0.08, "usa": -0.03},
),
GeopoliticalEvent(
    event_id="ukraine_talks_2025",
    date="2025-03-15",
    event_type="diplomacy",
    actors=["russia", "ukraine", "eu", "usa"],
    description="乌克兰危机和谈重启，但进展有限",
    impact_score=0.1,
    region="europe",
    trust_impact={"russia-ukraine": 0.1},
    economic_impact={"global": 0.02},
),
GeopoliticalEvent(
    event_id="iran_nuclear_2025",
    date="2025-06-01",
    event_type="nuclear",
    actors=["iran", "usa", "israel", "eu"],
    description="伊朗核计划接近武器化，美以军事选项讨论升温",
    impact_score=-0.5,
    region="middle_east",
    trust_impact={"iran-usa": -0.4, "iran-israel": -0.5},
    economic_impact={"oil": 0.15},
),
GeopoliticalEvent(
    event_id="red_sea_crisis_2025",
    date="2025-09-01",
    event_type="military",
    actors=["yemen_houthi", "usa", "israel", "saudi"],
    description="胡塞武装封锁红海，全球航运绕行好望角",
    impact_score=-0.3,
    region="middle_east",
    trust_impact={"yemen-usa": -0.3, "yemen-saudi": -0.3},
    economic_impact={"shipping": -0.1, "oil": 0.08},
),
GeopoliticalEvent(
    event_id="taiwan_straits_2026",
    date="2026-01-15",
    event_type="military",
    actors=["china", "usa", "taiwan"],
    description="解放军台海联合巡航常态化，美航母战斗群部署",
    impact_score=-0.6,
    region="asia_pacific",
    trust_impact={"usa-china": -0.4},
    economic_impact={"taiwan": -0.15, "china": -0.05},
),
GeopoliticalEvent(
    event_id="persian_gulf_war_2026",
    date="2026-04-01",
    event_type="war",
    actors=["iran", "usa", "israel", "saudi"],
    description="伊朗封锁霍尔木兹海峡，美以考虑军事打击",
    impact_score=-0.8,
    region="middle_east",
    trust_impact={"iran-usa": -0.6, "iran-saudi": -0.5, "iran-israel": -0.6},
    economic_impact={"oil": -0.3, "iran": -0.4},
),
GeopoliticalEvent(
    event_id="eu_china_summit_2026",
    date="2026-04-20",
    event_type="diplomacy",
    actors=["eu", "china"],
    description="中欧峰会：投资协定谈判重启，电动汽车关税争端缓和",
    impact_score=0.2,
    region="europe_asia",
    trust_impact={"eu-china": 0.2},
    economic_impact={"eu": 0.03, "china": 0.03},
),
GeopoliticalEvent(
    event_id="g7_summit_2026",
    date="2026-05-01",
    event_type="diplomacy",
    actors=["g7", "china", "russia"],
    description="G7峰会：协调对华科技封锁，乌克兰重建方案",
    impact_score=0.1,
    region="global",
    trust_impact={"g7-china": -0.1},
    economic_impact={"global": 0.01},
),
