"""
Three-Layer Geopolitical Simulator with Game Theory + Public Opinion Feedback
三层地缘政治模拟器（博弈论 + 舆论反馈机制）

核心改进:
1. 国际压力机制 → 联合国决议/经济制裁/外交孤立
2. 国内政治斗争 → 强硬派vs温和派/政权更替/策略突变
"""

import json
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

class DiplomaticState(Enum):
    """外交状态"""
    COOPERATION = "cooperation"      # 合作
    NEGOTIATION = "negotiation"     # 谈判中
    PRESSURE = "pressure"           # 施压
    HOSTILE = "hostile"             # 敌对
    BROKEN = "broken"               # 断交

class MilitaryPosture(Enum):
    """军事姿态"""
    PEACEFUL = "peaceful"          # 和平
    DEFENSIVE = "defensive"         # 防御
    SHOW_OF_FORCE = "show_of_force" # 武力展示
    MOBILIZATION = "mobilization"   # 动员
    DEPLOYMENT = "deployment"       # 部署
    ENGAGED = "engaged"             # 交战

class WarIntensity(Enum):
    """战争强度"""
    NONE = "none"                   # 无冲突
    SKIRMISH = "skirmish"          # 小规模冲突
    LOCAL_WAR = "local_war"        # 局部战争
    FULL_SCALE = "full_scale"      # 全面战争

class Strategy(Enum):
    """博弈策略"""
    COOPERATE = "cooperate"         # 合作
    DEFECT = "defect"              # 背叛/对抗
    DETER = "deter"                # 威慑
    CONCEDE = "concede"            # 让步
    ESCALATE = "escalate"          # 升级

class UNResolutionType(Enum):
    """联合国决议类型"""
    CEASEFIRE = "ceasefire"         # 停火决议
    SANCTION = "sanction"           # 制裁决议
    PEACEKEEPING = "peacekeeping"   # 维和决议
    CONDEMN = "condemn"             # 谴责决议
    HUMANITARIAN = "humanitarian"   # 人道主义决议

class FactionType(Enum):
    """国内政治派系"""
    HARDLINERS = "hardliners"       # 强硬派（民族主义/军事派）
    MODERATES = "moderates"         # 温和派（务实主义/改革派）
    BUSINESS = "business"           # 商业/经济派

@dataclass
class PoliticalFaction:
    """政治派系"""
    faction_type: FactionType
    strength: float                 # 势力（0-1）
    influence: float                # 影响力（0-1）
    public_support: float           # 公众支持率（0-1）

@dataclass
class UNResolution:
    """联合国决议"""
    resolution_id: str
    type: UNResolutionType
    target_countries: List[str]     # 针对哪些国家
    support_rate: float             # 支持率（0-1）
    passed: bool                    # 是否通过
    description: str

@dataclass
class CountryState:
    """国家状态（增强版，包含国内政治和国际压力）"""
    id: str
    name: str
    
    # 外交层
    diplomatic_state: DiplomaticState = DiplomaticState.NEGOTIATION
    relations: Dict[str, float] = field(default_factory=dict)
    trust_history: Dict[str, List[float]] = field(default_factory=dict)
    
    # 军事层
    military_posture: MilitaryPosture = MilitaryPosture.PEACEFUL
    military_readiness: float = 0.0
    
    # 战争层
    war_intensity: WarIntensity = WarIntensity.NONE
    casualties: int = 0
    territory_held: float = 1.0
    
    # 资源
    economic_strength: float = 0.5
    military_strength: float = 0.5
    public_support: float = 0.7
    
    # ============ 新增：舆论反馈 ============
    # 国内政治斗争
    factions: Dict[FactionType, PoliticalFaction] = field(default_factory=dict)
    dominant_faction: FactionType = FactionType.MODERATES
    government_stability: float = 0.8  # 政府稳定性
    
    # 国际压力
    international_pressure: float = 0.0  # 国际压力（0-100）
    diplomatic_isolation: float = 0.0    # 外交孤立程度（0-1）
    un_sanctions: int = 0                # UN制裁轮数
    
    # 博弈论
    current_strategy: Strategy = Strategy.COOPERATE
    strategy_history: List[Dict] = field(default_factory=list)
    
    # 历史
    actions_log: List[Dict] = field(default_factory=list)

