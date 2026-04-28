"""
20轮完整外交模拟测试
测试所有扩展模块在实际轮次推进中的表现
"""

import sys
import os
import json
import random

sys.path.insert(0, 'app/services')

from diplomacy_integration import DiplomacyIntegration

# 配置5个国家
AGENT_CONFIGS = [
    {'agent_id': 'usa', 'name': '美国', 'stance': 'opposing', 'sentiment_bias': -0.3, 
     'political_system': 'democracy', 'nuclear_warheads': 5800, 'initial_approval': 0.55,
     'nuclear_second_strike': True, 'nuclear_delivery': 50},
    {'agent_id': 'china', 'name': '中国', 'stance': 'neutral', 'sentiment_bias': 0.0,
     'political_system': 'autocracy', 'nuclear_warheads': 350, 'no_first_use': True, 
     'initial_approval': 0.70, 'nuclear_second_strike': True, 'nuclear_delivery': 10},
    {'agent_id': 'russia', 'name': '俄罗斯', 'stance': 'opposing', 'sentiment_bias': 0.3,
     'political_system': 'hybrid', 'nuclear_warheads': 6500, 'initial_approval': 0.45,
     'nuclear_second_strike': True, 'nuclear_delivery': 55},
    {'agent_id': 'eu', 'name': '欧盟', 'stance': 'neutral', 'sentiment_bias': 0.0,
     'political_system': 'democracy', 'nuclear_warheads': 0, 'initial_approval': 0.50},
    {'agent_id': 'iran', 'name': '伊朗', 'stance': 'opposing', 'sentiment_bias': -0.5,
     'political_system': 'autocracy', 'nuclear_warheads': 0, 'initial_approval': 0.35},
]

# 外交事件模板
EVENT_TEMPLATES = [
    {'event_type': 'STATEMENT', 'desc': '发表声明'},
    {'event_type': 'CONDITIONS', 'desc': '提出条件'},
    {'event_type': 'BREAK', 'desc': '关系破裂'},
    {'event_type': 'ULTIMATUM', 'desc': '发出最后通牒'},
    {'event_type': 'SANCTION', 'desc': '实施制裁'},
    {'event_type': 'TRADE', 'desc': '贸易谈判'},
    {'event_type': 'MEETING', 'desc': '外交会晤'},
    {'event_type': 'WITHDRAW', 'desc': '撤军/让步'},
]

# 国家间关系矩阵（初始倾向）
RELATIONSHIP_BIAS = {
    ('usa', 'china'): -0.3,
    ('usa', 'russia'): -0.5,
    ('usa', 'eu'): 0.4,
    ('usa', 'iran'): -0.6,
    ('china', 'russia'): 0.2,
    ('china', 'eu'): 0.1,
    ('china', 'iran'): 0.3,
    ('russia', 'eu'): -0.3,
    ('russia', 'iran'): 0.4,
    ('eu', 'iran'): -0.4,
}

def get_relationship_bias(a1, a2):
    key = (a1, a2)
    if key not in RELATIONSHIP_BIAS:
        key = (a2, a1)
    return RELATIONSHIP_BIAS.get(key, 0.0)


