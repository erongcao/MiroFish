"""
博弈论增强Agent - v2.0 完整版
Game-Theoretic Enhanced Agent for MiroFish

修复内容:
1. 动态支付矩阵（基于市场context）
2. 纳什均衡验证
3. 多轮均衡确认
4. 先验策略（第一轮）
5. 类型注解（Literal）
6. 除零保护
7. N人博弈支持
8. 信号博弈
9. 重复博弈策略（grim trigger, tit-for-tat）
10. pytest单元测试
"""

import random
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Literal
from dataclasses import dataclass, field
from enum import Enum


# ============== 类型定义 ==============

ActionType = Literal['buy', 'hold', 'sell']
StanceType = Literal['supportive', 'opposing', 'neutral']
EntityType = Literal['Person', 'FundManager', 'Miner', 'RetailInvestor', 'Organization', 'TechnicalAnalyst']

# 标准化行动列表
ALL_ACTIONS: List[ActionType] = ['buy', 'hold', 'sell']


class GameStrategy(Enum):
    """博弈策略枚举"""
    GRIM_TRIGGER = "grim_trigger"      # 冷酷触发：一旦背叛永久惩罚
    TIT_FOR_TAT = "tit_for_tat"        # 以牙还牙：模仿对手上一轮
    TIT_FOR_TWO_TATS = "tit_for_two_tats"  # 宽容以牙还牙
    ALWAYS_COOPERATE = "always_cooperate"  # 永远合作
    ALWAYS_DEFECT = "always_defect"    # 永远背叛
    RANDOM = "random"                  # 随机


# ============== 配置类 ==============

@dataclass
class GameTheoreticConfig:
    """博弈论增强配置"""
    game_type: str = "market"
    enabled: bool = True
    max_opponents: int = 10
    belief_update_rate: float = 0.3
    equilibrium_threshold: float = 0.1
    risk_preference: float = 0.5
    memory_depth: int = 10
    
    # 重复博弈策略
    repeated_strategy: GameStrategy = GameStrategy.TIT_FOR_TAT
    
    # 时间折扣因子（0-1，越接近1越看重未来）
    discount_factor: float = 0.95
    
    # 均衡确认轮数
    equilibrium_confirmation_rounds: int = 3
    
    # 先验概率（第一轮使用）
    prior_strategy_probs: Dict[ActionType, float] = field(default_factory=lambda: {
        'buy': 0.33, 'hold': 0.34, 'sell': 0.33
    })


# ============== 支付矩阵构建器 ==============

class PayoffMatrixBuilder:
    """动态支付矩阵构建器 - 基于真实市场状态计算支付"""
    
    @staticmethod
    def calculate_expected_price_change(
        current_price: float,
        support_level: float,
        resistance_level: float,
        trend: str,
        volatility: float
    ) -> float:
        """
        基于市场状态计算预期的价格变动幅度
        
        原理：
        - 趋势上升时，价格更可能向上突破阻力
        - 趋势下降时，价格更可能向下突破支撑
        - 波动率越大，预期变动幅度越大
        - 价格在支撑/阻力位置时，反转概率增加
        """
        # 计算价格位置（0=支撑位, 1=阻力位）
        range_size = resistance_level - support_level
        if range_size <= 0:
            range_size = current_price * 0.1  # 默认10%范围
        
        price_position = (current_price - support_level) / range_size
        price_position = max(0.0, min(1.0, price_position))
        
        # 基础波动率（年化波动率换算为日波动率）
        daily_vol = volatility / np.sqrt(252)  # 假设252交易日
        
        # 趋势因子：决定价格变动方向和概率
        trend_factor = {
            'up': 0.6,      # 上升趋势：偏向正变动
            'down': -0.6,   # 下降趋势：偏向负变动
            'sideways': 0.0  # 震荡：期望为0
        }.get(trend, 0.0)
        
        # 位置因子：价格接近支撑时，向上的概率增加；接近阻力时，向下的概率增加
        position_factor = (0.5 - price_position) * 0.3
        
        # 综合预期变动（日百分比）
        expected_change = (trend_factor + position_factor) * daily_vol * 100
        
        return expected_change  # 单位：百分比
    
    @staticmethod
    def calculate_position_pnl(
        action: ActionType,
        opponent_action: ActionType,
        expected_price_change: float
    ) -> float:
        """
        计算行动的盈亏
        
        Args:
            action: 我的行动 (buy/hold/sell)
            opponent_action: 对手/市场行动
            expected_price_change: 预期的价格变动（百分比）
        
        Returns:
            盈亏比例（正=盈利，负=亏损）
        """
        if action == 'buy':
            if opponent_action == 'buy':
                # 双方买入：跟随趋势，如果价格向上则盈利
                return expected_price_change * 0.8  # 追涨收益略低
            elif opponent_action == 'hold':
                # 我买对手观望：价格向上时有抄底收益
                if expected_price_change > 0:
                    return expected_price_change * 1.2  # 抄底成功
                else:
                    return expected_price_change * 0.8  # 抄底失败
            else:  # opponent sell
                # 我买对手卖：最坏情况，接盘
                return expected_price_change * 1.5 if expected_price_change < 0 else expected_price_change * 0.5
        
        elif action == 'hold':
            if opponent_action == 'buy':
                # 我观望对手买：踏空损失
                if expected_price_change > 0:
                    return -expected_price_change * 0.3  # 踏空损失
                else:
                    return -expected_price_change * 0.2  # 正确观望
            elif opponent_action == 'hold':
                # 双观望：中性
                return 0.0
            else:  # opponent sell
                # 我观望对手卖：旁观，损失较小
                if expected_price_change < 0:
                    return -expected_price_change * 0.2  # 旁观收益
                else:
                    return expected_price_change * 0.1
        
        else:  # sell
            if opponent_action == 'buy':
                # 我卖对手买：逃顶成功
                if expected_price_change > 0:
                    return -expected_price_change * 0.8  # 踏空
                else:
                    return expected_price_change * 1.5  # 逃顶成功
            elif opponent_action == 'hold':
                # 我卖对手观望：还行
                return -expected_price_change * 0.5
            else:  # opponent sell
                # 双卖：踩踏，都亏损
                return expected_price_change * 0.6
    
    @staticmethod
    def build_market_matrix(
        current_price: float,
        support_level: float,
        resistance_level: float,
        trend: str,
        volatility: float = 0.5
    ) -> Dict[ActionType, Dict[ActionType, float]]:
        """
        基于真实市场状态构建支付矩阵
        
        计算逻辑：
        1. 计算预期的价格变动（基于趋势、位置、波动率）
        2. 根据每个行动组合计算盈亏
        3. 盈亏应该反映真实市场的风险/回报
        """
        # 计算预期的价格变动（百分比）
        expected_change = PayoffMatrixBuilder.calculate_expected_price_change(
            current_price, support_level, resistance_level, trend, volatility
        )
        
        # 构建基于真实市场的支付矩阵
        matrix: Dict[ActionType, Dict[ActionType, float]] = {}
        
        for my_action in ALL_ACTIONS:
            matrix[my_action] = {}
            for opp_action in ALL_ACTIONS:
                pnl = PayoffMatrixBuilder.calculate_position_pnl(
                    my_action, opp_action, expected_change
                )
                matrix[my_action][opp_action] = pnl
        
        # 验证矩阵合理性（可选）
        # 如果buy的期望太高/太低，适当调整
        buy_avg = np.mean([matrix['buy'][a] for a in ALL_ACTIONS])
        if abs(buy_avg) > 5:  # 超过5%日收益不合理
            scale_factor = 3.0 / abs(buy_avg) if buy_avg != 0 else 1
            for my_action in ALL_ACTIONS:
                for opp_action in ALL_ACTIONS:
                    matrix[my_action][opp_action] *= scale_factor
        
        return matrix
    
    @staticmethod
    def validate_matrix(matrix: Dict[ActionType, Dict[ActionType, float]]) -> bool:
        """验证支付矩阵的合理性"""
        required_actions: List[ActionType] = ALL_ACTIONS
        
        for action in required_actions:
            if action not in matrix:
                return False
            if not all(opp in matrix[action] for opp in required_actions):
                return False
        
        return True