class DiplomaticEvent:
    """外交事件"""
    def __init__(self, name: str, actor: str, target: str, 
                 event_type: str, description: str, pressure: float,
                 actor_strategy: str = "", target_strategy: str = ""):
        self.name = name
        self.actor = actor
        self.target = target
        self.type = event_type
        self.description = description
        self.pressure = pressure
        self.actor_strategy = actor_strategy
        self.target_strategy = target_strategy

class MilitaryEvent:
    """军事事件"""
    def __init__(self, name: str, actors: List[str],
                 event_type: str, description: str,
                 tension_increase: float):
        self.name = name
        self.actors = actors
        self.type = event_type
        self.description = description
        self.tension_increase = tension_increase

class WarEvent:
    """战争事件"""
    def __init__(self, name: str, parties: List[str],
                 intensity: WarIntensity, territory_change: Dict[str, float],
                 casualties: Dict[str, int], description: str,
                 cause: str = ""):
        self.name = name
        self.parties = parties
        self.intensity = intensity
        self.territory_change = territory_change
        self.casualties = casualties
        self.description = description
        self.cause = cause

class InternationalPressureSystem:
    """
    国际压力系统
    将舆论/社交媒体转化为国际政治行动
    """
    
    def __init__(self):
        self.un_resolutions: List[UNResolution] = []
        self.global_pressure_map: Dict[str, float] = {}  # country_id -> pressure
    
    def analyze_media_content(self, content: str) -> Dict[str, float]:
        """
        分析社交媒体内容
        
        Returns:
            {
                'hardline_signal': float,  # 强硬信号强度
                'peace_signal': float,      # 和平信号强度
                'pressure_change': float    # 压力变化
            }
        """
        content_lower = content.lower()
        
        # 关键词映射
        hardline_keywords = ['制裁', '攻击', '威胁', '战争', '敌对', '强硬', '绝不退让']
        peace_keywords = ['对话', '谈判', '合作', '和平', '妥协', '理解', '和解']
        escalation_keywords = ['升级', '扩大', '全面', '核', '毁灭']
        
        hardline_count = sum(1 for k in hardline_keywords if k in content_lower)
        peace_count = sum(1 for k in peace_keywords if k in content_lower)
        escalation_count = sum(1 for k in escalation_keywords if k in content_lower)
        
        return {
            'hardline_signal': min(1.0, hardline_count * 0.2 + escalation_count * 0.3),
            'peace_signal': min(1.0, peace_count * 0.2),
            'pressure_change': (hardline_count * 5) - (peace_count * 3) + (escalation_count * 10)
        }
    
    def update_country_pressure(self, country_id: str, media_posts: List[str]):
        """更新国家国际压力"""
        total_pressure_change = 0
        
        for post in media_posts:
            analysis = self.analyze_media_content(post)
            total_pressure_change += analysis['pressure_change']
        
        if country_id not in self.global_pressure_map:
            self.global_pressure_map[country_id] = 0
        
        self.global_pressure_map[country_id] += total_pressure_change
        self.global_pressure_map[country_id] = max(0, min(100, self.global_pressure_map[country_id]))
    
    def generate_un_resolution(self, target_countries: List[str], 
                               global_tension: float) -> Optional[UNResolution]:
        """生成联合国决议"""
        # 只有高紧张度才会触发UN决议
        if global_tension < 60:
            return None
        
        # 计算针对这些国家的国际压力
        total_pressure = sum(self.global_pressure_map.get(c, 0) for c in target_countries)
        avg_pressure = total_pressure / len(target_countries) if target_countries else 0
        
        # 压力不够高则不生成决议
        if avg_pressure < 30:
            return None
        
        # 根据压力类型选择决议
        if avg_pressure > 70 and global_tension > 80:
            resolution_type = UNResolutionType.SANCTION
            description = f"对{', '.join(target_countries)}实施国际制裁"
        elif global_tension > 75:
            resolution_type = UNResolutionType.CEASEFIRE
            description = f"要求{', '.join(target_countries)}立即停火"
        elif avg_pressure > 50:
            resolution_type = UNResolutionType.CONDEMN
            description = f"谴责{', '.join(target_countries)}的敌对行动"
        else:
            resolution_type = UNResolutionType.HUMANITARIAN
            description = f"呼吁{', '.join(target_countries)}关注人道主义危机"
        
        # 计算支持率（基于国际压力）
        support_rate = min(0.95, avg_pressure / 100 + 0.2)
        
        resolution = UNResolution(
            resolution_id=f"UN{datetime.now().strftime('%Y%m%d')}_{len(self.un_resolutions)}",
            type=resolution_type,
            target_countries=target_countries,
            support_rate=support_rate,
            passed=support_rate > 0.6,  # 超过60%支持则通过
            description=description
        )
        
        self.un_resolutions.append(resolution)
        return resolution

