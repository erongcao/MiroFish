"""
博弈论增强Agent - 通用版本
Game-Theoretic Enhanced Agent (Generic Version)

与金融版本的核心区别：
- 行动类型可配置（不限于 buy/hold/sell）
- 支付矩阵通过用户定义的收益函数计算
- 移除所有市场特定术语和计算
- 保持完整的博弈论功能

功能：
1. 纳什均衡求解
2. 贝叶斯信念更新
3. 重复博弈策略（tit-for-tat, grim trigger等）
4. 信号博弈分析
5. 时间折扣因子
"""

import random
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Literal, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter


# ============== 类型定义 ==============

GameStage = Literal['one-shot', 'repeated', 'continuous']
SignalType = str  # 通用信号类型


# ============== 核心配置 ==============

@dataclass
class GenericGameConfig:
    """通用博弈论配置"""
    
    # 启用博弈论增强
    enabled: bool = True
    
    # 游戏类型
    game_stage: GameStage = 'repeated'
    
    # 可配置的行动列表
    actions: List[str] = field(default_factory=lambda: ['A', 'B'])
    
    # 支付矩阵： Dict[my_action, Dict[opp_action, payoff]]
    # 如果未提供，需要提供 payoff_fn 来计算
    payoff_matrix: Optional[Dict[str, Dict[str, float]]] = None
    
    # 可选的收益函数：payoff_fn(my_action, opp_action, context) -> float
    payoff_fn: Optional[Callable] = None
    
    # 先验信念（每个对手的初始信念分布）
    prior_beliefs: Dict[str, Dict[str, float]] = field(default_factory=lambda: {})
    
    # 信念更新学习率
    belief_update_rate: float = 0.3
    
    # 重复博弈策略类型
    repeated_strategy: str = 'tit_for_tat'  # tit_for_tat, grim_trigger, cooperated, defected
    
    # 时间折扣因子（0-1，越接近1越看重未来）
    discount_factor: float = 0.95
    
    # 均衡确认轮数
    equilibrium_confirmation_rounds: int = 3
    
    # 均衡阈值（用于情感一致性检测）
    equilibrium_threshold: float = 0.1
    
    # 风险偏好（0=极端风险规避, 0.5=中性, 1=极端风险偏好）
    risk_preference: float = 0.5
    
    # 记忆深度
    memory_depth: int = 10


# ============== 纳什均衡求解器 ==============

class NashEquilibriumSolver:
    """纳什均衡求解器（通用版本）"""
    
    def __init__(self, actions: List[str]):
        self.actions = actions
    
    def find_dominant_strategy(
        self, 
        payoff_matrix: Dict[str, Dict[str, float]]
    ) -> Optional[str]:
        """
        寻找占优策略
        如果某个策略对所有对手策略都是最优的，则为占优策略
        """
        if not payoff_matrix or not self.actions:
            return None
        
        best_actions = []
        best_payoffs = {}
        
        for my_action in self.actions:
            if my_action not in payoff_matrix:
                continue
            
            # 最小收益（最坏情况）
            worst_case = min(payoff_matrix[my_action].values())
            best_payoffs[my_action] = worst_case
        
        # 找最大最小
        if not best_payoffs:
            return None
        
        max_min = max(best_payoffs.values())
        best_actions = [a for a, p in best_payoffs.items() if p == max_min]
        
        return best_actions[0] if len(best_actions) == 1 else None
    
    def find_best_response(
        self,
        opponent_probs: Dict[str, float],
        payoff_matrix: Dict[str, Dict[str, float]]
    ) -> Tuple[str, float]:
        """
        计算最佳响应策略
        
        Returns:
            (最佳行动, 期望收益)
        """
        expected_payoffs = {}
        
        for my_action in self.actions:
            if my_action not in payoff_matrix:
                expected_payoffs[my_action] = 0.0
                continue
            
            ep = 0.0
            for opp_action, prob in opponent_probs.items():
                ep += prob * payoff_matrix[my_action].get(opp_action, 0.0)
            expected_payoffs[my_action] = ep
        
        if not expected_payoffs:
            return self.actions[0] if self.actions else 'A', 0.0
        
        best_action = max(expected_payoffs, key=expected_payoffs.get)
        return best_action, expected_payoffs[best_action]
    
    def verify_equilibrium(
        self,
        strategy_pair: Tuple[str, str],
        payoff_matrix: Dict[str, Dict[str, float]]
    ) -> Dict:
        """
        验证是否达到纳什均衡
        纳什均衡：没有人能通过单方面改变策略来获得更高收益
        """
        my_action, opp_action = strategy_pair
        
        my_payoff = payoff_matrix.get(my_action, {}).get(opp_action, 0.0)
        my_best = max(
            payoff_matrix.get(a, {}).get(opp_action, 0.0)
            for a in self.actions
        )
        
        opp_payoff = payoff_matrix.get(opp_action, {}).get(my_action, 0.0)
        opp_best = max(
            payoff_matrix.get(a, {}).get(my_action, 0.0)
            for a in self.actions
        )
        
        return {
            'is_nash': abs(my_payoff - my_best) < 1e-6 and abs(opp_payoff - opp_best) < 1e-6,
            'my_incentive_to_deviate': my_best - my_payoff,
            'opp_incentive_to_deviate': opp_best - opp_payoff
        }


