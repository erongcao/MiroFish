"""
Multi-Agent Political Simulation - 多智能体政治模拟
所有势力都是独立的Agent,互相博弈形成复杂的局势

核心改进 (v2):
1. Q-Learning策略适应:从历史博弈中学习
2. 情报不对称:不同Agent有不同情报等级
3. 动态联盟博弈:实时联盟形成/瓦解
4. 时间维度:动员延迟、情报延迟
5. 动态Payoff:随战争疲劳/资源实时调整
6. LLM高并发:Semaphore提升到30 + 超时控制
"""

import json
import time
import asyncio
import random
import math
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

from game_theory_diplomacy import (
    GameTheoryDiplomacy, DiplomaticAction, ConflictLevel,
    AgentDiplomaticState, PayoffMatrix
)
from llm_political_game import LLMClient, FORCE_CHARACTERS

try:
    from neo4j_adapter import Neo4jGraphAdapter
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

import uuid
from us_political_forces import US_POLITICAL_FORCES
from china_political_forces import CHINA_POLITICAL_FORCES
from russia_political_forces import RUSSIA_POLITICAL_FORCES
from eu_political_forces import EU_POLITICAL_FORCES

@dataclass
class Agent:
    """智能体"""
    agent_id: str
    name: str
    country: str
    force_type: str  # "government", "military", "financial", "lobby", etc.

    # 能力
    power: float = 0.5  # 影响力/国力
    resources: float = 100.0
    credibility: float = 1.0

    # 立场
    stance: Dict[str, float] = field(default=dict)  # 对其他国家的立场

    # 博弈状态
    reputation: float = 0.0
    war_exhaustion: float = 0.0
    trust: Dict[str, float] = field(default=dict)

    # 联盟和敌对
    allies: Set[str] = field(default_factory=set)
    enemies: Set[str] = field(default_factory=set)

    # 当前行动
    current_action: DiplomaticAction = DiplomaticAction.COOPERATE
    current_target: str = ""

    # 政府内部关系(如果是政府官员)
    government_role: str = ""  # "president", "secretary_of_state", "general", etc.
    faction: str = ""  # " Hawks", "doves", "pragmatists"

    # ============ 新增:问题3 - 情报等级 ============
    # 情报等级决定能看到多少信息(0=完全内部信息,1=完全透明)
    intelligence_level: float = 1.0  # 默认完全透明

    # ============ 新增:问题5 - 时间维度 ============
    time_to_mobilize: int = 0  # 动员延迟(轮数)
    mobilization_ready: float = 1.0  # 当前动员就绪度(0-1)
    intelligence_lag: int = 0  # 情报延迟(轮数)
    pending_actions: List[Dict] = field(default_factory=list)  # 延迟执行的行动

    # ============ 新增:问题2 - Q-Learning策略适应 ============
    q_table: Dict[str, float] = field(default_factory=dict)  # Q(s,a) 值
    learning_rate: float = 0.1  # alpha
    discount_factor: float = 0.9  # gamma
    epsilon: float = 0.2  # 探索率

    def get_alliance_power(self, all_agents: Dict[str, 'Agent']) -> float:
        """计算联盟总力量"""
        total = self.power
        for ally_id in self.allies:
            if ally_id in all_agents:
                total += all_agents[ally_id].power * 0.5
        return total

    def get_enemy_threat(self, all_agents: Dict[str, 'Agent']) -> float:
        """计算敌对威胁"""
        total = 0.0
        for enemy_id in self.enemies:
            if enemy_id in all_agents:
                total += all_agents[enemy_id].power
        return total

    def get_q(self, state_key: str, action: DiplomaticAction) -> float:
        key = f"{state_key}_{action.value}"
        return self.q_table.get(key, 0.0)

    def update_q(self, state_key: str, action: DiplomaticAction, reward: float,
                 next_state_key: str, max_next_q: float):
        """Q-Learning更新"""
        key = f"{state_key}_{action.value}"
        current_q = self.q_table.get(key, 0.0)
        # Q(s,a) = Q(s,a) + alpha * (r + gamma * max_a' Q(s',a') - Q(s,a))
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        self.q_table[key] = new_q

    def choose_action_epsilon_greedy(self, state_key: str,
                                    valid_actions: List[DiplomaticAction]) -> DiplomaticAction:
        """ε-贪心策略选择"""
        if random.random() < self.epsilon:
            return random.choice(valid_actions)
        # 贪心选择Q值最大的动作
        best_action = valid_actions[0]
        best_q = self.get_q(state_key, best_action)
        for action in valid_actions[1:]:
            q = self.get_q(state_key, action)
            if q > best_q:
                best_q = q
                best_action = action
        return best_action