class DomesticPoliticsSystem:
    """
    国内政治斗争系统
    模拟派系斗争对策略的影响
    """
    
    def __init__(self):
        self.faction_conflicts: List[Dict] = []
    
    def initialize_factions(self, country: CountryState):
        """初始化国家派系"""
        country.factions = {
            FactionType.HARDLINERS: PoliticalFaction(
                faction_type=FactionType.HARDLINERS,
                strength=0.3,
                influence=0.4,
                public_support=0.35
            ),
            FactionType.MODERATES: PoliticalFaction(
                faction_type=FactionType.MODERATES,
                strength=0.5,
                influence=0.5,
                public_support=0.45
            ),
            FactionType.BUSINESS: PoliticalFaction(
                faction_type=FactionType.BUSINESS,
                strength=0.2,
                influence=0.3,
                public_support=0.20
            )
        }
        country.dominant_faction = FactionType.MODERATES
    
    def update_factions(self, country: CountryState, war_intensity: WarIntensity,
                       casualties: int, economic_strength: float,
                       international_pressure: float):
        """更新派系力量对比"""
        
        hardliners = country.factions[FactionType.HARDLINERS]
        moderates = country.factions[FactionType.MODERATES]
        business = country.factions[FactionType.BUSINESS]
        
        # 战争期间：强硬派获得支持（民族主义）
        if war_intensity != WarIntensity.NONE:
            hardliners.public_support += 0.05
            hardliners.strength += 0.03
            
            # 但如果伤亡太高，温和派和商业派会崛起
            if casualties > 50:
                moderates.public_support += 0.03
                business.public_support += 0.02
                hardliners.public_support -= 0.02
        
        # 经济制裁：商业派受损，强硬派和温和派此消彼长
        if economic_strength < 0.4:
            business.public_support -= 0.05
            business.strength -= 0.03
            
            # 经济差 → 部分人转向强硬（认为是外部压力）
            # 部分人转向温和（希望解除制裁）
            if random.random() > 0.5:
                hardliners.public_support += 0.03
            else:
                moderates.public_support += 0.03
        
        # 国际压力大 → 温和派和商业派崛起（希望缓和）
        if international_pressure > 60:
            moderates.public_support += 0.04
            business.public_support += 0.03
            hardliners.public_support -= 0.03
        
        # 政府稳定性
        total_support = sum(f.public_support for f in country.factions.values())
        country.government_stability = min(1.0, total_support / 3 + 0.3)
        
        # 确定主导派系
        dominant = max(country.factions.items(), key=lambda x: x[1].public_support)
        country.dominant_faction = dominant[0]
        
        # 记录冲突
        if abs(hardliners.public_support - moderates.public_support) < 0.1:
            self.faction_conflicts.append({
                'country': country.id,
                'round': len(self.faction_conflicts),
                'type': 'power_struggle',
                'description': f'{country.name}国内出现权力斗争'
            })
    
    def get_faction_influence_on_strategy(self, country: CountryState) -> Dict[str, float]:
        """获取派系对策略的影响权重"""
        influence = {
            'cooperate': 0,
            'defect': 0,
            'escalate': 0,
            'deter': 0,
            'concede': 0
        }
        
        for faction_type, faction in country.factions.items():
            weight = faction.public_support * faction.influence
            
            if faction_type == FactionType.HARDLINERS:
                influence['defect'] += weight * 0.4
                influence['escalate'] += weight * 0.3
                influence['deter'] += weight * 0.2
                influence['cooperate'] -= weight * 0.3
            
            elif faction_type == FactionType.MODERATES:
                influence['cooperate'] += weight * 0.5
                influence['concede'] += weight * 0.3
                influence['defect'] -= weight * 0.2
                influence['escalate'] -= weight * 0.2
            
            elif faction_type == FactionType.BUSINESS:
                influence['cooperate'] += weight * 0.6
                influence['concede'] += weight * 0.2
                influence['escalate'] -= weight * 0.4
                influence['defect'] -= weight * 0.1
        
        return influence

