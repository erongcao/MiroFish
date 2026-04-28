"""
US Political Forces - 美国政治势力模型
超越两党框架，建模军工复合体、华尔街、游说团体、智库等深层势力
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class ForceType(Enum):
    """势力类型"""
    MILITARY_INDUSTRIAL = "military_industrial"  # 军工复合体
    FINANCIAL = "financial"                        # 金融资本
    TECH = "tech"                                  # 科技巨头
    LOBBY = "lobby"                                # 游说团体
    ENERGY = "energy"                              # 能源集团
    LABOR = "labor"                                # 工会/劳工
    THINK_TANK = "think_tank"                      # 智库
    MEDIA = "media"                                # 媒体集团
    RELIGIOUS = "religious"                        # 宗教保守派
    GUN = "gun"                                    # 枪支游说
    ENVIRONMENTAL = "environmental"                # 环保组织
    ETHNIC = "ethnic"                              # 族裔游说
    AGRICULTURAL = "agricultural"                  # 农业利益
    PHARMA = "pharma"                              # 医药集团
    LAW_ENFORCEMENT = "law_enforcement"            # 执法/情报

class InfluenceLevel(Enum):
    """影响力等级"""
    DOMINANT = 0.9        # 主导
    STRONG = 0.7          # 强
    MODERATE = 0.5        # 中等
    WEAK = 0.3            # 弱
    MARGINAL = 0.1        # 边缘

@dataclass
class PoliticalForce:
    """政治势力"""
    force_id: str
    name: str
    name_cn: str
    force_type: str
    
    # 影响力
    overall_influence: float = 0.5  # 0-1
    
    # 对两党的影响力
    influence_democrat: float = 0.0  # -1到1
    influence_republican: float = 0.0
    
    # 对华立场
    stance_china: float = 0.0  # -1(敌对)到1(友好)
    
    # 对俄立场
    stance_russia: float = 0.0
    
    # 对中东立场
    stance_middle_east: float = 0.0
    
    # 核心诉求
    core_interests: List[str] = field(default_factory=list)
    
    # 关键人物/组织
    key_figures: List[str] = field(default_factory=list)
    key_organizations: List[str] = field(default_factory=list)
    
    # 资金规模 (年度游说支出/政治捐款，百万美元)
    annual_spending_millions: float = 0.0
    
    # 历史影响案例
    historical_impacts: List[str] = field(default_factory=list)
    
    # 与政党的关系
    party_alignment: str = ""  # "democrat", "republican", "bipartisan", "neutral"
    
    # 媒体影响力
    media_control: List[str] = field(default_factory=list)

# 美国主要政治势力数据库
US_POLITICAL_FORCES = {
    # ===== 军工复合体 =====
    "military_industrial": PoliticalForce(
        force_id="military_industrial",
        name="Military-Industrial Complex",
        name_cn="军工复合体",
        force_type="military_industrial",
        overall_influence=0.85,
        influence_democrat=0.6,
        influence_republican=0.8,
        stance_china=-0.7,  # 强烈对华强硬
        stance_russia=-0.9,
        stance_middle_east=-0.3,
        core_interests=[
            "维持高额国防预算",
            "推动对外军事干预",
            "遏制中俄军事崛起",
            "维持技术优势",
            "扩大武器出口",
        ],
        key_figures=["Lloyd Austin (国防部长)", "Mark Milley (前参联会主席)"],
        key_organizations=[
            "Lockheed Martin",
            "Boeing",
            "Raytheon",
            "Northrop Grumman",
            "General Dynamics",
            "BAE Systems",
        ],
        annual_spending_millions=150.0,  # 游说支出
        historical_impacts=[
            "推动伊拉克战争",
            "维持阿富汗战争20年",
            "推动对台军售",
            "推动印太战略",
        ],
        party_alignment="bipartisan",
        media_control=["Defense News", "Breaking Defense"],
    ),
    
    # ===== 华尔街/金融资本 =====
    "wall_street": PoliticalForce(
        force_id="wall_street",
        name="Wall Street / Financial Capital",
        name_cn="华尔街/金融资本",
        force_type="financial",
        overall_influence=0.90,
        influence_democrat=0.7,
        influence_republican=0.6,
        stance_china=0.2,  # 希望合作但竞争
        stance_russia=-0.5,
        stance_middle_east=0.0,
        core_interests=[
            "维持美元霸权",
            "开放中国市场",
            "避免金融脱钩",
            "维持低利率环境",
            "减少监管",
        ],
        key_figures=[
            "Jamie Dimon (摩根大通CEO)",
            "Larry Fink (贝莱德CEO)",
            "David Solomon (高盛CEO)",
        ],
        key_organizations=[
            "Goldman Sachs",
            "JPMorgan Chase",
            "BlackRock",
            "Citigroup",
            "Bank of America",
            "Federal Reserve",
            "SEC",
        ],
        annual_spending_millions=200.0,
        historical_impacts=[
            "推动金融自由化",
            "影响TPP谈判",
            "反对对华全面脱钩",
            "推动ESG投资",
        ],
        party_alignment="bipartisan",
        media_control=["Bloomberg", "CNBC", "Financial Times"],
    ),
    
    # ===== 科技巨头 =====
    "tech_giants": PoliticalForce(
        force_id="tech_giants",
        name="Tech Giants / Silicon Valley",
        name_cn="科技巨头/硅谷",
        force_type="tech",
        overall_influence=0.80,
        influence_democrat=0.8,
        influence_republican=0.4,
        stance_china=-0.3,  # 竞争但依赖市场
        stance_russia=-0.6,
        stance_middle_east=0.0,
        core_interests=[
            "维持全球数据控制",
            "进入中国市场",
            "反对数据本地化",
            "推动AI监管宽松",
            "维持H1B签证",
        ],
        key_figures=[
            "Sundar Pichai (Google)",
            "Tim Cook (Apple)",
            "Satya Nadella (Microsoft)",
            "Mark Zuckerberg (Meta)",
        ],
        key_organizations=[
            "Google/Alphabet",
            "Apple",
            "Microsoft",
            "Meta",
            "Amazon",
            "Netflix",
            "OpenAI",
        ],
        annual_spending_millions=120.0,
        historical_impacts=[
            "推动互联网自由",
            "影响TikTok禁令",
            "推动AI出口管制",
            "影响数字贸易规则",
        ],
        party_alignment="democrat",
        media_control=["YouTube", "Twitter/X", "Facebook", "Instagram"],
    ),
    
    # ===== 犹太游说团体 (AIPAC等) =====
    "pro_israel_lobby": PoliticalForce(
        force_id="pro_israel_lobby",
        name="Pro-Israel Lobby (AIPAC, etc.)",
        name_cn="亲以色列游说团体",
        force_type="lobby",
        overall_influence=0.75,
        influence_democrat=0.6,
        influence_republican=0.7,
        stance_china=-0.2,
        stance_russia=-0.3,
        stance_middle_east=-0.8,  # 强烈支持以色列
        core_interests=[
            "无条件支持以色列",
            "反对伊朗核计划",
            "推动中东和平进程",
            "维持美以特殊关系",
            "反对反犹主义",
        ],
        key_figures=[
            "Howard Kohr (AIPAC CEO)",
            "Ron Dermer (以色列驻美大使)",
        ],
        key_organizations=[
            "AIPAC",
            "ADL",
            "J Street",
            "Republican Jewish Coalition",
            "Democratic Majority for Israel",
        ],
        annual_spending_millions=80.0,
        historical_impacts=[
            "推动耶路撒冷使馆搬迁",
            "推动亚伯拉罕协议",
            "反对伊朗核协议(JCPOA)",
            "推动对以军事援助",
        ],
        party_alignment="bipartisan",
        media_control=["Jerusalem Post", "Times of Israel"],
    ),
    
    # ===== 能源/石油集团 =====
    "energy_oil": PoliticalForce(
        force_id="energy_oil",
        name="Energy / Oil Interests",
        name_cn="能源/石油集团",
        force_type="energy",
        overall_influence=0.65,
        influence_democrat=0.3,
        influence_republican=0.8,
        stance_china=-0.1,
        stance_russia=-0.6,
        stance_middle_east=0.3,
        core_interests=[
            "维持石油美元体系",
            "反对气候激进政策",
            "扩大页岩油开采",
            "控制中东石油",
            "反对俄罗斯能源",
        ],
        key_figures=[
            "Darren Woods (埃克森美孚CEO)",
            "Mike Wirth (雪佛龙CEO)",
        ],
        key_organizations=[
            "ExxonMobil",
            "Chevron",
            "API (美国石油学会)",
            "Koch Industries",
        ],
        annual_spending_millions=100.0,
        historical_impacts=[
            "反对巴黎气候协定",
            "推动Keystone XL管道",
            "影响中东政策",
            "反对俄罗斯能源进口",
        ],
        party_alignment="republican",
        media_control=["Oil Price", "Energy Central"],
    ),
    
    # ===== 工会/劳工组织 =====
    "labor_unions": PoliticalForce(
        force_id="labor_unions",
        name="Labor Unions",
        name_cn="工会/劳工组织",
        force_type="labor",
        overall_influence=0.50,
        influence_democrat=0.7,
        influence_republican=-0.3,
        stance_china=-0.4,  # 反对中国制造业竞争
        stance_russia=-0.2,
        stance_middle_east=0.0,
        core_interests=[
            "保护美国制造业就业",
            "反对自由贸易协定",
            "提高最低工资",
            "推动工会化",
            "反对外包",
        ],
        key_figures=[
            "Liz Shuler (AFL-CIO主席)",
            "Sean O'Brien (Teamsters主席)",
        ],
        key_organizations=[
            "AFL-CIO",
            "Teamsters",
            "UAW",
            "SEIU",
            "NEA",
        ],
        annual_spending_millions=60.0,
        historical_impacts=[
            "反对TPP",
            "推动Buy American",
            "影响对华贸易政策",
            "推动制造业回流",
        ],
        party_alignment="democrat",
        media_control=["Labor Press", "Union News"],
    ),
    
    # ===== 智库/思想库 =====
    "think_tanks": PoliticalForce(
        force_id="think_tanks",
        name="Think Tanks",
        name_cn="智库/思想库",
        force_type="think_tank",
        overall_influence=0.60,
        influence_democrat=0.5,
        influence_republican=0.5,
        stance_china=-0.5,
        stance_russia=-0.6,
        stance_middle_east=-0.2,
        core_interests=[
            "塑造政策辩论",
            "培养政策人才",
            "推动特定议程",
            "影响公共舆论",
        ],
        key_figures=[
            "John Mearsheimer (现实主义)",
            "Graham Allison (修昔底德陷阱)",
            "Kissinger (现实主义)",
        ],
        key_organizations=[
            "Brookings Institution",
            "Heritage Foundation",
            "CSIS",
            "CFR",
            "RAND Corporation",
            "AEI",
            "Cato Institute",
        ],
        annual_spending_millions=50.0,
        historical_impacts=[
            "推动对华遏制战略",
            "推动印太战略",
            "影响北约东扩",
            "推动民主推广",
        ],
        party_alignment="bipartisan",
        media_control=["Foreign Affairs", "Foreign Policy"],
    ),
    
    # ===== 媒体集团 =====
    "media_conglomerates": PoliticalForce(
        force_id="media_conglomerates",
        name="Media Conglomerates",
        name_cn="媒体集团",
        force_type="media",
        overall_influence=0.70,
        influence_democrat=0.6,
        influence_republican=0.5,
        stance_china=-0.4,
        stance_russia=-0.7,
        stance_middle_east=-0.2,
        core_interests=[
            "维持新闻自由",
            "扩大受众",
            "塑造对华叙事",
            "推动点击/收视率",
        ],
        key_figures=[
            "Rupert Murdoch (福克斯)",
            "Jeff Bezos (华盛顿邮报)",
        ],
        key_organizations=[
            "Fox Corporation",
            "CNN (Warner Bros)",
            "MSNBC (Comcast)",
            "Washington Post",
            "New York Times",
            "Wall Street Journal",
        ],
        annual_spending_millions=40.0,
        historical_impacts=[
            "推动对华负面叙事",
            "影响公众对华认知",
            "推动俄罗斯门事件",
            "影响选举舆论",
        ],
        party_alignment="bipartisan",
        media_control=["Fox News", "CNN", "MSNBC", "NYT", "WSJ"],
    ),
    
    # ===== 宗教保守派 =====
    "religious_right": PoliticalForce(
        force_id="religious_right",
        name="Religious Right / Evangelicals",
        name_cn="宗教保守派/福音派",
        force_type="religious",
        overall_influence=0.55,
        influence_democrat=-0.2,
        influence_republican=0.8,
        stance_china=-0.5,  # 宗教自由问题
        stance_russia=0.2,  # 东正教纽带
        stance_middle_east=-0.6,  # 支持以色列
        core_interests=[
            "反对堕胎",
            "维护传统婚姻",
            "宗教自由",
            "支持以色列",
            "反对世俗化",
        ],
        key_figures=[
            "Franklin Graham",
            "Jerry Falwell Jr.",
        ],
        key_organizations=[
            "Focus on the Family",
            "Family Research Council",
            "Christian Coalition",
        ],
        annual_spending_millions=30.0,
        historical_impacts=[
            "推动特朗普当选",
            "影响中东政策",
            "反对LGBT权利",
            "推动宗教自由议题",
        ],
        party_alignment="republican",
        media_control=["Christian Broadcasting Network"],
    ),
    
    # ===== 枪支游说 (NRA) =====
    "gun_lobby": PoliticalForce(
        force_id="gun_lobby",
        name="Gun Lobby (NRA)",
        name_cn="枪支游说 (NRA)",
        force_type="gun",
        overall_influence=0.45,
        influence_democrat=-0.4,
        influence_republican=0.9,
        stance_china=-0.2,
        stance_russia=0.1,
        stance_middle_east=0.0,
        core_interests=[
            "反对枪支管制",
            "扩大隐蔽持枪权",
            "反对背景调查",
            "维护第二修正案",
        ],
        key_figures=["Wayne LaPierre (NRA CEO)"],
        key_organizations=["NRA", "NSSF", "Gun Owners of America"],
        annual_spending_millions=25.0,
        historical_impacts=[
            "阻止枪支管制立法",
            "影响最高法院大法官任命",
        ],
        party_alignment="republican",
        media_control=["NRA TV"],
    ),
    
    # ===== 环保组织 =====
    "environmental": PoliticalForce(
        force_id="environmental",
        name="Environmental Movement",
        name_cn="环保运动",
        force_type="environmental",
        overall_influence=0.50,
        influence_democrat=0.6,
        influence_republican=-0.3,
        stance_china=0.1,  # 气候合作
        stance_russia=-0.3,
        stance_middle_east=-0.2,
        core_interests=[
            "推动绿色新政",
            "反对化石燃料",
            "推动碳中和",
            "保护自然资源",
        ],
        key_figures=["Greta Thunberg", "Al Gore"],
        key_organizations=[
            "Sierra Club",
            "NRDC",
            "Greenpeace",
            "350.org",
        ],
        annual_spending_millions=35.0,
        historical_impacts=[
            "推动巴黎气候协定",
            "反对Keystone XL",
            "推动清洁能源转型",
        ],
        party_alignment="democrat",
        media_control=["Grist", "Inside Climate News"],
    ),
    
    # ===== 拉丁裔/移民游说 =====
    "latino_immigrant": PoliticalForce(
        force_id="latino_immigrant",
        name="Latino / Immigrant Rights",
        name_cn="拉丁裔/移民权利",
        force_type="ethnic",
        overall_influence=0.40,
        influence_democrat=0.7,
        influence_republican=-0.5,
        stance_china=0.0,
        stance_russia=0.0,
        stance_middle_east=0.0,
        core_interests=[
            "移民改革",
            "DACA保护",
            "反对边境墙",
            "拉丁裔权益",
        ],
        key_figures=["Thomas Saenz (MALDEF)"],
        key_organizations=[
            "MALDEF",
            "National Latino Action",
            " UnidosUS",
        ],
        annual_spending_millions=20.0,
        historical_impacts=[
            "推动DACA",
            "影响移民政策",
            "推动拉丁裔投票",
        ],
        party_alignment="democrat",
        media_control=["Univision", "Telemundo"],
    ),
    
    # ===== 医药/医保集团 =====
    "pharma_healthcare": PoliticalForce(
        force_id="pharma_healthcare",
        name="Pharma / Healthcare",
        name_cn="医药/医保集团",
        force_type="pharma",
        overall_influence=0.60,
        influence_democrat=0.4,
        influence_republican=0.5,
        stance_china=-0.1,  # 供应链依赖
        stance_russia=-0.2,
        stance_middle_east=0.0,
        core_interests=[
            "反对药品价格管制",
            "保护专利",
            "维持高药价",
            "反对全民医保",
        ],
        key_figures=[
            "Albert Bourla (辉瑞CEO)",
            "Alex Gorsky (强生前CEO)",
        ],
        key_organizations=[
            "PhRMA",
            "BIO",
            "Pfizer",
            "Johnson & Johnson",
            "Merck",
        ],
        annual_spending_millions=90.0,
        historical_impacts=[
            "阻止药品价格谈判",
            "推动COVID疫苗",
            "影响医保政策",
        ],
        party_alignment="bipartisan",
        media_control=["Medical News"],
    ),
    
    # ===== 情报/执法机构 =====
    "intelligence_law_enforcement": PoliticalForce(
        force_id="intelligence_law_enforcement",
        name="Intelligence / Law Enforcement",
        name_cn="情报/执法机构",
        force_type="law_enforcement",
        overall_influence=0.70,
        influence_democrat=0.5,
        influence_republican=0.6,
        stance_china=-0.8,  # 强烈对华敌对
        stance_russia=-0.9,
        stance_middle_east=-0.4,
        core_interests=[
            "扩大监控权力",
            "反恐",
            "反间谍",
            "网络安全",
            "维持预算",
        ],
        key_figures=[
            "William Burns (CIA局长)",
            "Christopher Wray (FBI局长)",
        ],
        key_organizations=[
            "CIA",
            "FBI",
            "NSA",
            "DHS",
            "DOD Intelligence",
        ],
        annual_spending_millions=10.0,  # 直接游说较少
        historical_impacts=[
            "推动对华技术封锁",
            "推动俄罗斯制裁",
            "推动反恐战争",
            "影响华为禁令",
        ],
        party_alignment="bipartisan",
        media_control=["Intelligence Community"],
    ),
}


class USPoliticalForcesModel:
    """美国政治势力模型"""
    
    def __init__(self):
        self.forces = US_POLITICAL_FORCES
    
    def get_force(self, force_id: str) -> Optional[PoliticalForce]:
        """获取特定势力"""
        return self.forces.get(force_id)
    
    def get_all_forces(self) -> List[PoliticalForce]:
        """获取所有势力"""
        return list(self.forces.values())
    
    def get_forces_by_type(self, force_type: str) -> List[PoliticalForce]:
        """按类型获取势力"""
        return [f for f in self.forces.values() if f.force_type == force_type]
    
    def get_forces_by_party_alignment(self, alignment: str) -> List[PoliticalForce]:
        """按政党倾向获取势力"""
        return [f for f in self.forces.values() if f.party_alignment == alignment]
    
    def calculate_composite_stance(self, target: str, 
                                   party_weights: Dict[str, float] = None) -> float:
        """计算复合立场（考虑所有势力）"""
        if party_weights is None:
            party_weights = {"democrat": 0.5, "republican": 0.5}
        
        total_weight = 0.0
        weighted_stance = 0.0
        
        for force in self.forces.values():
            # 根据政党权重计算势力影响力
            if force.party_alignment == "democrat":
                weight = party_weights.get("democrat", 0.5) * force.overall_influence
            elif force.party_alignment == "republican":
                weight = party_weights.get("republican", 0.5) * force.overall_influence
            else:
                weight = force.overall_influence
            
            stance = getattr(force, f"stance_{target}", 0.0)
            weighted_stance += stance * weight
            total_weight += weight
        
        return weighted_stance / total_weight if total_weight > 0 else 0.0
    
    def get_influential_forces_on_party(self, party: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """获取对特定政党最具影响力的势力"""
        forces = []
        for force in self.forces.values():
            influence = getattr(force, f"influence_{party}", 0.0)
            forces.append((force.name_cn, influence))
        
        forces.sort(key=lambda x: x[1], reverse=True)
        return forces[:top_n]
    
    def simulate_policy_shift(self, 
                              winning_party: str,
                              force_changes: Dict[str, float] = None) -> Dict:
        """模拟政党轮替后的政策变化"""
        if force_changes is None:
            force_changes = {}
        
        # 基础立场变化
        base_shift = {
            "democrat": {"china": 0.2, "russia": 0.1, "middle_east": 0.0},
            "republican": {"china": -0.3, "russia": -0.2, "middle_east": -0.1},
        }
        
        shift = base_shift.get(winning_party, {})
        
        # 考虑势力变化
        for force_id, change in force_changes.items():
            force = self.forces.get(force_id)
            if force:
                for target in ["china", "russia", "middle_east"]:
                    stance = getattr(force, f"stance_{target}", 0.0)
                    shift[target] = shift.get(target, 0.0) + stance * change * 0.1
        
        return {
            "winning_party": winning_party,
            "stance_changes": shift,
            "affected_forces": list(force_changes.keys()),
        }
    
    def get_conflict_drivers(self, target: str) -> List[Tuple[str, float]]:
        """获取推动对特定目标冲突的主要势力"""
        drivers = []
        for force in self.forces.values():
            stance = getattr(force, f"stance_{target}", 0.0)
            if stance < -0.3:  # 敌对立场
                drivers.append((force.name_cn, stance, force.overall_influence))
        
        # 按影响力排序
        drivers.sort(key=lambda x: x[2], reverse=True)
        return [(d[0], d[1]) for d in drivers]
    
    def get_cooperation_drivers(self, target: str) -> List[Tuple[str, float]]:
        """获取推动对特定目标合作的主要势力"""
        drivers = []
        for force in self.forces.values():
            stance = getattr(force, f"stance_{target}", 0.0)
            if stance > 0.2:  # 友好立场
                drivers.append((force.name_cn, stance, force.overall_influence))
        
        drivers.sort(key=lambda x: x[2], reverse=True)
        return [(d[0], d[1]) for d in drivers]
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "total_forces": len(self.forces),
            "forces": [
                {
                    "force_id": f.force_id,
                    "name": f.name_cn,
                    "type": f.force_type,
                    "influence": f.overall_influence,
                    "stance_china": f.stance_china,
                    "stance_russia": f.stance_russia,
                    "party_alignment": f.party_alignment,
                    "annual_spending": f.annual_spending_millions,
                }
                for f in self.forces.values()
            ]
        }


# 全局实例
us_forces = USPoliticalForcesModel()

if __name__ == "__main__":
    model = USPoliticalForcesModel()
    
    print("=== 美国政治势力模型测试 ===\n")
    
    # 所有势力
    print("美国主要政治势力:")
    for force in model.get_all_forces():
        print(f"  {force.name_cn:20s} | 影响力: {force.overall_influence:.1f} | "
              f"对华: {force.stance_china:+.1f} | 对俄: {force.stance_russia:+.1f} | "
              f"党派: {force.party_alignment}")
    
    print("\n=== 复合对华立场 ===")
    # 假设民主党执政
    dem_stance = model.calculate_composite_stance("china", {"democrat": 0.7, "republican": 0.3})
    print(f"民主党执政下: {dem_stance:+.2f}")
    
    # 假设共和党执政
    rep_stance = model.calculate_composite_stance("china", {"democrat": 0.3, "republican": 0.7})
    print(f"共和党执政下: {rep_stance:+.2f}")
    
    print("\n=== 对民主党最具影响力的势力 ===")
    for name, influence in model.get_influential_forces_on_party("democrat", 5):
        print(f"  {name}: {influence:+.2f}")
    
    print("\n=== 对共和党最具影响力的势力 ===")
    for name, influence in model.get_influential_forces_on_party("republican", 5):
        print(f"  {name}: {influence:+.2f}")
    
    print("\n=== 推动对华冲突的势力 ===")
    for name, stance in model.get_conflict_drivers("china"):
        print(f"  {name}: {stance:+.2f}")
    
    print("\n=== 推动对华合作的势力 ===")
    for name, stance in model.get_cooperation_drivers("china"):
        print(f"  {name}: {stance:+.2f}")
    
    print("\n=== 模拟政党轮替 ===")
    shift = model.simulate_policy_shift("republican")
    print(f"共和党胜选后对华立场变化: {shift['stance_changes']['china']:+.2f}")
    print(f"对俄立场变化: {shift['stance_changes']['russia']:+.2f}")