# ============== 重复博弈策略 ==============

class RepeatedGameStrategy:
    """
    重复博弈策略执行器（通用版本）
    
    支持策略：
    - tit_for_tat: 对手上次做什么我就做什么
    - grim_trigger: 一旦对手背叛，永远背叛
    - cooperated: 永远合作
    - defected: 永远背叛
    - suspicious_tit_for_tat: 最初背叛，之后 tit_for_tat
    """
    
    def __init__(self, strategy_type: str, discount_factor: float = 0.95):
        self.strategy_type = strategy_type
        self.discount_factor = discount_factor
        self.opponent_history: List[str] = []
        self.my_history: List[str] = []
        self.defected = False  # 用于 grim_trigger
    
    def record_opponent_action(self, action: str):
        """记录对手的行动"""
        self.opponent_history.append(action)
        
        # grim_trigger: 如果对手背叛，标记
        if action != self.get_cooperate_action():
            self.defected = True
    
    def record_my_action(self, action: str):
        """记录自己的行动"""
        self.my_history.append(action)
    
    def get_cooperate_action(self) -> str:
        """获取代表"合作"的动作（第一个动作）"""
        return self.my_history[0] if self.my_history else 'A'
    
    def choose_action(self, opponent_last_action: Optional[str] = None) -> str:
        """
        根据策略选择行动
        """
        if not self.opponent_history and not opponent_last_action:
            return self.get_cooperate_action()
        
        last_opp = opponent_last_action or self.opponent_history[-1]
        
        if self.strategy_type == 'tit_for_tat':
            return last_opp
        
        elif self.strategy_type == 'grim_trigger':
            if self.defected:
                return self.get_defect_action()
            return self.get_cooperate_action()
        
        elif self.strategy_type == 'suspicious_tit_for_tat':
            if len(self.opponent_history) == 0:
                return self.get_defect_action()  # 第一次先背叛
            return last_opp
        
        elif self.strategy_type == 'cooperated':
            return self.get_cooperate_action()
        
        elif self.strategy_type == 'defected':
            return self.get_defect_action()
        
        # 默认 tit_for_tat
        return last_opp
    
    def get_defect_action(self) -> str:
        """获取代表"背叛"的动作（第二个动作）"""
        return self.my_history[1] if len(self.my_history) > 1 else ('B' if self.get_cooperate_action() == 'A' else 'A')


# ============== 贝叶斯信念更新 ==============

