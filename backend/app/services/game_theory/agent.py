"""
博弈论增强型Agent
Game-Theoretic Enhanced Agent for MiroFish

这个模块继承MiroFish现有的Agent机制，加入博弈论决策层：
1. 观察其他Agent的行为
2. 构建博弈模型
3. 计算均衡策略
4. 基于均衡选择行动
"""

import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

# Import game theory core - handle both package and standalone modes
try:
    from .game_theory_core import (
        GameState, 
        RepeatedGame, 
        SignalingGame,
        build_market_game,
        analyze_sentiment_game
    )
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from game_theory_core import (
        GameState, 
        RepeatedGame, 
        SignalingGame,
        build_market_game,
        analyze_sentiment_game
    )

# Import config dataclass
try:
    from .config import GameTheoreticConfig
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from config import GameTheoreticConfig


@dataclass
class GameTheoreticConfig:
    """博弈论增强配置"""
    # 博弈类型
    game_type: str = "market"  # market | signaling | repeated
    
    # 是否启用博弈论决策
    enabled: bool = True
    
    # 博弈对手数量
    max_opponents: int = 3
    
    # 信念更新率
    belief_update_rate: float = 0.3
    
    # 策略稳定性阈值
    equilibrium_threshold: float = 0.1
    
    # 风险偏好 (0-1, 0=风险规避, 1=风险偏好)
    risk_preference: float = 0.5
    
    # 记忆深度（考虑过去多少轮）
    memory_depth: int = 5


