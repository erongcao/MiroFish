"""
博弈论模块 - OASIS 集成层

功能：
- Monkey-patch OASIS Agent 的决策方法
- 在 LLM 决策前注入博弈论战略分析
- 保持原有架构不变，实现博弈论增强

使用方法：
    from oasis_integration import integrate_game_theory
    integrate_game_theory(agents_config)
"""

import sys
import os
from typing import Dict, List, Any, Optional

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from game_theory_agent import GameTheoreticAgent, GameTheoreticConfig, create_gt_agents
    from generic_game_theory import GenericGameTheoreticAgent, GenericGameConfig
except ImportError:
    from .game_theory_agent import GameTheoreticAgent, GameTheoreticConfig, create_gt_agents
    from .generic_game_theory import GenericGameTheoreticAgent, GenericGameConfig

# 全局变量：存储博弈论增强的 Agent
_gt_agents: Dict[str, GameTheoreticAgent] = {}
_gt_enabled = False
_use_generic = False

# 原始方法引用
_original_perform_action = None


def is_game_theory_enabled() -> bool:
    """检查博弈论是否启用"""
    return _gt_enabled


def get_gt_agent(agent_id: str) -> Optional[GameTheoreticAgent]:
    """获取指定 Agent 的博弈论增强版本"""
    return _gt_agents.get(agent_id)


def enable_game_theory(agents_config: List[Dict], use_generic: bool = False) -> None:
    """
    启用博弈论增强
    
    Args:
        agents_config: Agent 配置列表
        use_generic: 是否使用通用版本（适用于非金融市场）
    """
    global _gt_enabled, _gt_agents, _use_generic
    
    _gt_enabled = True
    _use_generic = use_generic
    _gt_agents = {}
    
    # 根据配置类型选择创建函数
    if use_generic:
        # 通用版本 - 使用外部传入的收益函数
        for config in agents_config:
            agent_id = config.get('agent_id', config.get('name', f'agent_{len(_gt_agents)}'))
            agent_name = config.get('name', agent_id)
            
            # 通用配置
            gt_config = GenericGameConfig(
                actions=config.get('actions', ['A', 'B']),
                repeated_strategy=config.get('strategy', 'tit_for_tat'),
                discount_factor=config.get('discount_factor', 0.95),
                risk_preference=config.get('risk_preference', 0.5),
                belief_update_rate=config.get('belief_update_rate', 0.3)
            )
            
            # 收益函数
            payoff_fn = config.get('payoff_fn')
            
            gt_agent = GenericGameTheoreticAgent(agent_name, gt_config, payoff_fn)
            _gt_agents[agent_id] = gt_agent
    else:
        # 金融版本
        gt_configs = create_gt_agents(agents_config, gt_enabled=True)
        for i, config in enumerate(agents_config):
            agent_id = config.get('agent_id', f'agent_{i}')
            if i < len(gt_configs):
                _gt_agents[agent_id] = gt_configs[i]


def disable_game_theory() -> None:
    """禁用博弈论增强"""
    global _gt_enabled, _gt_agents
    _gt_enabled = False
    _gt_agents = {}


def compute_game_theory_context(
    agent_id: str,
    context: Dict[str, Any],
    observation: Optional[Dict] = None
) -> str:
    """
    计算博弈论上下文，注入到 prompt 中
    
    Args:
        agent_id: Agent ID
        context: 市场/环境上下文
        observation: 观察结果（对手历史等）
    
    Returns:
        博弈论分析文本，用于注入到 prompt
    """
    if not _gt_enabled or agent_id not in _gt_agents:
        return ""
    
    gt_agent = _gt_agents[agent_id]
    
    # 构建博弈论分析
    if _use_generic:
        result = gt_agent.decide_action(context)
    else:
        # 金融版本需要 observation
        if observation is None:
            observation = {'opponents': []}
        result = gt_agent.decide_action(context, observation)
    
    action = result.get('action', 'hold')
    reasoning = result.get('reasoning', '')
    gt_analysis = result.get('gt_analysis', {})
    
    # 构建战略提示
    strategic_prompt = f"""
[博弈论战略分析]
基于当前市场状态和历史博弈分析：
- 建议行动: {action}
- 战略推理: {reasoning}
"""
    
    # 添加纳什均衡信息
    if 'nash_check' in gt_analysis:
        nash = gt_analysis['nash_check']
        if nash.get('is_nash'):
            strategic_prompt += "- 当前处于纳什均衡状态\n"
        else:
            incentive = nash.get('my_incentive_to_deviate', 0)
            if incentive > 0.1:
                strategic_prompt += f"- 偏离动机强度: {incentive:.2f}\n"
    
    # 添加对手概率
    if 'opponent_probs' in gt_analysis:
        probs = gt_analysis['opponent_probs']
        if isinstance(probs, dict):
            for a, p in probs.items():
                if p > 0.3:
                    strategic_prompt += f"- 对手选择{a}的概率: {p:.0%}\n"
    
    # 添加信号博弈分析
    if 'signal_analysis' in gt_analysis:
        signal = gt_analysis['signal_analysis']
        if signal.get('type') == 'separating':
            strategic_prompt += f"- 信号博弈: 分离均衡 (置信度: {signal.get('inference_confidence', 0):.0%})\n"
    
    # 添加重复博弈建议
    if 'repeated_game' in gt_analysis:
        repeated = gt_analysis['repeated_game']
        if repeated.get('integration') == 'weighted_blend':
            strategic_prompt += f"- 重复博弈策略: {repeated.get('repeated_action')}\n"
    
    return strategic_prompt


