"""
博弈论核心模块
Game Theory Core for MiroFish

支持:
- 支付矩阵构建
- 纳什均衡计算
- 贝叶斯更新
- 重复博弈学习
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class Strategy(Enum):
    COOPERATE = "cooperate"
    DEFECT = "defect"
    MIXED = "mixed"


@dataclass
class Action:
    """行动：包含行动类型和预期收益"""
    name: str
    utility: float  # 支付值
    probability: float = 1.0  # 执行概率


@dataclass
class GameState:
    """博弈状态"""
    players: List[str]
    strategies: Dict[str, List[str]]  # 每个玩家的策略列表
    payoff_matrix: np.ndarray  # 支付矩阵
    current_round: int
    beliefs: Dict[str, np.ndarray] = None  # 贝叶斯信念
    
    def get_payoff(self, player: str, strategy_profile: Tuple) -> float:
        """获取特定策略组合下某玩家的支付"""
        idx = self.players.index(player)
        # 将策略转换为索引
        strategy_idx = [self.strategies[p].index(s) for p, s in zip(self.players, strategy_profile)]
        return self.payoff_matrix[(strategy_idx[0], strategy_idx[1])]
    
    def find_nash_equilibrium(self) -> List[Tuple]:
        """计算纳什均衡（双人博弈）"""
        n_players = len(self.players)
        equilibria = []
        
        # 穷举所有策略组合
        for strategy_profile in self._iterate_strategies():
            is_equilibrium = True
            for i, player in enumerate(self.players):
                # 检查玩家是否有动机偏离
                best_response = max(
                    [self.get_payoff(player, self._modify_strategy(strategy_profile, i, s)) 
                     for s in self.strategies[player]]
                )
                current_payoff = self.get_payoff(player, strategy_profile)
                if current_payoff < best_response - 1e-6:
                    is_equilibrium = False
                    break
            if is_equilibrium:
                equilibria.append(strategy_profile)
        
        return equilibria
    
    def _iterate_strategies(self):
        """迭代所有策略组合"""
        import itertools
        strategies_list = [self.strategies[p] for p in self.players]
        for combo in itertools.product(*strategies_list):
            yield combo
    
    def _modify_strategy(self, profile: Tuple, player_idx: int, new_strategy: str) -> Tuple:
        """修改特定玩家的策略"""
        new_profile = list(profile)
        new_profile[player_idx] = new_strategy
        return tuple(new_profile)


@dataclass
class BayesianUpdate:
    """贝叶斯更新器"""
    prior: np.ndarray  # 先验概率
    likelihood: np.ndarray  # 似然
    
    def update(self, observation: Any) -> np.ndarray:
        """基于观察更新后验概率"""
        posterior = self.prior * self.likelihood
        posterior /= posterior.sum()  # 归一化
        return posterior


class RepeatedGame:
    """重复博弈追踪器"""
    
    def __init__(self, players: List[str], base_game: GameState):
        self.players = players
        self.base_game = base_game
        self.history: List[Dict] = []
        self.fictitious_play_counts: Dict[str, Dict[str, int]] = {
            p: {s: 0 for s in base_game.strategies[p]} for p in players
        }
        
    def record_round(self, strategy_profile: Tuple, payoffs: Tuple):
        """记录一轮博弈结果"""
        self.history.append({
            'round': len(self.history),
            'strategies': strategy_profile,
            'payoffs': payoffs
        })
        # 更新虚拟对弈计数
        for i, player in enumerate(self.players):
            self.fictitious_play_counts[player][strategy_profile[i]] += 1
    
    def get_fictitious_play_probability(self, player: str) -> Dict[str, float]:
        """计算虚构对弈下的对手策略概率"""
        total = sum(self.fictitious_play_counts[player].values())
        if total == 0:
            return {s: 1.0/len(self.fictitious_play_counts[player]) for s in self.fictitious_play_counts[player]}
        return {s: c/total for s, c in self.fictitious_play_counts[player].items()}
    
    def best_response(self, player: str, opponent_probs: Dict[str, float]) -> str:
        """计算对对手策略概率的最佳响应"""
        expected_payoffs = {}
        for strategy in self.base_game.strategies[player]:
            expected_payoff = 0
            for opp_strategy, prob in opponent_probs.items():
                profile = (strategy, opp_strategy) if player == self.players[0] else (opp_strategy, strategy)
                expected_payoff += prob * self.base_game.get_payoff(player, profile)
            expected_payoffs[strategy] = expected_payoff
        
        return max(expected_payoffs, key=expected_payoffs.get)


class SignalingGame:
    """信号博弈（用于分析发言作为信息传递）"""
    
    def __init__(self, sender: str, receiver: str, signal_space: List[str], action_space: List[str]):
        self.sender = sender
        self.receiver = receiver
        self.signal_space = signal_space
        self.action_space = action_space
        self.type_prior = {}  # 发送者类型先验
        self.payoffs = {}  # 支付函数
        
    def set_type_prior(self, type_distribution: Dict[str, float]):
        """设置发送者类型分布"""
        self.type_prior = type_distribution
    
    def set_payoffs(self, sender_payoff: Dict, receiver_payoff: Dict):
        """设置支付函数"""
        self.payoffs['sender'] = sender_payoff
        self.payoffs['receiver'] = receiver_payoff
    
    def signaling_equilibrium(self) -> Dict:
        """计算完美贝叶斯均衡"""
        # 简化版：计算分离均衡
        equilibria = []
        
        # 检查是否有分离均衡（不同类型发送不同信号）
        for signal in self.signal_space:
            is_separating = True
            for t1, t2 in [(t1, t2) for t1 in self.type_prior for t2 in self.type_prior if t1 != t2]:
                # 如果两个类型可能发送同一信号，需要Pooling均衡
                if self._would_send_signal(t1, signal) and self._would_send_signal(t2, signal):
                    is_separating = False
                    break
            
            if is_separating:
                equilibria.append({
                    'type': 'separating',
                    'signal': signal,
                    'belief': {signal: 1.0}
                })
        
        # 如果没有分离均衡，返回混同均衡
        if not equilibria:
            for signal in self.signal_space:
                equilibria.append({
                    'type': 'pooling',
                    'signal': signal,
                    'belief': self.type_prior.copy()
                })
        
        return equilibria[0] if equilibria else None
    
    def _would_send_signal(self, type: str, signal: str) -> bool:
        """判断某类型发送某信号的条件"""
        # 简化的发送者最佳响应
        return True


def build_market_game(agents: List[Dict], current_price: float, support_level: float) -> GameState:
    """
    构建市场博弈模型
    
    用于ETH市场模拟中的多空博弈
    """
    players = [a['name'] for a in agents[:2]]  # 取前两个Agent作为博弈方
    
    # 策略空间：买入/持有/卖出
    strategies = {p: ['buy', 'hold', 'sell'] for p in players}
    
    # 构建支付矩阵（简化版：2x2）
    # 实际应该考虑更多信息
    payoff_matrix = np.array([
        [1.0, 0.5, -0.5],  # Agent0 buy
        [0.5, 0.0, 0.0],   # Agent0 hold  
        [-0.5, 0.0, 0.5]   # Agent0 sell
    ])
    
    return GameState(
        players=players,
        strategies=strategies,
        payoff_matrix=payoff_matrix,
        current_round=0
    )


def analyze_sentiment_game(sentiments: List[float]) -> Dict:
    """
    分析情感博弈
    
    判断群体情感是否趋向均衡
    """
    avg_sentiment = np.mean(sentiments)
    sentiment_variance = np.var(sentiments)
    
    # 如果方差很小，系统接近均衡
    is_equilibrium = sentiment_variance < 0.1
    
    return {
        'average_sentiment': avg_sentiment,
        'variance': sentiment_variance,
        'is_equilibrium': is_equilibrium,
        'dominant_sentiment': 'positive' if avg_sentiment > 0.2 else ('negative' if avg_sentiment < -0.2 else 'neutral')
    }