class GameTheoreticAgent:
    """
    博弈论增强型Agent
    
    在MiroFish原有Agent基础上加入博弈论决策层
    """
    
    def __init__(self, base_config: Dict, gt_config: GameTheoreticConfig):
        """
        初始化博弈论增强Agent
        
        Args:
            base_config: MiroFish原始Agent配置
            gt_config: 博弈论增强配置
        """
        self.base_config = base_config
        self.gt_config = gt_config
        
        # 博弈论状态
        self.repeated_game: Optional[RepeatedGame] = None
        self.beliefs: Dict[str, float] = {}  # 对其他Agent策略的信念
        self.payoff_history: List[float] = []
        self.equilibrium_history: List[Dict] = []
        
        # 从基础配置初始化
        self.name = base_config.get('entity_name', 'Unknown')
        self.stance = base_config.get('stance', 'neutral')
        self.sentiment_bias = base_config.get('sentiment_bias', 0.0)
        
    def init_repeated_game(self, opponents: List[str]):
        """初始化重复博弈追踪器"""
        game_state = GameState(
            players=[self.name] + opponents,
            strategies={p: ['buy', 'hold', 'sell'] for p in [self.name] + opponents},
            payoff_matrix=self._build_payoff_matrix(opponents),
            current_round=0
        )
        self.repeated_game = RepeatedGame([self.name] + opponents, game_state)
    
    def _build_payoff_matrix(self, opponents: List[str]) -> 'np.ndarray':
        """构建支付矩阵"""
        import numpy as np
        n_strategies = 3  # buy, hold, sell
        matrix = np.zeros((n_strategies, n_strategies))
        
        # 基于风险偏好和情感倾向调整支付
        risk_adj = self.gt_config.risk_preference * 0.5
        sentiment_adj = self.sentiment_bias * 0.3
        
        for i in range(n_strategies):
            for j in range(n_strategies):
                # 简化支付函数
                if i == 0:  # buy
                    base = 1.0 if j == 2 else (0.5 if j == 1 else 0.3)
                elif i == 1:  # hold
                    base = 0.0 if j == 2 else (0.0 if j == 1 else 0.2)
                else:  # sell
                    base = 1.0 if j == 0 else (0.5 if j == 1 else 0.0)
                
                matrix[i, j] = base + risk_adj + sentiment_adj
        
        return matrix
    
    def observe(self, other_agents: List[Dict], recent_actions: List[Dict]) -> Dict:
        """
        观察其他Agent的行为，更新信念
        
        Args:
            other_agents: 其他Agent的配置列表
            recent_actions: 最近N轮的行动记录
            
        Returns:
            观察结果摘要
        """
        observation = {
            'opponents': [],
            'strategy_counts': {},
            'sentiment_trend': []
        }
        
        for agent in other_agents:
            agent_name = agent.get('entity_name', 'unknown')
            
            # 统计该Agent的策略
            agent_actions = [a for a in recent_actions if a.get('agent_name') == agent_name]
            strategy_count = {}
            for action in agent_actions:
                action_type = action.get('action_type', 'unknown')
                strategy_count[action_type] = strategy_count.get(action_type, 0) + 1
            
            # 更新信念（贝叶斯更新）
            if agent_name not in self.beliefs:
                self.beliefs[agent_name] = {}
            
            for strategy, count in strategy_count.items():
                prior = self.beliefs[agent_name].get(strategy, 0.1)
                # 简化的贝叶斯更新
                posterior = prior + self.gt_config.belief_update_rate * (count / max(len(agent_actions), 1) - prior)
                self.beliefs[agent_name][strategy] = posterior
            
            observation['opponents'].append({
                'name': agent_name,
                'beliefs': self.beliefs.get(agent_name, {}),
                'stance': agent.get('stance', 'neutral')
            })
        
        return observation
    
    def compute_equilibrium(self) -> Dict:
        """
        计算当前博弈的纳什均衡
        
        Returns:
            均衡结果
        """
        if not self.repeated_game:
            return {'status': 'no_game', 'message': 'Repeated game not initialized'}
        
        # 计算虚构对弈概率
        opponent_probs = {}
        for opponent in self.repeated_game.players[1:]:
            opponent_probs[opponent] = self.repeated_game.get_fictitious_play_probability(opponent)
        
        # 寻找最佳响应
        best_responses = {}
        for opponent, probs in opponent_probs.items():
            best_response = self.repeated_game.best_response(self.name, probs)
            best_responses[opponent] = best_response
        
        # 构建均衡策略
        equilibrium = {
            'status': 'equilibrium_found',
            'best_responses': best_responses,
            'confidence': 1.0 - self.gt_config.equilibrium_threshold,
            'opponent_beliefs': opponent_probs
        }
        
        self.equilibrium_history.append(equilibrium)
        
        return equilibrium
    
    def decide_action(self, context: Dict, observation: Dict) -> Dict:
        """
        基于博弈论决策行动
        
        这是核心方法，替代MiroFish原有的简单规则
        
        Args:
            context: 当前上下文（价格、市场状态等）
            observation: 观察结果（其他Agent行为）
            
        Returns:
            决策结果，包含行动和建议
        """
        if not self.gt_config.enabled:
            return self._fallback_decision(context)
        
        # 1. 分析情感博弈
        sentiments = [self.sentiment_bias]
        for opp in observation.get('opponents', []):
            stance = opp.get('stance', 'neutral')
            sentiment = 0.5 if stance == 'supportive' else (-0.5 if stance == 'opposing' else 0.0)
            sentiments.append(sentiment)
        
        sentiment_analysis = analyze_sentiment_game(sentiments)
        
        # 2. 检查是否接近均衡
        if sentiment_analysis['is_equilibrium']:
            # 均衡时采取保守策略
            return {
                'action': 'hold',
                'reasoning': f'市场接近均衡({sentiment_analysis["dominant_sentiment"]})，观望',
                'gt_analysis': sentiment_analysis
            }
        
        # 3. 如果有历史记录，使用重复博弈
        if self.repeated_game and len(self.repeated_game.history) > 0:
            equilibrium = self.compute_equilibrium()
            
            if equilibrium['status'] == 'equilibrium_found':
                # 基于均衡策略决定行动
                dominant_strategy = max(
                    equilibrium['best_responses'].values(),
                    key=list(equilibrium['best_responses'].values()).count
                )
                
                # 加入风险偏好调整
                if self.gt_config.risk_preference > 0.7:
                    # 风险偏好型：更激进
                    if dominant_strategy == 'hold':
                        dominant_strategy = 'buy'
                elif self.gt_config.risk_preference < 0.3:
                    # 风险规避型：更保守
                    if dominant_strategy == 'sell':
                        dominant_strategy = 'hold'
                
                reasoning = f"基于博弈论均衡: {dominant_strategy}"
                if self.stance == 'supportive':
                    reasoning += ", 立场偏多"
                elif self.stance == 'opposing':
                    reasoning += ", 立场偏空"
                
                return {
                    'action': dominant_strategy,
                    'reasoning': reasoning,
                    'gt_analysis': equilibrium,
                    'sentiment': sentiment_analysis
                }
        
        # 4. 基于观察的启发式决策
        return self._heuristic_decision(context, observation)
    
    def _heuristic_decision(self, context: Dict, observation: Dict) -> Dict:
        """基于观察的启发式决策（博弈论不可用时的后备）"""
        price_trend = context.get('price_trend', 'neutral')
        support_level = context.get('support_level', 0)
        
        # 分析对手立场
        opponent_stances = [opp.get('stance', 'neutral') for opp in observation.get('opponents', [])]
        bearish_count = opponent_stances.count('opposing')
        bullish_count = opponent_stances.count('supportive')
        
        # 博弈论决策
        if bullish_count > bearish_count + 1:
            action = 'buy' if self.stance != 'opposing' else 'hold'
            reasoning = f'多头占优({bullish_count}>{bearish_count})'
        elif bearish_count > bullish_count + 1:
            action = 'sell' if self.stance != 'supportive' else 'hold'
            reasoning = f'空头占优({bearish_count}>{bullish_count})'
        else:
            action = 'hold'
            reasoning = '多空僵持，等待信号'
        
        return {
            'action': action,
            'reasoning': reasoning,
            'opponent_analysis': {
                'bullish': bullish_count,
                'bearish': bearish_count
            }
        }
    
    def _fallback_decision(self, context: Dict) -> Dict:
        """后备决策（博弈论禁用时）"""
        stance = self.base_config.get('stance', 'neutral')
        sentiment = self.base_config.get('sentiment_bias', 0)
        
        if stance == 'supportive' and sentiment > 0:
            return {'action': 'buy', 'reasoning': '立场偏多'}
        elif stance == 'opposing' and sentiment < 0:
            return {'action': 'sell', 'reasoning': '立场偏空'}
        else:
            return {'action': 'hold', 'reasoning': '中立观望'}
    
    def update_from_result(self, action: str, payoff: float):
        """从结果中学习，更新模型"""
        self.payoff_history.append(payoff)
        
        if self.repeated_game:
            # 记录到重复博弈
            # 这里需要推断对手的行动（简化处理）
            opponent_action = 'hold'  # 默认
            self.repeated_game.record_round(
                (action, opponent_action),
                (payoff, 0.0)
            )
    
    def get_strategy_profile(self) -> Dict:
        """获取当前策略配置"""
        return {
            'name': self.name,
            'game_type': self.gt_config.game_type,
            'enabled': self.gt_config.enabled,
            'risk_preference': self.gt_config.risk_preference,
            'equilibrium_history_length': len(self.equilibrium_history),
            'payoff_trend': 'increasing' if len(self.payoff_history) > 1 and self.payoff_history[-1] > self.payoff_history[0] else 'decreasing'
        }