def inject_game_theory_to_prompt(
    original_prompt: str,
    agent_id: str,
    context: Dict[str, Any],
    observation: Optional[Dict] = None
) -> str:
    """
    将博弈论分析注入到原始 prompt 中
    
    Args:
        original_prompt: 原始 OASIS prompt
        agent_id: Agent ID
        context: 环境上下文
        observation: 观察结果
    
    Returns:
        注入后的 prompt
    """
    if not _gt_enabled:
        return original_prompt
    
    # 计算博弈论上下文
    gt_context = compute_game_theory_context(agent_id, context, observation)
    
    if not gt_context:
        return original_prompt
    
    # 在 prompt 末尾添加博弈论分析
    # 注意：需要找到合适的位置插入
    if "[博弈论战略分析]" in original_prompt:
        # 避免重复注入
        return original_prompt
    
    # 找到 "# RESPONSE FORMAT" 或类似标记，在其之前插入
    if "# RESPONSE FORMAT" in original_prompt:
        return original_prompt.replace(
            "# RESPONSE FORMAT",
            f"{gt_context}\n\n# RESPONSE FORMAT"
        )
    
    # 否则在末尾添加
    return f"{original_prompt}\n\n{gt_context}"


def get_game_theory_summary() -> Dict[str, Any]:
    """获取当前博弈论状态摘要"""
    if not _gt_enabled:
        return {"enabled": False}
    
    summary = {
        "enabled": True,
        "use_generic": _use_generic,
        "agents": {}
    }
    
    for agent_id, agent in _gt_agents.items():
        profile = agent.get_profile() if hasattr(agent, 'get_profile') else {}
        summary["agents"][agent_id] = profile
    
    return summary


# ============================================================
# Monkey-patch 集成（可选）
# ============================================================

_oasis_agent_module = None
_original_astep = None


def _patch_oasis_agent():
    """
    Monkey-patch OASIS Agent 的决策方法
    这是一个可选的高级集成方式
    """
    global _original_astep, _oasis_agent_module
    
    try:
        # 动态导入 OASIS 模块
        from oasis.social_agent.agent import SocialAgent
        _oasis_agent_module = SocialAgent
        
        # 保存原始方法
        _original_astep = SocialAgent.astep
        
        async def patched_astep(self, *args, **kwargs):
            """
            劫持 astep 方法，在决策前注入博弈论分析
            """
            if not _gt_enabled:
                return await _original_astep(self, *args, **kwargs)
            
            # 获取 Agent ID
            agent_id = str(self.social_agent_id)
            
            if agent_id not in _gt_agents:
                return await _original_astep(self, *args, **kwargs)
            
            # 构建上下文（这里需要从 OASIS 环境获取）
            # 注意：这需要根据实际的 OASIS 接口调整
            context = {
                'agent_id': agent_id,
                'round': getattr(self, 'current_round', 0),
            }
            
            # 计算博弈论上下文
            gt_context = compute_game_theory_context(agent_id, context)
            
            if gt_context:
                # 将博弈论上下文注入到消息中
                # 这里需要修改 user_msg 的内容
                # 实际实现需要根据 OASIS 的具体接口
                pass
            
            return await _original_astep(self, *args, **kwargs)
        
        # 应用 patch
        SocialAgent.astep = patched_astep
        print("[博弈论] OASIS Agent monkey-patched successfully")
        
    except ImportError as e:
        print(f"[博弈论] OASIS 模块未找到，跳过 monkey-patch: {e}")
    except Exception as e:
        print(f"[博弈论] Monkey-patch 失败: {e}")