class BayesianBeliefUpdater:
    """
    贝叶斯信念更新器（通用版本）
    
    核心公式：P(belief | action) ∝ P(action | belief) × P(belief)
    """
    
    def __init__(self, actions: List[str], learning_rate: float = 0.3):
        self.actions = actions
        self.learning_rate = learning_rate
        self.beliefs: Dict[str, Dict[str, float]] = {}  # agent_name -> belief distribution
        self.action_history: List[str] = []  # 聚合所有观察到的行动
    
    def initialize_belief(self, agent_name: str, prior: Optional[Dict[str, float]] = None):
        """初始化信念"""
        if prior:
            self.beliefs[agent_name] = prior.copy()
        else:
            # 均匀分布
            prob = 1.0 / len(self.actions)
            self.beliefs[agent_name] = {a: prob for a in self.actions}
    
    def update_belief(
        self, 
        agent_name: str, 
        observed_action: str,
        likelihood_matrix: Optional[Dict[str, Dict[str, float]]] = None
    ):
        """
        对单个Agent的信念进行贝叶斯更新
        """
        if agent_name not in self.beliefs:
            self.initialize_belief(agent_name)
        
        prior = self.beliefs[agent_name].copy()
        
        # 归一化先验
        total_prior = sum(prior.values())
        if total_prior > 0:
            normalized_prior = {a: p / total_prior for a, p in prior.items()}
        else:
            normalized_prior = {a: 1.0 / len(self.actions) for a in self.actions}
        
        # 获取似然（如果没提供，使用默认的基于观察到的行动）
        if likelihood_matrix is None:
            likelihood_matrix = self._default_likelihood(observed_action)
        
        likelihoods = likelihood_matrix.get(observed_action, 
            {a: 1.0 / len(self.actions) for a in self.actions})
        
        # 贝叶斯更新：posterior ∝ likelihood × prior
        posterior = {}
        for a in self.actions:
            posterior[a] = likelihoods.get(a, 0) * normalized_prior.get(a, 0)
        
        # 归一化后验
        total_posterior = sum(posterior.values())
        if total_posterior > 0:
            posterior = {a: max(0.01, p / total_posterior) for a, p in posterior.items()}
        else:
            posterior = {a: 1.0 / len(self.actions) for a in self.actions}
        
        # 使用学习率平滑更新
        new_belief = {}
        for a in self.actions:
            old_prob = prior.get(a, 1.0 / len(self.actions))
            new_prob = (1 - self.learning_rate) * old_prob + self.learning_rate * posterior[a]
            new_belief[a] = max(0.01, new_prob)
        
        # 归一化
        total = sum(new_belief.values())
        if total > 0:
            new_belief = {a: p / total for a, p in new_belief.items()}
        
        self.beliefs[agent_name] = new_belief
    
    def _default_likelihood(self, observed_action: str) -> Dict[str, Dict[str, float]]:
        """
        默认似然函数：
        观察到 action X 认为对手倾向 X
        """
        likelihood = {}
        for obs in self.actions:
            likelihood[obs] = {}
            for belief in self.actions:
                # 如果观察到的行动与信念一致，似然高
                likelihood[obs][belief] = 0.7 if obs == belief else (0.3 / (len(self.actions) - 1) if len(self.actions) > 1 else 0.3)
        return likelihood
    
    def update_market_belief(self, all_observed_actions: List[str]):
        """
        聚合所有行动的信念更新（市场共识）
        """
        if not all_observed_actions:
            return
        
        self.action_history.extend(all_observed_actions)
        
        # 统计频率
        counts = Counter(all_observed_actions)
        total = len(all_observed_actions)
        
        # 更新每个行动的频率作为信念
        for action in self.actions:
            self.beliefs['__market__'] = self.beliefs.get('__market__', 
                {a: 1.0 / len(self.actions) for a in self.actions})
            
            old = self.beliefs['__market__'].get(action, 0)
            new = counts.get(action, 0) / total
            
            # 平滑更新
            self.beliefs['__market__'][action] = (
                1 - self.learning_rate
            ) * old + self.learning_rate * new
    
    def get_belief(self, agent_name: str) -> Dict[str, float]:
        """获取信念分布"""
        if agent_name not in self.beliefs:
            self.initialize_belief(agent_name)
        return self.beliefs[agent_name].copy()
    
    def get_market_belief(self) -> Dict[str, float]:
        """获取市场共识信念"""
        return self.beliefs.get('__market__', 
            {a: 1.0 / len(self.actions) for a in self.actions}).copy()