class MultiAgentPoliticalSimulation:
    """多智能体政治模拟系统"""

    def __init__(self, llm_provider: str = "ollama"):
        self.llm = LLMClient(llm_provider)

        # 所有智能体
        self.agents: Dict[str, Agent] = {}

        # 博弈论引擎
        self.gt_engine = GameTheoryDiplomacy()

        # 历史记录
        self.round_history: List[Dict] = []

        # Neo4j 图数据库
        self.neo4j = None
        self.simulation_id = str(uuid.uuid4())[:8]
        if NEO4J_AVAILABLE:
            try:
                self.neo4j = Neo4jGraphAdapter()
                if self.neo4j.connected:
                    print(f"[Neo4j] 已连接,simulation_id={self.simulation_id}")
                else:
                    print("[Neo4j] 连接失败,图数据仅存内存")
                    self.neo4j = None
            except Exception as e:
                print(f"[Neo4j] 初始化失败: {e}")
                self.neo4j = None

        # 初始化所有势力Agent
        self._initialize_all_agents()

    def _initialize_all_agents(self):
        """初始化所有势力Agent"""
        print("\n" + "="*60)
        print("初始化多智能体系统")
        print("="*60)

        # 1. 美国势力 (14个)
        for force_id, force in US_POLITICAL_FORCES.items():
            # ============ 问题3+5: 情报等级 + 时间维度 ============
            # 情报等级:政府/军方高,平民低;美国整体最高
            intel_level = 0.9 if force.force_type in ["government", "military", "military_industrial"] else 0.5
            mob_delay = 2 if force.force_type in ["military", "military_industrial"] else 0
            intel_lag = 1 if force.force_type == "civilian" else 0

            agent = Agent(
                agent_id=f"us_{force_id}",
                name=f"美国{force.name_cn}",
                country="usa",
                force_type=force.force_type,
                power=force.overall_influence * 0.8,
                resources=100.0,
                intelligence_level=intel_level,
                time_to_mobilize=mob_delay,
                intelligence_lag=intel_lag,
                stance={
                    "china": force.stance_china,
                    "russia": force.stance_russia,
                    "iran": force.stance_middle_east,
                },
            )

            # 设置初始盟友/敌对
            if force.party_alignment == "bipartisan":
                agent.allies.add("us_military_industrial")
            if force.force_type == "military_industrial":
                agent.enemies.update(["cn_military_red", "ru_siloviki"])

            self.agents[agent.agent_id] = agent
            print(f"  [美国] {agent.name} (power={agent.power:.2f}, intel={intel_level:.1f})")

        # 2. 中国势力 (10个)
        for force_id, force in CHINA_POLITICAL_FORCES.items():
            intel_level = 0.85 if getattr(force, 'force_type', '') in ["government", "military"] else 0.5
            mob_delay = 2 if getattr(force, 'force_type', '') in ["military", "security"] else 1
            agent = Agent(
                agent_id=f"cn_{force_id}",
                name=f"中国{force.name_cn}",
                country="china",
                force_type=getattr(force, 'force_type', force.ideology),
                power=force.overall_influence * 0.8,
                resources=100.0,
                intelligence_level=intel_level,
                time_to_mobilize=mob_delay,
                stance={
                    "usa": getattr(force, 'stance_usa', 0),
                    "russia": getattr(force, 'stance_russia', 0),
                    "taiwan": getattr(force, 'stance_taiwan', 0),
                },
            )

            self.agents[agent.agent_id] = agent
            print(f"  [中国] {agent.name} (power={agent.power:.2f}, intel={intel_level:.1f})")

        # 3. 俄罗斯势力 (9个)
        for force_id, force in RUSSIA_POLITICAL_FORCES.items():
            intel_level = 0.85 if getattr(force, 'force_type', '') in ["government", "military", "siloviki"] else 0.5
            mob_delay = 2 if getattr(force, 'force_type', '') in ["military", "siloviki"] else 1
            agent = Agent(
                agent_id=f"ru_{force_id}",
                name=f"俄罗斯{force.name_cn}",
                country="russia",
                force_type=getattr(force, 'force_type', 'security'),
                power=force.overall_influence * 0.8,
                resources=100.0,
                intelligence_level=intel_level,
                time_to_mobilize=mob_delay,
                stance={
                    "west": getattr(force, 'stance_west', 0),
                    "china": getattr(force, 'stance_china', 0),
                },
            )

            self.agents[agent.agent_id] = agent
            print(f"  [俄罗斯] {agent.name} (power={agent.power:.2f}, intel={intel_level:.1f})")

        # 4. 欧盟势力 (10个)
        for force_id, force in EU_POLITICAL_FORCES.items():
            intel_level = 0.8 if getattr(force, 'force_type', '') in ["government", "military"] else 0.5
            mob_delay = 2 if getattr(force, 'force_type', '') == "military" else 1
            agent = Agent(
                agent_id=f"eu_{force_id}",
                name=f"欧盟{force.name_cn}",
                country="eu",
                force_type=getattr(force, 'force_type', 'political'),
                power=force.overall_influence * 0.6,  # 欧盟力量打折
                resources=80.0,
                intelligence_level=intel_level,
                time_to_mobilize=mob_delay,
                stance={
                    "usa": getattr(force, 'stance_usa', 0),
                    "china": getattr(force, 'stance_china', 0),
                    "russia": getattr(force, 'stance_russia', 0),
                },
            )

            self.agents[agent.agent_id] = agent
            print(f"  [欧盟] {agent.name} (power={agent.power:.2f}, intel={intel_level:.1f})")

        # 5. 政府内部派系(特殊Agent)
        self._add_government_agents()

        # 6. 其他国家势力
        self._add_other_country_agents()

        # 7. 根据报告调整初始状态(战争已持续2个月)
        self._adjust_initial_state_for_war()

        # 8. 初始化博弈论引擎
        self._initialize_game_theory_engine()

        print(f"\n[初始化完成] 共 {len(self.agents)} 个智能体")

    def _adjust_initial_state_for_war(self):
        """根据战争报告调整初始状态(2026年4月,战争已持续2个月)"""
        print("\n[战争状态调整] 2026年4月,美以伊战争持续2个月")

        for agent_id, agent in self.agents.items():
            # 伊朗:GDP的65%被摧毁,通胀70%,货币贬值30倍
            if agent.country == "iran":
                agent.resources = 35.0  # 经济崩溃
                agent.war_exhaustion = 0.65  # 高战争疲劳
                print(f"  [伊朗] {agent.name}: 资源={agent.resources:.1f} (经济崩溃)")

            # 美国:13人死亡,365人受伤,花费500亿美元
            elif agent.country == "usa":
                agent.resources = 85.0  # 高债务但仍有资源
                agent.war_exhaustion = 0.25  # 中等战争疲劳
                print(f"  [美国] {agent.name}: 资源={agent.resources:.1f} (战争成本)")

            # 以色列:本土受打击,2238人受伤
            elif agent.country == "israel":
                agent.resources = 70.0
                agent.war_exhaustion = 0.45
                print(f"  [以色列] {agent.name}: 资源={agent.resources:.1f} (本土受袭)")

            # 中国:能源进口受阻,但总体稳定
            elif agent.country == "china":
                agent.resources = 90.0
                agent.war_exhaustion = 0.15
                print(f"  [中国] {agent.name}: 资源={agent.resources:.1f} (能源受阻)")

            # 俄罗斯:受制裁但支持伊朗
            elif agent.country == "russia":
                agent.resources = 75.0
                agent.war_exhaustion = 0.20
                print(f"  [俄罗斯] {agent.name}: 资源={agent.resources:.1f} (制裁+支持)")

            # 欧盟:能源危机,通胀高企
            elif agent.country == "eu":
                agent.resources = 60.0
                agent.war_exhaustion = 0.30
                print(f"  [欧盟] {agent.name}: 资源={agent.resources:.1f} (能源危机)")

            # 沙特:石油收入波动,立场分化
            elif agent.country == "saudi":
                agent.resources = 80.0
                agent.war_exhaustion = 0.20
                print(f"  [沙特] {agent.name}: 资源={agent.resources:.1f} (石油波动)")

            # 海湾国家:阿联酋、巴林强硬
            elif agent.country in ["uae", "bahrain"]:
                agent.resources = 75.0
                agent.war_exhaustion = 0.25
                print(f"  [海湾] {agent.name}: 资源={agent.resources:.1f} (强硬立场)")

            # 印度、日本、韩国:能源进口受阻
            elif agent.country in ["india", "japan", "south_korea"]:
                agent.resources = 70.0
                agent.war_exhaustion = 0.20
                print(f"  [亚洲] {agent.name}: 资源={agent.resources:.1f} (能源受阻)")

    def _initialize_game_theory_engine(self):
        """初始化博弈论引擎"""
        agent_configs = []
        for agent_id, agent in self.agents.items():
            stance = "neutral"
            if agent.force_type in ["military_industrial", "military", "security", "siloviki"]:
                stance = "opposing"
            elif agent.force_type in ["financial", "reformist", "pragmatist", "oligarchs"]:
                stance = "supportive"

            # 计算sentiment_bias
            sentiment = 0.0
            if "usa" in agent.stance:
                sentiment = agent.stance["usa"]
            elif "china" in agent.stance:
                sentiment = -agent.stance["china"]

            agent_configs.append({
                "agent_id": agent_id,
                "stance": stance,
                "sentiment_bias": sentiment,
            })

        self.gt_engine.initialize_agents(agent_configs)
        print(f"  [博弈论引擎] 初始化 {len(agent_configs)} 个Agent")

    def _add_government_agents(self):
        """添加政府内部派系Agent"""
        # 特朗普政府内部派系
        government_agents = {
            # 美国政府
            "trump_president": {
                "name": "特朗普(总统)",
                "country": "usa",
                "role": "Commander in Chief",
                "faction": "nationalist",
                "power": 1.0,
                "stances": {"china": -0.7, "russia": 0.3, "iran": -0.6},
            },
            " Pompeo_state": {
                "name": "蓬佩奥(国务卿)",
                "country": "usa",
                "role": "Secretary of State",
                "faction": "hawk",
                "power": 0.8,
                "stances": {"china": -0.9, "russia": -0.8, "iran": -0.9},
            },
            "Mnuchin_treasury": {
                "name": "姆努钦(财长)",
                "country": "usa",
                "role": "Treasury Secretary",
                "faction": "pragmatist",
                "power": 0.7,
                "stances": {"china": -0.4, "russia": -0.3, "iran": -0.5},
            },
            "Esper_defense": {
                "name": "埃斯珀(防长)",
                "country": "usa",
                "role": "Defense Secretary",
                "faction": "military",
                "power": 0.75,
                "stances": {"china": -0.6, "russia": -0.5, "iran": -0.7},
            },

            # 中国政府
            "xi_president": {
                "name": "习近平(国家主席)",
                "country": "china",
                "role": "President",
                "faction": "central",
                "power": 1.0,
                "stances": {"usa": -0.5, "russia": 0.6, "taiwan": 0.9},
            },
            "yang_foreign": {
                "name": "杨洁篪(外事委主任)",
                "country": "china",
                "role": "Top Diplomat",
                "faction": "pragmatist",
                "power": 0.7,
                "stances": {"usa": -0.4, "russia": 0.5, "india": -0.3},
            },
            "wei_military": {
                "name": "魏凤和(防长)",
                "country": "china",
                "role": "Defense Minister",
                "faction": "military",
                "power": 0.75,
                "stances": {"usa": -0.8, "taiwan": 0.95},
            },

            # 俄罗斯政府
            "putin_president": {
                "name": "普京(总统)",
                "country": "russia",
                "role": "President",
                "faction": "central",
                "power": 1.0,
                "stances": {"usa": -0.8, "china": 0.6, "ukraine": -0.9},
            },
            "shoigu_defense": {
                "name": "绍伊古(防长)",
                "country": "russia",
                "role": "Defense Minister",
                "faction": "military",
                "power": 0.8,
                "stances": {"usa": -0.9, "ukraine": -0.95},
            },
            "lavrov_foreign": {
                "name": "拉夫罗夫(外长)",
                "country": "russia",
                "role": "Foreign Minister",
                "faction": "diplomat",
                "power": 0.7,
                "stances": {"usa": -0.7, "eu": -0.5},
            },

            # 欧盟政府
            "macron_france": {
                "name": "马克龙(法国总统)",
                "country": "france",
                "role": "President",
                "faction": "europeanist",
                "power": 0.8,
                "stances": {"usa": 0.4, "russia": -0.3, "china": 0.2},
            },
            "merkel_germany": {
                "name": "默克尔(德国总理)",
                "country": "germany",
                "role": "Chancellor",
                "faction": "pragmatist",
                "power": 0.85,
                "stances": {"usa": 0.5, "russia": -0.2, "china": 0.1},
            },
        }

        for agent_id, config in government_agents.items():
            agent = Agent(
                agent_id=agent_id,
                name=config["name"],
                country=config["country"],
                force_type="government",
                power=config["power"],
                resources=100.0,
                stance=config["stances"],
                government_role=config["role"],
                faction=config["faction"],
            )

            self.agents[agent_id] = agent
            print(f"  [政府] {agent.name} ({agent.faction})")

    def _add_other_country_agents(self):
        """添加其他重要国家势力Agent"""
        other_agents = {
            # 印度
            "india_military": {"name": "印度军方", "country": "india", "force_type": "military", "power": 0.6,
             "stances": {"china": -0.7, "usa": 0.3, "russia": 0.5}},
            "india_business": {"name": "印度商业集团", "country": "india", "force_type": "financial", "power": 0.5,
             "stances": {"china": -0.3, "usa": 0.4}},
            "india_government": {"name": "印度政府", "country": "india", "force_type": "government", "power": 0.7,
             "stances": {"china": -0.6, "usa": 0.5}},
            # 日本
            "japan_military": {"name": "日本自卫队", "country": "japan", "force_type": "military", "power": 0.55,
             "stances": {"china": -0.8, "usa": 0.9}},
            "japan_business": {"name": "日本财阀", "country": "japan", "force_type": "financial", "power": 0.7,
             "stances": {"china": -0.2, "usa": 0.6}},
            # 伊朗 - 战争已持续2个月,经济崩溃
            "iran_guard": {"name": "伊朗革命卫队", "country": "iran", "force_type": "military", "power": 0.7,
             "stances": {"usa": -0.95, "israel": -0.95}},
            "iran_government": {"name": "伊朗政府", "country": "iran", "force_type": "government", "power": 0.6,
             "stances": {"usa": -0.8, "china": 0.4}},
            # 沙特
            "saudi_royal": {"name": "沙特王室", "country": "saudi", "force_type": "government", "power": 0.8,
             "stances": {"iran": -0.9, "usa": 0.7}},
            "saudi_oil": {"name": "沙特阿美石油", "country": "saudi", "force_type": "energy", "power": 0.9,
             "stances": {"china": 0.5, "usa": 0.4}},
            # 以色列
            "israel_military": {"name": "以色列军方", "country": "israel", "force_type": "military", "power": 0.75,
             "stances": {"iran": -0.95, "usa": 0.9}},
            "israel_intel": {"name": "以色列摩萨德", "country": "israel", "force_type": "intelligence", "power": 0.7,
             "stances": {"iran": -0.95, "usa": 0.8}},
            # 朝鲜
            "nk_military": {"name": "朝鲜军方", "country": "north_korea", "force_type": "military", "power": 0.5,
             "stances": {"usa": -0.95, "china": 0.7}},
            # 英国
            "uk_government": {"name": "英国政府", "country": "uk", "force_type": "government", "power": 0.6,
             "stances": {"usa": 0.9, "china": -0.4}},
            "uk_financial": {"name": "伦敦金融城", "country": "uk", "force_type": "financial", "power": 0.7,
             "stances": {"usa": 0.6, "china": 0.2}},
            # 土耳其
            "turkey_military": {"name": "土耳其军方", "country": "turkey", "force_type": "military", "power": 0.6,
             "stances": {"usa": 0.3, "russia": -0.4}},
            # 韩国
            "sk_military": {"name": "韩国军方", "country": "south_korea", "force_type": "military", "power": 0.55,
             "stances": {"north_korea": -0.9, "usa": 0.9}},
            "sk_business": {"name": "韩国财阀", "country": "south_korea", "force_type": "financial", "power": 0.7,
             "stances": {"usa": 0.6, "china": 0.2}},
        }

        for agent_id, config in other_agents.items():
            agent = Agent(
                agent_id=agent_id,
                name=config["name"],
                country=config["country"],
                force_type=config["force_type"],
                power=config["power"],
                resources=100.0,
                stance=config["stances"],
            )
            self.agents[agent_id] = agent
            print(f"  [{config['country'].upper()}] {agent.name}")

    def run_round(self, round_num: int, scenario: str, context: str) -> Dict:
        """运行一轮模拟(同步包装异步方法)"""
        return asyncio.run(self.run_round_async(round_num, scenario, context))

    async def run_round_async(self, round_num: int, scenario: str, context: str) -> Dict:
        """异步运行一轮模拟"""
        print(f"\n{'='*60}")
        print(f"第 {round_num} 轮 - {len(self.agents)} 个智能体博弈")
        print(f"{'='*60}")

        # 1. LLM决策阶段 - 并行生成所有Agent决策
        start_time = time.time()
        decisions = await self._generate_all_decisions_async(scenario, context, round_num)
        llm_time = time.time() - start_time
        print(f"  LLM决策耗时: {llm_time:.1f}秒")

        # 2. 博弈论计算 - 所有两两博弈
        print(f"\n[阶段2] 博弈论计算 ({len(self.agents)}个Agent = {len(self.agents)*(len(self.agents)-1)//2}对)")
        payoff_results = self._calculate_all_bilateral_games(decisions)

        # 3. 联盟形成
        print("\n[阶段3] 联盟与敌对")
        self._update_alliances_and_enemies(payoff_results)

        # 4. 势力格局变化
        print("\n[阶段4] 势力格局分析")
        power_changes = self._analyze_power_shifts()

        # 5. 状态更新
        self._update_agent_states(payoff_results)

        # 记录历史
        round_data = {
            "round": round_num,
            "decisions": decisions,
            "payoffs": payoff_results,
            "power_changes": power_changes,
        }
        self.round_history.append(round_data)

        # 6. 打印报告
        self._print_round_report(round_num, decisions, payoff_results, power_changes)
        
        # 7. 持久化到Neo4j图数据库
        if self.neo4j and self.neo4j.connected:
            self._persist_round_to_neo4j(round_num, decisions, payoff_results)
        
        return round_data

    def _persist_round_to_neo4j(self, round_num: int, decisions: Dict, payoff_results: Dict):
        """将本轮数据持久化到Neo4j图数据库"""
        try:
            sim_node_id = f"sim_{self.simulation_id}"
            
            # 创建/更新模拟根节点
            self.neo4j.create_node(
                node_id=sim_node_id,
                labels=["Simulation"],
                properties={
                    "id": sim_node_id,
                    "scenario": "geopolitical_simulation",
                    "round": round_num,
                    "agent_count": len(self.agents),
                }
            )
            
            # 创建/更新本轮节点
            round_node_id = f"{sim_node_id}_round{round_num}"
            self.neo4j.create_node(
                node_id=round_node_id,
                labels=["Round"],
                properties={
                    "id": round_node_id,
                    "simulation_id": sim_node_id,
                    "round": round_num,
                }
            )
            
            # 关系：模拟 -> 轮次
            self.neo4j.create_edge(
                edge_type="HAS_ROUND",
                source_id=sim_node_id,
                target_id=round_node_id,
                properties={"round": round_num}
            )
            
            # 遍历所有Agent，创建节点和关系
            for agent_id, agent in self.agents.items():
                # 节点属性
                props = {
                    "id": agent_id,
                    "name": agent.name,
                    "country": agent.country,
                    "power": round(agent.power, 4),
                    "resources": round(agent.resources, 2),
                    "war_exhaustion": round(agent.war_exhaustion, 4),
                    "reputation": round(agent.reputation, 4),
                    "round": round_num,
                }
                
                self.neo4j.create_node(
                    node_id=agent_id,
                    labels=["Agent"],
                    properties=props
                )
                
                # 关系：轮次 -> Agent
                self.neo4j.create_edge(
                    edge_type="INCLUDES_AGENT",
                    source_id=round_node_id,
                    target_id=agent_id,
                    properties={"round": round_num}
                )
                
                # 决策关系
                if agent_id in decisions:
                    decision = decisions[agent_id]
                    action_val = decision.get('action', 'unknown')
                    if hasattr(action_val, 'value'):
                        action_val = str(action_val.value)
                    target = decision.get('target', '')
                    
                    self.neo4j.create_node(
                        node_id=f"{agent_id}_r{round_num}",
                        labels=["Decision"],
                        properties={
                            "id": f"{agent_id}_r{round_num}",
                            "agent_id": agent_id,
                            "action": action_val,
                            "target": target,
                            "round": round_num,
                            "reasoning": decision.get('reasoning', '')[:200],
                        }
                    )
                    
                    self.neo4j.create_edge(
                        edge_type="MADE_DECISION",
                        source_id=agent_id,
                        target_id=f"{agent_id}_r{round_num}",
                        properties={"action": action_val, "round": round_num}
                    )
            
            # 博弈结果关系（所有Agent两两博弈）
            for pair_key, result in payoff_results.items():
                if '|' not in pair_key:
                    continue
                
                agent_a_id, agent_b_id = pair_key.split('|')
                
                game_result_node_id = f"game_result_{pair_key}_r{round_num}".replace('|', '_')
                
                # 安全转换：enum -> str
                action_a_val = result.get('action_a', '')
                action_b_val = result.get('action_b', '')
                if hasattr(action_a_val, 'value'):
                    action_a_val = str(action_a_val.value)
                elif action_a_val is None:
                    action_a_val = ''
                if hasattr(action_b_val, 'value'):
                    action_b_val = str(action_b_val.value)
                elif action_b_val is None:
                    action_b_val = ''
                
                conflict_val = result.get('conflict_level', 'unknown')
                if hasattr(conflict_val, 'value'):
                    conflict_val = str(conflict_val.value)
                
                self.neo4j.create_node(
                    node_id=game_result_node_id,
                    labels=["GameResult"],
                    properties={
                        "id": game_result_node_id,
                        "agent_a": agent_a_id,
                        "agent_b": agent_b_id,
                        "payoff_a": round(result.get('payoff_a', 0), 2),
                        "payoff_b": round(result.get('payoff_b', 0), 2),
                        "action_a": action_a_val,
                        "action_b": action_b_val,
                        "conflict_level": conflict_val,
                        "trust_delta": round(result.get('trust_delta', 0), 4),
                        "round": round_num,
                    }
                )
                
                self.neo4j.create_edge(
                    edge_type="PARTICIPATED_IN",
                    source_id=agent_a_id,
                    target_id=game_result_node_id,
                    properties={"round": round_num}
                )
                self.neo4j.create_edge(
                    edge_type="PARTICIPATED_IN",
                    source_id=agent_b_id,
                    target_id=game_result_node_id,
                    properties={"round": round_num}
                )
            
            # 联盟和敌对关系
            for agent_id, agent in self.agents.items():
                for ally_id in agent.allies:
                    if ally_id in self.agents:
                        alliance_node_id = f"alliance_{agent_id}_{ally_id}_r{round_num}"
                        self.neo4j.create_node(
                            node_id=alliance_node_id,
                            labels=["Alliance"],
                            properties={
                                "id": alliance_node_id,
                                "type": "alliance",
                                "round": round_num,
                            }
                        )
                        self.neo4j.create_edge(
                            edge_type="ALLIED_WITH",
                            source_id=agent_id,
                            target_id=alliance_node_id,
                            properties={"round": round_num}
                        )
                        self.neo4j.create_edge(
                            edge_type="ALLIED_WITH",
                            source_id=ally_id,
                            target_id=alliance_node_id,
                            properties={"round": round_num}
                        )
                
                for enemy_id in agent.enemies:
                    if enemy_id in self.agents:
                        conflict_node_id = f"conflict_{agent_id}_{enemy_id}_r{round_num}"
                        self.neo4j.create_node(
                            node_id=conflict_node_id,
                            labels=["Conflict"],
                            properties={
                                "id": conflict_node_id,
                                "type": "hostility",
                                "round": round_num,
                            }
                        )
                        self.neo4j.create_edge(
                            edge_type="HOSTILE_TO",
                            source_id=agent_id,
                            target_id=conflict_node_id,
                            properties={"round": round_num}
                        )
                        self.neo4j.create_edge(
                            edge_type="HOSTILE_TO",
                            source_id=enemy_id,
                            target_id=conflict_node_id,
                            properties={"round": round_num}
                        )
            
            print(f"[Neo4j] 第{round_num}轮已持久化: {len(self.agents)}个Agent节点, {len(payoff_results)}个博弈结果")
            
        except Exception as e:
            print(f"[Neo4j] 持久化失败: {e}")

    def _generate_agent_decision(self, agent: Agent, scenario: str,
                                  context: str, round_num: int) -> Dict:
        """让LLM为Agent生成决策"""
        # 获取该Agent相关的其他Agent
        related_agents = []
        for other_id, other in self.agents.items():
            if other_id != agent.agent_id and other.country != agent.country:
                stance = agent.stance.get(other.country, 0.0)
                related_agents.append({
                    "name": other.name,
                    "country": other.country,
                    "stance": stance,
                    "power": other.power,
                })

        # 获取盟友和敌对
        allies = [self.agents[a].name for a in agent.allies if a in self.agents]
        enemies = [self.agents[e].name for e in agent.enemies if e in self.agents]

        prompt = f"""你是{agent.name}({agent.country.upper()})。

角色:{agent.government_role or agent.force_type}
派系:{agent.faction or 'N/A'}
影响力:{agent.power:.2f}
当前资源:{agent.resources:.1f}
战争疲劳:{agent.war_exhaustion:.2f}

立场:
{json.dumps(agent.stance, ensure_ascii=False, indent=2)}

盟友:{', '.join(allies) if allies else '无'}
敌对:{', '.join(enemies) if enemies else '无'}

当前场景:{scenario}
当前局势:{context}

作为{agent.name},基于你的立场和利益,选择行动:
- cooperate: 合作
- defect: 背叛(利用对方)
- deter: 威慑
- escalate: 升级冲突
- negotiate: 谈判
- sanction: 制裁
- appeasse: 绥靖

回复JSON:
{{
    "action": "行动",
    "target": "目标国家/势力",
    "reasoning": "决策理由(博弈论分析)",
    "allies_involved": ["盟友列表,如果有的话"],
    "expected_payoff": "预期收益"
}}"""

        messages = [
            {"role": "system", "content": "你是一个地缘政治博弈专家。"},
            {"role": "user", "content": prompt},
        ]

        response = self.llm.chat(messages, temperature=0.8, max_tokens=300)

        if response:
            try:
                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

                data = json.loads(content)
                action_str = data.get("action", "cooperate")

                action_map = {
                    "cooperate": DiplomaticAction.COOPERATE,
                    "defect": DiplomaticAction.DEFECT,
                    "deter": DiplomaticAction.DETER,
                    "escalate": DiplomaticAction.ESCALATE,
                    "negotiate": DiplomaticAction.NEGOTIATE,
                    "sanction": DiplomaticAction.SANCTION,
                    "appease": DiplomaticAction.APPEASE,
                    "ignore": DiplomaticAction.IGNORE,
                }

                return {
                    "action": action_map.get(action_str, DiplomaticAction.COOPERATE),
                    "target": data.get("target", "none"),
                    "reasoning": data.get("reasoning", ""),
                    "expected_payoff": data.get("expected_payoff", ""),
                }
            except:
                pass

        return {"action": DiplomaticAction.COOPERATE, "target": "none", "reasoning": "fallback"}

    async def _generate_agent_decision_async(self, agent: Agent, scenario: str,
                                              context: str, round_num: int) -> Dict:
        """异步生成单个Agent的决策"""
        try:
            # 复用同步方法的prompt构建逻辑
            related_agents = []
            for other_id, other in self.agents.items():
                if other_id != agent.agent_id and other.country != agent.country:
                    stance = agent.stance.get(other.country, 0.0)
                    related_agents.append({
                        "name": other.name,
                        "country": other.country,
                        "stance": stance,
                        "power": other.power,
                    })

            allies = [self.agents[a].name for a in agent.allies if a in self.agents]
            enemies = [self.agents[e].name for e in agent.enemies if e in self.agents]

            prompt = f"""你是{agent.name}({agent.country.upper()})。

角色:{agent.government_role or agent.force_type}
派系:{agent.faction or 'N/A'}
影响力:{agent.power:.2f}
当前资源:{agent.resources:.1f}
战争疲劳:{agent.war_exhaustion:.2f}

立场:
{json.dumps(agent.stance, ensure_ascii=False, indent=2)}

盟友:{', '.join(allies) if allies else '无'}
敌对:{', '.join(enemies) if enemies else '无'}

当前场景:{scenario}
当前局势:{context}

作为{agent.name},基于你的立场和利益,选择行动:
- cooperate: 合作
- defect: 背叛(利用对方)
- deter: 威慑
- escalate: 升级冲突
- negotiate: 谈判
- sanction: 制裁
- appeasse: 绥靖

回复JSON:
{{
    "action": "行动",
    "target": "目标国家/势力",
    "reasoning": "决策理由(博弈论分析)",
    "allies_involved": ["盟友列表,如果有的话"],
    "expected_payoff": "预期收益"
}}"""

            messages = [
                {"role": "system", "content": "你是一个地缘政治博弈专家。"},
                {"role": "user", "content": prompt},
            ]

            # 在线程池中执行LLM调用(避免阻塞事件循环)
            response = await asyncio.to_thread(
                self.llm.chat,
                messages,
                temperature=0.8,
                max_tokens=300
            )

            if response:
                try:
                    content = response.content.strip()
                    if content.startswith("```"):
                        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

                    data = json.loads(content)
                    action_str = data.get("action", "cooperate")

                    action_map = {
                        "cooperate": DiplomaticAction.COOPERATE,
                        "defect": DiplomaticAction.DEFECT,
                        "deter": DiplomaticAction.DETER,
                        "escalate": DiplomaticAction.ESCALATE,
                        "negotiate": DiplomaticAction.NEGOTIATE,
                        "sanction": DiplomaticAction.SANCTION,
                        "appease": DiplomaticAction.APPEASE,
                        "ignore": DiplomaticAction.IGNORE,
                    }

                    return {
                        "agent_id": agent.agent_id,
                        "decision": {
                            "action": action_map.get(action_str, DiplomaticAction.COOPERATE),
                            "target": data.get("target", "none"),
                            "reasoning": data.get("reasoning", ""),
                            "expected_payoff": data.get("expected_payoff", ""),
                        }
                    }
                except:
                    pass

            return {
                "agent_id": agent.agent_id,
                "decision": {"action": DiplomaticAction.COOPERATE, "target": "none", "reasoning": "fallback"}
            }
        except Exception as e:
            print(f"  [错误] {agent.name} 决策生成失败: {e}")
            return {
                "agent_id": agent.agent_id,
                "decision": {"action": DiplomaticAction.COOPERATE, "target": "none", "reasoning": f"错误: {str(e)[:50]}"}
            }

    async def _generate_all_decisions_async(self, scenario: str, context: str,
                                             round_num: int) -> Dict:
        """并行生成所有Agent的决策"""
        print(f"\n[阶段1] LLM决策生成 (并行: {len(self.agents)}个Agent, 并发限制: 10)")

        # 创建任务列表
        tasks = []
        for agent_id, agent in self.agents.items():
            if agent.resources <= 0:
                continue
            task = self._generate_agent_decision_async(agent, scenario, context, round_num)
            tasks.append(task)

        # 限制并发数避免过载Ollama(问题1修复:提升到30)
        semaphore = asyncio.Semaphore(30)

        async def bounded_task(task):
            async with semaphore:
                try:
                    return await asyncio.wait_for(task, timeout=30.0)
                except asyncio.TimeoutError:
                    print(f"  [超时] Agent决策超时,已跳过")
                    return {"agent_id": None, "decision": {"action": DiplomaticAction.COOPERATE, "target": "none", "reasoning": "timeout"}}

        bounded_tasks = [bounded_task(t) for t in tasks]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)

        # 收集结果
        decisions = {}
        success_count = 0
        for result in results:
            if isinstance(result, dict) and "agent_id" in result:
                decisions[result["agent_id"]] = result["decision"]
                success_count += 1
            elif isinstance(result, Exception):
                print(f"  [错误] 任务异常: {result}")

        print(f"  完成: {success_count}/{len(tasks)} 个决策")
        return decisions

    def _calculate_all_bilateral_games(self, decisions: Dict) -> Dict:
        """计算所有两两博弈"""
        results = {}
        agent_ids = list(self.agents.keys())

        for i, agent_a_id in enumerate(agent_ids):
            for agent_b_id in agent_ids[i+1:]:
                agent_a = self.agents[agent_a_id]
                agent_b = self.agents[agent_b_id]

                # 获取决策
                decision_a = decisions.get(agent_a_id, {})
                decision_b = decisions.get(agent_b_id, {})

                action_a = decision_a.get("action", DiplomaticAction.COOPERATE)
                action_b = decision_b.get("action", DiplomaticAction.COOPERATE)

                # 博弈论计算
                result = self.gt_engine.calculate_diplomatic_outcome(
                    agent_a_id, agent_b_id, action_a, action_b
                )

                # 添加行动信息到结果
                result["action_a"] = action_a
                result["action_b"] = action_b

                results[f"{agent_a_id}|{agent_b_id}"] = result

        return results

    def _update_alliances_and_enemies(self, payoff_results: Dict):
        """更新联盟和敌对关系(动态联盟博弈)"""
        # 基于博弈结果 + 联盟稳定性更新
        alliance_scores: Dict[Tuple[str, str], float] = {}

        for key, result in payoff_results.items():
            agent_a_id, agent_b_id = key.split("|")

            payoff_a = result["payoff_a"]
            payoff_b = result["payoff_b"]

            # ============ 问题4: 动态联盟博弈 ============
            # 计算联盟吸引力分数
            combined_payoff = payoff_a + payoff_b
            a = self.agents[agent_a_id]
            b = self.agents[agent_b_id]

            # 联盟收益 = 双方博弈收益 + 联盟力量加成 - 背叛风险
            alliance_bonus = 0.0
            if payoff_a > 2 and payoff_b > 2:
                # 同盟:力量叠加
                alliance_bonus = min(a.power, b.power) * 0.2
                alliance_scores[(agent_a_id, agent_b_id)] = combined_payoff + alliance_bonus
            elif payoff_a < 0 or payoff_b < 0:
                # 背叛风险:降低联盟吸引力
                alliance_scores[(agent_a_id, agent_b_id)] = combined_payoff - 2.0

        # 联盟形成:收益超过阈值则结盟
        for (a_id, b_id), score in alliance_scores.items():
            if score > 3.5:  # 联盟收益阈值
                self.agents[a_id].allies.add(b_id)
                self.agents[b_id].allies.add(a_id)
                self.agents[a_id].enemies.discard(b_id)
                self.agents[b_id].enemies.discard(a_id)
            elif score < -1.0:  # 联盟崩溃阈值
                self.agents[a_id].allies.discard(b_id)
                self.agents[b_id].allies.discard(a_id)
                self.agents[a_id].enemies.add(b_id)
                self.agents[b_id].enemies.add(a_id)

        # 同盟内部凝聚力检查:盟友间的博弈收益若持续为负则瓦解
        for agent in self.agents.values():
            for ally_id in list(agent.allies):
                key = "|".join(sorted([agent.agent_id, ally_id]))
                if key in payoff_results:
                    result = payoff_results[key]
                    a_payoff = result["payoff_a"] if agent.agent_id == key.split("|")[0] else result["payoff_b"]
                    if a_payoff < -1.0 and random.random() < 0.3:
                        # 30%概率盟友关系破裂
                        agent.allies.discard(ally_id)
                        self.agents[ally_id].enemies.add(agent.agent_id)

    def _analyze_power_shifts(self) -> Dict:
        """分析势力格局变化"""
        power_by_country = defaultdict(float)
        power_by_force = defaultdict(float)

        for agent in self.agents.values():
            power_by_country[agent.country] += agent.power
            power_by_force[agent.force_type] += agent.power

        return {
            "by_country": dict(power_by_country),
            "by_force_type": dict(power_by_force),
        }

    def _update_agent_states(self, payoff_results: Dict):
        """更新Agent状态 - 经济资源系统 + Q-Learning适应"""
        # ============ 问题2: Q-Learning策略适应 ============
        # 构建上一轮状态(所有Agent)
        prev_states = {}
        for agent in self.agents.values():
            fatigue_bucket = int(agent.war_exhaustion * 3)  # 0/1/2/3
            resource_bucket = int(agent.resources / 50)  # 0/1/2/3
            prev_states[agent.agent_id] = f"F{fatigue_bucket}_R{resource_bucket}"

        # 一次性创建valid_actions,避免循环内重复创建
        valid_actions = list(DiplomaticAction)

        for key, result in payoff_results.items():
            agent_a_id, agent_b_id = key.split("|")
            agent_a = self.agents[agent_a_id]
            agent_b = self.agents[agent_b_id]

            # 获取行动
            action_a = result.get("action_a", DiplomaticAction.COOPERATE)
            action_b = result.get("action_b", DiplomaticAction.COOPERATE)

            # 1. 资源消耗(根据行动类型)
            # 伊朗特殊处理:资源低于50时消耗减半(避免崩溃太快)
            if agent_a.country == "iran" and agent_a.resources < 50:
                cost_a = self._calculate_resource_cost(action_a, agent_a) * 0.3  # 消耗降至30%
            else:
                cost_a = self._calculate_resource_cost(action_a, agent_a)

            if agent_b.country == "iran" and agent_b.resources < 50:
                cost_b = self._calculate_resource_cost(action_b, agent_b) * 0.3  # 消耗降至30%
            else:
                cost_b = self._calculate_resource_cost(action_b, agent_b)

            # 2. 资源生成(经济实力)
            income_a = self._calculate_resource_income(agent_a)
            income_b = self._calculate_resource_income(agent_b)

            # 3. 净资源变化
            net_change_a = income_a - cost_a
            net_change_b = income_b - cost_b

            # 应用变化(考虑经济弹性)
            agent_a.resources = max(10.0, min(200.0, agent_a.resources + net_change_a))
            agent_b.resources = max(10.0, min(200.0, agent_b.resources + net_change_b))

            # 4. 战争疲劳(只在升级/冲突时增加)
            if action_a in [DiplomaticAction.ESCALATE, DiplomaticAction.DETER]:
                agent_a.war_exhaustion = min(1.0, agent_a.war_exhaustion + 0.15)
            elif action_a in [DiplomaticAction.COOPERATE, DiplomaticAction.NEGOTIATE]:
                agent_a.war_exhaustion = max(0.0, agent_a.war_exhaustion - 0.05)

            if action_b in [DiplomaticAction.ESCALATE, DiplomaticAction.DETER]:
                agent_b.war_exhaustion = min(1.0, agent_b.war_exhaustion + 0.15)
            elif action_b in [DiplomaticAction.COOPERATE, DiplomaticAction.NEGOTIATE]:
                agent_b.war_exhaustion = max(0.0, agent_b.war_exhaustion - 0.05)

            # 5. 伊朗内部冲突惩罚(革命卫队 vs 政府)
            if agent_a.country == "iran" and agent_b.country == "iran":
                if agent_a.force_type != agent_b.force_type:
                    # 革命卫队与政府冲突,双方资源消耗(但可控)
                    agent_a.resources = max(10.0, agent_a.resources - 0.5)
                    agent_b.resources = max(10.0, agent_b.resources - 0.5)

            # 6. 美国内部冲突惩罚(军工 vs 华尔街等)
            if agent_a.country == "usa" and agent_b.country == "usa":
                if agent_a.force_type != agent_b.force_type:
                    # 不同势力冲突,资源消耗(但可控)
                    agent_a.resources = max(10.0, agent_a.resources - 0.3)
                    agent_b.resources = max(10.0, agent_b.resources - 0.3)

            # ============ 问题2: Q-Learning更新 ============
            # 基于本轮收益更新Q表
            prev_state_a = prev_states.get(agent_a_id, "F0_R2")
            prev_state_b = prev_states.get(agent_b_id, "F0_R2")

            # 计算当前状态(两个Agent都要计算)
            curr_fatigue_a = int(agent_a.war_exhaustion * 3)
            curr_resource_a = int(agent_a.resources / 50)
            curr_state_a = f"F{curr_fatigue_a}_R{curr_resource_a}"

            curr_fatigue_b = int(agent_b.war_exhaustion * 3)
            curr_resource_b = int(agent_b.resources / 50)
            curr_state_b = f"F{curr_fatigue_b}_R{curr_resource_b}"

            # max Q(s') for both agents
            max_q_a = max(agent_a.get_q(curr_state_a, a) for a in valid_actions)
            max_q_b = max(agent_b.get_q(curr_state_b, b) for b in valid_actions)

            # 奖励 = 收益 - 成本(问题6: 动态奖励)
            reward_a = result["payoff_a"] - cost_a + (agent_a.war_exhaustion * -2)
            reward_b = result["payoff_b"] - cost_b + (agent_b.war_exhaustion * -2)

            # Q-Learning更新
            agent_a.update_q(prev_state_a, action_a, reward_a, curr_state_a, max_q_a)
            agent_b.update_q(prev_state_b, action_b, reward_b, curr_state_b, max_q_b)

            # epsilon衰减(每轮降低2%,最低5%)
            agent_a.epsilon = max(0.05, agent_a.epsilon * 0.98)
            agent_b.epsilon = max(0.05, agent_b.epsilon * 0.98)

    def _calculate_resource_income(self, agent: Agent) -> float:
        """计算资源生成(经济系统v2 - 战争消耗版)"""
        # 基础经济产出(大幅降低,战争时期经济受损)
        base_income = {
            "usa": 1.5,      # 美国高债务,增长乏力
            "china": 1.2,    # 中国转型期,增速放缓
            "russia": 0.8,   # 俄罗斯受制裁,经济困难
            "eu": 1.3,       # 欧盟能源危机,通胀高企
            "saudi": 1.0,    # 沙特石油收入但波动大
            "iran": 0.5,     # 伊朗受制裁,经济脆弱
            "japan": 0.9,    # 日本长期停滞
            "uk": 0.8,       # 英国脱欧后经济疲软
            "germany": 1.0,  # 德国能源危机
            "france": 0.9,   # 法国社会动荡
            "india": 0.7,    # 印度基础设施不足
            "south_korea": 0.8,  # 韩国出口依赖
            "israel": 0.6,   # 以色列军费高
            "turkey": 0.5,   # 土耳其通胀严重
            "north_korea": 0.2,  # 朝鲜经济极度困难
            "brazil": 0.6,   # 巴西政治不稳定
        }

        income = base_income.get(agent.country, 0.5)

        # 势力类型加成(降低)
        type_bonus = {
            "financial": 0.3,      # 金融集团赚钱能力强
            "energy": 0.2,         # 能源集团有资源收入
            "tech": 0.2,           # 科技集团创新收入
            "military": -0.3,      # 军事集团消耗大
            "government": 0.1,     # 政府有税收
        }
        income += type_bonus.get(agent.force_type, 0)

        # 战争疲劳严重减少经济产出(经济受战争影响)
        fatigue_penalty = agent.war_exhaustion * 2.0
        income -= fatigue_penalty

        # 国内冲突惩罚(美国内部分裂影响经济)
        # 如果Agent有敌对关系,经济产出降低
        domestic_conflict = len(agent.enemies) * 0.1
        income -= domestic_conflict

        # 资源枯竭惩罚(资源低于30时,经济严重受损)
        if agent.resources < 30:
            income -= (30 - agent.resources) * 0.3

        # 高通胀惩罚(资源高于100时,通胀压力)
        if agent.resources > 100:
            income -= (agent.resources - 100) * 0.02

        # 伊朗特殊惩罚(战争+制裁+封锁)
        if agent.country == "iran":
            # 战争摧毁了65% GDP,但革命卫队控制经济+外部支持
            income -= 0.1
            # 通胀70%,货币贬值30倍
            income -= 0.05
            # 霍尔木兹海峡封锁影响石油出口(但仍有影子出口+中俄支持)
            income -= 0.05
            # 革命卫队控制经济,效率低下但有外部支持
            if agent.force_type == "military":
                income -= 0.05

        # 美国特殊惩罚(战争成本+国内分裂)
        elif agent.country == "usa":
            # 500亿美元战争花费
            income -= 0.1
            # 国内政治分裂影响经济
            if len(agent.enemies) > 3:
                income -= 0.1

        # 以色列特殊惩罚(本土受袭)
        elif agent.country == "israel":
            income -= 0.1

        # 欧盟特殊惩罚(能源危机)
        elif agent.country == "eu":
            income -= 0.15

        # 中国特殊惩罚(能源进口受阻)
        elif agent.country == "china":
            income -= 0.05

        # 俄罗斯特殊惩罚(制裁)
        elif agent.country == "russia":
            income -= 0.05

        # 海湾国家(石油收入波动)
        elif agent.country in ["saudi", "uae", "bahrain"]:
            income -= 0.05

        # 亚洲国家(能源进口受阻)
        elif agent.country in ["india", "japan", "south_korea"]:
            income -= 0.1

        return max(0.3, income)  # 最小收入保障(提高)

    def _calculate_resource_cost(self, action: DiplomaticAction, agent: Agent) -> float:
        """计算资源消耗 - 战争消耗版"""
        base_costs = {
            DiplomaticAction.COOPERATE: 0.5,      # 合作成本低
            DiplomaticAction.DEFECT: 1.0,         # 背叛成本
            DiplomaticAction.DETER: 2.0,          # 威慑消耗
            DiplomaticAction.ESCALATE: 3.0,     # 升级冲突消耗(大幅降低)
            DiplomaticAction.NEGOTIATE: 1.0,    # 谈判成本
            DiplomaticAction.SANCTION: 2.0,     # 制裁消耗
            DiplomaticAction.APPEASE: 1.5,      # 绥靖成本
            DiplomaticAction.IGNORE: 0.3,       # 无视成本
        }

        base = base_costs.get(action, 2.0)

        # 战争疲劳增加成本
        fatigue_multiplier = 1.0 + agent.war_exhaustion * 0.5

        # 资源越少,效率越低
        resource_factor = 1.0 + (100.0 - agent.resources) / 200.0

        cost = base * fatigue_multiplier * resource_factor

        return max(0.5, min(15.0, cost))  # 限制范围

    def _print_round_report(self, round_num: int, decisions: Dict,
                           payoff_results: Dict, power_changes: Dict):
        """打印轮次报告"""
        print(f"\n{'='*60}")
        print(f"第 {round_num} 轮报告 - {len(self.agents)} 个智能体")
        print(f"{'='*60}")

        # 按国家分组统计
        print("\n[行动统计 - 按国家]")
        for country in ["usa", "china", "russia", "eu"]:
            country_agents = [a for a in self.agents.values() if a.country == country]
            actions = [decisions.get(a.agent_id, {}).get("action", DiplomaticAction.COOPERATE)
                      for a in country_agents]

            action_counts = {}
            for action in actions:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1

            print(f"  {country.upper()}: {action_counts}")

        # 关键博弈
        print("\n[关键博弈结果]")
        significant_games = [(k, v) for k, v in payoff_results.items()
                             if abs(v["payoff_a"]) > 3 or abs(v["payoff_b"]) > 3]

        for key, result in significant_games[:5]:
            a_id, b_id = key.split("|")
            agent_a = self.agents.get(a_id)
            agent_b = self.agents.get(b_id)

            if agent_a and agent_b:
                print(f"  {agent_a.name} vs {agent_b.name}:")
                print(f"    收益: ({result['payoff_a']:+.1f}, {result['payoff_b']:+.1f})")
                print(f"    冲突: {result['conflict_level']}")

        # 势力格局
        print("\n[势力格局]")
        for country, power in sorted(power_changes["by_country"].items(),
                                     key=lambda x: x[1], reverse=True):
            print(f"  {country.upper()}: {power:.2f}")

        # 联盟网络
        print("\n[主要联盟]")
        alliance_count = defaultdict(int)
        for agent in self.agents.values():
            if agent.allies:
                for ally in agent.allies:
                    key = tuple(sorted([agent.country, self.agents[ally].country]))
                    alliance_count[key] += 1

        for (c1, c2), count in sorted(alliance_count.items(),
                                     key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {c1.upper()}-{c2.upper()}: {count}个联盟")

        # 资源状态
        print("\n[资源状态 - 前10名]")
        resource_ranking = [(a.agent_id, a.resources, a.war_exhaustion)
                          for a in self.agents.values()]
        resource_ranking.sort(key=lambda x: x[1], reverse=True)

        for i, (aid, res, fatigue) in enumerate(resource_ranking[:10], 1):
            agent = self.agents[aid]
            print(f"  {i}. {agent.name}: 资源={res:.1f}, 疲劳={fatigue:.2f}")

    def run_full_simulation(self, scenario: str, context: str, rounds: int = 3):
        """运行完整模拟(同步包装)"""
        asyncio.run(self.run_full_simulation_async(scenario, context, rounds))

    async def run_full_simulation_async(self, scenario: str, context: str, rounds: int = 3):
        """异步运行完整模拟"""
        print(f"\n{'='*60}")
        print(f"多智能体政治模拟系统")
        print(f"{'='*60}")
        print(f"智能体数量: {len(self.agents)}")
        print(f"博弈对数: {len(self.agents)*(len(self.agents)-1)//2}")
        print(f"模拟轮数: {rounds}")
        print(f"LLM: {self.llm.provider}/{self.llm.model}")
        print(f"并行并发: 10")
        print(f"{'='*60}")

        for round_num in range(1, rounds + 1):
            await self.run_round_async(round_num, scenario, context)

        # 最终报告
        self._print_final_report()

    def _print_final_report(self):
        """打印最终报告"""
        print(f"\n{'='*60}")
        print("模拟结束 - 最终报告")
        print(f"{'='*60}")

        # 胜者排名
        print("\n[势力排名 - 综合国力]")
        final_ranking = []
        for agent in self.agents.values():
            # 综合分数 = 资源 * (1 - 战争疲劳)
            score = agent.resources * max(0.1, 1 - agent.war_exhaustion)
            final_ranking.append((agent.name, agent.country, score, agent.reputation))

        final_ranking.sort(key=lambda x: x[2], reverse=True)
        for i, (name, country, score, rep) in enumerate(final_ranking[:15], 1):
            print(f"  {i}. {name} ({country.upper()}): {score:.1f}分")

        # 联盟网络
        print("\n[最终联盟网络]")
        alliance_groups = self._identify_alliance_blocks()
        for i, group in enumerate(alliance_groups, 1):
            countries = [self.agents[a].country.upper() for a in group]
            print(f"  阵营{i}: {', '.join(set(countries))}")

        # 战争疲劳排名
        print("\n[战争疲劳 - 前5]")
        fatigue_ranking = [(a.name, a.war_exhaustion) for a in self.agents.values()]
        fatigue_ranking.sort(key=lambda x: x[1], reverse=True)
        for name, fatigue in fatigue_ranking[:5]:
            print(f"  {name}: {fatigue:.2f}")

    def _identify_alliance_blocks(self) -> List[Set[str]]:
        """识别联盟集团"""
        # 简化:按国家分组
        country_agents = defaultdict(set)
        for agent in self.agents.values():
            country_agents[agent.country].add(agent.agent_id)

        return list(country_agents.values())


# 全局实例
multi_agent_sim = MultiAgentPoliticalSimulation()

if __name__ == "__main__":
    print("=== 多智能体政治模拟系统 ===\n")

    sim = MultiAgentPoliticalSimulation()

    scenario = "波斯湾战争:伊朗封锁霍尔木兹海峡"
    context = "油价暴涨300%,全球能源危机"

    sim.run_full_simulation(scenario, context, rounds=2)
