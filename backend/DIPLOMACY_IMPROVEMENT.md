# MiroFish 博弈论外交系统改进方案

## 🎯 核心改进

### 1. 真实博弈论机制
**旧系统**：
- 外交压力 = 0
- 成功/失败随机
- 失败即战争

**新系统**：
- 囚徒困境收益矩阵
- 成本/收益计算
- 声誉系统
- 可信度机制

### 2. 升级阶梯（Escalation Ladder）
**旧系统**：
- 和平 → 战争（直接跳跃）

**新系统**：
- 和平 → 紧张 → 危机 → 制裁 → 代理人战争 → 有限战争 → 全面战争

### 3. Agent 智能提升
**旧系统**：
- 固定策略（deter/escalate/defect）
- 无记忆
- 无学习

**新系统**：
- 基于历史预测对手
- 信任度动态更新
- 战争疲劳机制
- 资源约束

## 📁 新增文件

| 文件 | 功能 |
|------|------|
| `game_theory_diplomacy.py` | 核心博弈论引擎 |
| `diplomacy_integration.py` | 与现有系统集成 |

## 🔧 关键改进点

### 收益矩阵
```python
# 囚徒困境扩展
cooperate_cooperate: (3.0, 3.0)    # 双赢
cooperate_defect:     (0.0, 5.0)    # 被背叛
defect_cooperate:     (5.0, 0.0)    # 背叛成功
defect_defect:        (1.0, 1.0)    # 双输
```

### 外交行动成本
| 行动 | 成本 | 说明 |
|------|------|------|
| 合作 | 2.0 | 需要投入资源 |
| 背叛 | 1.0 | 成本低但损害声誉 |
| 威慑 | 5.0 | 需要军力展示 |
| 升级 | 8.0 | 代价最高 |
| 谈判 | 3.0 | 需要时间 |
| 制裁 | 4.0 | 有经济成本 |

### 冲突升级规则
```
成功合作 → 降级
失败 + 背叛/升级 → 升级
```

## 🚀 部署步骤

### 1. 复制文件
```bash
cp game_theory_diplomacy.py /tmp/mirofish/backend/app/services/
cp diplomacy_integration.py /tmp/mirofish/backend/app/services/
```

### 2. 修改配置
在 `simulation_config.json` 中添加：
```json
{
  "diplomacy_config": {
    "enable_game_theory_diplomacy": true,
    "escalation_ladder": true,
    "reputation_system": true
  }
}
```

### 3. 修改模拟启动器
在 `enhanced_simulation.py` 中集成：
```python
from diplomacy_integration import DiplomacyIntegration

# 初始化
diplomacy = DiplomacyIntegration(simulation_dir, config)
diplomacy.initialize(agent_configs)

# 处理外交事件
result = diplomacy.process_diplomatic_event(event, round_num)

# 每轮结束
diplomacy.advance_round()
```

### 4. 重启模拟
```bash
cd /tmp/mirofish/backend
.venv/bin/python3 scripts/run_parallel_simulation.py \
  --config uploads/simulations/sim_f937065ceb6a/simulation_config.json \
  --max-rounds 68
```

## 📊 预期效果

| 指标 | 旧系统 | 新系统 |
|------|--------|--------|
| 外交成功率 | ~6% | ~30-40% |
| 战争触发 | 立即 | 渐进升级 |
| Agent 行为 | 固定 | 自适应 |
| 合作激励 | 无 | 有 |
| 可预测性 | 高 | 中等 |

## ⚠️ 注意事项

1. **需要重新训练/配置 Agent**：现有 Agent 配置可能需要调整 stance 和 sentiment_bias
2. **LLM 提示词更新**：需要向 LLM 提供外交上下文（声誉、信任度、历史）
3. **数据库迁移**：可能需要添加新表存储外交状态
4. **测试验证**：建议先小规模测试（10-20轮）验证机制

## 🎮 测试建议

```python
# 快速测试
python3 -c "
from game_theory_diplomacy import GameTheoryDiplomacy

d = GameTheoryDiplomacy()
d.initialize_agents([
    {'agent_id': 'usa', 'stance': 'opposing'},
    {'agent_id': 'china', 'stance': 'neutral'},
])

# 模拟10轮
for i in range(10):
    action_usa = d.get_agent_strategy('usa', 'china', [...])
    action_china = d.get_agent_strategy('china', 'usa', [...])
    result = d.calculate_diplomatic_outcome('usa', 'china', action_usa, action_china)
    print(f'Round {i}: {result}')
    d.advance_round()
"
```

## 🔮 未来扩展

1. **联盟机制**：多个 Agent 联合行动
2. **第三方调解**：联合国/欧盟介入
3. **经济制裁网络**：多边制裁
4. **核威慑**：特殊机制
5. **民意系统**：国内政治压力

---

**准备好部署了吗？** 🦐
