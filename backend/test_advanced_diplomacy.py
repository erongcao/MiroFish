"""
Advanced Diplomacy Tests - 高级外交机制测试
测试联盟、调解、多边外交
"""

import sys
sys.path.insert(0, '/tmp/mirofish/backend/app/services')

from game_theory_diplomacy import (
    GameTheoryDiplomacy, DiplomaticAction, ConflictLevel
)

def test_alliance_mechanics():
    """测试联盟机制"""
    print("=== 测试 1: 联盟形成 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "uk", "stance": "supportive", "sentiment_bias": 0.3},
        {"agent_id": "france", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "russia", "stance": "opposing", "sentiment_bias": 0.3},
    ])
    
    # 美英合作建立信任
    for _ in range(3):
        d.calculate_diplomatic_outcome("usa", "uk",
                                        DiplomaticAction.COOPERATE,
                                        DiplomaticAction.COOPERATE)
        d.advance_round()
    
    trust_usa_uk = d.agents["usa"].get_trust("uk")
    print(f"美英信任度: {trust_usa_uk:.2f}")
    
    # 美法合作
    for _ in range(2):
        d.calculate_diplomatic_outcome("usa", "france",
                                        DiplomaticAction.COOPERATE,
                                        DiplomaticAction.COOPERATE)
        d.advance_round()
    
    # 英美法 vs 俄罗斯
    print("\n联盟 vs 俄罗斯:")
    result = d.calculate_diplomatic_outcome("usa", "russia",
                                             DiplomaticAction.DETER,
                                             DiplomaticAction.DETER)
    print(f"USA 威慑俄罗斯: 冲突级别={result['conflict_level']}")
    
    # 英国支持美国
    result = d.calculate_diplomatic_outcome("uk", "russia",
                                             DiplomaticAction.DETER,
                                             DiplomaticAction.DETER)
    print(f"UK 威慑俄罗斯: 冲突级别={result['conflict_level']}")

def test_third_party_mediation():
    """测试第三方调解"""
    print("\n=== 测试 2: 第三方调解 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "israel", "stance": "opposing", "sentiment_bias": -0.5},
        {"agent_id": "iran", "stance": "opposing", "sentiment_bias": -0.5},
        {"agent_id": "un", "stance": "neutral", "sentiment_bias": 0},
    ])
    
    # 以伊冲突升级
    for _ in range(3):
        d.calculate_diplomatic_outcome("israel", "iran",
                                        DiplomaticAction.ESCALATE,
                                        DiplomaticAction.ESCALATE)
        d.advance_round()
    
    conflict_key = f"{min('israel', 'iran')}|{max('israel', 'iran')}"
    print(f"以伊冲突级别: {d.conflict_levels[conflict_key].value}")
    
    # 联合国调解
    print("\n联合国调解:")
    # 调解者通过谈判降低紧张度
    result = d.calculate_diplomatic_outcome("un", "israel",
                                           DiplomaticAction.NEGOTIATE,
                                           DiplomaticAction.COOPERATE)
    print(f"UN 调解以色列: 成功={result['success']}")
    
    # 调解成功可能降低冲突级别
    if result['success']:
        current = d.conflict_levels[conflict_key]
        if current == ConflictLevel.CRISIS:
            d.conflict_levels[conflict_key] = ConflictLevel.TENSION
        elif current == ConflictLevel.TENSION:
            d.conflict_levels[conflict_key] = ConflictLevel.PEACE
        print(f"调解后冲突级别: {d.conflict_levels[conflict_key].value}")

def test_multilateral_diplomacy():
    """测试多边外交"""
    print("\n=== 测试 3: 多边外交 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "china", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "russia", "stance": "opposing", "sentiment_bias": 0.3},
        {"agent_id": "eu", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "india", "stance": "neutral", "sentiment_bias": 0},
    ])
    
    # 多边会议
    print("G5 峰会:")
    agents = ["usa", "china", "russia", "eu", "india"]
    
    # 每对进行外交
    for i, a in enumerate(agents):
        for b in agents[i+1:]:
            # 峰会期间倾向于合作
            action_a = DiplomaticAction.COOPERATE if d.agents[a].cooperation_bias > 0.4 else DiplomaticAction.NEGOTIATE
            action_b = DiplomaticAction.COOPERATE if d.agents[b].cooperation_bias > 0.4 else DiplomaticAction.NEGOTIATE
            
            result = d.calculate_diplomatic_outcome(a, b, action_a, action_b)
            if result['success']:
                print(f"  {a}-{b}: 达成协议")
            else:
                print(f"  {a}-{b}: 谈判破裂")
    
    # 统计合作成果
    peace_count = sum(1 for level in d.conflict_levels.values() if level == ConflictLevel.PEACE)
    print(f"\n峰会后和平关系: {peace_count}/{len(d.conflict_levels)}")