class GameTheoryEngine:
    """博弈论引擎（增强版，包含舆论反馈）"""
    
    PAYOFF_MATRIX = {
        (Strategy.COOPERATE, Strategy.COOPERATE): (3, 3),
        (Strategy.COOPERATE, Strategy.DEFECT): (0, 5),
        (Strategy.DEFECT, Strategy.COOPERATE): (5, 0),
        (Strategy.DEFECT, Strategy.DEFECT): (1, 1),
        (Strategy.DETER, Strategy.COOPERATE): (2, 1),
        (Strategy.DETER, Strategy.DEFECT): (1, 0),
        (Strategy.CONCEDE, Strategy.DEFECT): (1, 4),
        (Strategy.ESCALATE, Strategy.COOPERATE): (4, -1),
    }
    
    @classmethod
    def calculate_payoff(cls, actor_strategy: Strategy, target_strategy: Strategy) -> Tuple[float, float]:
        key = (actor_strategy, target_strategy)
        if key in cls.PAYOFF_MATRIX:
            return cls.PAYOFF_MATRIX[key]
        return (2, 2)
    
    @classmethod
    def choose_best_strategy(cls, country: CountryState, target_id: str, 
                            global_tension: float,
                            international_pressure: float = 0,
                            domestic_politics: Optional[DomesticPoliticsSystem] = None) -> Strategy:
        """
        选择最优策略（包含舆论反馈）
        """
        relation = country.relations.get(target_id, 0)
        military_ratio = country.military_strength / (country.military_strength + 0.1)
        
        strategies = [Strategy.COOPERATE, Strategy.DEFECT, Strategy.DETER, Strategy.ESCALATE]
        weights = []
        
        for s in strategies:
            weight = cls._strategy_weight(s, relation, military_ratio, 
                                         country.public_support, global_tension)
            
            # ============ 新增：舆论反馈影响 ============
            # 国际压力大 → 更倾向合作/让步
            if international_pressure > 50:
                if s == Strategy.COOPERATE:
                    weight += international_pressure * 0.01
                elif s == Strategy.ESCALATE:
                    weight -= international_pressure * 0.015
            
            # 国内派系影响
            if domestic_politics and country.factions:
                faction_influence = domestic_politics.get_faction_influence_on_strategy(country)
                influence_key = s.value.lower()
                if influence_key in faction_influence:
                    weight += faction_influence[influence_key] * 0.5
            
            weights.append(weight)
        
        total = sum(weights)
        if total == 0:
            return Strategy.COOPERATE
        
        r = random.uniform(0, total)
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return strategies[i]
        
        return strategies[-1]
    
    @classmethod
    def _strategy_weight(cls, strategy: Strategy, relation: float, 
                        military_ratio: float, support: float, tension: float) -> float:
        if strategy == Strategy.COOPERATE:
            return max(0, relation * 2 + (1 - tension/100) * 1.5 + support * 1)
        elif strategy == Strategy.DEFECT:
            return max(0, -relation * 2 + military_ratio * 1.5 + (1 - support) * 0.5)
        elif strategy == Strategy.DETER:
            return max(0, military_ratio * 2 + tension/100 * 1.5 - relation * 1)
        elif strategy == Strategy.ESCALATE:
            return max(0, -relation * 3 + tension/100 * 2 + (1 - support) * 1)
        return 0

