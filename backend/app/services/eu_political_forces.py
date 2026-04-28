"""
EU Political Forces - 欧盟政治势力模型
建模法德轴心、军工复合体、华尔街（欧洲）、绿党、民族主义者等
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class EUPoliticalForce:
    """欧盟政治势力"""
    force_id: str
    name: str
    name_cn: str
    
    # 影响力 (0-1)
    overall_influence: float = 0.5
    
    # 主要影响的国家
    primary_countries: List[str] = field(default_factory=list)
    
    # 对外立场
    stance_usa: float = 0.0
    stance_china: float = 0.0
    stance_russia: float = 0.0
    
    # 核心诉求
    core_interests: List[str] = field(default_factory=list)
    
    # 关键组织
    key_organizations: List[str] = field(default_factory=list)
    
    # 政党倾向
    party_alignment: str = ""  # "pro_eu", "eurosceptic", "sovereignist"

# 欧盟主要政治势力
EU_POLITICAL_FORCES = {
    # ===== 法德轴心 =====
    "france_germany_axis": EUPoliticalForce(
        force_id="france_germany_axis",
        name="Franco-German Axis",
        name_cn="法德轴心",
        overall_influence=0.85,
        primary_countries=["france", "germany"],
        stance_usa=0.4,  # 盟友但有分歧
        stance_china=-0.2,  # 竞争但合作
        stance_russia=-0.5,  # 制裁但对话
        core_interests=[
            "欧洲一体化",
            "欧洲战略自主",
            "欧元稳定",
            "规范制定",
            "多边主义",
        ],
        key_organizations=[
            "法德部长理事会",
            "空中客车",
            "法德TV5 Monde",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 欧洲军工复合体 =====
    "eu_military_industrial": EUPoliticalForce(
        force_id="eu_military_industrial",
        name="EU Military-Industrial Complex",
        name_cn="欧洲军工复合体",
        overall_influence=0.65,
        primary_countries=["france", "germany", "italy", "spain"],
        stance_usa=-0.1,  # 既合作又竞争
        stance_china=-0.4,
        stance_russia=-0.3,
        core_interests=[
            "欧洲防务独立",
            "武器出口",
            "维持北约但增强自主",
            "军费增加",
            "国防工业整合",
        ],
        key_organizations=[
            "Airbus Defence & Space",
            "Thales (法国)",
            "Leonardo (意大利)",
            "KNDS (法德)",
            "BAE Systems (英)",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 欧洲金融资本 =====
    "eu_financial_capital": EUPoliticalForce(
        force_id="eu_financial_capital",
        name="European Financial Capital",
        name_cn="欧洲金融资本",
        overall_influence=0.75,
        primary_countries=["uk", "germany", "france", "luxembourg", "netherlands"],
        stance_usa=0.3,
        stance_china=0.3,  # 希望进入中国市场
        stance_russia=-0.2,
        core_interests=[
            "伦敦金融城",
            "欧元国际化",
            "开放市场",
            "金融服务出口",
            "金融监管协调",
        ],
        key_organizations=[
            "伦敦金融城",
            "德意志银行",
            "汇丰银行",
            "法国巴黎银行",
            "欧洲央行",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 绿党/气候派 =====
    "green_climate": EUPoliticalForce(
        force_id="green_climate",
        name="Green / Climate Movement",
        name_cn="绿党/气候派",
        overall_influence=0.55,
        primary_countries=["germany", "france", "netherlands", "scandinavia"],
        stance_usa=0.5,
        stance_china=-0.2,  # 气候合作但人权关切
        stance_russia=-0.3,
        core_interests=[
            "碳中和",
            "绿色新政",
            "可再生能源",
            "气候外交",
            "ESG标准",
        ],
        key_organizations=[
            "欧洲绿党",
            "德国绿党",
            "绿色和平",
            "欧洲气候组织",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 民族主义者/疑欧派 =====
    "nationalists_eurosceptics": EUPoliticalForce(
        force_id="nationalists_eurosceptics",
        name="Nationalists / Eurosceptics",
        name_cn="民族主义者/疑欧派",
        overall_influence=0.50,
        primary_countries=["france", "italy", "hungary", "poland", "czech"],
        stance_usa=0.3,
        stance_china=0.0,
        stance_russia=0.3,  # 亲俄倾向
        core_interests=[
            "反对欧盟集权",
            "保护本国利益",
            "限制移民",
            "主权优先",
            "反对联邦欧洲",
        ],
        key_organizations=[
            "法国国民联盟",
            "意大利联盟党",
            "匈牙利青民盟",
            "波兰法律与公正党",
            "捷克ANO",
        ],
        party_alignment="eurosceptic",
    ),
    
    # ===== 欧洲科技巨头 =====
    "eu_tech_giants": EUPoliticalForce(
        force_id="eu_tech_giants",
        name="European Tech Giants",
        name_cn="欧洲科技巨头",
        overall_influence=0.50,
        primary_countries=["germany", "france", "netherlands", "sweden"],
        stance_usa=-0.3,  # 反垄断
        stance_china=-0.2,
        stance_russia=0.0,
        core_interests=[
            "数字主权",
            "数据保护",
            "反美国科技霸权",
            "AI监管领导",
            "进入中国市场",
        ],
        key_organizations=[
            "ASML (荷兰)",
            "SAP (德国)",
            "安谋 (英国)",
            "爱立信 (瑞典)",
            "Spotify (瑞典)",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 亲美大西洋派 =====
    "atlanticists": EUPoliticalForce(
        force_id="atlanticists",
        name="Atlanticist / Pro-American",
        name_cn="大西洋主义者/亲美派",
        overall_influence=0.60,
        primary_countries=["poland", "uk", "baltics", "romania"],
        stance_usa=0.9,
        stance_china=-0.6,
        stance_russia=-0.9,
        core_interests=[
            "北约优先",
            "美国安全保障",
            "抗俄援乌",
            "情报合作",
            "反对欧洲战略自主过快",
        ],
        key_organizations=[
            "波兰政府",
            "英国政府",
            "北约",
            "美国大使馆",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 欧洲工会/劳工 =====
    "eu_labor": EUPoliticalForce(
        force_id="eu_labor",
        name="European Labor Unions",
        name_cn="欧洲工会/劳工",
        overall_influence=0.40,
        primary_countries=["germany", "france", "italy", "spain"],
        stance_usa=0.2,
        stance_china=-0.3,  # 中国竞争
        stance_russia=-0.2,
        core_interests=[
            "工人权益",
            "反对外包",
            "最低工资",
            "贸易保护",
            "就业保障",
        ],
        key_organizations=[
            "欧洲工会联合会",
            "德国工会联合会(DGB)",
            "法国总工会(CGT)",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 欧洲农业利益 =====
    "eu_agriculture": EUPoliticalForce(
        force_id="eu_agriculture",
        name="European Agricultural Lobby",
        name_cn="欧洲农业利益",
        overall_influence=0.45,
        primary_countries=["france", "spain", "italy", "poland"],
        stance_usa=-0.3,
        stance_china=-0.2,
        stance_russia=-0.1,
        core_interests=[
            "共同农业政策",
            "农业补贴",
            "食品安全",
            "保护农民",
            "反对转基因",
        ],
        key_organizations=[
            "欧盟农民协会(COPA)",
            "法国农民协会(FNSEA)",
        ],
        party_alignment="pro_eu",
    ),
    
    # ===== 主权主义者 =====
    "sovereignists": EUPoliticalForce(
        force_id="sovereignists",
        name="Sovereignists",
        name_cn="主权主义者",
        overall_influence=0.45,
        primary_countries=["france", "italy", "hungary", "czech"],
        stance_usa=0.0,
        stance_china=0.1,
        stance_russia=0.4,
        core_interests=[
            "民族主权",
            "欧盟改革非联邦化",
            "反对布鲁塞尔官僚",
            "灵活合作",
            "多极世界",
        ],
        key_organizations=[
            "法国重建欧洲",
            "意大利五星运动",
        ],
        party_alignment="sovereignist",
    ),
}


class EUPoliticalForcesModel:
    """欧盟政治势力模型"""
    
    def __init__(self):
        self.forces = EU_POLITICAL_FORCES
    
    def get_force(self, force_id: str) -> Optional[EUPoliticalForce]:
        return self.forces.get(force_id)
    
    def get_all_forces(self) -> List[EUPoliticalForce]:
        return list(self.forces.values())
    
    def get_forces_by_alignment(self, alignment: str) -> List[EUPoliticalForce]:
        return [f for f in self.forces.values() if f.party_alignment == alignment]
    
    def calculate_composite_stance(self, target: str) -> float:
        """计算复合立场"""
        total_weight = 0.0
        weighted_stance = 0.0
        
        for force in self.forces.values():
            weight = force.overall_influence
            stance = getattr(force, f"stance_{target}", 0.0)
            weighted_stance += stance * weight
            total_weight += weight
        
        return weighted_stance / total_weight if total_weight > 0 else 0.0
    
    def get_conflict_drivers(self, target: str) -> List[tuple]:
        drivers = []
        for force in self.forces.values():
            stance = getattr(force, f"stance_{target}", 0.0)
            if stance < -0.3:
                drivers.append((force.name_cn, stance, force.overall_influence))
        drivers.sort(key=lambda x: x[2], reverse=True)
        return [(d[0], d[1]) for d in drivers]
    
    def get_cooperation_drivers(self, target: str) -> List[tuple]:
        drivers = []
        for force in self.forces.values():
            stance = getattr(force, f"stance_{target}", 0.0)
            if stance > 0.2:
                drivers.append((force.name_cn, stance, force.overall_influence))
        drivers.sort(key=lambda x: x[2], reverse=True)
        return [(d[0], d[1]) for d in drivers]
    
    def to_dict(self) -> Dict:
        return {
            "total_forces": len(self.forces),
            "forces": [
                {
                    "force_id": f.force_id,
                    "name": f.name_cn,
                    "influence": f.overall_influence,
                    "stance_usa": f.stance_usa,
                    "stance_china": f.stance_china,
                    "stance_russia": f.stance_russia,
                    "alignment": f.party_alignment,
                }
                for f in self.forces.values()
            ]
        }


# 全局实例
eu_forces = EUPoliticalForcesModel()

if __name__ == "__main__":
    model = EUPoliticalForcesModel()
    
    print("=== 欧盟政治势力模型 ===\n")
    
    print("主要政治势力:")
    for force in model.get_all_forces():
        print(f"  {force.name_cn:20s} | 影响力: {force.overall_influence:.1f} | "
              f"对美: {force.stance_usa:+.1f} | 对华: {force.stance_china:+.1f} | "
              f"对俄: {force.stance_russia:+.1f}")
    
    print("\n=== 复合立场 ===")
    for target in ["usa", "china", "russia"]:
        stance = model.calculate_composite_stance(target)
        print(f"对{target}: {stance:+.2f}")
    
    print("\n=== 按立场分类 ===")
    for alignment in ["pro_eu", "eurosceptic", "sovereignist"]:
        forces = model.get_forces_by_alignment(alignment)
        if forces:
            print(f"\n{alignment}:")
            for f in forces:
                print(f"  {f.name_cn}")
    
    print("\n=== 推动对华强硬的势力 ===")
    for name, stance in model.get_conflict_drivers("china"):
        print(f"  {name}: {stance:+.2f}")
    
    print("\n=== 推动对华合作的势力 ===")
    for name, stance in model.get_cooperation_drivers("china"):
        print(f"  {name}: {stance:+.2f}")
