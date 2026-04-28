"""
种子文件解析器
解析用户提供的地缘政治种子文件，提取详细的Agent定义
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AgentDefinition:
    """Agent定义"""
    id: str
    name: str
    entity_type: str  # Country, Organization, Person, Faction
    parent_entity: Optional[str]  # 所属国家/组织
    role: str  # 角色描述
    stance: str  # 立场: supportive, opposing, neutral
    activity_level: float  # 活跃度 0-1
    influence: float  # 影响力 0-5
    description: str  # 详细描述
    key_attributes: Dict[str, Any]  # 关键属性


class SeedFileParser:
    """种子文件解析器"""
    
    def __init__(self, seed_text: str):
        self.seed_text = seed_text
        self.agents: List[AgentDefinition] = []
    
    def parse(self) -> List[AgentDefinition]:
        """解析种子文件，提取所有Agent定义"""
        self.agents = []
        
        # 1. 提取伊朗阵营 (4个Agent)
        self._extract_iran_faction()
        
        # 2. 提取代理力量 (4个Agent)
        self._extract_proxy_forces()
        
        # 3. 提取以色列 (1个Agent)
        self._extract_israel()
        
        # 4. 提取域外大国 (5个Agent)
        self._extract_external_powers()
        
        # 5. 提取美国阵营 (6个Agent)
        self._extract_us_faction()
        
        return self.agents
    
    def _extract_iran_faction(self):
        """提取伊朗阵营"""
        iran_agents = [
            {
                "id": "iran_supreme_leader",
                "name": "哈梅内伊",
                "role": "精神最高领袖",
                "stance": "opposing",
                "activity": 0.4,
                "influence": 4.5,
                "description": "反美、宗教领导、意识形态优先、谨慎决策"
            },
            {
                "id": "iran_president",
                "name": "伊朗总统",
                "role": "总统",
                "stance": "neutral",
                "activity": 0.5,
                "influence": 3.5,
                "description": "务实派、推进谈判、寻求解除制裁"
            },
            {
                "id": "iran_foreign_minister",
                "name": "伊朗外交部长",
                "role": "外交部长",
                "stance": "neutral",
                "activity": 0.6,
                "influence": 3.0,
                "description": "专业外交官、穿梭外交、与欧盟中国保持沟通"
            },
            {
                "id": "iran_revolutionary_guard",
                "name": "伊朗革命卫队",
                "role": "革命卫队",
                "stance": "opposing",
                "activity": 0.5,
                "influence": 4.0,
                "description": "强硬路线、控制霍尔木兹海峡、威胁封锁"
            }
        ]
        
        for agent_data in iran_agents:
            self.agents.append(AgentDefinition(
                id=agent_data["id"],
                name=agent_data["name"],
                entity_type="Person",  # 修正：从 Faction 改为 Person
                parent_entity="伊朗",
                role=agent_data["role"],
                stance=agent_data["stance"],
                activity_level=agent_data["activity"],
                influence=agent_data["influence"],
                description=agent_data["description"],
                key_attributes={"faction": "伊朗阵营", "military_strength": 4}
            ))
    
    def _extract_proxy_forces(self):
        """提取代理力量"""
        proxy_agents = [
            {
                "id": "hezbollah",
                "name": "真主党",
                "role": "黎巴嫩什叶派武装",
                "stance": "opposing",
                "activity": 0.6,
                "influence": 3.5,
                "description": "反以反美、黎巴嫩政治力量、持续火箭弹袭击"
            },
            {
                "id": "houthi",
                "name": "胡塞武装",
                "role": "也门武装组织",
                "stance": "opposing",
                "activity": 0.5,
                "influence": 3.0,
                "description": "反沙特反美、封锁红海航运"
            },
            {
                "id": "hamas",
                "name": "哈马斯",
                "role": "加沙控制者",
                "stance": "opposing",
                "activity": 0.4,
                "influence": 2.5,
                "description": "反以色列、加沙控制、激进路线"
            },
            {
                "id": "plo",
                "name": "巴解组织",
                "role": "约旦河西岸控制者",
                "stance": "neutral",
                "activity": 0.3,
                "influence": 2.0,
                "description": "温和派、和谈路线、与哈马斯竞争"
            }
        ]
        
        for agent_data in proxy_agents:
            self.agents.append(AgentDefinition(
                id=agent_data["id"],
                name=agent_data["name"],
                entity_type="Organization",  # 修正：代理力量是组织
                parent_entity=None,
                role=agent_data["role"],
                stance=agent_data["stance"],
                activity_level=agent_data["activity"],
                influence=agent_data["influence"],
                description=agent_data["description"],
                key_attributes={"faction": "代理力量", "military_strength": 3}
            ))
    
    def _extract_israel(self):
        """提取以色列"""
        self.agents.append(AgentDefinition(
            id="israel",
            name="以色列",
            entity_type="Country",
            parent_entity=None,
            role="国家",
            stance="supportive",
            activity_level=0.5,
            influence=4.0,
            description="强硬安全立场、打击恐怖主义、威胁扩大地面行动",
            key_attributes={"military_strength": 5, "us_alliance": True}
        ))
    
    def _extract_external_powers(self):
        """提取域外大国"""
        external_agents = [
            {
                "id": "china",
                "name": "中国",
                "stance": "neutral",
                "activity": 0.5,
                "influence": 4.5,
                "description": "表面劝和促谈，实际暗中支持伊朗、对抗美国印太战略"
            },
            {
                "id": "russia",
                "name": "俄罗斯",
                "stance": "supportive",
                "activity": 0.6,
                "influence": 4.0,
                "description": "公开支持伊朗、提供武器、在叙利亚有军事基地"
            },
            {
                "id": "eu",
                "name": "欧盟",
                "stance": "neutral",
                "activity": 0.4,
                "influence": 3.5,
                "description": "表面劝和、担忧油价、人道主义立场"
            },
            {
                "id": "india",
                "name": "印度",
                "stance": "neutral",
                "activity": 0.3,
                "influence": 3.0,
                "description": "QUAD同盟、不想选边、从伊朗进口能源"
            },
            {
                "id": "pakistan",
                "name": "巴基斯坦",
                "stance": "neutral",
                "activity": 0.3,
                "influence": 2.5,
                "description": "伊斯兰国家、美国盟友、可能支持决议但不会出兵"
            }
        ]
        
        for agent_data in external_agents:
            self.agents.append(AgentDefinition(
                id=agent_data["id"],
                name=agent_data["name"],
                entity_type="Country",
                parent_entity=None,
                role="域外大国",
                stance=agent_data["stance"],
                activity_level=agent_data["activity"],
                influence=agent_data["influence"],
                description=agent_data["description"],
                key_attributes={"great_power": True}
            ))
    
    def _extract_us_faction(self):
        """提取美国阵营"""
        us_agents = [
            {
                "id": "trump",
                "name": "特朗普",
                "role": "总统",
                "stance": "opposing",
                "activity": 0.8,
                "influence": 4.5,
                "description": "极限施压、TACO风格、交易外交、不想真开战"
            },
            {
                "id": "vance",
                "name": "万斯",
                "role": "副总统",
                "stance": "neutral",
                "activity": 0.3,
                "influence": 2.5,
                "description": "孤立主义、美国优先、不愿海外军事介入"
            },
            {
                "id": "rubio",
                "name": "卢比奥",
                "role": "国务卿",
                "stance": "opposing",
                "activity": 0.5,
                "influence": 3.0,
                "description": "对伊朗强硬派、支持最大压力制裁"
            },
            {
                "id": "hegseth",
                "name": "海格塞斯",
                "role": "国防部长",
                "stance": "opposing",
                "activity": 0.4,
                "influence": 3.0,
                "description": "支持军事选项、加强中东军事部署"
            },
            {
                "id": "carlson",
                "name": "塔克·卡尔森",
                "role": "媒体评论员",
                "stance": "neutral",
                "activity": 0.6,
                "influence": 2.5,
                "description": "反建制派、质疑对外援助、呼吁减少干预"
            },
            {
                "id": "newsom",
                "name": "纽森",
                "role": "加州州长",
                "stance": "opposing",
                "activity": 0.3,
                "influence": 2.0,
                "description": "民主党温和派、批评特朗普中东政策"
            }
        ]
        
        for agent_data in us_agents:
            self.agents.append(AgentDefinition(
                id=agent_data["id"],
                name=agent_data["name"],
                entity_type="Person",
                parent_entity="美国",
                role=agent_data["role"],
                stance=agent_data["stance"],
                activity_level=agent_data["activity"],
                influence=agent_data["influence"],
                description=agent_data["description"],
                key_attributes={"faction": "美国阵营", "us_government": True}
            ))
    
    def to_simulation_config(self) -> Dict[str, Any]:
        """转换为模拟配置格式"""
        agent_configs = []
        
        for i, agent in enumerate(self.agents):
            config = {
                "agent_id": i,
                "entity_uuid": f"seed_{agent.id}",
                "entity_name": agent.name,
                "entity_type": agent.entity_type,
                "activity_level": agent.activity_level,
                "posts_per_hour": max(1, int(agent.activity_level * 5)),
                "comments_per_hour": max(2, int(agent.activity_level * 8)),
                "active_hours": self._get_active_hours(agent),
                "response_delay_min": max(5, int(60 / agent.activity_level)),
                "response_delay_max": max(30, int(120 / agent.activity_level)),
                "sentiment_bias": self._get_sentiment_bias(agent.stance),
                "stance": agent.stance,
                "influence_weight": agent.influence,
                "description": agent.description,
                "parent_entity": agent.parent_entity,
                "role": agent.role,
                "key_attributes": agent.key_attributes
            }
            agent_configs.append(config)
        
        return {
            "agent_count": len(agent_configs),
            "agents": agent_configs,
            "factions": self._group_by_faction()
        }
    
    def _get_active_hours(self, agent: AgentDefinition) -> List[int]:
        """根据Agent类型确定活跃时间"""
        if agent.entity_type == "Person" and agent.parent_entity == "美国":
            # 美国官员按美国时间活跃
            return [9, 10, 11, 12, 13, 14, 15, 16, 20, 21, 22]
        elif agent.parent_entity == "伊朗":
            # 伊朗官员按伊朗时间活跃
            return [6, 7, 8, 9, 10, 11, 12, 13, 18, 19, 20]
        else:
            # 其他国家/组织按标准工作时间
            return [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    
    def _get_sentiment_bias(self, stance: str) -> float:
        """根据立场确定情感倾向"""
        if stance == "opposing":
            return -0.3
        elif stance == "supportive":
            return 0.3
        else:
            return 0.0
    
    def _group_by_faction(self) -> Dict[str, List[str]]:
        """按阵营分组"""
        factions = {}
        for agent in self.agents:
            if agent.parent_entity:
                faction = agent.parent_entity
            else:
                faction = "独立力量"
            
            if faction not in factions:
                factions[faction] = []
            factions[faction].append(agent.name)
        
        return factions
    
    def save_to_json(self, filepath: str):
        """保存解析结果到JSON"""
        data = {
            "agents": [asdict(agent) for agent in self.agents],
            "simulation_config": self.to_simulation_config()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[SeedParser] 已保存 {len(self.agents)} 个Agent定义到 {filepath}")


# 便捷函数
def parse_seed_file(seed_text: str) -> List[AgentDefinition]:
    """解析种子文件"""
    parser = SeedFileParser(seed_text)
    return parser.parse()


def create_simulation_config_from_seed(seed_text: str) -> Dict[str, Any]:
    """从种子文件创建模拟配置"""
    parser = SeedFileParser(seed_text)
    parser.parse()
    return parser.to_simulation_config()


if __name__ == "__main__":
    # 测试
    test_seed = """
    # 伊朗阵营
    - 精神最高领袖: 反美、宗教领导
    - 伊朗总统: 务实派、推进谈判
    """
    
    parser = SeedFileParser(test_seed)
    agents = parser.parse()
    
    print(f"解析到 {len(agents)} 个Agent")
    for agent in agents:
        print(f"  {agent.name} ({agent.entity_type}): {agent.description}")
