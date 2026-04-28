"""
China Political Forces - 中国政治势力模型
建模党内派系、军方、金融资本、民营资本等深层势力
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class ChinaPoliticalForce:
    """中国政治势力"""
    force_id: str
    name: str
    name_cn: str
    
    # 影响力 (0-1)
    overall_influence: float = 0.5
    
    # 对习近平的影响力
    influence_xi: float = 0.0
    
    # 意识形态倾向
    ideology: str = ""  # "reformist", "conservative", "nationalist", "pragmatic"
    
    # 对外立场
    stance_usa: float = 0.0
    stance_russia: float = 0.0
    stance_taiwan: float = 0.0  # 统一问题
    stance_west: float = 0.0
    
    # 核心诉求
    core_interests: List[str] = field(default_factory=list)
    
    # 关键人物
    key_figures: List[str] = field(default_factory=list)
    
    # 与习近平/党中央关系
    party_relation: str = ""  # "loyal", "independent", "competing"

# 中国主要政治势力
CHINA_POLITICAL_FORCES = {
    # ===== 军方/红二代 =====
    "military_red": ChinaPoliticalForce(
        force_id="military_red",
        name="Military / Red Aristocracy",
        name_cn="军方/红二代",
        overall_influence=0.85,
        influence_xi=0.7,
        ideology="nationalist",
        stance_usa=-0.8,
        stance_russia=0.6,
        stance_taiwan=0.9,  # 统一立场强硬
        stance_west=-0.6,
        core_interests=[
            "加速强军",
            "统一台湾",
            "维护南海主权",
            "反对美帝围堵",
            "扩军备战",
        ],
        key_figures=[
            "习近平 (军委主席)",
            "李尚福 (前防长/落马)",
            "魏凤和 (前防长)",
            "董军 (防长)",
        ],
        party_relation="loyal",
    ),
    
    # ===== 安全部门 =====
    "security": ChinaPoliticalForce(
        force_id="security",
        name="Security / Intelligence",
        name_cn="安全部门",
        overall_influence=0.80,
        influence_xi=0.8,
        ideology="conservative",
        stance_usa=-0.9,
        stance_russia=0.4,
        stance_taiwan=0.8,
        stance_west=-0.7,
        core_interests=[
            "维护政权安全",
            "网络主权",
            "意识形态安全",
            "反间谍",
            "社会控制",
        ],
        key_figures=[
            "陈一新 (政法委书记)",
            "王小洪 (公安部长)",
        ],
        party_relation="loyal",
    ),
    
    # ===== 改革派/市场派 =====
    "reformists": ChinaPoliticalForce(
        force_id="reformists",
        name="Reformists / Market Forces",
        name_cn="改革派/市场派",
        overall_influence=0.50,
        influence_xi=0.3,
        ideology="reformist",
        stance_usa=0.2,  # 希望合作
        stance_russia=0.1,
        stance_taiwan=0.3,  # 温和统一
        stance_west=0.3,
        core_interests=[
            "深化改革开放",
            "市场经济",
            "与西方合作",
            "技术引进",
            "融入全球经济",
        ],
        key_figures=[
            "李强 (总理)",
            "丁薛祥 (常务副总理)",
            "何立峰 (副总理)",
        ],
        party_relation="pragmatic",
    ),
    
    # ===== 国企/央企派 =====
    "soe_elites": ChinaPoliticalForce(
        force_id="soe_elites",
        name="SOE Elites / State Capital",
        name_cn="国企/央企派",
        overall_influence=0.70,
        influence_xi=0.5,
        ideology="pragmatic",
        stance_usa=-0.3,
        stance_russia=0.4,
        stance_taiwan=0.5,
        stance_west=-0.2,
        core_interests=[
            "做大做强国企",
            "国内市场保护",
            "一带一路战略",
            "双循环战略",
            "关键技术自主",
        ],
        key_figures=[
            "刘鹤 (政协主席/前副总理)",
            "肖捷 (财政部长)",
        ],
        party_relation="pragmatic",
    ),
    
    # ===== 民企/科技资本 =====
    "private_capital": ChinaPoliticalForce(
        force_id="private_capital",
        name="Private Capital / Tech Elite",
        name_cn="民企/科技资本",
        overall_influence=0.60,
        influence_xi=0.2,
        ideology="reformist",
        stance_usa=0.4,  # 希望开放
        stance_russia=-0.2,
        stance_taiwan=0.0,
        stance_west=0.4,
        core_interests=[
            "反垄断松绑",
            "进入国际市场",
            "技术突破",
            "宽松监管",
            "资本家权益保护",
        ],
        key_figures=[
            "马云 (阿里/已低调)",
            "马化腾 (腾讯)",
            "张一鸣 (字节)",
            "王传福 (比亚迪)",
            "任正非 (华为)",
        ],
        party_relation="independent",
    ),
    
    # ===== 外交系统 =====
    "diplomats": ChinaPoliticalForce(
        force_id="diplomats",
        name="Diplomatic System",
        name_cn="外交系统",
        overall_influence=0.55,
        influence_xi=0.6,
        ideology="pragmatic",
        stance_usa=-0.5,
        stance_russia=0.7,
        stance_taiwan=0.6,
        stance_west=-0.3,
        core_interests=[
            "大国外交",
            "上合组织/金砖",
            "不结盟",
            "多极世界",
            "避免直接对抗",
        ],
        key_figures=[
            "王毅 (外长)",
            "马朝旭 (副外长)",
        ],
        party_relation="loyal",
    ),
    
    # ===== 文宣系统 =====
    "propaganda": ChinaPoliticalForce(
        force_id="propaganda",
        name="Propaganda / Ideological System",
        name_cn="文宣系统",
        overall_influence=0.65,
        influence_xi=0.7,
        ideology="conservative",
        stance_usa=-0.7,
        stance_russia=0.5,
        stance_taiwan=0.8,
        stance_west=-0.6,
        core_interests=[
            "意识形态安全",
            "舆论引导",
            "民族主义宣传",
            "历史叙事",
            "文化自信",
        ],
        key_figures=[
            "李书磊 (宣传部长)",
            "慎海雄 (新华社社长)",
        ],
        party_relation="loyal",
    ),
    
    # ===== 太子党/权贵 =====
    "princelings": ChinaPoliticalForce(
        force_id="princelings",
        name="Princelings / Red Families",
        name_cn="太子党/权贵家族",
        overall_influence=0.70,
        influence_xi=0.6,
        ideology="nationalist",
        stance_usa=-0.6,
        stance_russia=0.6,
        stance_taiwan=0.8,
        stance_west=-0.5,
        core_interests=[
            "家族利益保护",
            "红色江山永续",
            "反和平演变",
            "维护特权",
            "强大国家",
        ],
        key_figures=[
            "习近平",
            "王岐山 (国家副主席)",
            "刘鹤",
        ],
        party_relation="loyal",
    ),
    
    # ===== 民族主义/战狼派 =====
    "nationalist_wolf warriors": ChinaPoliticalForce(
        force_id="nationalist_wolf warriors",
        name="Nationalists / Wolf Warriors",
        name_cn="民族主义/战狼派",
        overall_influence=0.45,
        influence_xi=0.4,
        ideology="nationalist",
        stance_usa=-0.9,
        stance_russia=0.3,
        stance_taiwan=0.9,
        stance_west=-0.8,
        core_interests=[
            "强硬外交",
            "反美帝",
            "武统台湾",
            "历史仇恨教育",
            "抵制西方",
        ],
        key_figures=[
            "胡锡进 (环时总编)",
            "金灿荣 (鹰派学者)",
            "戴旭 (鹰派)",
        ],
        party_relation="independent",
    ),
    
    # ===== 地方官员 =====
    "local_officials": ChinaPoliticalForce(
        force_id="local_officials",
        name="Local Officials / Provincial Elite",
        name_cn="地方官员/诸侯",
        overall_influence=0.55,
        influence_xi=0.3,
        ideology="pragmatic",
        stance_usa=0.0,
        stance_russia=0.2,
        stance_taiwan=0.4,
        stance_west=0.1,
        core_interests=[
            "经济增长政绩",
            "招商引资",
            "地方保护",
            "对上负责",
            "回避风险",
        ],
        key_figures=[
            "各省市自治区党委书记",
            "长三角/珠三角书记",
        ],
        party_relation="pragmatic",
    ),
}


class ChinaPoliticalForcesModel:
    """中国政治势力模型"""
    
    def __init__(self):
        self.forces = CHINA_POLITICAL_FORCES
    
    def get_force(self, force_id: str) -> Optional[ChinaPoliticalForce]:
        return self.forces.get(force_id)
    
    def get_all_forces(self) -> List[ChinaPoliticalForce]:
        return list(self.forces.values())
    
    def get_forces_by_ideology(self, ideology: str) -> List[ChinaPoliticalForce]:
        return [f for f in self.forces.values() if f.ideology == ideology]
    
    def get_forces_by_party_relation(self, relation: str) -> List[ChinaPoliticalForce]:
        return [f for f in self.forces.values() if f.party_relation == relation]
    
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
        """获取推动冲突的主要势力"""
        drivers = []
        for force in self.forces.values():
            stance = getattr(force, f"stance_{target}", 0.0)
            if stance < -0.3:
                drivers.append((force.name_cn, stance, force.overall_influence))
        drivers.sort(key=lambda x: x[2], reverse=True)
        return [(d[0], d[1]) for d in drivers]
    
    def get_cooperation_drivers(self, target: str) -> List[tuple]:
        """获取推动合作的主要势力"""
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
                    "ideology": f.ideology,
                    "stance_usa": f.stance_usa,
                    "stance_russia": f.stance_russia,
                    "party_relation": f.party_relation,
                }
                for f in self.forces.values()
            ]
        }


# 全局实例
china_forces = ChinaPoliticalForcesModel()

if __name__ == "__main__":
    model = ChinaPoliticalForcesModel()
    
    print("=== 中国政治势力模型 ===\n")
    
    print("主要政治势力:")
    for force in model.get_all_forces():
        print(f"  {force.name_cn:20s} | 影响力: {force.overall_influence:.1f} | "
              f"意识形态: {force.ideology:12s} | 对美: {force.stance_usa:+.1f}")
    
    print("\n=== 复合立场 ===")
    for target in ["usa", "russia", "taiwan", "west"]:
        stance = model.calculate_composite_stance(target)
        print(f"对{target}: {stance:+.2f}")
    
    print("\n=== 推动反美的势力 ===")
    for name, stance in model.get_conflict_drivers("usa"):
        print(f"  {name}: {stance:+.2f}")
    
    print("\n=== 推动对美合作的势力 ===")
    for name, stance in model.get_cooperation_drivers("usa"):
        print(f"  {name}: {stance:+.2f}")
    
    print("\n=== 按意识形态分类 ===")
    for ideology in ["reformist", "conservative", "nationalist", "pragmatic"]:
        forces = model.get_forces_by_ideology(ideology)
        if forces:
            print(f"\n{ideology}:")
            for f in forces:
                print(f"  {f.name_cn}")
