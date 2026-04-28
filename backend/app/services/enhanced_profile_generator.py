"""
Enhanced Profile Generator - 增强型Profile生成器
在 persona 中注入当前事件、关系网络、阵营信息
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List, Any, Optional

class EnhancedProfileGenerator:
    """
    增强型Profile生成器
    在 persona 中注入：
    1. 当前局势/活跃事件
    2. 关系网络（敌友）
    3. 阵营信息和立场
    4. 当前紧张度
    """
    
    def __init__(self, simulation_dir: str, config: Dict[str, Any]):
        self.simulation_dir = simulation_dir
        self.config = config
        self.enabled = True
        
        # 尝试导入 GraphRAG
        try:
            from app.services.graph_rag import GraphRAGEnhancer
            self.graph_rag = GraphRAGEnhancer()
            print(f"[EnhancedProfile] GraphRAG enabled: {self.graph_rag.enabled}")
        except Exception as e:
            print(f"[EnhancedProfile] GraphRAG import failed: {e}")
            self.graph_rag = None
        
        # 尝试导入 WorldState
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            import world_state_engine
            self.world_state = None  # 需要单独初始化
        except:
            self.world_state = None
    
    def load_world_state(self):
        """加载世界状态"""
        import json
        state_file = os.path.join(self.simulation_dir, 'world_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_current_events(self) -> List[Dict]:
        """获取当前活跃事件"""
        events_file = os.path.join(self.simulation_dir, 'events_state.json')
        if os.path.exists(events_file):
            import json
            with open(events_file, 'r') as f:
                data = json.load(f)
                return data.get('current_events', [])
        return []
    
    def build_enhanced_persona(self, agent_id: str, agent_name: str, 
                               base_description: str,
                               faction: str = "",
                               stance: str = "") -> str:
        """
        构建增强的 persona
        
        Args:
            agent_id: Agent ID
            agent_name: Agent 名称
            base_description: 基础描述
            faction: 阵营
            stance: 立场
        
        Returns:
            str: 增强后的 persona
        """
        persona = f"【角色】{agent_name}\n"
        
        # 1. 基础描述
        persona += f"【背景】{base_description}\n"
        
        # 2. 阵营信息
        if faction:
            persona += f"【阵营】{faction}\n"
        if stance:
            stance_map = {
                'opposing': '反对立场（对美国/西方敌对）',
                'supportive': '支持立场（对美国/西方友好）',
                'neutral': '中立立场'
            }
            stance_desc = stance_map.get(stance, stance)
            persona += f"【立场】{stance_desc}\n"
        
        # 3. 关系网络（从 GraphRAG）
        if self.graph_rag and self.graph_rag.enabled:
            try:
                context = self.graph_rag.get_agent_context(agent_id, agent_name)
                if context and context.relationships:
                    # 过滤掉 BELONGS_TO
                    rels = [r for r in context.relationships 
                           if r.get('type') != 'BELONGS_TO']
                    if rels:
                        persona += "\n【重要关系】\n"
                        for rel in rels[:5]:
                            trust = rel.get('trust', 0) or 0
                            if trust < -0.5:
                                rel_desc = "敌对"
                            elif trust > 0.5:
                                rel_desc = "友好/盟友"
                            elif trust > 0:
                                rel_desc = "初步接触"
                            else:
                                rel_desc = "中立"
                            persona += f"- 与{rel['target']}: {rel['type']} ({rel_desc})\n"
            except Exception as e:
                print(f"[EnhancedProfile] GraphRAG query failed: {e}")
        
        # 4. 当前事件
        events = self.get_current_events()
        if events:
            persona += "\n【当前局势】\n"
            for event in events[:3]:
                persona += f"- {event.get('name', '未知事件')}: {event.get('description', '')[:50]}...\n"
        
        # 5. 世界状态紧张度
        world_state = self.load_world_state()
        if world_state:
            tension = world_state.get('global_tension', 50)
            persona += f"\n【地区局势】紧张度: {tension:.0f}/100"
            if tension > 70:
                persona += " (高度紧张，可能爆发冲突)"
            elif tension > 50:
                persona += " (中等紧张，对话与对抗并存)"
            else:
                persona += " (相对平静，对话为主)"
        
        # 6. 行为指导
        persona += "\n\n【行为指导】你应根据上述关系和当前局势发表言论。如果与敌对势力互动，应表达反对/批评；如果与盟友互动，可表达支持/合作。同时，关注当前事件的影响。"
        
        return persona
    
    def enhance_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """增强单个Profile"""
        agent_id = str(profile.get('id', ''))
        agent_name = profile.get('name', '')
        base_desc = profile.get('persona', profile.get('description', ''))
        faction = profile.get('key_attributes', {}).get('faction', '')
        stance = profile.get('stance', '')
        
        # 构建增强 persona
        enhanced_persona = self.build_enhanced_persona(
            agent_id=agent_id,
            agent_name=agent_name,
            base_description=base_desc,
            faction=faction,
            stance=stance
        )
        
        # 更新 profile
        profile['persona'] = enhanced_persona[:2000]  # 限制长度
        profile['user_char'] = enhanced_persona[:1000]  # Twitter 用
        profile['graph_enhanced'] = True
        
        return profile
    
    def enhance_profiles(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """增强所有Profile"""
        return [self.enhance_profile(p) for p in profiles]
