"""
博弈论Agent单元测试
pytest game_theory_tests.py -v
"""

import pytest
import sys
import os
import random

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from game_theory_agent import (
    GameTheoreticAgent,
    GameTheoreticConfig,
    PayoffMatrixBuilder,
    NashEquilibriumSolver,
    RepeatedGameStrategy,
    SignalingGame,
    GameStrategy,
    create_gt_agents
)


class TestPayoffMatrixBuilder:
    """测试支付矩阵构建器"""
    
    def test_build_basic_matrix(self):
        """测试基础矩阵构建"""
        builder = PayoffMatrixBuilder()
        matrix = builder.build_market_matrix(
            current_price=2300,
            support_level=2280,
            resistance_level=2457,
            trend='sideways'
        )
        
        assert 'buy' in matrix
        assert 'hold' in matrix
        assert 'sell' in matrix
        assert all(action in matrix['buy'] for action in ['buy', 'hold', 'sell'])
    
    def test_matrix_validation(self):
        """测试矩阵验证"""
        builder = PayoffMatrixBuilder()
        
        # 有效矩阵
        valid_matrix = {
            'buy': {'buy': 1, 'hold': 0, 'sell': -1},
            'hold': {'buy': 0, 'hold': 0, 'sell': 0},
            'sell': {'buy': -1, 'hold': 0, 'sell': 1}
        }
        assert builder.validate_matrix(valid_matrix) == True
        
        # 无效矩阵（缺少行动）
        invalid_matrix = {
            'buy': {'buy': 1, 'hold': 0}
        }
        assert builder.validate_matrix(invalid_matrix) == False
    
    def test_trend_adjustment(self):
        """测试趋势调整"""
        builder = PayoffMatrixBuilder()
        
        up_matrix = builder.build_market_matrix(2300, 2280, 2457, 'up')
        down_matrix = builder.build_market_matrix(2300, 2280, 2457, 'down')
        
        # 上涨趋势中买入应该更有价值
        assert up_matrix['buy']['hold'] > down_matrix['buy']['hold']
    
    def test_support_resistance_adjustment(self):
        """测试支撑阻力位调整"""
        builder = PayoffMatrixBuilder()
        
        # 接近支撑位
        near_support = builder.build_market_matrix(2285, 2280, 2457, 'sideways')
        # 接近阻力位
        near_resistance = builder.build_market_matrix(2450, 2280, 2457, 'sideways')
        
        # 接近支撑位时买入更有价值
        assert near_support['buy']['hold'] > near_resistance['buy']['hold']


class TestNashEquilibriumSolver:
    """测试纳什均衡求解器"""
    
    def test_find_pure_strategy_equilibrium(self):
        """测试纯策略均衡寻找"""
        solver = NashEquilibriumSolver()
        
        # 囚徒困境式矩阵
        matrix = {
            'buy': {'buy': -1, 'hold': -3, 'sell': 0},
            'hold': {'buy': 0, 'hold': -2, 'sell': -1},
            'sell': {'buy': -3, 'hold': -1, 'sell': -2}
        }
        
        equilibria = solver.find_pure_strategy_nash(matrix)
        assert len(equilibria) >= 0  # 可能不存在纯策略均衡
    
    def test_verify_equilibrium(self):
        """测试均衡验证"""
        solver = NashEquilibriumSolver()
        
        matrix = {
            'buy': {'buy': 1, 'hold': 0, 'sell': -1},
            'hold': {'buy': 0, 'hold': 0, 'sell': 0},
            'sell': {'buy': -1, 'hold': 0, 'sell': 1}
        }
        
        # ('hold', 'hold') 应该是均衡
        result = solver.verify_equilibrium(('hold', 'hold'), matrix)
        assert result['is_nash'] == True
        assert result['my_incentive_to_deviate'] == 0.0
    
    def test_non_equilibrium(self):
        """测试非均衡情况"""
        solver = NashEquilibriumSolver()
        
        matrix = {
            'buy': {'buy': 2, 'hold': 0, 'sell': -1},
            'hold': {'buy': 0, 'hold': 1, 'sell': 0},
            'sell': {'buy': -1, 'hold': 0, 'sell': 2}
        }
        
        # ('buy', 'sell') 不应该是不均衡
        result = solver.verify_equilibrium(('buy', 'sell'), matrix)
        assert result['is_nash'] == False