# ============== 信号博弈 ==============

class GenericSignalingGame:
    """
    通用信号博弈分析
    
    发送者有不同类型，发送信号，接收者根据信号行动
    均衡可能是分离的（不同类型发不同信号）或混同的（所有类型发同一信号）
    """
    
    def __init__(self, signal_types: List[str], receiver_actions: List[str]):
        self.signal_types = signal_types
        self.receiver_actions = receiver_actions
        self.signal_history: List[SignalType] = []
    
    def extract_signal_from_message(self, message: str, sentiment: float = 0.0) -> str:
        """
        从消息中提取信号（简单关键词匹配）
        可以被子类重写实现更复杂的分析
        """
        # 简单的关键词匹配
        positive_keywords = ['good', 'great', 'agree', 'support', 'yes', '合作', '支持', '同意', '好']
        negative_keywords = ['bad', 'no', 'oppose', 'reject', 'disagree', '拒绝', '反对', '不好', '差']
        
        msg_lower = message.lower()
        
        for kw in positive_keywords:
            if kw in msg_lower:
                return self.signal_types[0] if len(self.signal_types) > 0 else 'positive'
        
        for kw in negative_keywords:
            if kw in msg_lower:
                return self.signal_types[-1] if len(self.signal_types) > 1 else 'negative'
        
        return self.signal_types[len(self.signal_types) // 2] if len(self.signal_types) > 2 else 'neutral'
    
    def analyze_equilibrium(
        self, 
        signals: List[str],
        receiver_actions: List[str]
    ) -> Dict:
        """
        分析信号博弈均衡
        
        Returns:
            {
                'type': 'separating' | 'pooling' | 'inconclusive',
                'dominant_signal': 主要信号,
                'signal_counts': 信号统计,
                'inference_confidence': 推断置信度
            }
        """
        if not signals:
            return {
                'type': 'inconclusive',
                'dominant_signal': self.signal_types[0] if self.signal_types else 'none',
                'signal_counts': {},
                'inference_confidence': 0
            }
        
        # 统计信号分布
        signal_counts = Counter(signals)
        total = len(signals)
        
        # 找主要信号
        dominant_signal = signal_counts.most_common(1)[0][0] if signal_counts else self.signal_types[0]
        
        # 计算清晰度（主要信号占比）
        clarity = signal_counts[dominant_signal] / total if total > 0 else 0
        
        # 判断均衡类型
        if clarity > 0.7:
            eq_type = 'separating'  # 分离均衡：信号清晰
        elif clarity < 0.4:
            eq_type = 'pooling'  # 混同均衡：信号混乱
        else:
            eq_type = 'inconclusive'
        
        return {
            'type': eq_type,
            'dominant_signal': dominant_signal,
            'signal_counts': dict(signal_counts),
            'signal_clarity': clarity,
            'inference_confidence': clarity
        }
    
    def get_action_from_signal(self, signal: str) -> str:
        """从信号推断接收者应该采取的行动"""
        # 简化：直接映射
        signal_idx = self.signal_types.index(signal) if signal in self.signal_types else len(self.signal_types) // 2
        action_idx = min(signal_idx, len(self.receiver_actions) - 1)
        return self.receiver_actions[action_idx]


# ============== 通用博弈论Agent ==============

class GenericGameTheoreticAgent:
    """
    通用博弈论增强Agent
    
    可以配置任意行动空间和收益函数，用于任何领域：
    - 外交博弈：合作/对抗/中立
    - 资源竞争：开发/保护/分享
    - 社交互动：主动/被动/拒绝
    - 等等...
    """
    
    def __init__(
        self,
        name: str,
        config: GenericGameConfig,
        payoff_fn: Optional[Callable] = None
    ):
        self.name = name
        self.config = config
        self.actions = config.actions
        
        # 初始化组件
        self.equilibrium_solver = NashEquilibriumSolver(self.actions)
        self.belief_updater = BayesianBeliefUpdater(
            self.actions, 
            config.belief_update_rate
        )
        self.repeated_strategy = RepeatedGameStrategy(
            config.repeated_strategy,
            config.discount_factor
        )
        self.signaling_game = GenericSignalingGame(
            signal_types=['positive', 'neutral', 'negative'],
            receiver_actions=self.actions[:2] if len(self.actions) >= 2 else self.actions
        )
        
        # 状态
        self.beliefs: Dict[str, Dict[str, float]] = {}  # 对手信念
        self.market_belief: Dict[str, float] = {a: 1.0/len(self.actions) for a in self.actions}
        self.action_history: List[str] = []
        self.payoff_history: List[float] = []
        self.equilibrium_rounds = 0
        self.equilibrium_candidate: Optional[str] = None
        
        # 自定义收益函数
        self.custom_payoff_fn = payoff_fn or config.payoff_fn
    
    def build_payoff_matrix(self, context: Optional[Dict] = None) -> Dict[str, Dict[str, float]]:
        """
        构建支付矩阵
        
        如果提供了自定义 payoff_fn，使用它计算
        否则使用配置的 payoff_matrix
        """
        if self.custom_payoff_fn:
            matrix = {}
            for my_action in self.actions:
                matrix[my_action] = {}
                for opp_action in self.actions:
                    matrix[my_action][opp_action] = self.custom_payoff_fn(
                        my_action, opp_action, context or {}
                    )
            return matrix
        
        if self.config.payoff_matrix:
            return self.config.payoff_matrix
        
        # 默认：协调博弈（双方选择相同行动都获益）
        matrix = {}
        for i, my_action in enumerate(self.actions):
            matrix[my_action] = {}
            for j, opp_action in enumerate(self.actions):
                if i == j:
                    matrix[my_action][opp_action] = 2.0  # 协调成功
                else:
                    matrix[my_action][opp_action] = 0.0  # 协调失败
        return matrix
    
    def observe(self, opponents: List[Dict], recent_actions: List[Dict]) -> Dict:
        """
        观察其他Agent的行为并更新信念
        """
        observation = {'opponents': []}
        
        # 收集所有观察到的行动
        all_observed_actions: List[str] = []
        
        for opponent in opponents:
            opp_name = opponent.get('name', opponent.get('entity_name', 'unknown'))
            opp_actions = [
                a.get('action_type', a.get('action', 'unknown')) 
                for a in recent_actions 
                if a.get('agent_name') == opp_name
            ]
            
            all_observed_actions.extend(opp_actions)
            
            # 更新个体信念
            for action in opp_actions:
                self.belief_updater.update_belief(opp_name, action)
            
            # 获取更新后的信念
            belief = self.belief_updater.get_belief(opp_name)
            
            observation['opponents'].append({
                'name': opp_name,
                'beliefs': belief,
                'recent_actions': opp_actions[-5:]
            })
        
        # 更新市场共识信念
        if all_observed_actions:
            self.belief_updater.update_market_belief(all_observed_actions)
            self.market_belief = self.belief_updater.get_market_belief()
        
        return observation
    
    def _check_equilibrium(
        self, 
        payoff_matrix: Dict[str, Dict[str, float]]
    ) -> Dict:
        """
        检查是否接近纳什均衡
        """
        if not self.action_history:
            return {'current_state': 'no_history', 'is_nash_equilibrium': False}
        
        # 基于市场信念计算当前策略分布
        current_probs = self.market_belief.copy()
        
        # 计算当前策略的期望收益
        current_payoff = 0.0
        for my_action, my_prob in current_probs.items():
            for opp_action, opp_prob in current_probs.items():
                p = my_prob * opp_prob
                current_payoff += p * payoff_matrix.get(my_action, {}).get(opp_action, 0)
        
        # 检查最佳响应
        best_response, best_payoff = self.equilibrium_solver.find_best_response(
            current_probs, payoff_matrix
        )
        
        nash_incentive = best_payoff - current_payoff
        is_nash = abs(nash_incentive) < 0.01
        
        # 多轮确认
        if is_nash:
            if self.equilibrium_candidate == 'nash':
                self.equilibrium_rounds += 1
            else:
                self.equilibrium_candidate = 'nash'
                self.equilibrium_rounds = 1
        else:
            self.equilibrium_candidate = None
            self.equilibrium_rounds = 0
        
        confirmed = self.equilibrium_rounds >= self.config.equilibrium_confirmation_rounds
        
        return {
            'current_state': 'nash' if is_nash else 'off_equilibrium',
            'is_nash_equilibrium': is_nash,
            'nash_incentive': nash_incentive,
            'confirmed_equilibrium': confirmed,
            'confirmation_rounds': self.equilibrium_rounds
        }
    
    def decide_action(
        self, 
        context: Optional[Dict] = None
    ) -> Dict:
        """
        基于博弈论选择行动
        
        决策流程：
        1. 构建支付矩阵
        2. 检查纳什均衡
        3. 使用贝叶斯信念计算对手策略概率
        4. 计算最佳响应
        5. 应用重复博弈策略调整
        6. 应用信号博弈调整
        """
        context = context or {}
        
        # 1. 构建支付矩阵
        payoff_matrix = self.build_payoff_matrix(context)
        
        # 2. 检查纳什均衡
        eq_analysis = self._check_equilibrium(payoff_matrix)
        
        # 3. 使用市场信念作为对手策略概率
        opponent_probs = self.market_belief.copy()
        
        # 4. 计算最佳响应
        best_action, expected_payoffs = self.equilibrium_solver.find_best_response(
            opponent_probs, payoff_matrix
        )
        
        # 5. 验证纳什均衡
        nash_check = self.equilibrium_solver.verify_equilibrium(
            (best_action, max(opponent_probs, key=opponent_probs.get)),
            payoff_matrix
        )
        
        # 6. 重复博弈策略调整
        final_action = best_action
        reasoning = f'博弈论最优: {best_action}'
        
        if self.action_history:
            opp_last = self.action_history[-1] if self.action_history else None
            repeated_action = self.repeated_strategy.choose_action(opp_last)
            
            # 如果重复博弈策略有足够历史支持
            history_confidence = min(len(self.action_history) / 10.0, 1.0)
            
            if history_confidence >= 0.3 and repeated_action != best_action:
                if history_confidence > 0.5:
                    final_action = repeated_action
                    reasoning = f'重复博弈策略主导: {repeated_action}'
                else:
                    final_action = best_action
                    reasoning = f'市场博弈优先: {best_action} (重复博弈建议: {repeated_action})'
        
        # 7. 信号博弈调整（如果有）
        if 'message' in context:
            signal = self.signaling_game.extract_signal_from_message(
                context['message'], 
                context.get('sentiment', 0.0)
            )
            signal_analysis = self.signaling_game.analyze_equilibrium([signal], [])
            signal_action = self.signaling_game.get_action_from_signal(signal)
            
            if signal_analysis.get('inference_confidence', 0) > 0.7:
                final_action = signal_action
                reasoning = f'信号博弈覆盖: {signal_action}'
        
        return {
            'action': final_action,
            'reasoning': reasoning,
            'gt_analysis': {
                'equilibrium': eq_analysis,
                'nash_check': nash_check,
                'expected_payoffs': expected_payoffs,
                'opponent_probs': opponent_probs,
                'payoff_matrix': payoff_matrix
            }
        }
    
    def update(self, action: str, payoff: float):
        """更新历史记录"""
        self.action_history.append(action)
        self.payoff_history.append(payoff)
        self.repeated_strategy.record_my_action(action)
        self.repeated_strategy.record_opponent_action(action)
    
    def get_profile(self) -> Dict:
        """获取Agent配置摘要"""
        return {
            'name': self.name,
            'actions': self.actions,
            'strategy': self.config.repeated_strategy,
            'discount_factor': self.config.discount_factor,
            'history_length': len(self.action_history),
            'equilibrium_confirmed': self.equilibrium_rounds >= self.config.equilibrium_confirmation_rounds
        }


# ============== 工厂函数 ==============

def create_generic_agents(
    names: List[str],
    actions: List[str] = None,
    payoff_fn: Callable = None,
    config: Optional[GenericGameConfig] = None
) -> List[GenericGameTheoreticAgent]:
    """
    创建通用博弈论Agent列表
    
    Args:
        names: Agent名称列表
        actions: 行动空间，默认 ['A', 'B']
        payoff_fn: 收益函数 fn(my_action, opp_action, context) -> float
        config: 配置对象，默认新建
    
    Returns:
        Agent列表
    """
    if actions is None:
        actions = ['A', 'B']
    
    if config is None:
        config = GenericGameConfig()
    
    config.actions = actions
    
    agents = []
    for name in names:
        agent = GenericGameTheoreticAgent(name, config, payoff_fn)
        agents.append(agent)
    
    return agents


# ============== 示例用法 ==============

if __name__ == '__main__':
    # 示例1：协调博弈（所有人都想协调的场景）
    print('=' * 60)
    print('示例1：协调博弈')
    print('=' * 60)
    
    def coordination_payoff(my, opp, ctx):
        """协调收益：双方选择相同则都获益"""
        return 2.0 if my == opp else 0.0
    
    agents = create_generic_agents(
        names=['Alice', 'Bob', 'Charlie'],
        actions=['A', 'B'],
        payoff_fn=coordination_payoff
    )
    
    for agent in agents:
        result = agent.decide_action({})
        print(f'{agent.name}: {result["action"]} ({result["reasoning"]})')
    
    # 示例2：猎鹿博弈（合作收益大于单独行动）
    print()
    print('=' * 60)
    print('示例2：猎鹿博弈（合作 vs 单独行动）')
    print('=' * 60)
    
    def stag_hunt_payoff(my, opp, ctx):
        """
        猎鹿博弈：
        - 双方合作(A) = 3
        - 单方合作(A) + 单方背叛(B) = 1
        - 双方背叛(B) = 0
        """
        if my == 'A' and opp == 'A':
            return 3.0  # 合作成功
        elif my == 'A' and opp == 'B':
            return 1.0  # 被背叛
        elif my == 'B' and opp == 'A':
            return 1.0  # 背叛合作者
        else:
            return 0.0  # 双方背叛
    
    agents = create_generic_agents(
        names=['David', 'Eve'],
        actions=['A', 'B'],  # A=合作（猎鹿），B=单独行动（抓兔子）
        payoff_fn=stag_hunt_payoff
    )
    
    # 模拟几轮
    for i in range(3):
        print(f'\n第{i+1}轮:')
        for agent in agents:
            result = agent.decide_action({})
            print(f'  {agent.name}: {result["action"]}')
        
        # 更新（这里简化：假设所有人都选A）
        for agent in agents:
            agent.update('A', 3.0 if len(agents) > 1 else 0.0)
    
    # 示例3：石头剪刀布（零和博弈）
    print()
    print('=' * 60)
    print('示例3：石头剪刀布（零和博弈）')
    print('=' * 60)
    
    def rock_paper_scissors_payoff(my, opp, ctx):
        """石头剪刀布：赢=1，输=-1，平=0"""
        if my == opp:
            return 0.0
        if (my == 'rock' and opp == 'scissors') or \
           (my == 'scissors' and opp == 'paper') or \
           (my == 'paper' and opp == 'rock'):
            return 1.0
        return -1.0
    
    agents = create_generic_agents(
        names=['Player1', 'Player2'],
        actions=['rock', 'paper', 'scissors'],
        payoff_fn=rock_paper_scissors_payoff
    )
    
    for agent in agents:
        result = agent.decide_action({})
        print(f'{agent.name}: {result["action"]}')
