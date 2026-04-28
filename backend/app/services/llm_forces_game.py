"""
LLM Political Forces Game - LLM政治势力博弈引擎
让不同国家的政治势力通过LLM进行决策和博弈
"""

import json
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# 势力角色设定
FORCE_PROMPTS = {
    # 美国势力
    "us_military_industrial": """你是美国军工复合体的代表（洛克希德·马丁、波音、雷神等）。
你的核心利益：维持高额国防预算、推动对外军事干预、遏制中俄军事崛起、扩大武器出口。
你倾向于对华强硬，支持增加军费，推动印太战略。""",
    
    "us_wall_street": """你是华尔街/金融资本的代表（高盛、摩根大通、贝莱德等）。
你的核心利益：维持美元霸权、开放中国市场、避免金融脱钩、维持低利率环境。
你倾向于对华务实合作，反对全面脱钩，希望继续在中国赚钱。""",
    
    "us_tech_giants": """你是美国科技巨头的代表（谷歌、苹果、微软等）。
你的核心利益：维持全球数据控制、进入中国市场、反对数据本地化、推动AI监管宽松。
你对华立场矛盾：既想竞争又想合作，希望维持技术领先但不想失去中国市场。""",
    
    "us_pro_israel_lobby": """你是亲以色列游说团体（AIPAC等）的代表。
你的核心利益：无条件支持以色列、反对伊朗核计划、推动中东和平进程、维持美以特殊关系。
你推动美国在中东保持军事存在，反对伊朗。""",
    
    # 中国势力
    "cn_military_red": """你是中国军方/红二代的代表。
你的核心利益：加速强军、统一台湾、维护南海主权、反对美帝围堵、扩军备战。
你对美立场强硬，支持武统台湾，主张对美斗争。""",
    
    "cn_security": """你是中国安全部门（政法委、公安部等）的代表。
你的核心利益：维护政权安全、网络主权、意识形态安全、反间谍、社会控制。
你对美极度警惕，认为美国试图颠覆中国政权。""",
    
    "cn_reformists": """你是中国改革派/市场派的代表（国务院系统）。
你的核心利益：深化改革开放、市场经济、与西方合作、技术引进、融入全球经济。
你希望与美国保持合作关系，避免对抗，推动经济全球化。""",
    
    "cn_private_capital": """你是中国民企/科技资本的代表（腾讯、字节、华为等）。
你的核心利益：反垄断松绑、进入国际市场、技术突破、宽松监管、资本家权益保护。
你希望对外开放，反对过度监管，希望与美国科技企业合作。""",
    
    # 俄罗斯势力
    "ru_siloviki": """你是俄罗斯强力部门（FSB、对外情报局等）的代表。
你的核心利益：维持国家安全控制、扩大情报权力、反西方渗透、控制信息空间。
你对西方极度敌对，支持强硬对外政策，推动反美联盟。""",
    
    "ru_oligarchs": """你是俄罗斯寡头/商业精英的代表。
你的核心利益：保护海外资产、避免更多制裁、维持贸易通道、进入中国市场。
你希望缓和与西方关系，避免更多制裁，转向东方市场。""",
    
    "ru_military_industrial": """你是俄罗斯军工复合体的代表。
你的核心利益：扩大国防预算、推动武器出口、维持技术优势、乌克兰战争继续。
你支持对外强硬，推动军事扩张，对抗北约。""",
    
    # 欧盟势力
    "eu_franco_german": """你是法德轴心的代表。
你的核心利益：欧洲一体化、欧洲战略自主、欧元稳定、规范制定、多边主义。
你希望在中美之间保持平衡，推动欧洲成为独立一极。""",
    
    "eu_atlanticists": """你是欧盟亲美派（波兰、波罗的海国家等）的代表。
你的核心利益：北约优先、美国安全保障、抗俄援乌、情报合作。
你坚定支持美国，反对欧洲战略自主过快，主张对俄强硬。""",
    
    "eu_tech_giants": """你是欧洲科技巨头的代表（ASML、SAP等）。
你的核心利益：数字主权、数据保护、反美国科技霸权、AI监管领导。
你希望减少对美国科技依赖，同时进入中国市场。""",
}