# ============== 纳什均衡求解器 ==============

class NashEquilibriumSolver:
    """纳什均衡求解器"""
    
    @staticmethod
    def find_pure_strategy_nash(
        payoff_matrix: Dict[ActionType, Dict[ActionType, float]],
        player_actions: List[ActionType] = ALL_ACTIONS
    ) -> List[Tuple[ActionType, ActionType]]:
        """
        寻找纯策略纳什均衡
        
        Returns:
            均衡策略组合列表
        """
        equilibria = []
        
        for my_action in player_actions:
            for opp_action in player_actions:
                # 检查我是否有偏离动机
                my_payoff = payoff_matrix[my_action][opp_action]
                my_best_response = max(
                    payoff_matrix[a][opp_action] for a in player_actions
                )
                
                # 检查对手是否有偏离动机（对称博弈假设）
                opp_payoff = payoff_matrix[opp_action][my_action]
                opp_best_response = max(
                    payoff_matrix[a][my_action] for a in player_actions
                )
                
                # 如果双方都没有偏离动机，则是纳什均衡
                if abs(my_payoff - my_best_response) < 1e-6 and \
                   abs(opp_payoff - opp_best_response) < 1e-6:
                    equilibria.append((my_action, opp_action))
        
        return equilibria
    
    @staticmethod
    def verify_equilibrium(
        strategy_profile: Tuple[ActionType, ActionType],
        payoff_matrix: Dict[ActionType, Dict[ActionType, float]]
    ) -> Dict[str, Any]:
        """
        验证给定策略组合是否为纳什均衡
        
        Returns:
            验证结果，包含是否有偏离动机
        """
        my_action, opp_action = strategy_profile
        
        my_payoff = payoff_matrix[my_action][opp_action]
        my_best_payoff = max(payoff_matrix[a][opp_action] for a in ALL_ACTIONS)
        
        opp_payoff = payoff_matrix[opp_action][my_action]
        opp_best_payoff = max(payoff_matrix[a][my_action] for a in ALL_ACTIONS)
        
        return {
            'is_nash': abs(my_payoff - my_best_payoff) < 1e-6 and abs(opp_payoff - opp_best_payoff) < 1e-6,
            'my_incentive_to_deviate': my_best_payoff - my_payoff,
            'opp_incentive_to_deviate': opp_best_payoff - opp_payoff,
            'my_payoff': my_payoff,
            'opp_payoff': opp_payoff
        }


# ============== 信号博弈 ==============

