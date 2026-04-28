"""
Political-Diplomatic Integration - 政党-外交整合
将政党数据与外交模拟整合
"""

import sys
import os
from typing import Dict, List, Optional, Tuple

# 导入政党数据库
try:
    from political_party_database import party_db, PoliticalPartyDatabase
    PARTY_DB_AVAILABLE = True
except ImportError:
    PARTY_DB_AVAILABLE = False

class PoliticalDiplomaticIntegration:
    """政党-外交整合器"""
    
    def __init__(self):
        self.party_db = party_db if PARTY_DB_AVAILABLE else None
        self.current_rulings: Dict[str, str] = {}  # country_id -> party_id
        
        if self.party_db:
            # 初始化当前执政党
            countries = ["usa", "china", "russia", "germany", "france", 
                        "uk", "japan", "india", "south_korea", "brazil",
                        "italy", "australia", "turkey"]
            for country_id in countries:
                party = self.party_db.get_ruling_party(country_id)
                if party:
                    self.current_rulings[country_id] = party.party_id
    
    def get_diplomatic_stance(self, country_id: str, target: str) -> float:
        """获取国家对目标国的外交立场"""
        if not self.party_db:
            return 0.0
        
        party = self.party_db.get_ruling_party(country_id)
        if not party:
            return 0.0
        
        target_stance = getattr(party, f"stance_{target}", 0.0)
        return target_stance
    
    def simulate_election_impact(self, country_id: str, new_ruling_party_id: str) -> Dict:
        """模拟政党轮替对外交的影响"""
        if not self.party_db:
            return {}
        
        old_party = self.party_db.get_ruling_party(country_id)
        new_party = self.party_db.get_party(new_ruling_party_id)
        
        if not old_party or not new_party:
            return {}
        
        impacts = {
            "country_id": country_id,
            "old_party": old_party.name_cn,
            "new_party": new_party.name_cn,
            "stance_changes": {},
        }
        
        # 计算对各国立场变化
        for target in ["usa", "china", "russia"]:
            old_stance = getattr(old_party, f"stance_{target}", 0.0)
            new_stance = getattr(new_party, f"stance_{target}", 0.0)
            change = new_stance - old_stance
            
            impacts["stance_changes"][target] = {
                "old": old_stance,
                "new": new_stance,
                "change": change,
                "improved": change > 0,
                "deteriorated": change < 0,
            }
        
        # 评估外交政策变化
        if old_party.foreign_policy != new_party.foreign_policy:
            impacts["policy_change"] = {
                "old": old_party.foreign_policy,
                "new": new_party.foreign_policy,
            }
        
        return impacts
    
    def get_bilateral_potential(self, country_a: str, country_b: str) -> Dict:
        """评估双边关系潜力"""
        if not self.party_db:
            return {"potential": 0.5, "level": "medium"}
        
        party_a = self.party_db.get_ruling_party(country_a)
        party_b = self.party_db.get_ruling_party(country_b)
        
        if not party_a or not party_b:
            return {"potential": 0.5, "level": "medium"}
        
        # 计算基础潜力
        potential = self.party_db.calculate_diplomatic_potential(country_a, country_b)
        
        # 评估各维度
        ideology_match = party_a.ideology == party_b.ideology
        same_economic = party_a.economic_policy == party_b.economic_policy
        
        # 跨党际友好加成
        cross_border_bonus = 0.0
        if party_b.party_id in self.party_db.get_friendly_parties(party_a.party_id):
            cross_border_bonus = 0.2
        
        final_potential = min(1.0, potential + cross_border_bonus)
        
        # 确定等级
        if final_potential >= 0.8:
            level = "very_high"
        elif final_potential >= 0.65:
            level = "high"
        elif final_potential >= 0.5:
            level = "medium"
        elif final_potential >= 0.35:
            level = "low"
        else:
            level = "very_low"
        
        return {
            "potential": final_potential,
            "level": level,
            "party_a": party_a.name_cn,
            "party_b": party_b.name_cn,
            "ideology_match": ideology_match,
            "cross_border_friends": cross_border_bonus > 0,
        }
    
    def get_regime_type(self, country_id: str) -> str:
        """判断政权类型"""
        if not self.party_db:
            return "unknown"
        
        party = self.party_db.get_ruling_party(country_id)
        if not party:
            return "unknown"
        
        # 基于意识形态判断
        ideology = party.ideology
        
        # 威权/非民主政权
        if ideology in ["communist", "socialist", "nationalist_conservative", "authoritarian_nationalist"]:
            return "authoritarian_nationalist"
        elif country_id in ["russia"]:
            return "competitive_authoritarian"  # 俄罗斯特殊处理
        elif ideology in ["far_right", "nationalist"] and country_id in ["turkey"]:
            return "competitive_authoritarian"
        elif country_id in ["iran", "saudi_arabia", "north_korea"]:
            return "authoritarian_nationalist"  # 神权/君主/极权
        elif ideology in ["far_right", "conservative"] and party.is_ruling:
            return "democratic"
        else:
            return "democratic"
    
    def get_regime_compatibility(self, country_a: str, country_b: str) -> Tuple[float, str]:
        """评估政权兼容度"""
        regime_a = self.get_regime_type(country_a)
        regime_b = self.get_regime_type(country_b)
        
        # 兼容度矩阵
        compatibility = {
            ("democratic", "democratic"): (0.8, "民主同盟"),
            ("one_party", "one_party"): (0.6, "一党制伙伴"),
            ("democratic", "one_party"): (0.3, "意识形态分歧"),
            ("democratic", "competitive_authoritarian"): (0.4, "民主-威权竞争"),
            ("one_party", "competitive_authoritarian"): (0.5, "非民主协调"),
            ("competitive_authoritarian", "competitive_authoritarian"): (0.5, "威权伙伴"),
            ("democratic", "authoritarian_nationalist"): (0.2, "民主-威权对立"),
            ("authoritarian_nationalist", "authoritarian_nationalist"): (0.6, "威权伙伴"),
            ("authoritarian_nationalist", "competitive_authoritarian"): (0.5, "非民主协调"),
            ("authoritarian_nationalist", "one_party"): (0.6, "威权伙伴"),
            ("competitive_authoritarian", "authoritarian_nationalist"): (0.5, "非民主协调"),
            ("one_party", "authoritarian_nationalist"): (0.6, "威权伙伴"),
        }
        
        key = (regime_a, regime_b)
        if key in compatibility:
            return compatibility[key]
        
        # 反向查找
        key = (regime_b, regime_a)
        if key in compatibility:
            return compatibility[key]
        
        return (0.5, "未知")
    
    def get_alliance_predictability(self, country_a: str, country_b: str) -> float:
        """评估同盟可预测性"""
        if not self.party_db:
            return 0.5
        
        # 政党轮替频率 (简化)
        party_a = self.party_db.get_ruling_party(country_a)
        party_b = self.party_db.get_ruling_party(country_b)
        
        if not party_a or not party_b:
            return 0.5
        
        # 连续执政越长越稳定
        ruling_stability_a = 0.8 if party_a.is_ruling else 0.4
        ruling_stability_b = 0.8 if party_b.is_ruling else 0.4
        
        # 政权类型稳定性
        regime_type_a = self.get_regime_type(country_a)
        regime_type_b = self.get_regime_type(country_b)
        
        regime_stability_a = 1.0 if regime_type_a in ["one_party", "competitive_authoritarian"] else 0.6
        regime_stability_b = 1.0 if regime_type_b in ["one_party", "competitive_authoritarian"] else 0.6
        
        # 外交政策一致性
        policy_consistency_a = 0.8 if regime_type_a != "democratic" else 0.6
        policy_consistency_b = 0.8 if regime_type_b != "democratic" else 0.6
        
        # 综合可预测性
        predictability = (
            ruling_stability_a * 0.2 +
            ruling_stability_b * 0.2 +
            regime_stability_a * 0.2 +
            regime_stability_b * 0.2 +
            policy_consistency_a * 0.1 +
            policy_consistency_b * 0.1
        )
        
        return min(1.0, predictability)
    
    def get_conflict_risk_factors(self, country_a: str, country_b: str) -> Dict:
        """评估冲突风险因素"""
        if not self.party_db:
            return {}
        
        party_a = self.party_db.get_ruling_party(country_a)
        party_b = self.party_db.get_ruling_party(country_b)
        
        if not party_a or not party_b:
            return {}
        
        risks = []
        risk_score = 0.0
        
        # 意识形态对立
        if party_a.ideology in ["far_right", "far_left"] and party_b.ideology in ["far_right", "far_left"]:
            if party_a.ideology != party_b.ideology:
                risks.append("极端意识形态对立")
                risk_score += 0.2
        
        # 对美立场对立
        if party_a.stance_usa * party_b.stance_usa < -0.1:
            risks.append("对美立场严重对立")
            risk_score += 0.15
        
        # 对华立场对立  
        if party_a.stance_china * party_b.stance_china < -0.1:
            risks.append("对华立场严重对立")
            risk_score += 0.15
        
        # 民族主义风险
        if party_a.ideology == "nationalist" or party_b.ideology == "nationalist":
            risks.append("任一为民族主义政党")
            risk_score += 0.1
        
        # 民主-威权对立
        regime_a = self.get_regime_type(country_a)
        regime_b = self.get_regime_type(country_b)
        if regime_a == "democratic" and regime_b in ["one_party", "competitive_authoritarian"]:
            risks.append("民主-威权意识形态分歧")
            risk_score += 0.15
        elif regime_b == "democratic" and regime_a in ["one_party", "competitive_authoritarian"]:
            risks.append("民主-威权意识形态分歧")
            risk_score += 0.15
        
        return {
            "risk_score": min(1.0, risk_score),
            "risk_factors": risks,
            "party_a": party_a.name_cn,
            "party_b": party_b.name_cn,
        }