@dataclass
class ForceDecision:
    """势力决策"""
    force_id: str
    force_name: str
    country: str
    
    # 决策内容
    action: str  # "cooperate", "confront", "neutral", "escalate", "deescalate"
    target: str  # 目标国家/势力
    
    # 决策理由
    reasoning: str
    
    # 预期结果
    expected_outcome: str
    
    # 风险评估
    risk_level: float  # 0-1
    
    # 资源投入
    resource_commitment: float  # 0-1

@dataclass
class GameScenario:
    """博弈场景"""
    scenario_id: str
    name: str
    description: str
    
    # 参与势力
    forces: List[str]
    
    # 初始条件
    initial_conditions: Dict[str, Any]
    
    # 胜利条件
    victory_conditions: Dict[str, Any]

# 预设博弈场景
SCENARIOS = {
    "taiwan_crisis": GameScenario(
        scenario_id="taiwan_crisis",
        name="台海危机",
        description="""2027年，中国宣布对台采取军事行动。美国必须决定是否军事介入。
各方势力博弈：
- 美国：军工复合体希望介入，华尔街希望避免，科技巨头矛盾
- 中国：军方强硬，改革派担忧经济制裁，民企恐慌
- 欧盟：法德希望调停，亲美派支持美国
- 俄罗斯：观望，可能趁机在乌克兰行动""",
        forces=[
            "us_military_industrial", "us_wall_street", "us_tech_giants",
            "cn_military_red", "cn_security", "cn_reformists", "cn_private_capital",
            "eu_franco_german", "eu_atlanticists",
            "ru_siloviki", "ru_oligarchs",
        ],
        initial_conditions={
            "taiwan_status": "tension",
            "us_commitment": 0.5,
            "china_resolve": 0.8,
            "global_economy": 0.7,
        },
        victory_conditions={
            "us": "维持台海现状或中国让步",
            "china": "实现统一",
            "eu": "避免被卷入，维持贸易",
            "russia": "分散西方注意力",
        },
    ),
    
    "trade_war": GameScenario(
        scenario_id="trade_war",
        name="中美贸易战升级",
        description="""美国宣布对中国商品加征60%关税，中国反制。
各方势力博弈：
- 美国：华尔街反对，军工支持，农业受损
- 中国：改革派担忧，民企恐慌，军方无所谓
- 欧盟：趁机抢占中国市场
- 俄罗斯：转向中国""",
        forces=[
            "us_wall_street", "us_military_industrial", "us_tech_giants",
            "cn_reformists", "cn_private_capital", "cn_military_red",
            "eu_franco_german", "eu_tech_giants",
            "ru_oligarchs", "ru_siloviki",
        ],
        initial_conditions={
            "tariff_level": 0.6,
            "trade_volume": 0.5,
            "supply_chain": 0.4,
        },
        victory_conditions={
            "us": "减少对华逆差，制造业回流",
            "china": "维持出口，技术自主",
            "eu": "抢占市场份额",
            "russia": "深化中俄合作",
        },
    ),
    
    "ukraine_escalation": GameScenario(
        scenario_id="ukraine_escalation",
        name="乌克兰局势升级",
        description="""俄罗斯在乌克兰使用战术核武器，北约必须回应。
各方势力博弈：
- 美国：军工兴奋，华尔街恐慌，欧洲盟友施压
- 俄罗斯：军方强硬，寡头恐惧，民众不安
- 欧盟：法德恐慌，亲美派强硬，能源危机
- 中国：观望，评估机会""",
        forces=[
            "us_military_industrial", "us_wall_street", "us_pro_israel_lobby",
            "ru_siloviki", "ru_military_industrial", "ru_oligarchs",
            "eu_franco_german", "eu_atlanticists",
            "cn_security", "cn_reformists",
        ],
        initial_conditions={
            "nuclear_risk": 0.3,
            "nato_unity": 0.6,
            "russia_isolation": 0.8,
            "china_opportunity": 0.5,
        },
        victory_conditions={
            "us": "遏制俄罗斯，维持北约",
            "russia": "避免崩溃，保住乌克兰",
            "eu": "结束战争，恢复能源",
            "china": "坐收渔利",
        },
    ),
}