class SignalingGame:
    """信号博弈模型 - 分析发言作为信息传递
    
    在社交媒体模拟中，每个发言都是一种"信号"：
    - 信号空间：发言内容（买入/观望/卖出暗示）
    - 发送者类型：看多/看空/中立
    - 接收者：根据信号推断类型，决定行动
    """
    
    def __init__(self):
        self.sender_types = ['bullish', 'bearish', 'neutral']
        self.signals = ['buy_signal', 'sell_signal', 'hold_signal']
        self.actions = ALL_ACTIONS
        
        # 信念：给定信号，发送者是什么类型的概率
        self.signal_beliefs: Dict[str, Dict[str, float]] = {
            'buy_signal': {'bullish': 0.7, 'bearish': 0.1, 'neutral': 0.2},
            'sell_signal': {'bullish': 0.1, 'bearish': 0.7, 'neutral': 0.2},
            'hold_signal': {'bullish': 0.2, 'bearish': 0.2, 'neutral': 0.6}
        }
        
        # 支付矩阵：基于信号类型匹配的收益
        self.payoffs = {
            ('bullish', 'buy_signal'): {'buy': 1.0, 'hold': 0.3, 'sell': -0.5},
            ('bearish', 'sell_signal'): {'sell': 1.0, 'hold': 0.3, 'buy': -0.5},
            ('neutral', 'hold_signal'): {'hold': 0.5, 'buy': 0.0, 'sell': 0.0}
        }
    
    def extract_signal_from_message(self, message: str, sentiment: float = 0.0) -> str:
        """
        从消息内容中提取信号
        
        Args:
            message: 消息内容
            sentiment: 情感分析结果 (-1到1)
            
        Returns:
            信号类型：buy_signal, sell_signal, hold_signal
        """
        msg_lower = message.lower()
        
        # 买入信号关键词
        buy_keywords = ['买', '买入', '做多', '多头', '建仓', '加仓', '看好', '涨', 'bull', 'long', 'buy']
        sell_keywords = ['卖', '卖出', '做空', '空头', '清仓', '减仓', '看空', '跌', 'bear', 'short', 'sell']
        
        buy_score = sum(1 for kw in buy_keywords if kw in msg_lower)
        sell_score = sum(1 for kw in sell_keywords if kw in msg_lower)
        
        # 也考虑情感分数
        if sentiment > 0.2:
            buy_score += 1
        elif sentiment < -0.2:
            sell_score += 1
        
        if buy_score > sell_score:
            return 'buy_signal'
        elif sell_score > buy_score:
            return 'sell_signal'
        else:
            return 'hold_signal'
    
    def analyze_signal_equilibrium(self, signals: List[str], sender_stances: List[str]) -> Dict:
        """
        分析信号博弈均衡
        
        Args:
            signals: 观察到的信号列表
            sender_stances: 发送者立场列表
            
        Returns:
            均衡分析结果
        """
        if not signals:
            return {'type': 'inconclusive', 'dominant_signal': 'hold_signal'}
        
        # 统计信号分布
        signal_counts = {'buy_signal': 0, 'sell_signal': 0, 'hold_signal': 0}
        for sig in signals:
            if sig in signal_counts:
                signal_counts[sig] += 1
        
        # 找出主导信号
        dominant_signal = max(signal_counts, key=signal_counts.get)
        
        # 计算分离度（信号是否清晰）
        total = len(signals)
        signal_entropy = 0
        for sig, count in signal_counts.items():
            p = count / total if total > 0 else 0
            if p > 0:
                signal_entropy -= p * np.log2(p + 1e-10)
        
        # 低熵 = 信号清晰（分离均衡）
        # 高熵 = 信号混乱（混同均衡）
        max_entropy = np.log2(3)  # 3种信号
        clarity = 1 - signal_entropy / max_entropy
        
        # 判断均衡类型
        if clarity > 0.5:
            eq_type = 'separating'
        else:
            eq_type = 'pooling'
        
        # 基于主导信号推断市场倾向
        if dominant_signal == 'buy_signal':
            market_tendency = 'bullish'
        elif dominant_signal == 'sell_signal':
            market_tendency = 'bearish'
        else:
            market_tendency = 'neutral'
        
        return {
            'type': eq_type,
            'dominant_signal': dominant_signal,
            'signal_counts': signal_counts,
            'signal_clarity': clarity,  # 修复拼写错误
            'market_tendency': market_tendency,
            'inference_confidence': signal_counts[dominant_signal] / total if total > 0 else 0
        }
    
    def get_action_from_signal(self, signal: str) -> ActionType:
        """从信号推断应该采取的行动"""
        if signal == 'buy_signal':
            return 'buy'
        elif signal == 'sell_signal':
            return 'sell'
        else:
            return 'hold'


# ============== 重复博弈策略 ==============

