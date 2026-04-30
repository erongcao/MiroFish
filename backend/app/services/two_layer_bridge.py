"""
Two-Layer Integration Bridge - 双层集成桥接器
将三层地缘政治模拟器与OASIS社交媒体模拟器结合

核心修复 (v2):
- 新增 OASIS Agent ID → 地缘政治国家 ID 的映射
- 社交媒体舆论现在能正确影响国际压力、国内派系和策略选择
"""

import os
import sys
import csv
from typing import Dict, List, Any, Optional

# 导入CountryState以便类型检查
try:
    from app.services.three_layer_simulator import CountryState
except ImportError:
    # 回退定义
    class CountryState:
        def __init__(self, id, name):
            self.id = id
            self.name = name
            self.international_pressure = 0
            self.public_support = 0.5


# 地缘政治国家ID与国家名称的映射（用于从CSV的entity_name推断country_id）
COUNTRY_NAME_TO_ID = {
    "美国": "usa", "美国": "usa", "United States": "usa",
    "伊朗": "iran", "伊朗": "iran",
    "以色列": "israel", "以色列": "israel",
    "俄罗斯": "russia", "俄国": "russia", "Russia": "russia",
    "中国": "china", "中国": "china", "China": "china",
    "欧盟": "eu", "欧洲": "eu", "EU": "eu",
    "沙特": "saudi", "沙特阿拉伯": "saudi",
    "朝鲜": "dprk", "北韩": "dprk",
    "韩国": "rok", "南韩": "rok",
    "日本": "japan",
    "英国": "uk", "英国": "uk",
    "法国": "france",
    "德国": "germany",
    "印度": "india",
    "巴基斯坦": "pakistan",
    "土耳其": "turkey",
    "澳大利亚": "australia",
    "巴西": "brazil",
    "墨西哥": "mexico",
}

# CSV中常见的force/faction类型关键词 → 国家ID
FORCE_KEYWORD_TO_COUNTRY = {
    "美国": "usa", "美": "usa", "US": "usa", "America": "usa",
    "伊朗": "iran", "伊": "iran",
    "以色列": "israel", "以": "israel",
    "俄罗斯": "russia", "俄": "russia", "Russia": "russia",
    "中国": "china", "中": "china", "China": "china",
    "欧盟": "eu", "欧": "eu", "EU": "eu", "Europe": "eu",
    "沙特": "saudi", "沙": "saudi",
    "朝鲜": "dprk", "北韩": "dprk",
    "韩国": "rok", "南韩": "rok", "Korea": "rok",
    "日本": "japan", "日": "japan",
    "英国": "uk", "英": "uk",
    "法国": "france", "法": "france",
    "德国": "germany", "德": "germany",
    "印度": "india", "印": "india",
    "巴基斯坦": "pakistan", "巴": "pakistan",
}


