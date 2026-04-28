"""
Political Party Database - 政党数据库
记录各国主要政党及其意识形态、对华对美立场、政策倾向
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class Ideology(Enum):
    """意识形态"""
    FAR_LEFT = "far_left"
    LEFT = "left"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    RIGHT = "right"
    FAR_RIGHT = "far_right"
    CONSERVATIVE = "conservative"
    LIBERAL = "liberal"
    NATIONALIST = "nationalist"
    SOCIALIST = "socialist"
    COMMUNIST = "communist"
    FASCIST = "fascist"
    GREEN = "green"

class Stance(Enum):
    """对华/对美立场"""
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"
    COMPLEX = "complex"  # 复杂/摇摆

@dataclass
class PoliticalParty:
    """政党信息"""
    party_id: str
    name: str
    name_cn: str
    country_id: str
    ideology: str
    is_ruling: bool = False
    
    # 对华立场 (-1完全敌对到+1完全友好)
    stance_china: float = 0.0
    
    # 对美立场 (-1完全敌对到+1完全友好)
    stance_usa: float = 0.0
    
    # 对俄立场
    stance_russia: float = 0.0
    
    # 内政倾向
    domestic_policy: str = ""  # "progressive", "conservative", "populist"
    
    # 经济政策
    economic_policy: str = ""  # "free_market", "state_led", "mixed"
    
    # 外交政策
    foreign_policy: str = ""  # "internationalist", "isolationist", "multialignment"
    
    # 与其他国家政党的关系
    party_relations: Dict[str, float] = field(default_factory=dict)  # party_id -> relation (-1 to 1)

# 主要国家政党数据库
PARTY_DATABASE: Dict[str, List[PoliticalParty]] = {
    # ===== 美国 =====
    "usa": [
        PoliticalParty(
            party_id="usa_democrat",
            name="Democratic Party",
            name_cn="民主党",
            country_id="usa",
            ideology="center_left",
            is_ruling=True,
            stance_china=-0.3,  # 竞争但合作
            stance_usa=1.0,
            stance_russia=-0.5,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="internationalist",
        ),
        PoliticalParty(
            party_id="usa_republican",
            name="Republican Party",
            name_cn="共和党",
            country_id="usa",
            ideology="center_right",
            is_ruling=False,
            stance_china=-0.6,  # 更强硬
            stance_usa=1.0,
            stance_russia=-0.7,
            domestic_policy="conservative",
            economic_policy="free_market",
            foreign_policy="america_first",
        ),
    ],
    
    # ===== 中国 =====
    "china": [
        PoliticalParty(
            party_id="china_cpc",
            name="Communist Party of China",
            name_cn="中国共产党",
            country_id="china",
            ideology="communist",
            is_ruling=True,
            stance_china=1.0,
            stance_usa=-0.4,  # 竞争关系
            stance_russia=0.6,  # 战略合作
            domestic_policy="state_led",
            economic_policy="state_led",
            foreign_policy="multialignment",
        ),
    ],
    
    # ===== 俄罗斯 =====
    "russia": [
        PoliticalParty(
            party_id="russia_united_russia",
            name="United Russia",
            name_cn="统一俄罗斯党",
            country_id="russia",
            ideology="conservative",
            is_ruling=True,
            stance_china=0.6,
            stance_usa=-0.8,
            stance_russia=1.0,
            domestic_policy="conservative",
            economic_policy="state_led",
            foreign_policy="eurasian",
        ),
        PoliticalParty(
            party_id="russia_kprf",
            name="Communist Party",
            name_cn="俄罗斯联邦共产党",
            country_id="russia",
            ideology="communist",
            is_ruling=False,
            stance_china=0.7,
            stance_usa=-0.7,
            stance_russia=0.8,
            domestic_policy="progressive",
            economic_policy="state_led",
            foreign_policy="internationalist",
        ),
        PoliticalParty(
            party_id="russia_ldpr",
            name="Liberal Democratic Party",
            name_cn="自由民主党",
            country_id="russia",
            ideology="nationalist",
            is_ruling=False,
            stance_china=0.3,
            stance_usa=-0.9,
            stance_russia=0.9,
            domestic_policy="populist",
            economic_policy="mixed",
            foreign_policy="nationalist",
        ),
    ],
    
    # ===== 日本 =====
    "japan": [
        PoliticalParty(
            party_id="japan_ldp",
            name="Liberal Democratic Party",
            name_cn="自由民主党",
            country_id="japan",
            ideology="conservative",
            is_ruling=True,
            stance_china=-0.4,  # 领土争议
            stance_usa=0.8,
            stance_russia=-0.5,
            domestic_policy="conservative",
            economic_policy="free_market",
            foreign_policy="alliance_usa",
        ),
        PoliticalParty(
            party_id="japan_constitutional_democratic",
            name="Constitutional Democratic Party",
            name_cn="立宪民主党",
            country_id="japan",
            ideology="liberal",
            is_ruling=False,
            stance_china=0.0,
            stance_usa=0.7,
            stance_russia=-0.3,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="internationalist",
        ),
    ],
    
    # ===== 德国 =====
    "germany": [
        PoliticalParty(
            party_id="germany_cdu",
            name="Christian Democratic Union",
            name_cn="基督教民主联盟",
            country_id="germany",
            ideology="center_right",
            is_ruling=True,
            stance_china=0.0,  # 经济合作但人权关切
            stance_usa=0.7,
            stance_russia=-0.5,
            domestic_policy="conservative",
            economic_policy="social_market",
            foreign_policy="european_integration",
        ),
        PoliticalParty(
            party_id="germany_spd",
            name="Social Democratic Party",
            name_cn="社会民主党",
            country_id="germany",
            ideology="center_left",
            is_ruling=False,
            stance_china=0.1,
            stance_usa=0.6,
            stance_russia=-0.4,
            domestic_policy="progressive",
            economic_policy="social_democratic",
            foreign_policy="european_integration",
        ),
        PoliticalParty(
            party_id="germany_green",
            name="Alliance 90/The Greens",
            name_cn="联盟90/绿党",
            country_id="germany",
            ideology="green",
            is_ruling=False,
            stance_china=-0.2,
            stance_usa=0.5,
            stance_russia=-0.6,
            domestic_policy="progressive",
            economic_policy="green_economy",
            foreign_policy="rules_based",
        ),
        PoliticalParty(
            party_id="germany_afd",
            name="Alternative for Germany",
            name_cn="德国选择党",
            country_id="germany",
            ideology="far_right",
            is_ruling=False,
            stance_china=0.2,
            stance_usa=-0.3,
            stance_russia=0.4,
            domestic_policy="populist",
            economic_policy="mixed",
            foreign_policy="eurosceptic",
        ),
    ],
    
    # ===== 法国 =====
    "france": [
        PoliticalParty(
            party_id="france_renaissance",
            name="Renaissance",
            name_cn="复兴党",
            country_id="france",
            ideology="center",
            is_ruling=True,
            stance_china=0.0,
            stance_usa=0.8,
            stance_russia=-0.4,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="european_strategic",
        ),
        PoliticalParty(
            party_id="france_republicains",
            name="The Republicans",
            name_cn="共和党",
            country_id="france",
            ideology="center_right",
            is_ruling=False,
            stance_china=0.1,
            stance_usa=0.7,
            stance_russia=-0.5,
            domestic_policy="conservative",
            economic_policy="free_market",
            foreign_policy="european_integration",
        ),
        PoliticalParty(
            party_id="france_national_rally",
            name="National Rally",
            name_cn="国民联盟",
            country_id="france",
            ideology="far_right",
            is_ruling=False,
            stance_china=0.3,
            stance_usa=-0.2,
            stance_russia=0.5,
            domestic_policy="populist",
            economic_policy="mixed",
            foreign_policy="national_sovereignty",
        ),
        PoliticalParty(
            party_id="france_lfi",
            name="La France Insoumise",
            name_cn="不屈法国",
            country_id="france",
            ideology="far_left",
            is_ruling=False,
            stance_china=0.4,
            stance_usa=-0.4,
            stance_russia=0.3,
            domestic_policy="progressive",
            economic_policy="state_led",
            foreign_policy="anti_nato",
        ),
    ],
    
    # ===== 英国 =====
    "uk": [
        PoliticalParty(
            party_id="uk_labour",
            name="Labour Party",
            name_cn="工党",
            country_id="uk",
            ideology="center_left",
            is_ruling=True,
            stance_china=-0.2,
            stance_usa=0.7,
            stance_russia=-0.5,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="atlanticist",
        ),
        PoliticalParty(
            party_id="uk_conservative",
            name="Conservative Party",
            name_cn="保守党",
            country_id="uk",
            ideology="center_right",
            is_ruling=False,
            stance_china=-0.3,
            stance_usa=0.8,
            stance_russia=-0.6,
            domestic_policy="conservative",
            economic_policy="free_market",
            foreign_policy="global_britain",
        ),
    ],
    
    # ===== 印度 =====
    "india": [
        PoliticalParty(
            party_id="india_bjp",
            name="Bharatiya Janata Party",
            name_cn="印度人民党",
            country_id="india",
            ideology="hindu_nationalist",
            is_ruling=True,
            stance_china=-0.4,  # 边境争议
            stance_usa=0.4,  # QUAD但保持独立
            stance_russia=0.3,  # 传统友好
            domestic_policy="conservative",
            economic_policy="mixed",
            foreign_policy="strategic_autonomy",
        ),
        PoliticalParty(
            party_id="india_congress",
            name="Indian National Congress",
            name_cn="国大党",
            country_id="india",
            ideology="center_left",
            is_ruling=False,
            stance_china=-0.2,
            stance_usa=0.5,
            stance_russia=0.4,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="non_alignment",
        ),
    ],
    
    # ===== 韩国 =====
    "south_korea": [
        PoliticalParty(
            party_id="sk_dpp",
            name="Democratic Party of Korea",
            name_cn="共同民主党",
            country_id="south_korea",
            ideology="center_left",
            is_ruling=True,
            stance_china=0.0,
            stance_usa=0.6,
            stance_russia=-0.2,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="alliance_usa",
        ),
        PoliticalParty(
            party_id="sk_ppp",
            name="People Power Party",
            name_cn="国民力量党",
            country_id="south_korea",
            ideology="conservative",
            is_ruling=False,
            stance_china=-0.3,
            stance_usa=0.8,
            stance_russia=-0.3,
            domestic_policy="conservative",
            economic_policy="free_market",
            foreign_policy="alliance_usa",
        ),
    ],
    
    # ===== 意大利 =====
    "italy": [
        PoliticalParty(
            party_id="italy_fdi",
            name="Brothers of Italy",
            name_cn="意大利兄弟党",
            country_id="italy",
            ideology="far_right",
            is_ruling=True,
            stance_china=-0.2,
            stance_usa=0.6,
            stance_russia=-0.3,
            domestic_policy="conservative",
            economic_policy="mixed",
            foreign_policy="european_integration",
        ),
        PoliticalParty(
            party_id="italy_pd",
            name="Democratic Party",
            name_cn="民主党",
            country_id="italy",
            ideology="center_left",
            is_ruling=False,
            stance_china=0.0,
            stance_usa=0.7,
            stance_russia=-0.4,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="european_integration",
        ),
    ],
    
    # ===== 巴西 =====
    "brazil": [
        PoliticalParty(
            party_id="brazil_pt",
            name="Workers' Party",
            name_cn="劳工党",
            country_id="brazil",
            ideology="left",
            is_ruling=True,
            stance_china=0.5,  # 金砖伙伴
            stance_usa=0.0,
            stance_russia=0.4,
            domestic_policy="progressive",
            economic_policy="state_led",
            foreign_policy="multialignment",
        ),
        PoliticalParty(
            party_id="brazil_pl",
            name="Liberal Party",
            name_cn="自由党",
            country_id="brazil",
            ideology="right",
            is_ruling=False,
            stance_china=0.2,
            stance_usa=0.5,
            stance_russia=0.0,
            domestic_policy="conservative",
            economic_policy="free_market",
            foreign_policy="pro_usa",
        ),
    ],
    
    # ===== 澳大利亚 =====
    "australia": [
        PoliticalParty(
            party_id="au_labor",
            name="Australian Labor Party",
            name_cn="工党",
            country_id="australia",
            ideology="center_left",
            is_ruling=True,
            stance_china=-0.3,
            stance_usa=0.7,
            stance_russia=-0.5,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="alliance_usa",
        ),
        PoliticalParty(
            party_id="au_liberal",
            name="Liberal Party",
            name_cn="自由党",
            country_id="australia",
            ideology="center_right",
            is_ruling=False,
            stance_china=-0.4,
            stance_usa=0.8,
            stance_russia=-0.6,
            domestic_policy="conservative",
            economic_policy="free_market",
            foreign_policy="alliance_usa",
        ),
    ],
    
    # ===== 土耳其 =====
    "turkey": [
        PoliticalParty(
            party_id="turkey_akp",
            name="Justice and Development Party",
            name_cn="正义与发展党",
            country_id="turkey",
            ideology="conservative",
            is_ruling=True,
            stance_china=0.0,
            stance_usa=-0.2,
            stance_russia=0.3,
            domestic_policy="conservative",
            economic_policy="mixed",
            foreign_policy="strategic_autonomy",
        ),
        PoliticalParty(
            party_id="turkey_chp",
            name="Republican People's Party",
            name_cn="共和人民党",
            country_id="turkey",
            ideology="center_left",
            is_ruling=False,
            stance_china=-0.1,
            stance_usa=0.3,
            stance_russia=-0.4,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="western_alignment",
        ),
    ],
    
    # ===== 沙特阿拉伯 =====
    "saudi_arabia": [
        PoliticalParty(
            party_id="saudi_council",
            name="Saudi Cabinet",
            name_cn="沙特内阁",
            country_id="saudi_arabia",
            ideology="conservative",
            is_ruling=True,
            stance_china=0.3,
            stance_usa=0.2,
            stance_russia=0.1,
            domestic_policy="conservative",
            economic_policy="state_led",
            foreign_policy="regional_hegemony",
        ),
    ],
    
    # ===== 伊朗 =====
    "iran": [
        PoliticalParty(
            party_id="iran_reformists",
            name="Reformists",
            name_cn="改革派",
            country_id="iran",
            ideology="centrist",
            is_ruling=False,
            stance_china=0.3,
            stance_usa=-0.5,
            stance_russia=0.4,
            domestic_policy="progressive",
            economic_policy="mixed",
            foreign_policy="moderate",
        ),
        PoliticalParty(
            party_id="iran_hardliners",
            name="Principalists/Hardliners",
            name_cn="强硬派",
            country_id="iran",
            ideology="conservative",
            is_ruling=True,
            stance_china=0.2,
            stance_usa=-0.8,
            stance_russia=0.5,
            domestic_policy="conservative",
            economic_policy="state_led",
            foreign_policy="resistance_axis",
        ),
    ],
}


# 跨党际友好关系 (party_id -> [friendly party_ids])
CROSS_BORDER_PARTY_RELATIONS = {
    # 保守派国际
    "usa_republican": ["uk_conservative", "germany_afd", "france_national_rally", "japan_ldp"],
    "uk_conservative": ["usa_republican", "aus_liberal"],
    
    # 社会党国际
    "usa_democrat": ["uk_labour", "germany_spd", "france_renaissance", "au_labor"],
    "uk_labour": ["usa_democrat", "germany_spd", "sk_dpp"],
    
    # 共产党/左翼
    "china_cpc": ["russia_kprf", "france_lfi", "brazil_pt"],
    "russia_kprf": ["china_cpc", "france_lfi"],
    
    # 民族主义者
    "india_bjp": ["usa_republican", "japan_ldp"],
    "russia_ldpr": ["france_national_rally"],
    
    # 绿党
    "germany_green": ["france_greens", "uk_greens"],
}


class PoliticalPartyDatabase:
    """政党数据库"""
    
    def __init__(self):
        self.parties = PARTY_DATABASE
        self.cross_border = CROSS_BORDER_PARTY_RELATIONS
    
    def get_ruling_party(self, country_id: str) -> Optional[PoliticalParty]:
        """获取执政党"""
        parties = self.parties.get(country_id, [])
        for party in parties:
            if party.is_ruling:
                return party
        return None if not parties else parties[0]  # 默认第一个
    
    def get_all_parties(self, country_id: str) -> List[PoliticalParty]:
        """获取所有政党"""
        return self.parties.get(country_id, [])
    
    def get_party(self, party_id: str) -> Optional[PoliticalParty]:
        """根据ID获取政党"""
        for parties in self.parties.values():
            for party in parties:
                if party.party_id == party_id:
                    return party
        return None
    
    def get_country_stance(self, country_id: str, target: str) -> float:
        """获取国家对另一个国家的平均立场"""
        parties = self.get_all_parties(country_id)
        if not parties:
            return 0.0
        
        # 按执政党加权
        ruling = self.get_ruling_party(country_id)
        if ruling:
            target_stance = getattr(ruling, f"stance_{target}", 0.0)
            return target_stance
        
        # 无执政党信息则平均
        stances = [getattr(p, f"stance_{target}", 0.0) for p in parties]
        return sum(stances) / len(stances)
    
    def get_parties_by_ideology(self, ideology: str) -> List[PoliticalParty]:
        """按意识形态筛选政党"""
        result = []
        for parties in self.parties.values():
            for party in parties:
                if ideology in party.ideology:
                    result.append(party)
        return result
    
    def get_friendly_parties(self, party_id: str) -> List[str]:
        """获取跨党际友好政党"""
        return self.cross_border.get(party_id, [])
    
    def calculate_diplomatic_potential(self, country_a: str, country_b: str) -> float:
        """计算两国建交/合作潜力"""
        party_a = self.get_ruling_party(country_a)
        party_b = self.get_ruling_party(country_b)
        
        if not party_a or not party_b:
            return 0.5
        
        # 基础分数
        base = 0.5
        
        # 意识形态相近加成
        if party_a.ideology == party_b.ideology:
            base += 0.2
        elif party_a.ideology in [party_b.ideology] or party_b.ideology in [party_a.ideology]:
            base += 0.1
        
        # 跨党际友好
        if party_b.party_id in self.get_friendly_parties(party_a.party_id):
            base += 0.3
        
        # 对外立场相近
        for target in ["usa", "china", "russia"]:
            stance_a = getattr(party_a, f"stance_{target}", 0.0)
            stance_b = getattr(party_b, f"stance_{target}", 0.0)
            similarity = 1.0 - abs(stance_a - stance_b) / 2.0
            base += similarity * 0.1
        
        return max(0.0, min(1.0, base))
    
    def get_political_similarity(self, country_a: str, country_b: str) -> Dict[str, float]:
        """获取两国政治相似度"""
        party_a = self.get_ruling_party(country_a)
        party_b = self.get_ruling_party(country_b)
        
        if not party_a or not party_b:
            return {"overall": 0.5}
        
        # 意识形态相似度
        ideology_sim = 1.0 if party_a.ideology == party_b.ideology else 0.5
        
        # 外交立场相似度
        foreign_sim = {}
        for target in ["usa", "china", "russia"]:
            s_a = getattr(party_a, f"stance_{target}", 0.0)
            s_b = getattr(party_b, f"stance_{target}", 0.0)
            foreign_sim[target] = 1.0 - abs(s_a - s_b) / 2.0
        
        # 综合相似度
        overall = (ideology_sim + sum(foreign_sim.values()) / 3) / 2
        
        return {
            "overall": overall,
            "ideology": ideology_sim,
            "foreign_usa": foreign_sim["usa"],
            "foreign_china": foreign_sim["china"],
            "foreign_russia": foreign_sim["russia"],
        }
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        result = {}
        for country_id, parties in self.parties.items():
            result[country_id] = [
                {
                    "party_id": p.party_id,
                    "name": p.name,
                    "name_cn": p.name_cn,
                    "ideology": p.ideology,
                    "is_ruling": p.is_ruling,
                    "stance_china": p.stance_china,
                    "stance_usa": p.stance_usa,
                    "stance_russia": p.stance_russia,
                }
                for p in parties
            ]
        return result


# 全局实例
party_db = PoliticalPartyDatabase()

if __name__ == "__main__":
    db = PoliticalPartyDatabase()
    
    print("=== 政党数据库测试 ===\n")
    
    # 执政党
    print("主要国家执政党:")
    for country_id in ["usa", "china", "russia", "germany", "france", "india", "uk"]:
        party = db.get_ruling_party(country_id)
        if party:
            print(f"  {country_id}: {party.name_cn} ({party.ideology})")
    
    print("\n=== 对华对美立场 ===")
    for country_id in ["usa", "china", "russia", "japan", "germany", "france", "india", "uk", "australia"]:
        party = db.get_ruling_party(country_id)
        if party:
            china = party.stance_china
            usa = party.stance_usa
            print(f"  {country_id:12s}: 对华={china:+.1f} 对美={usa:+.1f}")
    
    print("\n=== 政治相似度 ===")
    pairs = [("usa", "uk"), ("usa", "germany"), ("usa", "france"), 
             ("china", "russia"), ("india", "russia")]
    for a, b in pairs:
        sim = db.get_political_similarity(a, b)
        print(f"  {a}-{b}: {sim['overall']:.2f} (外交:中美{sim['foreign_usa']:.2f} 中俄{sim['foreign_china']:.2f})")
    
    print("\n=== 合作潜力 ===")
    for a, b in pairs:
        potential = db.calculate_diplomatic_potential(a, b)
        print(f"  {a}-{b}: {potential:.2f}")
    
    print("\n=== 跨党际友好关系 ===")
    for party_id, friends in db.cross_border.items():
        party = db.get_party(party_id)
        if party:
            print(f"  {party.name_cn} ({party.country_id}):")
            for friend_id in friends[:3]:
                friend = db.get_party(friend_id)
                if friend:
                    print(f"    -> {friend.name_cn} ({friend.country_id})")