def create_game_theoretic_agent(base_config: Dict, gt_config: Optional[GameTheoreticConfig] = None) -> GameTheoreticAgent:
    """
    工厂函数：从MiroFish配置创建博弈论增强Agent
    
    Args:
        base_config: MiroFish原始Agent配置
        gt_config: 博弈论配置（默认新建）
        
    Returns:
        GameTheoreticAgent实例
    """
    if gt_config is None:
        gt_config = GameTheoreticConfig()
    
    return GameTheoreticAgent(base_config, gt_config)


# 示例使用
if __name__ == "__main__":
    # 示例配置
    base_config = {
        'entity_name': '李明',
        'stance': 'neutral',
        'sentiment_bias': 0.2,
        'activity_level': 0.6
    }
    
    gt_config = GameTheoreticConfig(
        game_type='market',
        enabled=True,
        risk_preference=0.5
    )
    
    # 创建Agent
    agent = create_game_theoretic_agent(base_config, gt_config)
    
    # 初始化博弈
    agent.init_repeated_game(['王总', '张矿工'])
    
    # 模拟观察
    observation = {
        'opponents': [
            {'name': '王总', 'stance': 'neutral', 'beliefs': {'buy': 0.4, 'hold': 0.4, 'sell': 0.2}},
            {'name': '张矿工', 'stance': 'opposing', 'beliefs': {'buy': 0.2, 'hold': 0.3, 'sell': 0.5}}
        ]
    }
    
    # 决策
    context = {'price_trend': '下降', 'support_level': 2300}
    decision = agent.decide_action(context, observation)
    
    print(f"Agent: {agent.name}")
    print(f"Decision: {decision}")