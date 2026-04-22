"""
MiroFish 博弈论集成示例
展示如何将博弈论增强Agent集成到MiroFish模拟中

使用方法:
    from game_theory_integration import integrate_gt_to_simulation
    integrate_gt_to_simulation(simulation_config)
"""

from typing import Dict, List, Optional

try:
    from . import GameTheoreticAgent, GameTheoreticConfig, create_game_theoretic_agent
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from game_theory import GameTheoreticAgent, GameTheoreticConfig, create_game_theoretic_agent


def create_gt_agents_from_mirofish_entities(entities: List[Dict], gt_enabled: bool = True) -> List[GameTheoreticAgent]:
    """
    从MiroFish实体配置创建博弈论增强Agent
    
    Args:
        entities: MiroFish实体列表
        gt_enabled: 是否启用博弈论
        
    Returns:
        GameTheoreticAgent列表
    """
    agents = []
    
    for entity in entities:
        gt_config = GameTheoreticConfig(
            enabled=gt_enabled,
            game_type='market',  # 可以是 market/signaling/repeated
            risk_preference=0.5,  # 基于sentiment_bias调整
            belief_update_rate=0.3,
            memory_depth=5
        )
        
        # 根据实体类型调整风险偏好
        entity_type = entity.get('entity_type', 'Person')
        if entity_type in ['FundManager', 'Organization']:
            gt_config.risk_preference = 0.3  # 机构更保守
        elif entity_type in ['RetailInvestor']:
            gt_config.risk_preference = 0.7  # 散户更激进
        
        agent = create_game_theoretic_agent(entity, gt_config)
        agents.append(agent)
    
    return agents


def build_game_from_market_state(agents: List[GameTheoreticAgent], market_state: Dict) -> Dict:
    """
    从市场状态构建博弈结构
    
    Args:
        agents: 博弈论Agent列表
        market_state: 市场状态（价格、趋势、支撑等）
        
    Returns:
        博弈结果摘要
    """
    results = {
        'agents': [],
        'equilibrium': None,
        'recommended_actions': {}
    }
    
    # 初始化重复博弈
    opponent_names = [a.name for a in agents[1:]] if len(agents) > 1 else []
    if opponent_names and len(agents) > 0:
        agents[0].init_repeated_game(opponent_names)
    
    # 收集市场状态
    context = {
        'price': market_state.get('price', 2300),
        'price_trend': market_state.get('trend', 'neutral'),
        'support_level': market_state.get('support', 2280),
        'volume': market_state.get('volume', 'normal')
    }
    
    # 为每个Agent计算决策
    for i, agent in enumerate(agents):
        other_agents = [{'entity_name': a.name, 'stance': 'neutral'} for a in agents[:i] + agents[i+1:]]
        recent_actions = market_state.get('recent_actions', [])
        
        observation = agent.observe(other_agents, recent_actions)
        decision = agent.decide_action(context, observation)
        
        results['agents'].append({
            'name': agent.name,
            'decision': decision,
            'profile': agent.get_strategy_profile()
        })
        results['recommended_actions'][agent.name] = decision.get('action', 'hold')
    
    # 分析整体均衡
    actions = list(results['recommended_actions'].values())
    if actions.count('buy') > actions.count('sell') * 2:
        results['equilibrium'] = 'bullish_dominant'
    elif actions.count('sell') > actions.count('buy') * 2:
        results['equilibrium'] = 'bearish_dominant'
    else:
        results['equilibrium'] = 'mixed'
    
    return results


def run_gt_simulation_round(agents: List[GameTheoreticAgent], market_data: Dict) -> Dict:
    """
    运行一轮博弈论增强模拟
    
    这是对MiroFish原生模拟的增强
    """
    round_result = {
        'round': market_data.get('round', 0),
        'agent_decisions': [],
        'market_impact': {}
    }
    
    # 构建博弈
    game_result = build_game_from_market_state(agents, market_data)
    
    # 记录决策
    for agent_result in game_result['agents']:
        decision = agent_result['decision']
        round_result['agent_decisions'].append({
            'agent': agent_result['name'],
            'action': decision.get('action'),
            'reasoning': decision.get('reasoning'),
            'gt_analysis': decision.get('gt_analysis', {})
        })
        
        # 更新Agent状态（从结果学习）
        payoff = _calculate_payoff(decision.get('action'), market_data)
        agent_result['profile'].update_from_result(decision.get('action'), payoff)
    
    # 评估市场影响
    actions = [d['action'] for d in round_result['agent_decisions']]
    if actions.count('buy') > actions.count('sell'):
        round_result['market_impact']['pressure'] = 'upward'
    else:
        round_result['market_impact']['pressure'] = 'downward'
    
    return round_result


def _calculate_payoff(action: str, market_data: Dict) -> float:
    """计算行动的支付（简化版）"""
    price_change = market_data.get('price_change', 0)
    
    if action == 'buy':
        return price_change if price_change > 0 else price_change * 0.5
    elif action == 'sell':
        return -price_change if price_change < 0 else -price_change * 0.5
    else:
        return 0.0


def analyze_game_equilibrium(agents: List[GameTheoreticAgent]) -> Dict:
    """
    分析多Agent博弈的均衡状态
    
    Returns:
        均衡分析报告
    """
    all_strategies = {}
    
    for agent in agents:
        profile = agent.get_strategy_profile()
        all_strategies[agent.name] = profile.get('payoff_trend', 'unknown')
    
    # 检查是否收敛
    trends = list(all_strategies.values())
    is_converging = trends.count(trends[0]) / len(trends) > 0.7 if trends else False
    
    return {
        'agents': all_strategies,
        'convergence': is_converging,
        'equilibrium_type': 'correlated' if is_converging else 'none',
        'stability': 'high' if is_converging else 'unstable'
    }


# 使用示例
if __name__ == "__main__":
    # 从MiroFish实体创建Agent
    sample_entities = [
        {'entity_name': '李明', 'entity_type': 'Person', 'stance': 'neutral', 'sentiment_bias': 0.2},
        {'entity_name': '王总', 'entity_type': 'FundManager', 'stance': 'neutral', 'sentiment_bias': 0.1},
        {'entity_name': '张矿工', 'entity_type': 'Miner', 'stance': 'opposing', 'sentiment_bias': -0.3},
    ]
    
    agents = create_gt_agents_from_mirofish_entities(sample_entities, gt_enabled=True)
    
    # 模拟市场状态
    market_state = {
        'price': 2310,
        'trend': '下降',
        'support': 2280,
        'volume': 'high',
        'recent_actions': [
            {'agent_name': '李明', 'action_type': 'CREATE_POST'},
            {'agent_name': '王总', 'action_type': 'CREATE_POST'},
        ],
        'price_change': -2.5
    }
    
    # 运行博弈
    result = build_game_from_market_state(agents, market_state)
    
    print("=" * 50)
    print("博弈论增强模拟结果")
    print("=" * 50)
    for agent_result in result['agents']:
        print(f"\n{agent_result['name']}:")
        print(f"  行动: {agent_result['decision'].get('action')}")
        print(f"  推理: {agent_result['decision'].get('reasoning')}")
    
    print(f"\n市场均衡: {result['equilibrium']}")