def test_nuclear_deterrence():
    """测试核威慑特殊机制"""
    print("\n=== 测试 4: 核威慑 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "russia", "stance": "opposing", "sentiment_bias": 0.3},
    ])
    
    # 核大国直接冲突
    print("核大国对峙:")
    
    # 第一轮: 威慑
    result = d.calculate_diplomatic_outcome("usa", "russia",
                                           DiplomaticAction.DETER,
                                           DiplomaticAction.DETER)
    print(f"威慑对威慑: {result['conflict_level']}")
    
    # 第二轮: 一方升级
    result = d.calculate_diplomatic_outcome("usa", "russia",
                                           DiplomaticAction.ESCALATE,
                                           DiplomaticAction.DETER)
    print(f"升级对威慑: {result['conflict_level']}")
    
    # 第三轮: 双方升级（核战争风险）
    result = d.calculate_diplomatic_outcome("usa", "russia",
                                           DiplomaticAction.ESCALATE,
                                           DiplomaticAction.ESCALATE)
    print(f"升级对升级: {result['conflict_level']}")
    
    # 核战争阈值检查
    conflict_key = f"{min('usa', 'russia')}|{max('usa', 'russia')}"
    if d.conflict_levels[conflict_key] in [ConflictLevel.LIMITED_WAR, ConflictLevel.TOTAL_WAR]:
        print("⚠️  核战争风险！")
        # 核威慑可能触发"相互确保毁灭"
        print("触发 MAD 机制: 双方收益归零")

def test_economic_sanctions():
    """测试经济制裁网络"""
    print("\n=== 测试 5: 经济制裁 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "china", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "eu", "stance": "neutral", "sentiment_bias": 0},
        {"agent_id": "russia", "stance": "opposing", "sentiment_bias": 0.3},
    ])
    
    # 美国制裁俄罗斯
    print("美国制裁俄罗斯:")
    result = d.calculate_diplomatic_outcome("usa", "russia",
                                           DiplomaticAction.SANCTION,
                                           DiplomaticAction.DETER)
    print(f"制裁结果: 成功={result['success']}, 冲突={result['conflict_level']}")
    print(f"俄罗斯资源: {d.agents['russia'].resources:.1f}")
    
    # 欧盟跟随制裁
    print("\n欧盟跟随制裁:")
    result = d.calculate_diplomatic_outcome("eu", "russia",
                                           DiplomaticAction.SANCTION,
                                           DiplomaticAction.DETER)
    print(f"联合制裁结果: 成功={result['success']}")
    print(f"俄罗斯资源(双重制裁): {d.agents['russia'].resources:.1f}")
    
    # 中国不制裁（合作）
    print("\n中国不制裁（与俄罗斯合作）:")
    result = d.calculate_diplomatic_outcome("china", "russia",
                                           DiplomaticAction.COOPERATE,
                                           DiplomaticAction.COOPERATE)
    print(f"中俄合作: 成功={result['success']}")

def test_crisis_escalation_management():
    """测试危机升级管理"""
    print("\n=== 测试 6: 危机管理 ===")
    
    d = GameTheoryDiplomacy()
    d.initialize_agents([
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "china", "stance": "neutral", "sentiment_bias": 0},
    ])
    
    # 逐步升级
    stages = [
        (DiplomaticAction.DETER, DiplomaticAction.DETER, "威慑"),
        (DiplomaticAction.DETER, DiplomaticAction.ESCALATE, "一方升级"),
        (DiplomaticAction.ESCALATE, DiplomaticAction.ESCALATE, "双方升级"),
        (DiplomaticAction.ESCALATE, DiplomaticAction.ESCALATE, "继续升级"),
        (DiplomaticAction.NEGOTIATE, DiplomaticAction.NEGOTIATE, "紧急谈判"),
    ]
    
    for i, (a_action, b_action, desc) in enumerate(stages):
        result = d.calculate_diplomatic_outcome("usa", "china", a_action, b_action)
        print(f"阶段 {i+1} ({desc}): {result['conflict_level']}")
        
        if result['conflict_level'] in ['limited_war', 'total_war']:
            print("⚠️  战争爆发！测试停止")
            break
        
        d.advance_round()

def test_agent_personality_types():
    """测试不同性格类型的 Agent"""
    print("\n=== 测试 7: Agent 性格类型 ===")
    
    personalities = [
        ("hawk", "opposing", -0.5, "鹰派"),
        ("dove", "supportive", 0.5, "鸽派"),
        ("realist", "neutral", 0, "现实主义者"),
        ("opportunist", "neutral", -0.2, "机会主义者"),
    ]
    
    for agent_id, stance, sentiment, name in personalities:
        d = GameTheoryDiplomacy()
        d.initialize_agents([
            {"agent_id": agent_id, "stance": stance, "sentiment_bias": sentiment},
            {"agent_id": "opponent", "stance": "neutral", "sentiment_bias": 0},
        ])
        
        # 测试策略选择
        action = d.get_agent_strategy(agent_id, "opponent",
                                      [DiplomaticAction.COOPERATE, DiplomaticAction.DEFECT,
                                       DiplomaticAction.DETER, DiplomaticAction.ESCALATE])
        
        print(f"{name} ({agent_id}): 选择 {action.value}")
        print(f"  攻击性={d.agents[agent_id].aggression:.2f}, 合作倾向={d.agents[agent_id].cooperation_bias:.2f}")

if __name__ == "__main__":
    print("🎮 高级外交机制测试开始\n")
    
    test_alliance_mechanics()
    test_third_party_mediation()
    test_multilateral_diplomacy()
    test_nuclear_deterrence()
    test_economic_sanctions()
    test_crisis_escalation_management()
    test_agent_personality_types()
    
    print("\n✅ 所有高级测试完成!")
