"""
Russia Political Forces - 俄罗斯政治势力模型
超越统一俄罗斯党，建模寡头、安全部门、军工业、东正教等深层势力
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class RussiaPoliticalForce:
    """俄罗斯政治势力"""
    force_id: str
    name: str
    name_cn: str
    
    # 影响力 (0-1)
    overall_influence: float = 0.5
    
    # 对普京/统一俄罗斯党的影响力
    influence_putin: float = 0.0
    
    # 对外立场
    stance_west: float = 0.0      # 对西方 (-1敌对到1友好)
    stance_china: float = 0.0     # 对中国
    stance_cis: float = 0.0       # 对独联体/前苏联国家
    
    # 核心诉求
    core_interests: List[str] = field(default_factory=list)
    
    # 关键人物
    key_figures: List[str] = field(default_factory=list)
    
    # 与普京关系
    putin_relation: str = ""  # "loyal", "independent", "oppositional", "pragmatic"

# 俄罗斯主要政治势力
RUSSIA_POLITICAL_FORCES = {
    # ===== 安全部门/ siloviki =====
    "siloviki": RussiaPoliticalForce(
        force_id="siloviki",
        name="Siloviki (Security Services)",
        name_cn="强力部门/西罗维基",
        overall_influence=0.90,
        influence_putin=0.8,
        stance_west=-0.9,
        stance_china=0.3,
        stance_cis=0.5,
        core_interests=[
            "维持国家安全控制",
            "扩大情报权力",
            "反西方渗透",
            "控制信息空间",
            "维持军事优势",
        ],
        key_figures=[
            "Sergey Shoigu (国防部长)",
            "Sergey Lavrov (外长)",
            "Nikolai Patrushev (安全会议秘书)",
            "Alexander Bortnikov (FSB局长)",
            "Sergey Naryshkin (对外情报局长)",
        ],
        putin_relation="loyal",
    ),
    
    # ===== 寡头/金融资本 =====
    "oligarchs": RussiaPoliticalForce(
        force_id="oligarchs",
        name="Oligarchs / Business Elite",
        name_cn="寡头/商业精英",
        overall_influence=0.70,
        influence_putin=0.4,
        stance_west=-0.2,  # 受制裁影响但希望缓和
        stance_china=0.5,
        stance_cis=0.3,
        core_interests=[
            "保护海外资产",
            "避免更多制裁",
            "维持贸易通道",
            "进入中国市场",
            "维持国内垄断",
        ],
        key_figures=[
            "Gennady Timchenko (石油贸易)",
            "Arkady Rotenberg (建筑/能源)",
            "Yuri Kovalchuk (银行/媒体)",
            "Suleiman Kerimov (矿业)",
        ],
        putin_relation="pragmatic",
    ),
    
    # ===== 军工业 =====
    "military_industrial": RussiaPoliticalForce(
        force_id="military_industrial",
        name="Military-Industrial Complex",
        name_cn="军工复合体",
        overall_influence=0.75,
        influence_putin=0.7,
        stance_west=-0.8,
        stance_china=0.4,
        stance_cis=0.6,
        core_interests=[
            "扩大国防预算",
            "推动武器出口",
            "维持技术优势",
            "乌克兰战争继续",
            "对抗北约扩张",
        ],
        key_figures=[
            "Sergey Chemezov (Rostec CEO)",
            "Alexei Rakhmanov (联合造船)",
        ],
        putin_relation="loyal",
    ),
    
    # ===== 能源集团 =====
    "energy_sector": RussiaPoliticalForce(
        force_id="energy_sector",
        name="Energy Sector (Gazprom, Rosneft)",
        name_cn="能源集团 (俄气/俄油)",
        overall_influence=0.80,
        influence_putin=0.6,
        stance_west=-0.3,  # 需要欧洲市场
        stance_china=0.7,  # 转向东方
        stance_cis=0.4,
        core_interests=[
            "维持能源出口",
            "建设对华管道",
            "控制欧洲能源",
            "维持高油价",
            "避免全面脱钩",
        ],
        key_figures=[
            "Alexei Miller (Gazprom CEO)",
            "Igor Sechin (Rosneft CEO)",
        ],
        putin_relation="loyal",
    ),
    
    # ===== 东正教会 =====
    "orthodox_church": RussiaPoliticalForce(
        force_id="orthodox_church",
        name="Russian Orthodox Church",
        name_cn="俄罗斯东正教会",
        overall_influence=0.50,
        influence_putin=0.5,
        stance_west=-0.4,  # 反自由主义
        stance_china=0.2,
        stance_cis=0.6,  # 保护东正教兄弟
        core_interests=[
            "维护传统价值观",
            "反对LGBT",
            "保护乌克兰教会",
            "扩大宗教影响",
            "支持保守主义",
        ],
        key_figures=[
            "Patriarch Kirill (大牧首)",
        ],
        putin_relation="loyal",
    ),
    
    # ===== 民族主义/皇俄派 =====
    "nationalists": RussiaPoliticalForce(
        force_id="nationalists",
        name="Nationalists / Imperialists",
        name_cn="民族主义者/皇俄派",
        overall_influence=0.40,
        influence_putin=0.3,
        stance_west=-0.9,
        stance_china=-0.2,  # 警惕中国
        stance_cis=0.8,  # 重建帝国
        core_interests=[
            "恢复俄罗斯帝国",
            "整合俄语人口",
            "对抗西方自由主义",
            "扩张领土",
            "强硬的对外政策",
        ],
        key_figures=[
            "Alexander Dugin (欧亚主义)",
            "Ramzan Kadyrov (车臣)",
            "Yevgeny Prigozhin (瓦格纳/已故)",
        ],
        putin_relation="independent",
    ),
    
    # ===== 技术/IT精英 =====
    "tech_elite": RussiaPoliticalForce(
        force_id="tech_elite",
        name="Tech / IT Elite",
        name_cn="科技/IT精英",
        overall_influence=0.35,
        influence_putin=0.2,
        stance_west=0.2,  # 希望开放
        stance_china=0.4,
        stance_cis=0.1,
        core_interests=[
            "避免技术封锁",
            "维持人才流动",
            "进入国际市场",
            "减少审查",
            "维持创新环境",
        ],
        key_figures=[
            "Arkady Volozh (Yandex创始人)",
            "Pavel Durov (Telegram/流亡)",
        ],
        putin_relation="oppositional",
    ),
    
    # ===== 地方精英 =====
    "regional_elites": RussiaPoliticalForce(
        force_id="regional_elites",
        name="Regional Elites",
        name_cn="地方精英",
        overall_influence=0.45,
        influence_putin=0.3,
        stance_west=-0.1,
        stance_china=0.3,
        stance_cis=0.2,
        core_interests=[
            "维持地方自治",
            "获取联邦资金",
            "保护地方利益",
            "避免中央过度控制",
        ],
        key_figures=[
            "Moscow mayor (Sobyanin)",
            "Tatarstan president",
            "Chechen leader (Kadyrov)",
        ],
        putin_relation="pragmatic",
    ),
    
    # ===== 自由派/反对派 =====
    "liberal_opposition": RussiaPoliticalForce(
        force_id="liberal_opposition",
        name="Liberal Opposition",
        name_cn="自由派/反对派",
        overall_influence=0.15,
        influence_putin=-0.5,
        stance_west=0.8,
        stance_china=0.0,
        stance_cis=0.0,
        core_interests=[
            "民主改革",
            "反普京",
            "西方化",
            "自由选举",
            "减少腐败",
        ],
        key_figures=[
            "Alexei Navalny (已故)",
            "Mikhail Khodorkovsky (流亡)",
            "Vladimir Kara-Murza (监禁)",
        ],
        putin_relation="oppositional",
    ),
}


class RussiaPoliticalForcesModel:
    """俄罗斯政治势力模型"""
    
    def __init__(self):
        self.forces = RUSSIA_POLITICAL_FORCES
    
    def get_force(self, force_id: str) -> Optional[RussiaPoliticalForce]:
        return self.forces.get(force_id)
    
    def get_all_forces(self) -> List[RussiaPoliticalForce]:
        return list(self.forces.values())
    
    def get_forces_by_putin_relation(self, relation: str) -> List[RussiaPoliticalForce]:
        """按与普京关系筛选"""
        return [f for f in self.forces.values() if f.putin_relation == relation]
    
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
    
    def to_dict(self) -> Dict:
        return {
            "total_forces": len(self.forces),
            "forces": [
                {
                    "force_id": f.force_id,
                    "name": f.name_cn,
                    "influence": f.overall_influence,
                    "stance_west": f.stance_west,
                    "stance_china": f.stance_china,
                    "putin_relation": f.putin_relation,
                }
                for f in self.forces.values()
            ]
        }


# 全局实例
russia_forces = RussiaPoliticalForcesModel()

if __name__ == "__main__":
    model = RussiaPoliticalForcesModel()
    
    print("=== 俄罗斯政治势力模型 ===\n")
    
    print("主要政治势力:")
    for force in model.get_all_forces():
        print(f"  {force.name_cn:20s} | 影响力: {force.overall_influence:.1f} | "
              f"对西方: {force.stance_west:+.1f} | 对中国: {force.stance_china:+.1f} | "
              f"普京关系: {force.putin_relation}")
    
    print("\n=== 复合立场 ===")
    for target in ["west", "china", "cis"]:
        stance = model.calculate_composite_stance(target)
        print(f"对{target}: {stance:+.2f}")
    
    print("\n=== 推动反西方冲突的势力 ===")
    for name, stance in model.get_conflict_drivers("west"):
        print(f"  {name}: {stance:+.2f}")
    
    print("\n=== 普京忠诚派 ===")
    for force in model.get_forces_by_putin_relation("loyal"):
        print(f"  {force.name_cn}")