class TwoLayerBridge:
    """
    双层架构桥接器
    
    上层: ThreeLayerSimulator (地缘政治)
    下层: OASIS (社交媒体)
    
    桥接机制:
    1. 上层事件 -> 下层context
    2. 下层舆论 -> 上层反馈（修复：正确的Agent→Country映射）
    """
    
    def __init__(self, simulation_dir: str, config: Dict[str, Any],
                 agent_country_mapping: Optional[Dict[str, str]] = None):
        self.simulation_dir = simulation_dir
        self.config = config
        self.enabled = True
        
        # Agent ID → Country ID 映射（OASIS层 → 地缘政治层）
        # 格式: { "0": "usa", "1": "iran", ... } 或 { "twitter_0": "usa", ... }
        self.agent_to_country: Dict[str, str] = agent_country_mapping or {}
        
        # 如果没有传入映射，尝试从profiles CSV自动加载
        if not self.agent_to_country:
            self._try_load_mapping_from_profiles()
        
        # 尝试导入三层模拟器（增强版）
        try:
            from app.services.enhanced_three_layer import EnhancedThreeLayerSimulator
            self.geo_simulator = EnhancedThreeLayerSimulator(config)
            print("[TwoLayerBridge] 增强版三层地缘政治模拟器已加载")
        except Exception as e:
            print(f"[TwoLayerBridge] 增强版模拟器加载失败: {e}")
            # 回退到原版
            try:
                from app.services.three_layer_simulator import ThreeLayerSimulator
                self.geo_simulator = ThreeLayerSimulator(config)
                print("[TwoLayerBridge] 原版三层地缘政治模拟器已加载")
            except Exception as e2:
                print(f"[TwoLayerBridge] 三层模拟器加载失败: {e2}")
                self.geo_simulator = None
        
        # 尝试导入增强Profile生成器
        try:
            from app.services.enhanced_profile_generator import EnhancedProfileGenerator
            self.profile_generator = EnhancedProfileGenerator(simulation_dir, config)
            print("[TwoLayerBridge] 增强Profile生成器已加载")
        except Exception as e:
            print(f"[TwoLayerBridge] Profile生成器加载失败: {e}")
            self.profile_generator = None
    
    def get_current_context(self, agent_id: str, agent_name: str) -> Dict[str, Any]:
        """
        获取当前上下文（供OASIS Agent使用）
        
        返回:
        - current_events: 当前活跃事件
        - global_tension: 全局紧张度
        - war_status: 战争状态
        - diplomatic_situation: 外交局势
        """
        if not self.geo_simulator:
            return {}
        
        context = {
            "global_tension": self.geo_simulator.global_tension,
            "round": self.geo_simulator.round,
            "current_events": [],
            "war_status": {},
            "agent_state": None
        }
        
        # 添加最近外交事件
        for event in self.geo_simulator.diplomatic_events[-3:]:
            context["current_events"].append({
                "type": "diplomatic",
                "name": event.name,
                "description": event.description
            })
        
        # 添加最近军事事件
        for event in self.geo_simulator.military_events[-3:]:
            context["current_events"].append({
                "type": "military",
                "name": event.name,
                "description": event.description
            })
        
        # 添加最近战争事件
        for event in self.geo_simulator.war_events[-3:]:
            context["current_events"].append({
                "type": "war",
                "name": event.name,
                "description": event.description
            })
        
        # 添加该Agent的当前状态
        if agent_id in self.geo_simulator.countries:
            state = self.geo_simulator.countries[agent_id]
            context["agent_state"] = {
                "military_posture": state.military_posture.value,
                "war_intensity": state.war_intensity.value,
                "casualties": state.casualties,
                "public_support": state.public_support
            }
            context["war_status"] = {
                "intensity": state.war_intensity.value,
                "territory_held": state.territory_held
            }
        
        return context
    
    def build_context_prompt(self, agent_id: str, agent_name: str) -> str:
        """
        构建上下文提示词（供Agent生成内容时使用）
        """
        context = self.get_current_context(agent_id, agent_name)
        
        if not context or not context.get("global_tension"):
            return ""
        
        prompt_parts = []
        
        # 全局紧张度
        tension = context["global_tension"]
        prompt_parts.append(f"【全局局势】紧张度: {tension:.0f}/100")
        
        if tension > 80:
            prompt_parts.append("⚠️ 高度紧张，战争一触即发")
        elif tension > 60:
            prompt_parts.append("🔶 中度紧张，对抗加剧")
        elif tension > 40:
            prompt_parts.append("🔷 相对平静，但存在分歧")
        else:
            prompt_parts.append("🟢 基本和平，对话为主")
        
        # 当前事件
        events = context.get("current_events", [])
        if events:
            prompt_parts.append("\n【近期动态】")
            for event in events[-3:]:
                emoji = {"diplomatic": "📊", "military": "🎖️", "war": "💥"}.get(event["type"], "•")
                prompt_parts.append(f"{emoji} {event['name']}: {event['description']}")
        
        # Agent特定状态
        agent_state = context.get("agent_state", {})
        if agent_state:
            war_intensity = agent_state.get("war_intensity", "none")
            if war_intensity != "none":
                prompt_parts.append(f"\n⚔️ 你的国家正在卷入{war_intensity}级别的冲突")
                prompt_parts.append(f"   伤亡: {agent_state.get('casualties', 0)}")
                prompt_parts.append(f"   国内支持率: {agent_state.get('public_support', 0)*100:.0f}%")
        
        # 行为指导
        prompt_parts.append("\n【发言指导】")
        if tension > 80:
            prompt_parts.append("局势危急，你的发言应该反映战争的紧迫性。")
        elif tension > 60:
            prompt_parts.append("局势紧张，对抗加剧。你的发言应该反映当前的对立状态。")
        elif tension > 40:
            prompt_parts.append("存在分歧，但仍有对话空间。你的发言应该体现谈判意愿。")
        else:
            prompt_parts.append("基本和平，可以讨论合作与发展。")
        
        return "\n".join(prompt_parts)
    
    def simulate_round(self, media_posts: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        执行地缘政治层模拟轮次
        
        Args:
            media_posts: 可选的社交媒体帖子 {country_id: [posts]}
                           如果为None，则使用本轮通过 process_social_media_round 收集的帖子
        """
        if not self.geo_simulator:
            return {}
        
        # 如果传入了 media_posts，直接使用；否则传 None 让 geo_simulator 自己处理
        return self.geo_simulator.simulate_round(media_posts=media_posts)
    
    def on_social_media_action(self, agent_id: str, agent_name: str, 
                               action_type: str, content: str) -> Dict[str, Any]:
        """
        处理社交媒体动作对上层的影响（完整版）
        
        1. 分析内容 → 国际压力变化
        2. 更新国内派系
        3. 触发UN决议
        4. 影响策略选择
        """
        if not self.geo_simulator:
            return {}
        
        # 使用国际压力系统分析内容
        if hasattr(self.geo_simulator, 'pressure_system'):
            pressure_system = self.geo_simulator.pressure_system
            analysis = pressure_system.analyze_media_content(content)
        else:
            # 回退到简单分析
            positive_words = ["和平", "对话", "合作", "谈判", "停火"]
            negative_words = ["战争", "攻击", "威胁", "制裁", "敌对"]
            content_lower = content.lower()
            positive_count = sum(1 for w in positive_words if w in content_lower)
            negative_count = sum(1 for w in negative_words if w in content_lower)
            analysis = {
                'hardline_signal': min(1.0, negative_count * 0.2),
                'peace_signal': min(1.0, positive_count * 0.2),
                'pressure_change': (negative_count * 5) - (positive_count * 3)
            }
        
        # 更新国际压力
        if agent_id in self.geo_simulator.countries:
            country = self.geo_simulator.countries[agent_id]
            
            # 更新压力值
            if hasattr(self.geo_simulator, 'pressure_system'):
                self.geo_simulator.pressure_system.update_country_pressure(
                    agent_id, [content]
                )
                country.international_pressure = self.geo_simulator.pressure_system.global_pressure_map.get(agent_id, 0)
            else:
                country.international_pressure += analysis['pressure_change']
                country.international_pressure = max(0, min(100, country.international_pressure))
            
            # 更新国内支持率
            public_support_change = analysis['peace_signal'] * 0.02 - analysis['hardline_signal'] * 0.01
            country.public_support = max(0, min(1, country.public_support + public_support_change))
            
            # 更新国内派系（如果有DomesticPoliticsSystem）
            if hasattr(self.geo_simulator, 'domestic_system') and country.factions:
                self.geo_simulator.domestic_system.update_factions(
                    country=country,
                    war_intensity=country.war_intensity,
                    casualties=country.casualties,
                    economic_strength=country.economic_strength,
                    international_pressure=country.international_pressure
                )
        
        return {
            "hardline_signal": analysis.get('hardline_signal', 0),
            "peace_signal": analysis.get('peace_signal', 0),
            "pressure_change": analysis.get('pressure_change', 0),
            "international_pressure": self.geo_simulator.countries.get(agent_id, CountryState("", "")).international_pressure if agent_id in self.geo_simulator.countries else 0
        }
    
    def _resolve_country_id(self, agent_id: str, agent_name: str = "") -> Optional[str]:
        """
        将OASIS Agent ID（或名称）解析为地缘政治层的Country ID。
        优先级：
        1. 显式映射表 agent_to_country
        2. 从 agent_name 中匹配国家关键词
        3. 回退到 None（无法解析）
        """
        # 1. 查映射表
        if agent_id in self.agent_to_country:
            return self.agent_to_country[agent_id]
        
        # 2. 尝试从 agent_name 推断
        name_to_check = agent_name.lower() if agent_name else ""
        for keyword, country_id in FORCE_KEYWORD_TO_COUNTRY.items():
            if keyword in name_to_check:
                return country_id
        
        # 3. 检查 agent_id 本身是否就是国家名
        agent_lower = agent_id.lower()
        for keyword, country_id in FORCE_KEYWORD_TO_COUNTRY.items():
            if keyword in agent_lower:
                return country_id
        
        return None

    def _try_load_mapping_from_profiles(self):
        """尝试从 profiles CSV 加载 Agent → Country 映射"""
        for platform in ["twitter", "reddit"]:
            csv_path = os.path.join(self.simulation_dir, f"{platform}_profiles.csv")
            if not os.path.exists(csv_path):
                continue
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        user_id = str(row.get("user_id", "")).strip()
                        entity_name = row.get("entity_name", "").strip()
                        if not user_id or not entity_name:
                            continue
                        
                        # 从 entity_name 推断 country_id
                        country_id = self._resolve_country_id(user_id, entity_name)
                        if country_id:
                            self.agent_to_country[user_id] = country_id
                        elif entity_name:
                            # 尝试直接匹配
                            en_lower = entity_name.lower()
                            if en_lower in COUNTRY_NAME_TO_ID:
                                self.agent_to_country[user_id] = COUNTRY_NAME_TO_ID[en_lower]
                
                if self.agent_to_country:
                    print(f"[TwoLayerBridge] 从 {platform}_profiles.csv 加载了 {len(self.agent_to_country)} 个映射")
                    break
            except Exception as e:
                print(f"[TwoLayerBridge] 加载 profiles CSV 失败: {e}")

    def process_social_media_round(self, actions: List[Dict]) -> Dict[str, Any]:
        """
        处理一轮社交媒体动作（批量处理）
        
        Args:
            actions: 社交媒体动作列表
                [{agent_id, agent_name, action_type, action_args: {content}}]
        
        Returns:
            round_impact: 本轮影响摘要
        """
        if not self.geo_simulator:
            return {}
        
        # 按国家收集帖子（关键修复：映射 agent_id → country_id）
        media_posts: Dict[str, List[str]] = {}  # country_id -> [posts]
        
        for action in actions:
            agent_id = str(action.get("agent_id", ""))
            agent_name = action.get("agent_name", "")
            content = action.get("action_args", {}).get("content", "")
            
            if not content:
                continue
            
            # 解析为 country_id
            country_id = self._resolve_country_id(agent_id, agent_name)
            
            if country_id:
                if country_id not in media_posts:
                    media_posts[country_id] = []
                media_posts[country_id].append(content)
                
                # 逐个处理舆论反馈（使用映射后的 country_id）
                self.on_social_media_action(
                    agent_id=country_id,  # 使用 country_id，不是 agent_id
                    agent_name=agent_name,
                    action_type=action.get("action_type", ""),
                    content=content
                )
            else:
                # 无法解析时，尝试直接用 agent_id（向后兼容）
                self.on_social_media_action(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    action_type=action.get("action_type", ""),
                    content=content
                )
        
        # 生成UN决议（基于累积压力）
        un_resolutions = []
        if hasattr(self.geo_simulator, 'pressure_system') and self.geo_simulator.global_tension > 60:
            high_pressure_countries = [
                cid for cid, c in self.geo_simulator.countries.items()
                if c.international_pressure > 40
            ]
            
            if high_pressure_countries and hasattr(self.geo_simulator, 'un_resolutions'):
                resolution = self.geo_simulator.pressure_system.generate_un_resolution(
                    high_pressure_countries, self.geo_simulator.global_tension
                )
                if resolution:
                    self.geo_simulator.un_resolutions.append(resolution)
                    un_resolutions.append({
                        "type": resolution.type.value,
                        "target": resolution.target_countries,
                        "passed": resolution.passed,
                        "description": resolution.description
                    })
                    
                    # 应用UN决议效果
                    for target_id in resolution.target_countries:
                        if target_id in self.geo_simulator.countries:
                            country = self.geo_simulator.countries[target_id]
                            if resolution.type.value == "sanction":
                                country.economic_strength *= 0.9
                                country.un_sanctions += 1
                            elif resolution.type.value == "ceasefire":
                                if country.war_intensity.value != "none":
                                    self.geo_simulator.global_tension -= 10
        
        return {
            "media_posts_count": sum(len(posts) for posts in media_posts.values()),
            "countries_involved": list(media_posts.keys()),
            "un_resolutions": un_resolutions,
            "global_tension": self.geo_simulator.global_tension
        }
    
    def get_enriched_context(self, agent_id: str, agent_name: str) -> Dict[str, Any]:
        """
        获取增强上下文（包含舆论反馈影响）
        支持 OASIS Agent ID 自动映射到地缘政治国家
        """
        # 解析 country_id（支持 OASIS agent ID → 地缘政治国家映射）
        country_id = self._resolve_country_id(agent_id, agent_name) or agent_id
        
        base_context = self.get_current_context(agent_id, agent_name)
        
        if not base_context:
            return {}
        
        # 添加舆论反馈信息（使用 country_id 查找）
        if country_id in self.geo_simulator.countries:
            country = self.geo_simulator.countries[country_id]
            base_context["international_pressure"] = country.international_pressure
            base_context["dominant_faction"] = country.dominant_faction.value if hasattr(country, 'dominant_faction') else "moderates"
            base_context["government_stability"] = country.government_stability if hasattr(country, 'government_stability') else 0.8
            base_context["un_sanctions"] = country.un_sanctions if hasattr(country, 'un_sanctions') else 0
            
            # 添加派系信息
            if hasattr(country, 'factions') and country.factions:
                base_context["factions"] = {
                    faction.value: {
                        "strength": data.strength,
                        "public_support": data.public_support
                    }
                    for faction, data in country.factions.items()
                }
            # 标注原始 OASIS agent_id
            base_context["_oasis_agent_id"] = agent_id
        
        return base_context
    
    def build_enriched_prompt(self, agent_id: str, agent_name: str) -> str:
        """
        构建增强提示词（包含舆论反馈）
        """
        context = self.get_enriched_context(agent_id, agent_name)
        
        if not context:
            return ""
        
        # 基础提示词
        base_prompt = self.build_context_prompt(agent_id, agent_name)
        
        # 添加舆论反馈
        feedback_parts = []
        
        # 国际压力
        pressure = context.get("international_pressure", 0)
        if pressure > 50:
            feedback_parts.append(f"\n🌍 国际压力: {pressure:.0f}/100 (高强度)")
            feedback_parts.append("   你面临国际社会的强烈压力，可能需要调整策略。")
        elif pressure > 30:
            feedback_parts.append(f"\n🌍 国际压力: {pressure:.0f}/100 (中等)")
        
        # 派系信息
        factions = context.get("factions", {})
        if factions:
            feedback_parts.append("\n🏛️ 国内派系:")
            for faction_name, data in factions.items():
                support = data.get("public_support", 0) * 100
                feedback_parts.append(f"   - {faction_name}: 支持率{support:.0f}%")
        
        # UN制裁
        sanctions = context.get("un_sanctions", 0)
        if sanctions > 0:
            feedback_parts.append(f"\n📋 UN制裁: 已受到{sanctions}轮制裁")
            feedback_parts.append("   经济受损，需考虑妥协或寻求支持。")
        
        # 政府稳定性
        stability = context.get("government_stability", 1.0)
        if stability < 0.5:
            feedback_parts.append(f"\n⚠️ 政府稳定性: {stability:.0%} (不稳定)")
            feedback_parts.append("   国内政治动荡，需谨慎决策。")
        
        if feedback_parts:
            return base_prompt + "\n\n【舆论反馈】" + "\n".join(feedback_parts)
        
        return base_prompt
