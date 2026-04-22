"""
博弈论模块
Game Theory Module for MiroFish

包含:
- game_theory_agent.py: 金融版本（ETH市场专用）
- generic_game_theory.py: 通用版本（任意领域）
- oasis_integration.py: OASIS集成层

快速开始:
    from game_theory_agent import GameTheoreticAgent, GameTheoreticConfig
    
    # 金融版本
    config = GameTheoreticConfig()
    agent = GameTheoreticAgent(base_config, config)
    result = agent.decide_action(context, observation)

OASIS集成:
    from oasis_integration import setup_us_iran_simulation
    setup_us_iran_simulation()
"""

# 导入主要类
from .game_theory_agent import (
    GameTheoreticAgent,
    GameTheoreticConfig,
    GameStrategy,
    PayoffMatrixBuilder,
    NashEquilibriumSolver,
    SignalingGame,
    RepeatedGameStrategy,
    create_gt_agents,
    ALL_ACTIONS
)

from .generic_game_theory import (
    GenericGameTheoreticAgent,
    GenericGameConfig,
    create_generic_agents
)

# OASIS 集成
from .oasis_integration import (
    enable_game_theory,
    disable_game_theory,
    is_game_theory_enabled,
    get_gt_agent,
    compute_game_theory_context,
    inject_game_theory_to_prompt,
    setup_us_iran_simulation,
    get_game_theory_summary
)

__all__ = [
    # 金融版本
    'GameTheoreticAgent',
    'GameTheoreticConfig', 
    'GameStrategy',
    'PayoffMatrixBuilder',
    'NashEquilibriumSolver',
    'SignalingGame',
    'RepeatedGameStrategy',
    'create_gt_agents',
    'ALL_ACTIONS',
    # 通用版本
    'GenericGameTheoreticAgent',
    'GenericGameConfig',
    'create_generic_agents',
    # OASIS集成
    'enable_game_theory',
    'disable_game_theory',
    'is_game_theory_enabled',
    'get_gt_agent',
    'compute_game_theory_context',
    'inject_game_theory_to_prompt',
    'setup_us_iran_simulation',
    'get_game_theory_summary',
]