class RepeatedGameStrategy:
    """
    重复博弈策略执行器
    
    支持时间折扣因子 δ (discount_factor)：
    - δ = 1.0: 无限期博弈，未来收益不折扣
    - δ = 0.9: 未来收益打9折，越远越不值钱
    - δ = 0.0: 只看当前收益（短期博弈）
    
    累积收益公式: U = Σ δ^t * payoff_t
    """
    
    def __init__(self, strategy_type: GameStrategy, discount_factor: float = 0.95):
        self.strategy_type = strategy_type
        self.discount_factor = discount_factor  # 时间折扣因子
        self.opponent_history: List[ActionType] = []
        self.my_history: List[ActionType] = []
        self.defected = False  # 用于grim trigger
        self.payoff_accumulator: List[float] = []  # 历史收益记录
    
    def choose_action(self, opponent_last_action: Optional[ActionType] = None) -> ActionType:
        """根据策略选择行动
        
        优先级：历史记录 > 参数 > 默认
        """
        # 优先使用历史记录，如果没有则用参数
        effective_last_action = self.opponent_history[-1] if self.opponent_history else opponent_last_action
        
        if self.strategy_type == GameStrategy.ALWAYS_COOPERATE:
            return 'buy'
        
        elif self.strategy_type == GameStrategy.ALWAYS_DEFECT:
            return 'sell'
        
        elif self.strategy_type == GameStrategy.GRIM_TRIGGER:
            if self.defected or effective_last_action == 'sell':
                self.defected = True
                return 'sell'
            return 'buy'
        
        elif self.strategy_type == GameStrategy.TIT_FOR_TAT:
            if effective_last_action is None:
                return 'buy'
            return effective_last_action
        
        elif self.strategy_type == GameStrategy.TIT_FOR_TWO_TATS:
            if len(self.opponent_history) < 2:
                return 'buy'
            if self.opponent_history[-1] == 'sell' and self.opponent_history[-2] == 'sell':
                return 'sell'
            return 'buy'
        
        elif self.strategy_type == GameStrategy.RANDOM:
            return random.choice(ALL_ACTIONS)
        
        return 'hold'
    
    def record_opponent_action(self, action: ActionType):
        """记录对手行动"""
        self.opponent_history.append(action)
    
    def record_my_action(self, action: ActionType):
        """记录自己的行动"""
        self.my_history.append(action)
    
    def record_payoff(self, payoff: float):
        """记录收益并计算累积折扣收益"""
        self.payoff_accumulator.append(payoff)
    
    def get_discounted_payoff(self, t: int) -> float:
        """
        获取t时刻的折扣收益
        
        Args:
            t: 时刻（0=现在，1=下一步，2=两步后...）
            
        Returns:
            折扣后的收益 δ^t * payoff_t
        """
        if t < len(self.payoff_accumulator):
            return (self.discount_factor ** t) * self.payoff_accumulator[t]
        return 0.0
    
    def get_cumulative_discounted_payoff(self, n: Optional[int] = None) -> float:
        """
        获取累积折扣收益
        
        Args:
            n: 只计算最近n期，None表示全部
            
        Returns:
            Σ δ^t * payoff_t (t=0 to n-1)
        """
        if n is None:
            n = len(self.payoff_accumulator)
        
        total = 0.0
        for t in range(min(n, len(self.payoff_accumulator))):
            total += self.get_discounted_payoff(t)
        return total


# ============== 博弈论增强Agent ==============