class LLMForcesGame:
    """LLM政治势力博弈引擎"""
    
    def __init__(self):
        self.scenarios = SCENARIOS
        self.force_prompts = FORCE_PROMPTS
        self.game_history: List[Dict] = []
    
    def get_scenario(self, scenario_id: str) -> Optional[GameScenario]:
        return self.scenarios.get(scenario_id)
    
    def list_scenarios(self) -> List[Dict]:
        return [
            {
                "id": s.scenario_id,
                "name": s.name,
                "description": s.description[:100] + "...",
                "forces_count": len(s.forces),
            }
            for s in self.scenarios.values()
        ]
    
    def simulate_force_decision(self, force_id: str, scenario: GameScenario, 
                                 context: Dict = None) -> ForceDecision:
        """模拟单个势力的决策（简化版，实际应调用LLM）"""
        if context is None:
            context = {}
        
        prompt = self.force_prompts.get(force_id, "")
        
        # 基于势力特性做出决策（简化规则）
        # 实际应调用LLM API
        
        # 势力-行动映射（简化）
        force_actions = {
            # 美国
            "us_military_industrial": ("escalate", "china", 0.7, 0.8),
            "us_wall_street": ("deescalate", "china", 0.3, 0.4),
            "us_tech_giants": ("cooperate", "china", 0.4, 0.5),
            "us_pro_israel_lobby": ("confront", "iran", 0.6, 0.7),
            
            # 中国
            "cn_military_red": ("escalate", "usa", 0.8, 0.9),
            "cn_security": ("confront", "usa", 0.7, 0.8),
            "cn_reformists": ("deescalate", "usa", 0.3, 0.4),
            "cn_private_capital": ("cooperate", "usa", 0.4, 0.5),
            
            # 俄罗斯
            "ru_siloviki": ("escalate", "west", 0.7, 0.8),
            "ru_oligarchs": ("deescalate", "west", 0.5, 0.3),
            "ru_military_industrial": ("confront", "west", 0.6, 0.7),
            
            # 欧盟
            "eu_franco_german": ("neutral", "all", 0.4, 0.5),
            "eu_atlanticists": ("confront", "russia", 0.6, 0.7),
            "eu_tech_giants": ("cooperate", "china", 0.3, 0.4),
        }
        
        action, target, risk, resource = force_actions.get(
            force_id, ("neutral", "all", 0.5, 0.5)
        )
        
        # 根据场景调整
        if scenario.scenario_id == "taiwan_crisis":
            if "cn" in force_id:
                target = "taiwan"
            elif "us" in force_id:
                target = "china"
        elif scenario.scenario_id == "ukraine_escalation":
            if "ru" in force_id:
                target = "ukraine"
            elif "us" in force_id or "eu" in force_id:
                target = "russia"
        
        return ForceDecision(
            force_id=force_id,
            force_name=force_id.replace("_", " ").title(),
            country=force_id.split("_")[0].upper(),
            action=action,
            target=target,
            reasoning=f"基于{force_id}的核心利益，在{scenario.name}场景下选择{action}",
            expected_outcome=f"预期通过{action}实现核心利益",
            risk_level=risk,
            resource_commitment=resource,
        )
    
    def run_game(self, scenario_id: str, rounds: int = 3) -> Dict:
        """运行完整博弈"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {"error": f"Scenario {scenario_id} not found"}
        
        print(f"\n{'='*60}")
        print(f"博弈场景: {scenario.name}")
        print(f"{'='*60}")
        print(scenario.description)
        print(f"\n参与势力: {len(scenario.forces)}个")
        print(f"博弈轮数: {rounds}")
        print(f"{'='*60}\n")
        
        # 运行多轮博弈
        all_decisions = []
        
        for round_num in range(1, rounds + 1):
            print(f"\n--- 第 {round_num} 轮 ---")
            
            round_decisions = []
            for force_id in scenario.forces:
                decision = self.simulate_force_decision(force_id, scenario)
                round_decisions.append(decision)
                
                print(f"\n{decision.force_name} ({decision.country})")
                print(f"  行动: {decision.action}")
                print(f"  目标: {decision.target}")
                print(f"  风险: {decision.risk_level:.1f}")
                print(f"  资源投入: {decision.resource_commitment:.1f}")
            
            all_decisions.append(round_decisions)
            
            # 计算本轮结果
            self._calculate_round_result(round_decisions, scenario)
        
        # 最终结果
        result = self._calculate_final_result(all_decisions, scenario)
        
        return result
    
    def _calculate_round_result(self, decisions: List[ForceDecision], scenario: GameScenario):
        """计算单轮结果"""
        # 统计行动
        actions = {}
        for d in decisions:
            actions[d.action] = actions.get(d.action, 0) + 1
        
        print(f"\n  本轮行动统计:")
        for action, count in actions.items():
            print(f"    {action}: {count}")
        
        # 判断趋势
        if actions.get("escalate", 0) > len(decisions) * 0.3:
            print(f"  ⚠️  局势升级！")
        elif actions.get("deescalate", 0) > len(decisions) * 0.3:
            print(f"  ✅ 局势缓和")
        else:
            print(f"  ➡️  局势僵持")
    
    def _calculate_final_result(self, all_decisions: List[List[ForceDecision]], 
                               scenario: GameScenario) -> Dict:
        """计算最终结果"""
        # 统计所有决策
        country_actions = {}
        for round_decisions in all_decisions:
            for d in round_decisions:
                country = d.country
                if country not in country_actions:
                    country_actions[country] = []
                country_actions[country].append(d.action)
        
        # 判断各国策略
        country_strategies = {}
        for country, actions in country_actions.items():
            action_counts = {}
            for a in actions:
                action_counts[a] = action_counts.get(a, 0) + 1
            
            dominant_action = max(action_counts, key=action_counts.get)
            country_strategies[country] = dominant_action
        
        # 判断赢家
        winners = []
        if scenario.scenario_id == "taiwan_crisis":
            if country_strategies.get("CN") == "escalate" and country_strategies.get("US") != "escalate":
                winners = ["CN"]
            elif country_strategies.get("US") == "escalate":
                winners = ["US"]
            else:
                winners = ["EU", "RU"]
        
        print(f"\n{'='*60}")
        print(f"博弈结束 - 最终结果")
        print(f"{'='*60}")
        
        print(f"\n各国策略:")
        for country, strategy in country_strategies.items():
            print(f"  {country}: {strategy}")
        
        print(f"\n预期赢家: {', '.join(winners)}")
        
        return {
            "scenario": scenario.name,
            "rounds": len(all_decisions),
            "country_strategies": country_strategies,
            "winners": winners,
            "total_decisions": sum(len(d) for d in all_decisions),
        }
    
    def export_game_log(self, result: Dict) -> str:
        """导出博弈日志"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_log_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return filename


# 全局实例
llm_game = LLMForcesGame()

if __name__ == "__main__":
    print("=== LLM政治势力博弈引擎 ===\n")
    
    # 列出场景
    print("可用场景:")
    for s in llm_game.list_scenarios():
        print(f"  {s['id']}: {s['name']} ({s['forces_count']}个势力)")
    
    # 运行台海危机模拟
    print("\n" + "="*60)
    result = llm_game.run_game("taiwan_crisis", rounds=3)
    
    print("\n" + "="*60)
    print("博弈统计:")
    print(f"  总决策数: {result['total_decisions']}")
    print(f"  预期赢家: {', '.join(result['winners'])}")
