"""
Game Theory Diplomacy Test - 博弈论外交系统测试
"""

import sys
sys.path.insert(0, '/tmp/mirofish/backend/app/services')

from game_theory_diplomacy import (
    GameTheoryDiplomacy, DiplomaticAction, ConflictLevel
)

def test_basic_mechanics():
    """测试基本机制"""
    print("=== 测试 1: 基本收益矩阵 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "a", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "b", "stance": "neutral", "sentiment_bias": 0},
    ])
    
    # 双方都合作 → 双赢
    result = d.calculate_diplomatic_outcome("a", "b", 
                                             DiplomaticAction.COOPERATE, 
                                             DiplomaticAction.COOPERATE)
    print(f"合作+合作: 成功={result['success']}, 收益A={result['payoff_a']:.1f}, 收益B={result['payoff_b']:.1f}")
    
    # A合作, B背叛 → A被利用
    result = d.calculate_diplomatic_outcome("a", "b",
                                             DiplomaticAction.COOPERATE,
                                             DiplomaticAction.DEFECT)
    print(f"合作+背叛: 成功={result['success']}, 收益A={result['payoff_a']:.1f}, 背叛={result['betrayal_by_b']}")
    
    # 双方都背叛 → 双输
    result = d.calculate_diplomatic_outcome("a", "b",
                                             DiplomaticAction.DEFECT,
                                             DiplomaticAction.DEFECT)
    print(f"背叛+背叛: 成功={result['success']}, 收益A={result['payoff_a']:.1f}, 收益B={result['payoff_b']:.1f}")

def test_escalation():
    """测试升级阶梯"""
    print("\n=== 测试 2: 冲突升级 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "iran", "stance": "opposing", "sentiment_bias": -0.3},
    ])
    
    # 连续升级
    actions = [
        (DiplomaticAction.DETER, DiplomaticAction.DETER),      # 威慑对威慑
        (DiplomaticAction.ESCALATE, DiplomaticAction.DETER),     # 升级对威慑
        (DiplomaticAction.ESCALATE, DiplomaticAction.ESCALATE), # 升级对升级
        (DiplomaticAction.ESCALATE, DiplomaticAction.ESCALATE), # 继续升级
    ]
    
    for i, (a_action, b_action) in enumerate(actions):
        result = d.calculate_diplomatic_outcome("usa", "iran", a_action, b_action)
        print(f"Round {i}: {a_action.value} vs {b_action.value} → {result['conflict_level']}")
        d.advance_round()

def test_reputation():
    """测试声誉系统"""
    print("\n=== 测试 3: 声誉影响 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "trustworthy", "stance": "supportive", "sentiment_bias": 0.3},
        {"agent_id": "traitor", "stance": "opposing", "sentiment_bias": -0.3},
    ])
    
    # trustworthy 一直合作
    for _ in range(3):
        d.calculate_diplomatic_outcome("trustworthy", "traitor",
                                        DiplomaticAction.COOPERATE,
                                        DiplomaticAction.COOPERATE)
        d.advance_round()
    
    print(f"Trustworthy 声誉: {d.agents['trustworthy'].reputation:.2f}")
    
    # traitor 背叛
    d.calculate_diplomatic_outcome("traitor", "trustworthy",
                                  DiplomaticAction.DEFECT,
                                  DiplomaticAction.COOPERATE)
    
    print(f"Traitor 背叛后声誉: {d.agents['traitor'].reputation:.2f}")
    print(f"Trustworthy 被背叛后信任: {d.agents['trustworthy'].get_trust('traitor'):.2f}")

def test_war_exhaustion():
    """测试战争疲劳"""
    print("\n=== 测试 4: 战争疲劳 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "aggressive", "stance": "opposing", "sentiment_bias": -0.5},
        {"agent_id": "defensive", "stance": "neutral", "sentiment_bias": 0},
    ])
    
    # 连续升级
    for i in range(5):
        d.calculate_diplomatic_outcome("aggressive", "defensive",
                                        DiplomaticAction.ESCALATE,
                                        DiplomaticAction.DETER)
        print(f"Round {i}: Aggressive 战争疲劳={d.agents['aggressive'].war_exhaustion:.2f}, "
              f"资源={d.agents['aggressive'].resources:.1f}")
        d.advance_round()

def test_strategy_adaptation():
    """测试策略适应"""
    print("\n=== 测试 5: 策略适应 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "tit_for_tat", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "always_defect", "stance": "opposing", "sentiment_bias": -0.5},
    ])
    
    # always_defect 一直背叛
    for i in range(5):
        result = d.calculate_diplomatic_outcome("tit_for_tat", "always_defect",
                                                DiplomaticAction.COOPERATE,
                                                DiplomaticAction.DEFECT)
        print(f"Round {i}: tit_for_tat 信任度={d.agents['tit_for_tat'].get_trust('always_defect'):.2f}")
        d.advance_round()
    
    # 现在 tit_for_tat 应该学会背叛
    action = d.get_agent_strategy("tit_for_tat", "always_defect",
                                  [DiplomaticAction.COOPERATE, DiplomaticAction.DEFECT,
                                   DiplomaticAction.DETER])
    print(f"第6轮 tit_for_tat 选择: {action.value}")

def test_diplomatic_scenarios():
    """测试外交场景"""
    print("\n=== 测试 6: 外交场景模拟 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "china", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "russia", "stance": "opposing", "sentiment_bias": 0.3},
        {"agent_id": "eu", "stance": "neutral", "sentiment_bias": 0},
    ])
    
    # 场景1: 中美贸易战
    print("\n场景1: 中美贸易谈判")
    result = d.calculate_diplomatic_outcome("usa", "china",
                                             DiplomaticAction.NEGOTIATE,
                                             DiplomaticAction.NEGOTIATE)
    print(f"结果: 成功={result['success']}, 冲突级别={result['conflict_level']}")
    
    # 场景2: 俄欧紧张
    print("\n场景2: 俄欧制裁")
    result = d.calculate_diplomatic_outcome("russia", "eu",
                                             DiplomaticAction.SANCTION,
                                             DiplomaticAction.DETER)
    print(f"结果: 成功={result['success']}, 冲突级别={result['conflict_level']}")
    
    # 场景3: 中美升级
    print("\n场景3: 中美升级")
    result = d.calculate_diplomatic_outcome("usa", "china",
                                             DiplomaticAction.ESCALATE,
                                             DiplomaticAction.ESCALATE)
    print(f"结果: 成功={result['success']}, 冲突级别={result['conflict_level']}")
    
    d.advance_round()
    
    # 场景4: 欧盟调解
    print("\n场景4: 欧盟调解中美")
    result = d.calculate_diplomatic_outcome("eu", "usa",
                                             DiplomaticAction.NEGOTIATE,
                                             DiplomaticAction.COOPERATE)
    print(f"结果: 成功={result['success']}, 冲突级别={result['conflict_level']}")

if __name__ == "__main__":
    print("🎮 博弈论外交系统测试开始\n")
    
    test_basic_mechanics()
    test_escalation()
    test_reputation()
    test_war_exhaustion()
    test_strategy_adaptation()
    test_diplomatic_scenarios()
    
    print("\n✅ 所有测试完成!")