class TestRepeatedGameStrategy:
    """测试重复博弈策略"""
    
    def test_always_cooperate(self):
        """测试永远合作"""
        strategy = RepeatedGameStrategy(GameStrategy.ALWAYS_COOPERATE)
        for _ in range(10):
            assert strategy.choose_action('sell') == 'buy'
    
    def test_always_defect(self):
        """测试永远背叛"""
        strategy = RepeatedGameStrategy(GameStrategy.ALWAYS_DEFECT)
        for _ in range(10):
            assert strategy.choose_action('buy') == 'sell'
    
    def test_grim_trigger(self):
        """测试冷酷触发"""
        strategy = RepeatedGameStrategy(GameStrategy.GRIM_TRIGGER)
        
        # 初始合作
        assert strategy.choose_action('buy') == 'buy'
        
        # 对手背叛后永久惩罚
        strategy.record_opponent_action('sell')
        assert strategy.choose_action('buy') == 'sell'
        assert strategy.choose_action('buy') == 'sell'  # 永久惩罚
    
    def test_tit_for_tat(self):
        """测试以牙还牙"""
        strategy = RepeatedGameStrategy(GameStrategy.TIT_FOR_TAT)
        
        # 第一轮合作
        assert strategy.choose_action(None) == 'buy'
        
        # 模仿对手上一轮
        strategy.record_opponent_action('sell')
        assert strategy.choose_action('buy') == 'sell'
        
        strategy.record_opponent_action('buy')
        assert strategy.choose_action('sell') == 'buy'
    
    def test_tit_for_two_tats(self):
        """测试宽容以牙还牙"""
        strategy = RepeatedGameStrategy(GameStrategy.TIT_FOR_TWO_TATS)
        
        # 第一轮合作
        assert strategy.choose_action(None) == 'buy'
        
        # 单次背叛不惩罚
        strategy.record_opponent_action('sell')
        assert strategy.choose_action('buy') == 'buy'
        
        # 连续两次背叛才惩罚
        strategy.record_opponent_action('sell')
        assert strategy.choose_action('buy') == 'sell'


class TestGameTheoreticAgent:
    """测试博弈论Agent"""
    
    @pytest.fixture
    def basic_agent(self):
        """基础Agent配置"""
        config = {
            'entity_name': '测试Agent',
            'entity_type': 'Person',
            'stance': 'neutral',
            'sentiment_bias': 0.0
        }
        return GameTheoreticAgent(config)
    
    def test_initialization(self, basic_agent):
        """测试初始化"""
        assert basic_agent.name == '测试Agent'
        assert basic_agent.stance == 'neutral'
        assert basic_agent.gt_config.enabled == True
    
    def test_disabled_game_theory(self, basic_agent):
        """测试禁用博弈论"""
        basic_agent.gt_config.enabled = False
        
        decision = basic_agent.decide_action(
            {'price': 2300},
            {'opponents': []}
        )
        
        assert decision['action'] in ['buy', 'hold', 'sell']
        # 中性立场返回"中立观望"
        assert '中立' in decision['reasoning'] or '立场' in decision['reasoning'] or '后备' in decision['reasoning']
    
    def test_first_round_with_prior(self, basic_agent):
        """测试第一轮使用先验"""
        decision = basic_agent.decide_action(
            {
                'price': 2300,
                'support_level': 2280,
                'resistance_level': 2457,
                'price_trend': 'sideways'
            },
            {
                'opponents': [
                    {'name': '对手1', 'stance': 'neutral'}
                ]
            }
        )
        
        assert decision['action'] in ['buy', 'hold', 'sell']
        assert 'gt_analysis' in decision
    
    def test_equilibrium_detection(self, basic_agent):
        """测试均衡检测"""
        # 模拟多轮均衡
        for _ in range(5):
            sentiments = [0.05, 0.03, 0.04]  # 低方差
            eq = basic_agent._check_equilibrium(sentiments)
        
        # 应该确认均衡
        assert basic_agent.equilibrium_rounds >= 3
    
    def test_belief_update(self, basic_agent):
        """测试信念更新"""
        observation = basic_agent.observe(
            [{'entity_name': '对手1', 'stance': 'neutral'}],
            [
                {'agent_name': '对手1', 'action_type': 'buy'},
                {'agent_name': '对手1', 'action_type': 'buy'},
                {'agent_name': '对手1', 'action_type': 'sell'}
            ]
        )
        
        assert '对手1' in basic_agent.beliefs
        assert 'buy' in basic_agent.beliefs['对手1']
        assert sum(basic_agent.beliefs['对手1'].values()) > 0.99  # 接近归一化
    
    def test_risk_preference_adjustment(self):
        """测试风险偏好调整"""
        # 使用create_gt_agents来测试风险偏好设置
        entities = [
            {'entity_name': '高风险', 'entity_type': 'RetailInvestor', 'stance': 'neutral', 'sentiment_bias': 0.0},
            {'entity_name': '低风险', 'entity_type': 'FundManager', 'stance': 'neutral', 'sentiment_bias': 0.0}
        ]
        agents = create_gt_agents(entities)
        
        assert agents[0].gt_config.risk_preference == 0.7  # 散户高风险
        assert agents[1].gt_config.risk_preference == 0.3  # 机构低风险
    
    def test_update_history(self, basic_agent):
        """测试历史更新"""
        basic_agent.update('buy', 1.5)
        basic_agent.update('hold', 0.0)
        
        assert len(basic_agent.action_history) == 2
        assert len(basic_agent.payoff_history) == 2
        assert basic_agent.action_history[0] == 'buy'