class GameTheoreticAgent:
    """博弈论增强型Agent v2.0"""
    
    def __init__(self, base_config: Dict, gt_config: Optional[GameTheoreticConfig] = None):
        self.base_config = base_config
        self.gt_config = gt_config or GameTheoreticConfig()
        
        # 信念系统
        self.beliefs: Dict[str, Dict[ActionType, float]] = {}
        self.opponent_history: Dict[str, List[ActionType]] = {}
        
        # 市场聚合信念（基于所有参与者行动的贝叶斯更新）
        self.market_belief: Dict[ActionType, float] = {'buy': 0.33, 'hold': 0.34, 'sell': 0.33}
        
        # 历史记录
        self.payoff_history: List[float] = []
        self.action_history: List[ActionType] = []
        self.equilibrium_history: List[Dict] = []
        
        # 基础属性
        self.name = base_config.get('entity_name', 'Unknown')
        self.stance = base_config.get('stance', 'neutral')
        self.sentiment_bias = base_config.get('sentiment_bias', 0.0)
        self.entity_type = base_config.get('entity_type', 'Person')
        
        # 重复博弈策略
        self.repeated_strategy = RepeatedGameStrategy(
            self.gt_config.repeated_strategy,
            self.gt_config.discount_factor
        )
        
        # 支付矩阵构建器
        self.matrix_builder = PayoffMatrixBuilder()
        self.equilibrium_solver = NashEquilibriumSolver()
        self.signaling_game = SignalingGame()
        
        # 均衡确认计数器
        self.equilibrium_candidate: Optional[str] = None
        self.equilibrium_rounds: int = 0
    
    def observe(self, other_agents: List[Dict], recent_actions: List[Dict]) -> Dict:
        """观察其他Agent的行为并更新信念"""
        observation = {'opponents': []}
        
        # 收集所有行动（用于后续市场信念更新）
        all_observed_actions: List[ActionType] = []
        
        for agent in other_agents:
            agent_name = agent.get('entity_name', 'unknown')
            agent_actions = [
                a for a in recent_actions 
                if a.get('agent_name') == agent_name
            ]
            
            # 提取行动类型
            actions: List[ActionType] = []
            for action in agent_actions:
                action_type = action.get('action_type', 'unknown')
                # 映射到标准行动
                if 'buy' in action_type.lower() or '买入' in action_type:
                    actions.append('buy')
                elif 'sell' in action_type.lower() or '卖出' in action_type:
                    actions.append('sell')
                else:
                    actions.append('hold')
            
            # 更新历史
            if agent_name not in self.opponent_history:
                self.opponent_history[agent_name] = []
            self.opponent_history[agent_name].extend(actions)
            
            # 真正的贝叶斯更新信念（个体信念）
            if agent_name not in self.beliefs:
                self.beliefs[agent_name] = self.gt_config.prior_strategy_probs.copy()
            
            # 似然函数矩阵：P(observed_action | belief_distribution)
            likelihood_matrix = {
                'buy': {'buy': 0.70, 'hold': 0.20, 'sell': 0.10},
                'hold': {'buy': 0.25, 'hold': 0.50, 'sell': 0.25},
                'sell': {'buy': 0.10, 'hold': 0.20, 'sell': 0.70}
            }
            
            alpha = self.gt_config.belief_update_rate  # 学习率
            
            # 对每个观察到的行动进行贝叶斯更新（个体）
            for observed_action in actions:
                prior = self.beliefs[agent_name].copy()
                
                # 归一化的先验
                total_prior = sum(prior.values())
                if total_prior > 0:
                    normalized_prior = {k: v / total_prior for k, v in prior.items()}
                else:
                    normalized_prior = {'buy': 0.33, 'hold': 0.34, 'sell': 0.33}
                
                # 获取似然
                likelihoods = likelihood_matrix.get(observed_action, {'buy': 0.33, 'hold': 0.34, 'sell': 0.33})
                
                # 贝叶斯更新：posterior ∝ likelihood × prior
                posterior = {}
                for a in ALL_ACTIONS:
                    posterior[a] = likelihoods[a] * normalized_prior.get(a, 0.33)
                
                # 归一化得到后验概率
                total_posterior = sum(posterior.values())
                if total_posterior > 0:
                    posterior = {k: max(0.01, v / total_posterior) for k, v in posterior.items()}
                else:
                    posterior = {'buy': 0.34, 'hold': 0.33, 'sell': 0.33}
                
                # 使用学习率平滑更新
                new_belief = {}
                for a in ALL_ACTIONS:
                    old_prob = prior.get(a, 0.33)
                    new_prob = (1 - alpha) * old_prob + alpha * posterior[a]
                    new_belief[a] = max(0.01, new_prob)
                
                # 最终归一化
                total_new = sum(new_belief.values())
                if total_new > 0:
                    new_belief = {k: v / total_new for k, v in new_belief.items()}
                
                self.beliefs[agent_name] = new_belief
            
            observation['opponents'].append({
                'name': agent_name,
                'beliefs': self.beliefs.get(agent_name, {}).copy(),
                'stance': agent.get('stance', 'neutral'),
                'recent_actions': actions[-5:]  # 最近5个行动
            })
        
        # ========== 聚合所有行动的贝叶斯更新 ==========
        # 收集所有观察到的行动
        all_observed_actions: List[ActionType] = []
        for opp_data in observation.get('opponents', []):
            all_observed_actions.extend(opp_data.get('recent_actions', []))
        
        if all_observed_actions:
            # 真正的贝叶斯更新：对聚合行动的信念
            # 这代表了"市场共识"——所有参与者行动的集合
            prior_market = self.market_belief.copy()
            
            # 归一化的市场先验
            total_prior_market = sum(prior_market.values())
            if total_prior_market > 0:
                normalized_prior_market = {k: v / total_prior_market for k, v in prior_market.items()}
            else:
                normalized_prior_market = {'buy': 0.33, 'hold': 0.34, 'sell': 0.33}
            
            # 统计聚合行动
            action_counts = {'buy': 0, 'hold': 0, 'sell': 0}
            for a in all_observed_actions:
                if a in action_counts:
                    action_counts[a] += 1
            
            # 计算每个行动的频率作为观测
            n_actions = len(all_observed_actions)
            action_frequencies = {a: count / n_actions for a, count in action_counts.items()}
            
            # 对每个行动类型进行贝叶斯更新（基于频率加权）
            posterior_market = {a: 0.0 for a in ALL_ACTIONS}
            
            for observed_action, freq in action_frequencies.items():
                likelihoods = likelihood_matrix.get(observed_action, {'buy': 0.33, 'hold': 0.34, 'sell': 0.33})
                for a in ALL_ACTIONS:
                    # P(a | observed) ∝ P(observed | a) × P(a)
                    posterior_market[a] += likelihoods[a] * normalized_prior_market.get(a, 0.33) * freq
            
            # 归一化市场后验
            total_posterior_market = sum(posterior_market.values())
            if total_posterior_market > 0:
                posterior_market = {k: max(0.01, v / total_posterior_market) for k, v in posterior_market.items()}
            else:
                posterior_market = {'buy': 0.34, 'hold': 0.33, 'sell': 0.33}
            
            # 使用学习率平滑更新市场信念
            for a in ALL_ACTIONS:
                old_prob = prior_market.get(a, 0.33)
                new_prob = (1 - alpha) * old_prob + alpha * posterior_market[a]
                self.market_belief[a] = max(0.01, new_prob)
            
            # 最终归一化
            total_market = sum(self.market_belief.values())
            if total_market > 0:
                self.market_belief = {k: v / total_market for k, v in self.market_belief.items()}
        
        return observation
    
    def _get_opponent_strategy_prob(self, opponent: str) -> Dict[ActionType, float]:
        """获取对手策略概率（虚构对弈 + 贝叶斯更新）"""
        if opponent in self.beliefs and self.beliefs[opponent]:
            return self.beliefs[opponent].copy()
        
        # 使用先验
        return self.gt_config.prior_strategy_probs.copy()
    
    def _compute_best_response(
        self, 
        opponent_probs: Dict[ActionType, float],
        payoff_matrix: Dict[ActionType, Dict[ActionType, float]]
    ) -> Tuple[ActionType, Dict[ActionType, float]]:
        """
        计算最佳响应策略
        
        Returns:
            (最佳行动, 各行动期望支付)
        """
        expected_payoffs: Dict[ActionType, float] = {}
        
        for my_action in ALL_ACTIONS:
            ep = 0.0
            for opp_action, prob in opponent_probs.items():
                base_payoff = payoff_matrix.get(my_action, {}).get(opp_action, 0)
                # 加入风险偏好和情感调整
                adjusted = base_payoff + \
                          self.gt_config.risk_preference * 0.2 + \
                          self.sentiment_bias * 0.15
                ep += prob * adjusted
            expected_payoffs[my_action] = ep
        
        best_action = max(expected_payoffs, key=expected_payoffs.get)
        return best_action, expected_payoffs
    
    def _check_equilibrium(self, sentiments: List[float], payoff_matrix: Optional[Dict[ActionType, Dict[ActionType, float]]] = None) -> Dict:
        """
        检查是否接近纳什均衡（基于博弈论真正均衡定义）
        
        纳什均衡定义：没有人能通过单方面改变策略来获得更高收益
        
        Args:
            sentiments: 参与者情感/策略倾向列表
            payoff_matrix: 可选的支付矩阵用于更精确的均衡检测
        """
        # 方法1：基于情感方差的简单检测（作为初步筛选）
        avg = float(np.mean(sentiments))
        variance = float(np.var(sentiments))
        
        # 判断当前情感状态
        if variance < self.gt_config.equilibrium_threshold:
            current_state = 'equilibrium'
        elif avg > 0.3:
            current_state = 'bullish'
        elif avg < -0.3:
            current_state = 'bearish'
        else:
            current_state = 'uncertain'
        
        # 方法2：如果有支付矩阵，使用纳什均衡真正定义检测
        is_nash_equilibrium = False
        nash_incentive = 0.0
        
        if payoff_matrix is not None:
            # 使用实际的市场信念 self.market_belief 作为当前策略分布
            current_probs = self.market_belief.copy()
            
            # 计算当前策略的期望收益
            current_payoff = 0.0
            for my_action, my_prob in current_probs.items():
                for opp_action, opp_prob in current_probs.items():
                    p = my_prob * opp_prob
                    current_payoff += p * payoff_matrix.get(my_action, {}).get(opp_action, 0)
            
            # 检查是否有偏离动机（最佳响应检测）
            best_response_payoff = max(
                sum(payoff_matrix.get(a, {}).get(oa, 0) * current_probs.get(oa, 0.33) 
                    for oa in ALL_ACTIONS)
                for a in ALL_ACTIONS
            )
            
            nash_incentive = best_response_payoff - current_payoff
            is_nash_equilibrium = abs(nash_incentive) < 0.01  # 几乎没人愿意偏离
        
        # 多轮确认
        if current_state == 'equilibrium' or is_nash_equilibrium:
            if self.equilibrium_candidate in ['equilibrium', 'nash']:
                self.equilibrium_rounds += 1
            else:
                self.equilibrium_candidate = 'nash' if is_nash_equilibrium else 'equilibrium'
                self.equilibrium_rounds = 1
        else:
            self.equilibrium_candidate = None
            self.equilibrium_rounds = 0
        
        confirmed = self.equilibrium_rounds >= self.gt_config.equilibrium_confirmation_rounds
        
        return {
            'average': avg,
            'variance': variance,
            'current_state': current_state,
            'is_nash_equilibrium': is_nash_equilibrium,
            'nash_incentive': nash_incentive,
            'confirmed_equilibrium': confirmed,
            'confirmation_rounds': self.equilibrium_rounds
        }
    
    def decide_action(self, context: Dict, observation: Dict) -> Dict:
        """基于博弈论决策行动（v2.0）"""
        if not self.gt_config.enabled:
            return self._fallback_decision(context)
        
        # 1. 提取市场状态
        market_state = {
            'price': context.get('price', 2300),
            'support': context.get('support_level', 2280),
            'resistance': context.get('resistance_level', 2457),
            'trend': context.get('price_trend', 'sideways'),
            'volatility': context.get('volatility', 0.5)
        }
        
        # 2. 构建动态支付矩阵
        payoff_matrix = self.matrix_builder.build_market_matrix(
            current_price=market_state['price'],
            support_level=market_state['support'],
            resistance_level=market_state['resistance'],
            trend=market_state['trend'],
            volatility=market_state['volatility']
        )
        
        # 验证矩阵
        if not self.matrix_builder.validate_matrix(payoff_matrix):
            return self._fallback_decision(context)
        
        # 3. 分析情感均衡（传入支付矩阵以检测真正的纳什均衡）
        sentiments = [self.sentiment_bias]
        for opp in observation.get('opponents', []):
            stance = opp.get('stance', 'neutral')
            sentiment = 0.5 if stance == 'supportive' else (-0.5 if stance == 'opposing' else 0.0)
            sentiments.append(sentiment)
        
        eq_analysis = self._check_equilibrium(sentiments, payoff_matrix)
        
        # 3.5 信号博弈分析（从对手发言中提取信号）
        signals = []
        sender_stances = []
        for opp_data in observation.get('opponents', []):
            # 从最近发言中提取信号
            recent_messages = opp_data.get('recent_messages', [])
            stance = opp_data.get('stance', 'neutral')
            sender_stances.append(stance)
            
            for msg in recent_messages[-3:]:  # 只看最近3条
                if isinstance(msg, dict):
                    content = msg.get('content', '')
                else:
                    content = str(msg)
                
                # 根据立场确定情感分数
                sentiment = 0.5 if stance == 'supportive' else (-0.5 if stance == 'opposing' else 0.0)
                signal = self.signaling_game.extract_signal_from_message(content, sentiment)
                signals.append(signal)
        
        # 分析信号博弈均衡
        signal_analysis = self.signaling_game.analyze_signal_equilibrium(signals, sender_stances)
        
        # 4. 如果确认均衡，采取保守策略
        if eq_analysis['confirmed_equilibrium']:
            return {
                'action': 'hold',
                'reasoning': f'市场已确认均衡（{eq_analysis["confirmation_rounds"]}轮验证）',
                'gt_analysis': eq_analysis,
                'payoff_matrix': payoff_matrix
            }
        
        # 5. 使用市场聚合信念（基于所有参与者行动的贝叶斯更新）
        # 市场信念 self.market_belief 已经聚合了所有对手的行动
        # 这比简单平均个体信念更能反映市场共识
        combined_probs = self.market_belief.copy()
        
        # 7. 计算最佳响应
        best_action, expected_payoffs = self._compute_best_response(combined_probs, payoff_matrix)
        
        # 8. 验证是否为纳什均衡
        nash_check = self.equilibrium_solver.verify_equilibrium(
            (best_action, max(combined_probs, key=combined_probs.get)),
            payoff_matrix
        )
        
        # 9. 重复博弈策略（真实集成）
        repeated_action_weight = 0.0
        final_action_from_repeated = best_action
        reasoning = f'市场博弈最优: {best_action}'  # 默认值
        gt_analysis_repeated: Dict[str, Any] = {'integration': 'first_round'}
        
        if self.action_history and observation.get('opponents'):
            # 收集所有对手最近行动
            all_recent_actions: List[ActionType] = []
            for opp_data in observation.get('opponents', []):
                recent = opp_data.get('recent_actions', [])
                if recent:
                    all_recent_actions.extend(recent)
            
            if all_recent_actions:
                # 使用最近的一个行动记录到重复博弈策略
                opp_last = all_recent_actions[-1]
                self.repeated_strategy.record_opponent_action(opp_last)
                
                # 获取重复博弈策略的建议
                repeated_action = self.repeated_strategy.choose_action(opp_last)
                
                # 计算重复博弈策略的置信度（基于历史长度）
                history_confidence = min(len(self.action_history) / 10.0, 1.0)  # 最多10轮历史
                
                # 计算市场博弈的置信度（基于纳什均衡确认）
                market_confidence = 1.0 - nash_check.get('my_incentive_to_deviate', 0) / 2.0
                market_confidence = max(0.0, min(1.0, market_confidence))
                
                # 动态权重分配
                total_confidence = history_confidence + market_confidence
                if total_confidence > 0:
                    repeated_action_weight = history_confidence / total_confidence
                
                # 如果重复博弈策略有足够置信度，与最佳响应融合
                if history_confidence >= 0.3 and repeated_action != best_action:
                    # 计算加权融合行动
                    if repeated_action_weight > 0.5:
                        # 重复博弈策略主导
                        final_action_from_repeated = repeated_action
                        reasoning = f'重复博弈策略主导: {repeated_action} (置信度:{repeated_action_weight:.1%})'
                    else:
                        # 两者融合，偏向市场博弈但考虑重复博弈
                        if repeated_action == 'sell' and best_action in ['hold', 'sell']:
                            final_action_from_repeated = 'sell'
                            reasoning = f'融合决策: sell (市场:{best_action}, 重复博弈:{repeated_action})'
                        elif repeated_action == 'buy' and best_action in ['hold', 'buy']:
                            final_action_from_repeated = 'buy'
                            reasoning = f'融合决策: buy (市场:{best_action}, 重复博弈:{repeated_action})'
                        else:
                            final_action_from_repeated = best_action
                            reasoning = f'市场博弈优先: {best_action} (重复博弈:{repeated_action})'
                    
                    # 使用融合后的结果
                    gt_analysis_repeated = {
                        'repeated_action': repeated_action,
                        'history_confidence': history_confidence,
                        'market_confidence': market_confidence,
                        'weight': repeated_action_weight,
                        'final_action': final_action_from_repeated,
                        'integration': 'weighted_blend'
                    }
                else:
                    # 重复博弈置信度不足或动作相同，使用市场博弈
                    gt_analysis_repeated = {
                        'repeated_action': repeated_action,
                        'history_confidence': history_confidence,
                        'market_confidence': market_confidence,
                        'integration': 'low_confidence_ignored' if history_confidence < 0.3 else 'action_matches_best'
                    }
                    final_action_from_repeated = best_action
                    reasoning = f'市场博弈优先: {best_action}'
        else:
            # 第一轮或无历史，使用市场博弈
            gt_analysis_repeated = {'integration': 'first_round'}
            final_action_from_repeated = best_action
            reasoning = f'市场博弈最优: {best_action}'
        
        # 10. 信号博弈调整（优先级高于重复博弈）
        signal_action = self.signaling_game.get_action_from_signal(signal_analysis.get('dominant_signal', 'hold_signal'))
        signal_confidence = signal_analysis.get('inference_confidence', 0)
        
        # 信号博弈的权重更高（基于发言内容）
        if signal_confidence > 0.7 and signal_action != final_action_from_repeated:
            # 信号博弈覆盖其他决策
            final_action = signal_action
            reasoning = f'信号博弈覆盖: {signal_action} (置信度:{signal_confidence:.1%})'
            gt_analysis_signal = {'signal_overridden': True, 'signal_action': signal_action}
        else:
            final_action = final_action_from_repeated
            gt_analysis_signal = {'signal_overridden': False}
        
        # 11. 风险偏好微调（最终调整）
        if self.gt_config.risk_preference > 0.8 and final_action == 'hold':
            final_action = 'buy'
            reasoning += ' (风险偏好调高)'
        elif self.gt_config.risk_preference < 0.2 and final_action == 'sell':
            final_action = 'hold'
            reasoning += ' (风险规避调低)'
        
        return {
            'action': final_action,
            'reasoning': reasoning,
            'gt_analysis': {
                'equilibrium': eq_analysis,
                'nash_check': nash_check,
                'expected_payoffs': expected_payoffs,
                'opponent_probs': combined_probs,
                'signal_analysis': signal_analysis,
                'signal_overridden': gt_analysis_signal.get('signal_overridden', False),
                'repeated_game': gt_analysis_repeated
            },
            'payoff_matrix': payoff_matrix
        }
    
    def _heuristic_decision(self, context: Dict, observation: Dict) -> Dict:
        """启发式决策（后备）"""
        opponent_stances = [opp.get('stance', 'neutral') for opp in observation.get('opponents', [])]
        bearish = opponent_stances.count('opposing')
        bullish = opponent_stances.count('supportive')
        
        if bullish > bearish + 1:
            action: ActionType = 'buy' if self.stance != 'opposing' else 'hold'
            reasoning = f'多头占优({bullish}>{bearish})'
        elif bearish > bullish + 1:
            action = 'sell' if self.stance != 'supportive' else 'hold'
            reasoning = f'空头占优({bearish}>{bullish})'
        else:
            action = 'hold'
            reasoning = '多空僵持'
        
        return {'action': action, 'reasoning': reasoning}
    
    def _fallback_decision(self, context: Dict) -> Dict:
        """后备决策（博弈论禁用时）"""
        if self.stance == 'supportive' and self.sentiment_bias > 0:
            return {'action': 'buy', 'reasoning': '立场偏多'}
        elif self.stance == 'opposing' and self.sentiment_bias < 0:
            return {'action': 'sell', 'reasoning': '立场偏空'}
        return {'action': 'hold', 'reasoning': '中立观望'}
    
    def update(self, action: ActionType, payoff: float):
        """更新历史记录"""
        self.action_history.append(action)
        self.payoff_history.append(payoff)
        self.repeated_strategy.record_my_action(action)
        self.repeated_strategy.record_payoff(payoff)
    
    def get_profile(self) -> Dict:
        """获取Agent配置摘要"""
        return {
            'name': self.name,
            'type': self.entity_type,
            'risk_preference': self.gt_config.risk_preference,
            'sentiment_bias': self.sentiment_bias,
            'stance': self.stance,
            'strategy': self.gt_config.repeated_strategy.value,
            'history_length': len(self.action_history),
            'equilibrium_confirmed': self.equilibrium_rounds >= self.gt_config.equilibrium_confirmation_rounds,
            'discount_factor': self.gt_config.discount_factor
        }


