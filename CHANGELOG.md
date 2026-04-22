# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-04-22

### Added

#### Game Theory Module (博弈论模块)

**Location**: `backend/app/services/game_theory/`

**Files**:
- `game_theory_agent.py` - 金融版本（ETH市场专用）
- `game_theory_tests.py` - 单元测试
- `generic_game_theory.py` - 通用版本（任意领域）

**Core Features**:

1. **Nash Equilibrium Solver** (纳什均衡求解器)
   - 占优策略检测
   - 最佳响应计算
   - 均衡验证

2. **Bayesian Belief Updating** (贝叶斯信念更新)
   - 个体信念更新（基于观察到的行动）
   - 市场聚合信念（聚合所有参与者行动）
   - 真正的贝叶斯公式：`P(belief|action) ∝ P(action|belief) × P(belief)`

3. **Repeated Game Strategies** (重复博弈策略)
   - Tit-for-Tat（以牙还牙）
   - Grim Trigger（永久惩罚）
   - Suspicious Tit-for-Tat
   - Cooperate/Defect Forever
   - 时间折扣因子 `δ`

4. **Signaling Game Analysis** (信号博弈分析)
   - 从消息中提取信号
   - 分离均衡 vs 混同均衡检测
   - 推断置信度计算

5. **Real Market Payoff Matrix** (真实市场支付矩阵)
   - 基于价格变动预期计算盈亏
   - 支持趋势、位置、波动率因素
   - `calculate_expected_price_change()`
   - `calculate_position_pnl()`

**Generic Version Features** (通用版本):
- 可配置行动空间
- 自定义收益函数
- 适用于：外交博弈、猎鹿博弈、石头剪刀布、资源竞争、社交互动等

**API Usage** (金融版本):

```python
from game_theory_agent import GameTheoreticAgent, GameTheoreticConfig

config = GameTheoreticConfig()
agent = GameTheoreticAgent(
    base_config={'entity_name': 'TestAgent', 'stance': 'neutral'},
    gt_config=config
)

# 观察
observation = agent.observe(opponents, recent_actions)

# 决策
result = agent.decide_action(context, observation)
# result['action'] -> 'buy', 'hold', 'sell'
```

**API Usage** (通用版本):

```python
from generic_game_theory import GenericGameTheoreticAgent, GenericGameConfig

config = GenericGameConfig(actions=['合作', '竞争', '中立'])
agent = GenericGameTheoreticAgent('外交Agent', config, payoff_fn=my_payoff_fn)

result = agent.decide_action(context)
```

### Fixed Issues (v1.x → v2.0)

- [x] Issue 1: 信号博弈未实际使用 → 已集成到 `decide_action()`
- [x] Issue 2: 支付矩阵是简化模型 → 改用真实市场计算
- [x] Issue 3: 重复博弈结果被忽略 → 实现加权融合
- [x] Issue 4: 贝叶斯更新不完整 → 实现真正贝叶斯公式
- [x] Issue 5: market_belief 被重置 → 只在有行动时更新
- [x] Issue 6: 纳什均衡用固定先验 → 改用实际市场信念
- [x] Issue 7: 硬编码行动列表 → 统一为 ALL_ACTIONS
- [x] Issue 8: 拼写错误 signal_clariy → signal_clarity
- [x] Issue 9: 缺乏时间折扣因子 → 添加 discount_factor
- [x] Issue 10: 缺少实体类型差异化 → 不同类型不同折扣因子

### Test Results

```
25 passed ✅
```

## [1.0.0] - 2026-04-21

### Added

- Initial MiroFish backend
- Simulation engine
- Frontend dashboard
- ETH market simulation demo