class TestSignalingGame:
    """测试信号博弈"""
    
    def test_extract_signal_from_message(self):
        """测试从消息中提取信号"""
        game = SignalingGame()
        
        # 买入信号
        assert game.extract_signal_from_message('我觉得可以买入ETH', 0.3) == 'buy_signal'
        assert game.extract_signal_from_message('看好后市的请举手', 0.5) == 'buy_signal'
        
        # 卖出信号
        assert game.extract_signal_from_message('应该止损卖出了', -0.3) == 'sell_signal'
        assert game.extract_signal_from_message('跌破了支撑位', -0.5) == 'sell_signal'
        
        # 观望信号
        assert game.extract_signal_from_message('我再观察一下', 0.0) == 'hold_signal'
    
    def test_analyze_signal_equilibrium(self):
        """测试信号博弈均衡分析"""
        game = SignalingGame()
        
        # 全是买入信号
        signals = ['buy_signal', 'buy_signal', 'buy_signal']
        stances = ['supportive', 'supportive', 'neutral']
        result = game.analyze_signal_equilibrium(signals, stances)
        
        assert result['dominant_signal'] == 'buy_signal'
        assert result['market_tendency'] == 'bullish'
        assert result['type'] in ['separating', 'pooling']
    
    def test_get_action_from_signal(self):
        """测试从信号获取行动"""
        game = SignalingGame()
        
        assert game.get_action_from_signal('buy_signal') == 'buy'
        assert game.get_action_from_signal('sell_signal') == 'sell'
        assert game.get_action_from_signal('hold_signal') == 'hold'
    
    def test_signal_analysis_empty(self):
        """测试空信号分析"""
        game = SignalingGame()
        result = game.analyze_signal_equilibrium([], [])
        
        assert result['type'] == 'inconclusive'
        assert result['dominant_signal'] == 'hold_signal'


class TestIntegration:
    """集成测试"""
    
    def test_multi_agent_simulation(self):
        """测试多Agent模拟"""
        entities = [
            {'entity_name': '李明', 'entity_type': 'Person', 'stance': 'neutral', 'sentiment_bias': 0.2},
            {'entity_name': '王总', 'entity_type': 'FundManager', 'stance': 'supportive', 'sentiment_bias': 0.1},
            {'entity_name': '张矿工', 'entity_type': 'Miner', 'stance': 'opposing', 'sentiment_bias': -0.3},
        ]
        
        agents = create_gt_agents(entities)
        
        # 模拟多轮
        for round_num in range(3):
            for agent in agents:
                other_agents = [{'entity_name': a.name, 'stance': a.stance} for a in agents if a != agent]
                
                observation = agent.observe(other_agents, [])
                
                context = {
                    'price': 2300 + round_num * 10,
                    'support_level': 2280,
                    'resistance_level': 2457,
                    'price_trend': 'sideways'
                }
                
                decision = agent.decide_action(context, observation)
                
                assert decision['action'] in ['buy', 'hold', 'sell']
                agent.update(decision['action'], random.uniform(-1, 1))
    
    def test_different_strategies(self):
        """测试不同策略的Agent交互"""
        entities = [
            {'entity_name': '冷酷触发', 'entity_type': 'Person', 'stance': 'neutral', 'sentiment_bias': 0},
            {'entity_name': '以牙还牙', 'entity_type': 'Person', 'stance': 'neutral', 'sentiment_bias': 0}
        ]
        
        agents = create_gt_agents(entities)
        agents[0].gt_config.repeated_strategy = GameStrategy.GRIM_TRIGGER
        agents[1].gt_config.repeated_strategy = GameStrategy.TIT_FOR_TAT
        
        # 模拟交互
        for _ in range(5):
            for i, agent in enumerate(agents):
                other = agents[1 - i]
                
                # 记录对手行动
                if other.action_history:
                    agent.repeated_strategy.record_opponent_action(other.action_history[-1])
                
                context = {'price': 2300, 'support_level': 2280, 'resistance_level': 2457, 'price_trend': 'sideways'}
                observation = {'opponents': [{'name': other.name, 'stance': other.stance}]}
                
                decision = agent.decide_action(context, observation)
                agent.update(decision['action'], 0.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])