class ThreeLayerSimulator:
    """
    三层地缘政治模拟器（完整版，含舆论反馈）
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.countries: Dict[str, CountryState] = {}
        self.round = 0
        
        # 子系统
        self.game_engine = GameTheoryEngine()
        self.pressure_system = InternationalPressureSystem()
        self.domestic_system = DomesticPoliticsSystem()
        
        # 事件历史
        self.diplomatic_events: List[DiplomaticEvent] = []
        self.military_events: List[MilitaryEvent] = []
        self.war_events: List[WarEvent] = []
        self.un_resolutions: List[UNResolution] = []
        
        # 全局紧张度
        self.global_tension = 30.0
        
        self._initialize_countries()
    
    def _initialize_countries(self):
        """初始化国家"""
        country_configs = [
            {"id": "iran", "name": "伊朗", "relations": {
                "usa": -0.8, "israel": -0.9, "saudi": -0.7,
                "russia": 0.5, "china": 0.3, "eu": -0.2
            }, "military_strength": 0.6, "economic_strength": 0.4},
            {"id": "usa", "name": "美国", "relations": {
                "iran": -0.8, "israel": 0.9, "russia": -0.6,
                "china": -0.5, "eu": 0.6
            }, "military_strength": 0.9, "economic_strength": 0.85},
            {"id": "israel", "name": "以色列", "relations": {
                "iran": -0.9, "hezbollah": -0.9, "hamas": -0.9,
                "usa": 0.9, "russia": 0.0, "china": 0.0
            }, "military_strength": 0.7, "economic_strength": 0.7},
            {"id": "russia", "name": "俄罗斯", "relations": {
                "iran": 0.5, "usa": -0.7, "israel": 0.0,
                "china": 0.6, "eu": -0.3
            }, "military_strength": 0.8, "economic_strength": 0.5},
            {"id": "china", "name": "中国", "relations": {
                "iran": 0.3, "usa": -0.5, "russia": 0.6,
                "israel": 0.0, "eu": 0.2
            }, "military_strength": 0.75, "economic_strength": 0.8},
            {"id": "eu", "name": "欧盟", "relations": {
                "iran": -0.2, "usa": 0.6, "russia": -0.3,
                "china": 0.2, "israel": 0.3
            }, "military_strength": 0.5, "economic_strength": 0.75},
        ]
        
        for c in country_configs:
            country = CountryState(
                id=c["id"],
                name=c["name"],
                relations=c.get("relations", {}),
                military_strength=c.get("military_strength", 0.5),
                economic_strength=c.get("economic_strength", 0.5)
            )
            # 初始化派系
            self.domestic_system.initialize_factions(country)
            self.countries[c["id"]] = country
        
        print(f"[ThreeLayer] 已初始化 {len(self.countries)} 个国家")
    
    def simulate_round(self, media_posts: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        模拟一轮（完整版，含舆论反馈）
        
        Args:
            media_posts: 可选的社交媒体帖子 {country_id: [posts]}
        """
        self.round += 1
        round_summary = {
            "round": self.round,
            "diplomatic_events": [],
            "military_events": [],
            "war_events": [],
            "un_resolutions": [],
            "faction_changes": [],
            "global_tension": self.global_tension
        }
        
        # 1. 分析社交媒体（舆论反馈）
        if media_posts:
            self._process_media_feedback(media_posts, round_summary)
        
        # 2. 更新国内政治
        self._update_domestic_politics(round_summary)
        
        # 3. 生成UN决议（基于国际压力）
        self._check_un_resolutions(round_summary)
        
        # 4. 策略更新（博弈论 + 舆论）
        self._update_strategies(round_summary)
        
        # 5. 外交层决策
        diplomatic_actions = self._diplomatic_layer_decision()
        round_summary["diplomatic_events"] = diplomatic_actions
        
        # 6. 军事层决策
        military_actions = self._military_layer_decision()
        round_summary["military_events"] = military_actions
        
        # 7. 战争层决策
        war_actions = self._war_layer_decision()
        round_summary["war_events"] = war_actions
        
        # 8. 舆论反馈
        self._update_public_opinion(round_summary)
        
        # 9. 检查降级条件
        self._check_de_escalation()
        
        return round_summary
    
    def _process_media_feedback(self, media_posts: Dict[str, List[str]], round_summary: Dict):
        """处理社交媒体舆论反馈"""
        for country_id, posts in media_posts.items():
            if country_id not in self.countries:
                continue
            
            # 更新国际压力
            self.pressure_system.update_country_pressure(country_id, posts)
            
            # 更新国家压力值
            country = self.countries[country_id]
            country.international_pressure = self.pressure_system.global_pressure_map.get(country_id, 0)
    
    def _update_domestic_politics(self, round_summary: Dict):
        """更新国内政治"""
        for country in self.countries.values():
            self.domestic_system.update_factions(
                country=country,
                war_intensity=country.war_intensity,
                casualties=country.casualties,
                economic_strength=country.economic_strength,
                international_pressure=country.international_pressure
            )
            
            # 记录派系变化
            round_summary["faction_changes"].append({
                "country": country.id,
                "dominant_faction": country.dominant_faction.value,
                "hardliner_support": country.factions[FactionType.HARDLINERS].public_support,
                "moderate_support": country.factions[FactionType.MODERATES].public_support,
                "business_support": country.factions[FactionType.BUSINESS].public_support,
                "stability": country.government_stability
            })
    
    def _check_un_resolutions(self, round_summary: Dict):
        """检查是否需要生成UN决议"""
        # 找出国际压力高的国家
        high_pressure_countries = [
            cid for cid, c in self.countries.items()
            if c.international_pressure > 40
        ]
        
        if high_pressure_countries and random.random() < self.global_tension / 200:
            resolution = self.pressure_system.generate_un_resolution(
                high_pressure_countries, self.global_tension
            )
            
            if resolution:
                self.un_resolutions.append(resolution)
                round_summary["un_resolutions"].append({
                    "type": resolution.type.value,
                    "target": resolution.target_countries,
                    "passed": resolution.passed,
                    "support_rate": resolution.support_rate,
                    "description": resolution.description
                })
                
                # UN决议影响
                for target_id in resolution.target_countries:
                    if target_id in self.countries:
                        country = self.countries[target_id]
                        
                        if resolution.type == UNResolutionType.SANCTION:
                            country.economic_strength *= 0.9
                            country.un_sanctions += 1
                            self.global_tension += 5
                        elif resolution.type == UNResolutionType.CEASEFIRE:
                            if country.war_intensity != WarIntensity.NONE:
                                self.global_tension -= 10
                        elif resolution.type == UNResolutionType.CONDEMN:
                            country.diplomatic_isolation += 0.1
                            country.public_support -= 0.05
    
    def _update_strategies(self, round_summary: Dict):
        """更新策略（含舆论反馈）"""
        for country_id, country in self.countries.items():
            for target_id in country.relations:
                if target_id not in self.countries:
                    continue
                
                best_strategy = self.game_engine.choose_best_strategy(
                    country, target_id, self.global_tension,
                    country.international_pressure,
                    self.domestic_system
                )
                
                predicted = self.game_engine.choose_best_strategy(
                    self.countries[target_id], country_id, self.global_tension,
                    self.countries[target_id].international_pressure,
                    self.domestic_system
                )
                
                payoff = self.game_engine.calculate_payoff(best_strategy, predicted)
                
                country.strategy_history.append({
                    "round": self.round,
                    "target": target_id,
                    "strategy": best_strategy.value,
                    "predicted_opponent": predicted.value,
                    "payoff": payoff[0]
                })
                
                country.current_strategy = best_strategy
        
        round_summary["strategies"] = {
            cid: c.current_strategy.value
            for cid, c in self.countries.items()
        }
    
    def _diplomatic_layer_decision(self) -> List[Dict]:
        """外交层决策"""
        actions = []
        
        strategy_actions = {
            Strategy.COOPERATE: [("MEETING", "提议举行会议", 0.05), ("TRADE", "签署贸易协议", 0.1)],
            Strategy.DEFECT: [("SANCTION", "实施新制裁", -0.1), ("ULTIMATUM", "发出最后通牒", -0.15)],
            Strategy.DETER: [("STATEMENT", "发表强硬声明", -0.05), ("CONDITIONS", "设定谈判条件", -0.02)],
            Strategy.ESCALATE: [("WITHDRAW", "撤回大使", -0.1), ("BREAK", "宣布断交", -0.2)],
            Strategy.CONCEDE: [("ACCEPT", "接受条件", 0.15), ("CONCEDE", "做出让步", 0.1)],
        }
        
        if self.global_tension / 100 > 0.3 and random.random() < self.global_tension / 100:
            valid_pairs = []
            for aid in self.countries:
                for tid in self.countries:
                    if aid != tid and tid in self.countries[aid].relations:
                        valid_pairs.append((aid, tid))
            
            if valid_pairs:
                actor_id, target_id = random.choice(valid_pairs)
            else:
                return actions
            
            country = self.countries[actor_id]
            current_strategy = country.current_strategy
            
            available_actions = strategy_actions.get(current_strategy, [])
            if not available_actions:
                available_actions = strategy_actions[Strategy.COOPERATE]
            
            action_type, desc, pressure = random.choice(available_actions)
            
            predicted = self.game_engine.choose_best_strategy(
                self.countries.get(target_id, country), actor_id, self.global_tension,
                self.countries.get(target_id, CountryState("", "")).international_pressure,
                self.domestic_system
            )
            
            event = DiplomaticEvent(
                name=f"{country.name} {desc}",
                actor=actor_id,
                target=target_id,
                event_type=action_type,
                description=desc,
                pressure=pressure,
                actor_strategy=current_strategy.value,
                target_strategy=predicted.value
            )
            
            self.diplomatic_events.append(event)
            
            if target_id in country.relations:
                country.relations[target_id] += pressure
                country.relations[target_id] = max(-1, min(1, country.relations[target_id]))
                
                if target_id not in country.trust_history:
                    country.trust_history[target_id] = []
                country.trust_history[target_id].append(pressure)
            
            actions.append({
                "type": action_type,
                "actor": actor_id,
                "target": target_id,
                "description": desc,
                "strategy": current_strategy.value,
                "predicted_opponent": predicted.value
            })
            
            if pressure < 0:
                self.global_tension += abs(pressure) * 20
            else:
                self.global_tension -= abs(pressure) * 10
        
        return actions
    
    def _military_layer_decision(self) -> List[Dict]:
        """军事层决策"""
        actions = []
        
        if self.global_tension > 50 and random.random() < (self.global_tension - 50) / 100:
            actors = random.sample(list(self.countries.keys()), 2)
            
            military_possibilities = [
                ("EXERCISE", "举行军事演习", 10),
                ("MOBILIZATION", "部队调动", 15),
                ("DEPLOYMENT", "增派部队", 20),
                ("BLOCKADE", "实施封锁", 25),
            ]
            
            action_type, desc, tension_inc = random.choice(military_possibilities)
            
            event = MilitaryEvent(
                name=f"军事行动: {desc}",
                actors=actors,
                event_type=action_type,
                description=desc,
                tension_increase=tension_inc
            )
            
            self.military_events.append(event)
            self.global_tension += tension_inc
            
            actions.append({
                "type": action_type,
                "actors": actors,
                "description": desc,
                "tension_increase": tension_inc
            })
        
        return actions
    
    def _war_layer_decision(self) -> List[Dict]:
        """战争层决策"""
        actions = []
        
        if self.global_tension > 80 and random.random() < (self.global_tension - 80) / 50:
            parties = random.sample(list(self.countries.keys()), 2)
            
            intensity_levels = [WarIntensity.SKIRMISH, WarIntensity.LOCAL_WAR]
            intensity = random.choice(intensity_levels) if self.global_tension > 90 else WarIntensity.SKIRMISH
            
            war_cause = "紧张局势升级"
            if self.diplomatic_events:
                last_event = self.diplomatic_events[-1]
                war_cause = f"{last_event.description}失败后军事对抗"
            
            war_event = WarEvent(
                name=f"冲突爆发: {intensity.value}",
                parties=parties,
                intensity=intensity,
                territory_change={parties[0]: random.uniform(-0.05, 0.05)},
                casualties={p: random.randint(10, 100) for p in parties},
                description=f"{self.countries[parties[0]].name}与{self.countries[parties[1]].name}发生{intensity.value}冲突",
                cause=war_cause
            )
            
            self.war_events.append(war_event)
            
            for party in parties:
                self.countries[party].war_intensity = intensity
                self.countries[party].casualties += war_event.casualties.get(party, 0)
                self.countries[party].territory_held += war_event.territory_change.get(party, 0)
                self.countries[party].public_support -= 0.05
                self.countries[party].military_posture = MilitaryPosture.ENGAGED
            
            self.global_tension = min(100, self.global_tension + 15)
            
            actions.append({
                "type": "WAR_OUTBREAK",
                "parties": parties,
                "intensity": intensity.value,
                "description": war_event.description,
                "cause": war_cause
            })
        
        return actions
    
    def _update_public_opinion(self, round_summary: Dict):
        """更新舆论"""
        if round_summary["war_events"]:
            for event in round_summary["war_events"]:
                self.global_tension += 5
        
        for event in round_summary["diplomatic_events"]:
            if event["type"] in ["MEETING", "TRADE", "ACCEPT"]:
                self.global_tension -= 3
            elif event["type"] in ["SANCTION", "ULTIMATUM", "BREAK"]:
                self.global_tension += 5
    
    def _check_de_escalation(self):
        """检查降级条件"""
        for country in self.countries.values():
            if country.war_intensity != WarIntensity.NONE:
                country.public_support -= 0.03
                country.military_strength *= 0.98
                
                if country.public_support < 0.3:
                    self.global_tension -= 5
                    
                    if country.war_intensity == WarIntensity.SKIRMISH:
                        country.war_intensity = WarIntensity.NONE
                        country.military_posture = MilitaryPosture.DEFENSIVE
    
    def get_state_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "round": self.round,
            "global_tension": self.global_tension,
            "countries": {
                cid: {
                    "name": c.name,
                    "diplomatic_state": c.diplomatic_state.value,
                    "military_posture": c.military_posture.value,
                    "war_intensity": c.war_intensity.value,
                    "casualties": c.casualties,
                    "public_support": c.public_support,
                    "current_strategy": c.current_strategy.value,
                    "military_strength": c.military_strength,
                    # 新增
                    "international_pressure": c.international_pressure,
                    "dominant_faction": c.dominant_faction.value,
                    "government_stability": c.government_stability,
                    "un_sanctions": c.un_sanctions
                }
                for cid, c in self.countries.items()
            },
            "event_counts": {
                "diplomatic": len(self.diplomatic_events),
                "military": len(self.military_events),
                "war": len(self.war_events),
                "un_resolutions": len(self.un_resolutions)
            }
        }
    
    def run_simulation(self, num_rounds: int, media_posts: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, Any]]:
        """运行完整模拟"""
        results = []
        
        print(f"[ThreeLayer] 开始模拟 {num_rounds} 轮")
        
        for i in range(num_rounds):
            round_posts = media_posts if media_posts else {}
            round_result = self.simulate_round(round_posts)
            results.append(round_result)
            
            summary = self.get_state_summary()
            print(f"Round {self.round}: tension={summary['global_tension']:.1f}, "
                  f"un={summary['event_counts']['un_resolutions']}, "
                  f"war={summary['event_counts']['war']}")
            
            self.global_tension = min(100, max(0, self.global_tension))
        
        return results
