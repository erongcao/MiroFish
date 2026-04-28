# MiroFish 框架扩展模块总结

## 新增模块

### 1. 联盟机制 (`alliance_system.py`)
- **功能**: 多 Agent 联合行动、联盟形成与维护
- **核心类**: `AllianceSystem`, `Alliance`
- **特性**:
  - 5种同盟类型（防御/进攻/经济/情报/综合）
  - 凝聚力动态计算
  - 集体防御自动触发
  - 集体行动（制裁/攻击）
  - 信任度驱动的联盟形成

### 2. 经济制裁网络 (`sanction_network.py`)
- **功能**: 多边制裁、制裁效果追踪、反制裁机制
- **核心类**: `SanctionNetwork`, `Sanction`
- **特性**:
  - 6种制裁类型
  - 4级严重程度
  - 多边制裁实力加成
  - 制裁效果衰减
  - 反制裁机制
  - 总经济影响计算

### 3. 第三方调解 (`third_party_mediation.py`)
- **功能**: 联合国/欧盟/中立国介入调解冲突
- **核心类**: `ThirdPartyMediation`, `MediationAttempt`
- **特性**:
  - 5种调解者类型
  - 调解成功概率计算
  - 冲突级别影响
  - 信任恢复机制
  - 调解冷却期
  - 自动寻找最佳调解者

### 4. 核威慑机制 (`nuclear_deterrence.py`)
- **功能**: 特殊威慑逻辑、相互确保毁灭、核门槛
- **核心类**: `NuclearDeterrence`, `NuclearArsenal`
- **特性**:
  - 4级核地位
  - 4种威慑姿态
  - 二次打击能力
  - 导弹防御
  - MAD 概率计算
  - 核交换模拟
  - 不首先使用承诺

### 5. 国内政治压力 (`domestic_politics.py`)
- **功能**: 民意、选举、政治约束对 Agent 外交决策的影响
- **核心类**: `DomesticPolitics`, `DomesticPoliticalState`
- **特性**:
  - 3种政治体制（民主/威权/混合）
  - 多议题民意追踪
  - 政治资本系统
  - 精英/军方/商界支持度
  - 任期限制影响
  - 政治生存检查
  - 媒体事件影响

## 集成建议

### 在 `diplomacy_integration.py` 中集成

```python
from alliance_system import AllianceSystem
from sanction_network import SanctionNetwork
from third_party_mediation import ThirdPartyMediation
from nuclear_deterrence import NuclearDeterrence
from domestic_politics import DomesticPolitics

class DiplomacyIntegration:
    def __init__(self, ...):
        # ... 现有代码 ...
        self.alliance_system = AllianceSystem()
        self.sanction_network = SanctionNetwork()
        self.mediation = ThirdPartyMediation()
        self.nuclear = NuclearDeterrence()
        self.domestic = DomesticPolitics()
```

### 在 `enhanced_simulation.py` 中集成

```python
# 在每轮处理中调用
self.alliance_system.update_alliances(trust_levels, round_num)
self.sanction_network.update_sanctions(economies, round_num)
self.domestic.advance_round()
```

## 文件清单

| 文件 | 大小 | 说明 |
|------|------|------|
| `alliance_system.py` | ~12KB | 联盟机制 |
| `sanction_network.py` | ~9KB | 制裁网络 |
| `third_party_mediation.py` | ~9KB | 第三方调解 |
| `nuclear_deterrence.py` | ~9KB | 核威慑 |
| `domestic_politics.py` | ~11KB | 国内政治 |
| **总计** | **~50KB** | **5个新模块** |

## 下一步

1. 在 `diplomacy_integration.py` 中集成新模块
2. 更新 `simulation_manager.py` 调用新功能
3. 测试完整模拟流程
4. 提交到 GitHub

---
*扩展完成时间: 2026-04-28*
*总代码量: ~1,500 行*
