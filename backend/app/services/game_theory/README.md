# Game Theory Module (博弈论模块)

## Overview

博弈论增强Agent模块，为MiroFish模拟引擎提供博弈论决策能力。

**两个版本**:
- `game_theory_agent.py` - 金融版本（ETH市场专用）
- `generic_game_theory.py` - 通用版本（任意领域）

---

## Financial Version (金融版本)

### Features

| Feature | Description |
|---------|-------------|
| **Nash Equilibrium** | 纳什均衡求解、最佳响应计算 |
| **Bayesian Belief Update** | 真正贝叶斯公式，聚合所有参与者行动 |
| **Repeated Game Strategies** | Tit-for-Tat, Grim Trigger, 时间折扣因子 |
| **Signaling Game** | 从消息提取信号，分析分离/混同均衡 |
| **Market Payoff Matrix** | 基于真实价格变动计算盈亏 |

### Quick Start

```python
from game_theory_agent import (
    GameTheoreticAgent,
    GameTheoreticConfig,
    GameStrategy,
    ALL_ACTIONS
)

# 创建配置
config = GameTheoreticConfig(
    repeated_strategy=GameStrategy.TIT_FOR_TAT,
    discount_factor=0.95,
    risk_preference=0.5
)

# 创建Agent
agent = GameTheoreticAgent(
    base_config={
        'entity_name': 'Trader1',
        'entity_type': 'FundManager',
        'stance': 'neutral',
        'sentiment_bias': 0.0
    },
    gt_config=config
)

# 观察市场
observation = agent.observe(
    other_agents=[{'entity_name': 'Trader2', 'stance': 'supportive'}],
    recent_actions=[{'agent_name': 'Trader2', 'action_type': 'buy'}]
)

# 决策
context = {
    'price': 2300,
    'support_level': 2280,
    'resistance_level': 2457,
    'price_trend': 'up',
    'volatility': 0.6
}

result = agent.decide_action(context, observation)

print(f"Action: {result['action']}")  # 'buy', 'hold', 'sell'
print(f"Reasoning: {result['reasoning']}")
```

### Configuration

```python
@dataclass
class GameTheoreticConfig:
    enabled: bool = True                    # 启用博弈论增强
    equilibrium_threshold: float = 0.1     # 均衡阈值
    risk_preference: float = 0.5           # 风险偏好 (0-1)
    memory_depth: int = 10                 # 记忆深度
    repeated_strategy: GameStrategy = GameStrategy.TIT_FOR_TAT
    discount_factor: float = 0.95          # 时间折扣因子
    equilibrium_confirmation_rounds: int = 3  # 均衡确认轮数
```

### Game Strategies

| Strategy | Description |
|----------|-------------|
| `TIT_FOR_TAT` | 对手上次做什么我就做什么 |
| `GRIM_TRIGGER` | 一旦对手背叛，永远背叛 |
| `TIT_FOR_TWO_TATS` | 连续两次背叛才反击 |
| `SUSPICIOUS_TFT` | 最初背叛，之后Tit-for-Tat |
| `COOPERATE` | 永远合作 |
| `DEFECT` | 永远背叛 |

### Entity Type Defaults

| Entity Type | Risk Preference | Strategy | Discount Factor |
|-------------|------------------|----------|------------------|
| FundManager | 0.3 (保守) | TIT_FOR_TAT | 0.98 (长期) |
| RetailInvestor | 0.7 (激进) | GRIM_TRIGGER | 0.80 (短期) |
| Miner | 0.5 (中性) | TIT_FOR_TWO_TATS | 0.95 (中期) |

---

## Generic Version (通用版本)

适用于任意领域的博弈论决策，不限于金融。

### Features

| Feature | Description |
|---------|-------------|
| **Custom Actions** | 可配置任意行动空间 |
| **Custom Payoff Function** | 自定义收益函数 |
| **Full Game Theory** | 保留所有博弈论功能 |

### Quick Start

