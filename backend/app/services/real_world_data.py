"""
Real World Data Integration - 真实世界数据集成
为地缘政治模拟提供真实经济数据、军事数据、贸易数据
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class CountryProfile:
    """国家档案 - 真实世界数据"""
    # 基本信息
    country_id: str
    name: str
    name_en: str
    region: str
    
    # 经济数据 (2023-2024估计值)
    gdp_usd: float = 0.0                    # GDP (万亿美元)
    gdp_growth: float = 0.0                 # GDP增长率
    population_millions: float = 0.0          # 人口 (百万)
    
    # 军事数据
    military_spending_usd: float = 0.0      # 军费开支 (十亿美元)
    military_personnel_thousands: float = 0.0 # 军事人员 (千人)
    nuclear_warheads: int = 0               # 核弹头数量
    
    # 贸易数据
    exports_usd: float = 0.0                # 出口额 (十亿美元)
    imports_usd: float = 0.0                # 进口额 (十亿美元)
    top_trading_partners: List[str] = field(default_factory=list)
    
    # 能源
    oil_production_mbpd: float = 0.0        # 石油产量 (百万桶/日)
    oil_consumption_mbpd: float = 0.0        # 石油消费 (百万桶/日)
    
    # 科技/工业
    r_and_d_spending_pct_gdp: float = 0.0   # 研发支出占GDP比例
    manufacturing_output_index: float = 100.0 # 制造业产出指数
    
    # 政治
    political_system: str = "unknown"       # 政治体制
    regime_stability: float = 0.5           # 政权稳定性 (0-1)
    
    # 文化/软实力
    language_family: str = ""
    religion_majority: str = ""
    cultural_influence_index: float = 50.0    # 文化影响力指数


# 真实世界数据 - 2023-2024估计值
REAL_WORLD_DATA = {
    "usa": CountryProfile(
        country_id="usa",
        name="美国",
        name_en="United States",
        region="North America",
        gdp_usd=27.36,
        gdp_growth=2.5,
        population_millions=335.0,
        military_spending_usd=886.0,
        military_personnel_thousands=1300.0,
        nuclear_warheads=5800,
        exports_usd=2000.0,
        imports_usd=3200.0,
        top_trading_partners=["china", "canada", "mexico", "japan", "germany"],
        oil_production_mbpd=13.0,
        oil_consumption_mbpd=20.0,
        r_and_d_spending_pct_gdp=3.5,
        manufacturing_output_index=100.0,
        political_system="democracy",
        regime_stability=0.85,
        language_family="indo_european",
        religion_majority="christianity",
        cultural_influence_index=95.0,
    ),
    "china": CountryProfile(
        country_id="china",
        name="中国",
        name_en="China",
        region="East Asia",
        gdp_usd=17.79,
        gdp_growth=5.2,
        population_millions=1412.0,
        military_spending_usd=296.0,
        military_personnel_thousands=2000.0,
        nuclear_warheads=350,
        exports_usd=3400.0,
        imports_usd=2600.0,
        top_trading_partners=["usa", "japan", "south_korea", "germany", "australia"],
        oil_production_mbpd=4.0,
        oil_consumption_mbpd=14.0,
        r_and_d_spending_pct_gdp=2.4,
        manufacturing_output_index=140.0,
        political_system="autocracy",
        regime_stability=0.80,
        language_family="sino_tibetan",
        religion_majority="none",
        cultural_influence_index=70.0,
    ),
    "russia": CountryProfile(
        country_id="russia",
        name="俄罗斯",
        name_en="Russia",
        region="Eurasia",
        gdp_usd=2.02,
        gdp_growth=3.6,
        population_millions=144.0,
        military_spending_usd=109.0,
        military_personnel_thousands=900.0,
        nuclear_warheads=6500,
        exports_usd=450.0,
        imports_usd=250.0,
        top_trading_partners=["china", "germany", "netherlands", "turkey", "belarus"],
        oil_production_mbpd=10.0,
        oil_consumption_mbpd=3.5,
        r_and_d_spending_pct_gdp=1.0,
        manufacturing_output_index=60.0,
        political_system="hybrid",
        regime_stability=0.65,
        language_family="indo_european",
        religion_majority="christianity",
        cultural_influence_index=55.0,
    ),
    "eu": CountryProfile(
        country_id="eu",
        name="欧盟",
        name_en="European Union",
        region="Europe",
        gdp_usd=18.35,
        gdp_growth=1.8,
        population_millions=448.0,
        military_spending_usd=300.0,
        military_personnel_thousands=1500.0,
        nuclear_warheads=0,  # France/UK have nukes but not EU as entity
        exports_usd=2500.0,
        imports_usd=2400.0,
        top_trading_partners=["usa", "china", "uk", "switzerland", "turkey"],
        oil_production_mbpd=1.5,
        oil_consumption_mbpd=10.0,
        r_and_d_spending_pct_gdp=2.3,
        manufacturing_output_index=90.0,
        political_system="democracy",
        regime_stability=0.75,
        language_family="indo_european",
        religion_majority="christianity",
        cultural_influence_index=85.0,
    ),
    "iran": CountryProfile(
        country_id="iran",
        name="伊朗",
        name_en="Iran",
        region="Middle East",
        gdp_usd=0.40,
        gdp_growth=3.0,
        population_millions=87.0,
        military_spending_usd=25.0,
        military_personnel_thousands=550.0,
        nuclear_warheads=0,
        exports_usd=50.0,
        imports_usd=60.0,
        top_trading_partners=["china", "turkey", "india", "uae", "iraq"],
        oil_production_mbpd=2.5,
        oil_consumption_mbpd=1.8,
        r_and_d_spending_pct_gdp=0.8,
        manufacturing_output_index=40.0,
        political_system="autocracy",
        regime_stability=0.50,
        language_family="indo_european",
        religion_majority="islam",
        cultural_influence_index=45.0,
    ),
}


# 双边贸易依存度矩阵 (2023估计, 占对方贸易总额的百分比)
TRADE_DEPENDENCY = {
    ("usa", "china"): 0.15,    # 美国15%贸易与中国
    ("china", "usa"): 0.12,    # 中国12%贸易与美国
    ("usa", "eu"): 0.18,
    ("eu", "usa"): 0.20,
    ("china", "eu"): 0.14,
    ("eu", "china"): 0.16,
    ("russia", "china"): 0.25,  # 俄罗斯25%贸易与中国
    ("china", "russia"): 0.05,
    ("russia", "eu"): 0.08,
    ("eu", "russia"): 0.06,
    ("iran", "china"): 0.30,    # 伊朗高度依赖中国
    ("china", "iran"): 0.03,
    ("iran", "russia"): 0.10,
    ("russia", "iran"): 0.02,
    ("usa", "iran"): 0.00,     # 几乎无贸易（制裁）
    ("iran", "usa"): 0.00,
}

# 军事同盟关系
MILITARY_ALLIANCES = {
    "nato": ["usa", "eu"],           # 北约
    "sco": ["china", "russia"],      # 上海合作组织
    "bilateral_usa_eu": ("usa", "eu"), # 美欧双边
}

# 文化相似度矩阵 (0-1)
CULTURAL_SIMILARITY = {
    ("usa", "eu"): 0.85,       # 西方文化
    ("usa", "china"): 0.30,
    ("china", "russia"): 0.40, # 社会主义历史
    ("russia", "eu"): 0.50,    # 地理接近
    ("iran", "russia"): 0.35,
    ("iran", "china"): 0.25,
    ("usa", "iran"): 0.20,
    ("eu", "iran"): 0.25,
}

# 历史冲突记忆 (影响初始信任)
HISTORICAL_CONFLICTS = {
    ("usa", "russia"): -0.4,   # 冷战遗产
    ("usa", "china"): -0.3,   # 贸易战
    ("usa", "iran"): -0.6,    # 1979革命、核问题
    ("china", "russia"): 0.1, # 近年合作
    ("russia", "eu"): -0.5,   # 乌克兰危机
    ("iran", "russia"): 0.0,  # 叙利亚合作但有分歧
    ("china", "iran"): 0.2,  # 能源合作
    ("eu", "iran"): -0.3,    # 核协议分歧
}


class RealWorldDataIntegration:
    """真实世界数据集成器"""
    
    def __init__(self):
        self.profiles = REAL_WORLD_DATA
        self.trade_dependency = TRADE_DEPENDENCY
        self.military_alliances = MILITARY_ALLIANCES
        self.cultural_similarity = CULTURAL_SIMILARITY
        self.historical_conflicts = HISTORICAL_CONFLICTS
    
    def get_profile(self, country_id: str) -> Optional[CountryProfile]:
        """获取国家档案"""
        return self.profiles.get(country_id)
    
    def get_trade_dependency(self, a: str, b: str) -> float:
        """获取双边贸易依存度"""
        key = (a, b)
        if key not in self.trade_dependency:
            key = (b, a)
        return self.trade_dependency.get(key, 0.0)
    
    def get_cultural_similarity(self, a: str, b: str) -> float:
        """获取文化相似度"""
        key = (a, b)
        if key not in self.cultural_similarity:
            key = (b, a)
        return self.cultural_similarity.get(key, 0.5)
    
    def get_historical_conflict(self, a: str, b: str) -> float:
        """获取历史冲突记忆 (-1到1, 负值表示冲突)"""
        key = (a, b)
        if key not in self.historical_conflicts:
            key = (b, a)
        return self.historical_conflicts.get(key, 0.0)
    
    def are_allies(self, a: str, b: str) -> bool:
        """检查是否是军事同盟"""
        for alliance_name, members in self.military_alliances.items():
            if isinstance(members, list):
                if a in members and b in members:
                    return True
            elif isinstance(members, tuple):
                if (a in members and b in members):
                    return True
        return False
    
    def calculate_economic_interdependence(self, a: str, b: str) -> float:
        """计算经济相互依存度 (综合贸易、投资、供应链)"""
        trade_dep = self.get_trade_dependency(a, b)
        
        # 获取GDP数据
        profile_a = self.get_profile(a)
        profile_b = self.get_profile(b)
        
        if not profile_a or not profile_b:
            return trade_dep
        
        # 经济体量差异调整
        gdp_ratio = min(profile_a.gdp_usd, profile_b.gdp_usd) / max(profile_a.gdp_usd, profile_b.gdp_usd)
        
        # 综合依存度
        interdependence = trade_dep * (0.5 + 0.5 * gdp_ratio)
        
        return min(1.0, interdependence)
    
    def calculate_initial_trust(self, a: str, b: str) -> float:
        """计算初始信任度 (基于历史、文化、同盟)"""
        # 基础信任
        base_trust = 0.5
        
        # 历史冲突影响
        historical = self.get_historical_conflict(a, b)
        
        # 文化相似度加成
        cultural = (self.get_cultural_similarity(a, b) - 0.5) * 0.3
        
        # 同盟关系加成
        alliance_bonus = 0.3 if self.are_allies(a, b) else 0.0
        
        # 贸易依存度加成
        trade = self.get_trade_dependency(a, b) * 0.2
        
        # 综合计算
        trust = base_trust + historical + cultural + alliance_bonus + trade
        
        # 限制在合理范围
        return max(0.0, min(1.0, trust))
    
    def calculate_power_index(self, country_id: str) -> float:
        """计算综合国力指数 (0-100)"""
        profile = self.get_profile(country_id)
        if not profile:
            return 50.0
        
        # 经济权重 40%
        economic_score = min(100, profile.gdp_usd / 27.36 * 100) * 0.4
        
        # 军事权重 30%
        military_score = min(100, profile.military_spending_usd / 886.0 * 100) * 0.3
        
        # 科技权重 15%
        tech_score = min(100, profile.r_and_d_spending_pct_gdp / 3.5 * 100) * 0.15
        
        # 软实力权重 15%
        soft_score = profile.cultural_influence_index * 0.15
        
        return economic_score + military_score + tech_score + soft_score
    
    def get_sanction_impact(self, target: str, imposer: str, 
                           severity: str) -> float:
        """计算制裁对目标国的实际经济影响"""
        trade_dep = self.get_trade_dependency(target, imposer)
        
        # 基础影响
        base_impact = {
            "light": 0.02,
            "moderate": 0.05,
            "severe": 0.10,
        }.get(severity, 0.05)
        
        # 根据贸易依存度调整
        adjusted_impact = base_impact * (1.0 + trade_dep * 5.0)
        
        # 考虑经济体量韧性
        profile = self.get_profile(target)
        if profile:
            # 大国更有韧性
            gdp_factor = min(1.0, 5.0 / profile.gdp_usd) if profile.gdp_usd > 0 else 1.0
            adjusted_impact *= gdp_factor
        
        return min(0.5, adjusted_impact)
    
    def to_dict(self) -> Dict:
        """导出所有数据为字典"""
        return {
            "profiles": {
                k: {
                    "name": v.name,
                    "name_en": v.name_en,
                    "gdp_usd": v.gdp_usd,
                    "military_spending": v.military_spending_usd,
                    "nuclear_warheads": v.nuclear_warheads,
                    "population": v.population_millions,
                    "political_system": v.political_system,
                    "regime_stability": v.regime_stability,
                }
                for k, v in self.profiles.items()
            },
            "trade_dependencies": {
                f"{k[0]}|{k[1]}": v 
                for k, v in self.trade_dependency.items()
            },
            "alliances": self.military_alliances,
            "cultural_similarity": {
                f"{k[0]}|{k[1]}": v 
                for k, v in self.cultural_similarity.items()
            },
            "historical_conflicts": {
                f"{k[0]}|{k[1]}": v 
                for k, v in self.historical_conflicts.items()
            },
        }


# 全局实例
real_world_data = RealWorldDataIntegration()

if __name__ == "__main__":
    # 测试
    rw = RealWorldDataIntegration()
    
    print("=== 真实世界数据测试 ===\n")
    
    # 国家档案
    for cid in ["usa", "china", "russia", "eu", "iran"]:
        p = rw.get_profile(cid)
        print(f"{p.name}: GDP=${p.gdp_usd}T, 军费=${p.military_spending_usd}B, 核弹头={p.nuclear_warheads}")
    
    print("\n=== 国力指数 ===")
    for cid in ["usa", "china", "russia", "eu", "iran"]:
        power = rw.calculate_power_index(cid)
        print(f"{cid}: {power:.1f}/100")
    
    print("\n=== 初始信任度 ===")
    pairs = [("usa", "china"), ("usa", "eu"), ("china", "russia"), ("russia", "eu"), ("usa", "iran")]
    for a, b in pairs:
        trust = rw.calculate_initial_trust(a, b)
        print(f"{a}-{b}: {trust:.2f}")
    
    print("\n=== 贸易依存度 ===")
    for a, b in pairs:
        dep = rw.get_trade_dependency(a, b)
        interdep = rw.calculate_economic_interdependence(a, b)
        print(f"{a}-{b}: 贸易依存={dep:.1%}, 综合依存={interdep:.1%}")
    
    print("\n=== 制裁影响估算 ===")
    for target, imposer in [("russia", "usa"), ("iran", "usa"), ("china", "usa")]:
        for sev in ["light", "moderate", "severe"]:
            impact = rw.get_sanction_impact(target, imposer, sev)
            print(f"{imposer}→{target} ({sev}): {impact:.1%}")