def run_simulation(max_rounds=20):
    print("=" * 60)
    print("🌍 MiroFish 地缘政治外交模拟 - 20轮测试")
    print("=" * 60)
    
    # 初始化外交系统
    integration = DiplomacyIntegration('/tmp/test_sim', {
        'enable_game_theory_diplomacy': True,
        'escalation_ladder': True,
        'reputation_system': True,
    })
    
    integration.initialize(AGENT_CONFIGS)
    print("\n✅ 5个国家已初始化")
    for agent in AGENT_CONFIGS:
        nukes = f"☢️ {agent['nuclear_warheads']}" if agent['nuclear_warheads'] > 0 else ""
        print(f"   {agent['name']} ({agent['agent_id']}): {agent['political_system']} {nukes}")
    
    # 注册调解者
    if integration.mediation:
        integration.mediation.register_mediator('un', 'un', credibility=0.8, power=0.6)
        integration.mediation.register_mediator('eu', 'regional', credibility=0.7, power=0.5, region='europe')
    
    # 记录事件历史
    event_history = []
    war_events = []
    alliance_events = []
    sanction_events = []
    mediation_events = []
    
    agent_ids = [a['agent_id'] for a in AGENT_CONFIGS]
    
    for round_num in range(1, max_rounds + 1):
        print(f"\n{'='*60}")
        print(f"📅 第 {round_num} 轮")
        print(f"{'='*60}")
        
        # 每轮生成2-3个外交事件
        num_events = random.randint(2, 3)
        
        for _ in range(num_events):
            # 随机选择参与方
            actor, target = random.sample(agent_ids, 2)
            
            # 根据关系倾向选择事件类型
            bias = get_relationship_bias(actor, target)
            
            if bias < -0.4:
                # 敌对关系：更可能冲突但也有合作可能
                event_type = random.choices(
                    ['ULTIMATUM', 'SANCTION', 'STATEMENT', 'BREAK', 'TRADE'],
                    weights=[0.25, 0.25, 0.2, 0.15, 0.15]
                )[0]
            elif bias > 0.3:
                # 友好关系：更可能合作
                event_type = random.choices(
                    ['TRADE', 'MEETING', 'CONDITIONS', 'STATEMENT', 'WITHDRAW'],
                    weights=[0.35, 0.3, 0.15, 0.1, 0.1]
                )[0]
            else:
                # 中性关系：随机
                event_type = random.choice([e['event_type'] for e in EVENT_TEMPLATES])
            
            # 处理外交事件
            event = {
                'actor': actor,
                'target': target,
                'event_type': event_type,
            }
            
            result = integration.process_diplomatic_event(event, round_num)
            
            # 记录事件
            event_record = {
                'round': round_num,
                'actor': actor,
                'target': target,
                'event_type': event_type,
                'war_triggered': result['war_triggered'],
                'conflict_level': result['conflict_level'],
            }
            event_history.append(event_record)
            
            if result['war_triggered']:
                war_events.append(event_record)
                print(f"💥 {actor} → {target}: {event_type} → 战争爆发！")
            else:
                print(f"📊 {actor} → {target}: {event_type} → {result['conflict_level']}")
            
            # 核威慑信息
            if result.get('nuclear_deterrence') and result['nuclear_deterrence'].get('nuclear_escalation'):
                nd = result['nuclear_deterrence']
                print(f"   ☢️ 核威慑: {nd.get('decision', 'N/A')} (MAD: {nd.get('mad_probability', 0):.1%})")
            
            # 集体防御
            if result.get('collective_defenders'):
                defenders = result['collective_defenders']
                print(f"   🛡️ 集体防御触发: {', '.join(defenders)} 支援 {target}")
        
        # 随机尝试建立同盟（每轮1次）
        if random.random() < 0.3 and integration.alliance_system:
            proposer = random.choice(agent_ids)
            potential_targets = [a for a in agent_ids if a != proposer]
            targets = random.sample(potential_targets, random.randint(1, 2))
            alliance_type = random.choice(['defensive', 'economic', 'intelligence'])
            
            alliance = integration.propose_alliance(proposer, targets, alliance_type, round_num)
            if alliance:
                alliance_events.append({
                    'round': round_num,
                    'alliance': alliance,
                })
                print(f"🤝 同盟建立: {alliance['name']} ({', '.join(alliance['members'])})")
        
        # 随机实施制裁（每轮概率）
        if random.random() < 0.4 and integration.sanction_network:
            imposers = random.sample(agent_ids, random.randint(1, 2))
            potential_targets = [a for a in agent_ids if a not in imposers]
            if potential_targets:
                target = random.choice(potential_targets)
                sanction_type = random.choice(['trade', 'financial', 'technology'])
                severity = random.choice(['light', 'moderate', 'severe'])
                
                sanction = integration.impose_sanction(imposers, target, sanction_type, severity, round_num)
                if sanction:
                    sanction_events.append({
                        'round': round_num,
                        'sanction': sanction,
                    })
                    print(f"⚠️ 制裁: {', '.join(imposers)} → {target} ({severity}, 影响: {sanction['economic_impact']:.1%})")
        
        # 随机尝试调解（如果冲突严重）- 提高触发概率
        if random.random() < 0.5 and integration.mediation:
            parties = random.sample(agent_ids, 2)
            mediator = integration.mediation.find_best_mediator(parties, 'crisis', round_num)
            if mediator:
                attempt = integration.attempt_mediation(mediator, parties, round_num)
                if attempt:
                    mediation_events.append({
                        'round': round_num,
                        'attempt': attempt,
                    })
                    print(f"🕊️ 调解: {mediator} 调解 {' vs '.join(parties)} → {attempt['outcome']}")
        
        # 推进轮次
        integration.advance_round()
        
        # 打印轮次摘要
        summary = integration.get_summary()
        print(f"\n📈 第{round_num}轮摘要:")
        print(f"   活跃同盟: {summary.get('alliances', {}).get('active', 0)}")
        print(f"   活跃制裁: {summary.get('sanctions', {}).get('active', 0)}")
        print(f"   冲突状态: {summary['conflict_summary']}")
    
    # 最终报告
    print(f"\n{'='*60}")
    print("📊 20轮模拟最终报告")
    print(f"{'='*60}")
    
    print(f"\n💥 战争事件: {len(war_events)} 次")
    for war in war_events:
        print(f"   Round {war['round']}: {war['actor']} vs {war['target']}")
    
    print(f"\n🤝 同盟建立: {len(alliance_events)} 个")
    for ae in alliance_events:
        a = ae['alliance']
        print(f"   Round {ae['round']}: {a['name']} ({', '.join(a['members'])})")
    
    print(f"\n⚠️ 制裁实施: {len(sanction_events)} 次")
    for se in sanction_events:
        s = se['sanction']
        print(f"   Round {se['round']}: {', '.join(s['imposers'])} → {s['target']} ({s['severity']})")
    
    print(f"\n🕊️ 调解尝试: {len(mediation_events)} 次")
    for me in mediation_events:
        m = me['attempt']
        print(f"   Round {me['round']}: {m['mediator']} → {m['outcome']}")
    
    # 最终状态
    final_summary = integration.get_summary()
    print(f"\n🌍 最终外交状态:")
    print(f"   总轮次: {final_summary['round']}")
    print(f"   活跃同盟: {final_summary.get('alliances', {}).get('active', 0)}")
    print(f"   总制裁: {final_summary.get('sanctions', {}).get('total_sanctions', 0)}")
    print(f"   核大国: {final_summary.get('nuclear_powers', 0)}")
    
    print(f"\n🏛️ 各国最终状态:")
    for agent_id, state in final_summary.get('agent_states', {}).items():
        print(f"   {agent_id}: 声誉={state['reputation']:.2f}, 资源={state['resources']:.1f}, 战争疲劳={state['war_exhaustion']:.2f}")
    
    # 保存结果
    results = {
        'total_rounds': max_rounds,
        'war_events': war_events,
        'alliance_events': alliance_events,
        'sanction_events': sanction_events,
        'mediation_events': mediation_events,
        'final_summary': final_summary,
        'event_history': event_history,
    }
    
    with open('/tmp/mirofish/backend/test_20rounds_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ 结果已保存到 test_20rounds_results.json")
    print("🎉 20轮模拟完成！")
    
    return results


if __name__ == '__main__':
    results = run_simulation(20)