# 全局实例
pol_dip_integration = PoliticalDiplomaticIntegration()

if __name__ == "__main__":
    integration = PoliticalDiplomaticIntegration()
    
    print("=== 政党-外交整合测试 ===\n")
    
    # 双边关系评估
    print("=== 双边关系潜力 ===")
    pairs = [
        ("usa", "uk"), ("usa", "germany"), ("usa", "france"),
        ("usa", "japan"), ("china", "russia"),
        ("india", "usa"), ("india", "china"),
        ("japan", "china"), ("germany", "china"),
    ]
    
    for a, b in pairs:
        result = integration.get_bilateral_potential(a, b)
        print(f"{a}-{b}: {result['potential']:.2f} ({result['level']}) | "
              f"{result['party_a']} <-> {result['party_b']}")
    
    print("\n=== 政权兼容度 ===")
    regime_pairs = [
        ("usa", "germany"), ("usa", "china"), 
        ("china", "russia"), ("usa", "russia"),
    ]
    for a, b in regime_pairs:
        score, desc = integration.get_regime_compatibility(a, b)
        print(f"{a}-{b}: {score:.2f} ({desc})")
    
    print("\n=== 同盟可预测性 ===")
    alliance_pairs = [
        ("usa", "uk"), ("usa", "japan"), 
        ("china", "russia"), ("usa", "germany"),
    ]
    for a, b in alliance_pairs:
        pred = integration.get_alliance_predictability(a, b)
        print(f"{a}-{b}: {pred:.2f}")
    
    print("\n=== 冲突风险因素 ===")
    risk_pairs = [
        ("usa", "china"), ("usa", "russia"),
        ("japan", "china"), ("india", "china"),
    ]
    for a, b in risk_pairs:
        risk = integration.get_conflict_risk_factors(a, b)
        if risk:
            print(f"{a}-{b}: 风险={risk['risk_score']:.2f}")
            for factor in risk['risk_factors']:
                print(f"  - {factor}")