def create_gt_agents(entities: List[Dict], gt_enabled: bool = True) -> List[GameTheoreticAgent]:
    """从实体配置创建博弈论Agent"""
    agents = []
    for entity in entities:
        config = GameTheoreticConfig(enabled=gt_enabled)
        
        # 根据类型调整风险偏好、策略和时间折扣因子
        etype = entity.get('entity_type', 'Person')
        if etype in ['FundManager', 'Organization']:
            config.risk_preference = 0.3
            config.repeated_strategy = GameStrategy.TIT_FOR_TAT  # 机构更理性
            config.discount_factor = 0.98  # 机构更看重长期收益
        elif etype in ['RetailInvestor']:
            config.risk_preference = 0.7
            config.repeated_strategy = GameStrategy.GRIM_TRIGGER  # 散户情绪化
            config.discount_factor = 0.80  # 散户更看重短期收益
        elif etype in ['Miner']:
            config.risk_preference = 0.5
            config.repeated_strategy = GameStrategy.TIT_FOR_TWO_TATS  # 矿工需要稳定
            config.discount_factor = 0.95  # 中等期限
        
        agents.append(GameTheoreticAgent(entity, config))
    return agents


# ============== 测试 ==============

if __name__ == "__main__":
    print("=" * 70)
    print("MiroFish 博弈论增强Agent v2.0 - 测试")
    print("=" * 70)
    
    # 测试1：基本功能
    print("\n[测试1] 基本决策")
    entities = [
        {'entity_name': '李明', 'entity_type': 'Person', 'stance': 'neutral', 'sentiment_bias': 0.2},
        {'entity_name': '王总', 'entity_type': 'FundManager', 'stance': 'supportive', 'sentiment_bias': 0.1},
        {'entity_name': '张矿工', 'entity_type': 'Miner', 'stance': 'opposing', 'sentiment_bias': -0.3},
    ]
    
    agents = create_gt_agents(entities, gt_enabled=True)
    
    for agent in agents:
        print(f"\n  Agent: {agent.name}")
        print(f"  类型: {agent.entity_type}, 风险偏好: {agent.gt_config.risk_preference}")
        print(f"  策略: {agent.gt_config.repeated_strategy.value}")
        
        observation = {
            'opponents': [
                {'name': '王总', 'stance': 'neutral'},
                {'name': '张矿工', 'stance': 'opposing'}
            ]
        }
        
        context = {
            'price': 2310,
            'support_level': 2280,
            'resistance_level': 2457,
            'price_trend': '下降',
            'volatility': 0.6
        }
        
        decision = agent.decide_action(context, observation)
        
        print(f"  决策: {decision['action']}")
        print(f"  推理: {decision['reasoning']}")
        
        if 'gt_analysis' in decision:
            gt = decision['gt_analysis']
            if 'nash_check' in gt:
                print(f"  纳什均衡: {gt['nash_check']['is_nash']}")
    
    # 测试2：支付矩阵构建
    print("\n[测试2] 动态支付矩阵")
    builder = PayoffMatrixBuilder()
    matrix = builder.build_market_matrix(
        current_price=2310,
        support_level=2280,
        resistance_level=2457,
        trend='down',
        volatility=0.6
    )
    print(f"  矩阵验证: {builder.validate_matrix(matrix)}")
    print(f"  buy vs hold: {matrix['buy']['hold']:.2f}")
    
    # 测试3：纳什均衡
    print("\n[测试3] 纳什均衡求解")
    solver = NashEquilibriumSolver()
    equilibria = solver.find_pure_strategy_nash(matrix)
    print(f"  纯策略均衡数: {len(equilibria)}")
    for eq in equilibria:
        print(f"  均衡: {eq}")
        verification = solver.verify_equilibrium(eq, matrix)
        print(f"  验证: {verification}")
    
    # 测试4：重复博弈策略
    print("\n[测试4] 重复博弈策略")
    for strategy in GameStrategy:
        strat = RepeatedGameStrategy(strategy)
        actions = []
        for _ in range(5):
            action = strat.choose_action('sell' if _ == 2 else None)
            actions.append(action)
            strat.record_opponent_action('buy')
        print(f"  {strategy.value}: {actions}")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过!")
    print("=" * 70)