```python
from generic_game_theory import (
    GenericGameTheoreticAgent,
    GenericGameConfig,
    create_generic_agents
)

# 定义收益函数
def stag_hunt_payoff(my, opp, ctx):
    """
    猎鹿博弈：
    - 双方合作(A) = 3
    - 单方背叛(B) = 1
    - 双方背叛(B) = 0
    """
    if my == 'A' and opp == 'A':
        return 3.0
    elif my == 'A' and opp == 'B':
        return 1.0
    elif my == 'B' and opp == 'A':
        return 1.0
    return 0.0

# 创建Agent
config = GenericGameConfig(
    actions=['A', 'B'],  # A=合作(猎鹿), B=单独(抓兔子)
    repeated_strategy='tit_for_tat',
    discount_factor=0.95
)

agents = create_generic_agents(
    names=['Alice', 'Bob'],
    actions=['A', 'B'],
    payoff_fn=stag_hunt_payoff,
    config=config
)

# 决策
for agent in agents:
    result = agent.decide_action({})
    print(f"{agent.name}: {result['action']}")
```

### Example Domains

| Domain | Actions | Payoff Logic |
|--------|---------|--------------|
| **外交博弈** | 合作/对抗/中立 | 合作=+2, 对抗=-1 |
| **猎鹿博弈** | 合作/背叛 | 双方合作=3, 单方背叛=1, 双方背叛=0 |
| **石头剪刀布** | 石头/布/剪刀 | 赢=1, 输=-1, 平=0 |
| **资源竞争** | 开发/保护/分享 | 视情况而定 |
| **社交互动** | 主动/被动/拒绝 | 社交资本回报 |

---

## API Reference

### GameTheoreticAgent (金融版本)

#### Methods

##### `__init__(base_config, gt_config)`
初始化Agent

##### `observe(other_agents, recent_actions) -> Dict`
观察其他Agent的行为并更新信念

##### `decide_action(context, observation) -> Dict`
基于博弈论选择行动

Returns:
```python
{
    'action': 'buy' | 'hold' | 'sell',
    'reasoning': str,
    'gt_analysis': {
        'equilibrium': {...},
        'nash_check': {...},
        'expected_payoffs': {...},
        'opponent_probs': {...},
        'signal_analysis': {...},
        'repeated_game': {...}
    },
    'payoff_matrix': {...}
}
```

##### `update(action, payoff)`
更新历史记录

##### `get_profile() -> Dict`
获取Agent配置摘要

### GenericGameTheoreticAgent (通用版本)

#### Methods

##### `decide_action(context) -> Dict`
基于博弈论选择行动（通用版本）

##### `build_payoff_matrix(context) -> Dict`
构建支付矩阵（使用自定义payoff_fn）

---

## Testing

```bash
cd /tmp/mirofish/backend/app/services/game_theory
pytest game_theory_tests.py -v
```

**Results**: 25 tests passed ✅

---

## OASIS Integration (与MiroFish集成)

### 方案3：决策辅助层

```python
# 1. 启用博弈论
from game_theory import setup_us_iran_simulation
setup_us_iran_simulation()

# 2. 在Agent决策前计算博弈论建议
from game_theory import compute_game_theory_context

gt_context = compute_game_theory_context(
    agent_id='美国政府',
    context={'round': 1},
    observation={'opponents': [...]}
)

# 3. 注入到prompt
enhanced_prompt = inject_game_theory_to_prompt(
    original_prompt,
    agent_id='美国政府',
    context={'round': 1}
)
```

### 美伊停战模拟预设

```python
from game_theory import setup_us_iran_simulation, get_gt_agent

setup_us_iran_simulation()

us_agent = get_gt_agent('美国政府')
result = us_agent.decide_action({'round': 1})
print(f"建议: {result['action']}")
print(f"推理: {result['reasoning']}")
```

### Monkey-Patch (可选)

```python
from game_theory import _patch_oasis_agent
_patch_oasis_agent()  # 自动劫持Agent决策，注入博弈论
```

---

## Version History

See [CHANGELOG.md](../../../../CHANGELOG.md) for full version history.

---

## Authors

MiroFish Development Team

---

## License

MIT