def _unpatch_oasis_agent():
    """恢复原始 OASIS 方法"""
    global _original_astep, _oasis_agent_module
    
    if _oasis_agent_module and _original_astep:
        _oasis_agent_module.astep = _original_astep
        print("[博弈论] OASIS Agent 已恢复")


# ============================================================
# 便捷函数
# ============================================================

def setup_us_iran_simulation():
    """
    设置美伊停战模拟的博弈论配置
    
    这是一个预设配置，展示如何为地缘政治模拟配置通用博弈论
    """
    # 美伊博弈配置
    agents_config = [
        {
            'name': '美国政府',
            'actions': ['遵守停战', '谈判', '维持驻军', '制裁维持', '军事威慑', '暗杀行动'],
            'strategy': 'tit_for_tat',
            'discount_factor': 0.95,
            'risk_preference': 0.3,
            'payoff_fn': _us_iran_payoff
        },
        {
            'name': '伊朗政府',
            'actions': ['遵守停战', '谈判', '挑衅行动', '代理人攻击', '核恢复', '求援中俄'],
            'strategy': 'grim_trigger',
            'discount_factor': 0.85,
            'risk_preference': 0.5,
            'payoff_fn': _iran_payoff
        },
        {
            'name': '伊朗革命卫队',
            'actions': ['挑衅行动', '代理人攻击', '撕毁停战', '遵守停战'],
            'strategy': 'defect',
            'discount_factor': 0.7,
            'risk_preference': 0.85,
            'payoff_fn': _irgc_payoff
        },
        {
            'name': '以色列',
            'actions': ['单独打击', '破坏停战', '情报共享', '遵守停战'],
            'strategy': 'defect',
            'discount_factor': 0.65,
            'risk_preference': 0.9,
            'payoff_fn': _israel_payoff
        },
        {
            'name': '中国',
            'actions': ['呼吁和平', '暗中援助', '经济合作', '外交庇护'],
            'strategy': 'suspicious_tit_for_tat',
            'discount_factor': 0.98,
            'risk_preference': 0.35,
            'payoff_fn': _china_payoff
        },
    ]
    
    enable_game_theory(agents_config, use_generic=True)
    return agents_config


def _us_iran_payoff(my_action, opp_action, context):
    """美伊博弈收益函数"""
    # 简化版
    if my_action == '遵守停战' and opp_action == '遵守停战':
        return 2.5
    elif my_action == '谈判' and opp_action == '谈判':
        return 2.0
    elif my_action in ['挑衅行动', '撕毁停战'] and opp_action in ['破坏停战', '单独打击']:
        return -3.0
    elif my_action == '挑衅行动' and opp_action == '遵守停战':
        return 1.5
    elif my_action == '遵守停战' and opp_action == '挑衅行动':
        return -1.0
    return 0.0


def _iran_payoff(my_action, opp_action, context):
    """伊朗博弈收益函数"""
    return _us_iran_payoff(my_action, opp_action, context)


def _irgc_payoff(my_action, opp_action, context):
    """革命卫队博弈收益函数"""
    # 卫队更激进
    if my_action in ['挑衅行动', '撕毁停战']:
        return 1.0 if opp_action == '遵守停战' else -1.0
    return 0.0


def _israel_payoff(my_action, opp_action, context):
    """以色列博弈收益函数"""
    if my_action == '单独打击':
        return 2.0 if opp_action in ['挑衅行动', '核恢复'] else -1.0
    return 0.0


def _china_payoff(my_action, opp_action, context):
    """中国博弈收益函数"""
    if my_action == '暗中援助' and opp_action in ['挑衅行动', '代理人攻击']:
        return 1.5
    elif my_action == '呼吁和平':
        return 1.0
    return 0.0


if __name__ == "__main__":
    # 测试
    print("=" * 50)
    print("博弈论 OASIS 集成测试")
    print("=" * 50)
    
    # 设置美伊模拟
    setup_us_iran_simulation()
    
    # 检查启用状态
    print(f"\n博弈论启用: {is_game_theory_enabled()}")
    print(f"Agent 数量: {len(_gt_agents)}")
    
    # 测试博弈论计算
    for agent_id, agent in _gt_agents.items():
        context = {'round': 1}
        result = agent.decide_action(context)
        print(f"\n{agent.name}:")
        print(f"  行动: {result.get('action')}")
        print(f"  推理: {result.get('reasoning')}")
