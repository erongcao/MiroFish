"""
OASIS模拟管理器
管理Twitter和Reddit双平台并行模拟
使用预设脚本 + LLM智能生成配置参数
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger
from .neo4j_adapter import get_neo4j_adapter
from .zep_entity_reader import ZepEntityReader, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .seed_parser import SeedFileParser, create_simulation_config_from_seed
from ..utils.locale import t

from .graph_rag import GraphRAGEnhancer, enhance_agent_prompt
from .enhanced_profile_generator import EnhancedProfileGenerator
from .two_layer_bridge import TwoLayerBridge

logger = get_logger('mirofish.simulation')


class SimulationStatus(str, Enum):
    """模拟状态"""
    CREATED = "created"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"      # 模拟被手动停止
    COMPLETED = "completed"  # 模拟自然完成
    FAILED = "failed"


class PlatformType(str, Enum):
    """平台类型"""
    TWITTER = "twitter"
    REDDIT = "reddit"


@dataclass
class SimulationState:
    """模拟状态"""
    simulation_id: str
    project_id: str
    graph_id: str
    
    # 平台启用状态
    enable_twitter: bool = True
    enable_reddit: bool = True
    
    # 状态
    status: SimulationStatus = SimulationStatus.CREATED
    
    # 准备阶段数据
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = field(default_factory=list)
    
    # 配置生成信息
    config_generated: bool = False
    config_reasoning: str = ""
    
    # 运行时数据
    current_round: int = 0
    twitter_status: str = "not_started"
    reddit_status: str = "not_started"
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 错误信息
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """完整状态字典（内部使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "config_reasoning": self.config_reasoning,
            "current_round": self.current_round,
            "twitter_status": self.twitter_status,
            "reddit_status": self.reddit_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """简化状态字典（API返回使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "error": self.error,
        }


class SimulationManager:
    """
    模拟管理器
    
    核心功能：
    1. 从Zep图谱读取实体并过滤
    2. 生成OASIS Agent Profile
    3. 使用LLM智能生成模拟配置参数
    4. 准备预设脚本所需的所有文件
    """
    
    # 模拟数据存储目录
    SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__), 
        '../../uploads/simulations'
    )
    
    def __init__(self):
        # 确保目录存在
        os.makedirs(self.SIMULATION_DATA_DIR, exist_ok=True)
        
        # 内存中的模拟状态缓存
        self._simulations: Dict[str, SimulationState] = {}
    
    def _get_simulation_dir(self, simulation_id: str) -> str:
        """获取模拟数据目录"""
        sim_dir = os.path.join(self.SIMULATION_DATA_DIR, simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        return sim_dir
    
    def _save_simulation_state(self, state: SimulationState):
        """保存模拟状态到文件"""
        sim_dir = self._get_simulation_dir(state.simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        state.updated_at = datetime.now().isoformat()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        
        self._simulations[state.simulation_id] = state
    
    def _load_simulation_state(self, simulation_id: str) -> Optional[SimulationState]:
        """从文件加载模拟状态"""
        if simulation_id in self._simulations:
            return self._simulations[simulation_id]
        
        sim_dir = self._get_simulation_dir(simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        if not os.path.exists(state_file):
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=data.get("project_id", ""),
            graph_id=data.get("graph_id", ""),
            enable_twitter=data.get("enable_twitter", True),
            enable_reddit=data.get("enable_reddit", True),
            status=SimulationStatus(data.get("status", "created")),
            entities_count=data.get("entities_count", 0),
            profiles_count=data.get("profiles_count", 0),
            entity_types=data.get("entity_types", []),
            config_generated=data.get("config_generated", False),
            config_reasoning=data.get("config_reasoning", ""),
            current_round=data.get("current_round", 0),
            twitter_status=data.get("twitter_status", "not_started"),
            reddit_status=data.get("reddit_status", "not_started"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            error=data.get("error"),
        )
        
        self._simulations[simulation_id] = state
        return state
    
    def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
    ) -> SimulationState:
        """
        创建新的模拟
        
        Args:
            project_id: 项目ID
            graph_id: Zep图谱ID
            enable_twitter: 是否启用Twitter模拟
            enable_reddit: 是否启用Reddit模拟
            
        Returns:
            SimulationState
        """
        import uuid
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=enable_twitter,
            enable_reddit=enable_reddit,
            status=SimulationStatus.CREATED,
        )
        
        self._save_simulation_state(state)
        logger.info(f"创建模拟: {simulation_id}, project={project_id}, graph={graph_id}")
        
        return state
    
    def prepare_simulation(
        self,
        simulation_id: str,
        simulation_requirement: str,
        document_text: str,
        defined_entity_types: Optional[List[str]] = None,
        use_llm_for_profiles: bool = True,
        progress_callback: Optional[callable] = None,
        parallel_profile_count: int = 3
    ) -> SimulationState:
        """
        准备模拟环境（全程自动化）
        
        步骤：
        1. 从Zep图谱读取并过滤实体
        2. 为每个实体生成OASIS Agent Profile（可选LLM增强，支持并行）
        3. 使用LLM智能生成模拟配置参数（时间、活跃度、发言频率等）
        4. 保存配置文件和Profile文件
        5. 复制预设脚本到模拟目录
        
        Args:
            simulation_id: 模拟ID
            simulation_requirement: 模拟需求描述（用于LLM生成配置）
            document_text: 原始文档内容（用于LLM理解背景）
            defined_entity_types: 预定义的实体类型（可选）
            use_llm_for_profiles: 是否使用LLM生成详细人设
            progress_callback: 进度回调函数 (stage, progress, message)
            parallel_profile_count: 并行生成人设的数量，默认3
            
        Returns:
            SimulationState
        """
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        try:
            state.status = SimulationStatus.PREPARING
            self._save_simulation_state(state)
            
            sim_dir = self._get_simulation_dir(simulation_id)
            
            # ========== 阶段1: 读取并过滤实体 ==========
            if progress_callback:
                progress_callback("reading", 0, t('progress.connectingZepGraph'))
            
            # 检查是否使用 Neo4j
            neo4j_adapter = get_neo4j_adapter()
            if neo4j_adapter.is_connected():
                # Neo4j 模式
                if progress_callback:
                    progress_callback("reading", 30, "正在从 Neo4j 读取实体...")
                
                neo4j_result = neo4j_adapter.get_entities(defined_entity_types)
                
                # 转换为 FilteredEntities 格式
                from .zep_entity_reader import EntityNode
                entities = []
                for e in neo4j_result["entities"]:
                    entities.append(EntityNode(
                        uuid=e["uuid"],
                        name=e["name"],
                        labels=e["labels"],
                        summary=e["summary"],
                        attributes=e["attributes"],
                        related_edges=e.get("related_edges", []),
                        related_nodes=e.get("related_nodes", [])
                    ))
                
                filtered = FilteredEntities(
                    entities=entities,
                    entity_types=neo4j_result["entity_types"],
                    total_count=neo4j_result["total_count"],
                    filtered_count=neo4j_result["filtered_count"]
                )
                
                if progress_callback:
                    progress_callback("reading", 50, f"Neo4j 实体读取完成: {filtered.filtered_count} 个")
            else:
                # Zep 模式
                reader = ZepEntityReader()
                
                if progress_callback:
                    progress_callback("reading", 30, t('progress.readingNodeData'))
                
                filtered = reader.filter_defined_entities(
                    graph_id=state.graph_id,
                    defined_entity_types=defined_entity_types,
                    enrich_with_edges=True
                )
            
            state.entities_count = filtered.filtered_count
            state.entity_types = list(filtered.entity_types)
            
            if progress_callback:
                progress_callback(
                    "reading", 100,
                    t('progress.readingComplete', count=filtered.filtered_count),
                    current=filtered.filtered_count,
                    total=filtered.filtered_count
                )
            
            if filtered.filtered_count == 0:
                state.status = SimulationStatus.FAILED
                state.error = "没有找到符合条件的实体，请检查图谱是否正确构建"
                self._save_simulation_state(state)
                return state
            
            # ========== 阶段2: 生成Agent Profile ==========
            total_entities = len(filtered.entities)
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 0,
                    t('progress.startGenerating'),
                    current=0,
                    total=total_entities
                )
            
            # 传入graph_id以启用Zep检索功能，获取更丰富的上下文
            generator = OasisProfileGenerator(graph_id=state.graph_id)
            
            def profile_progress(current, total, msg):
                if progress_callback:
                    progress_callback(
                        "generating_profiles", 
                        int(current / total * 100), 
                        msg,
                        current=current,
                        total=total,
                        item_name=msg
                    )
            
            # 设置实时保存的文件路径（优先使用 Reddit JSON 格式）
            realtime_output_path = None
            realtime_platform = "reddit"
            if state.enable_reddit:
                realtime_output_path = os.path.join(sim_dir, "reddit_profiles.json")
                realtime_platform = "reddit"
            elif state.enable_twitter:
                realtime_output_path = os.path.join(sim_dir, "twitter_profiles.csv")
                realtime_platform = "twitter"
            
            profiles = generator.generate_profiles_from_entities(
                entities=filtered.entities,
                use_llm=use_llm_for_profiles,
                progress_callback=profile_progress,
                graph_id=state.graph_id,  # 传入graph_id用于Zep检索
                parallel_count=parallel_profile_count,  # 并行生成数量
                realtime_output_path=realtime_output_path,  # 实时保存路径
                output_platform=realtime_platform  # 输出格式
            )
            
            state.profiles_count = len(profiles)
            
            # 保存Profile文件（注意：Twitter使用CSV格式，Reddit使用JSON格式）
            # Reddit 已经在生成过程中实时保存了，这里再保存一次确保完整性
            if progress_callback:
                progress_callback(
                    "generating_profiles", 95,
                    t('progress.savingProfiles'),
                    current=total_entities,
                    total=total_entities
                )
            
            if state.enable_reddit:
                generator.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "reddit_profiles.json"),
                    platform="reddit"
                )
            
            if state.enable_twitter:
                # Twitter使用CSV格式！这是OASIS的要求
                generator.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "twitter_profiles.csv"),
                    platform="twitter"
                )
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 100,
                    t('progress.profilesComplete', count=len(profiles)),
                    current=len(profiles),
                    total=len(profiles)
                )
            
            # ========== 阶段3: LLM智能生成模拟配置 ==========
            if progress_callback:
                progress_callback(
                    "generating_config", 0,
                    t('progress.analyzingRequirements'),
                    current=0,
                    total=3
                )
            
            config_generator = SimulationConfigGenerator()
            
            if progress_callback:
                progress_callback(
                    "generating_config", 30,
                    t('progress.callingLLMConfig'),
                    current=1,
                    total=3
                )
            
            sim_params = config_generator.generate_config(
                simulation_id=simulation_id,
                project_id=state.project_id,
                graph_id=state.graph_id,
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                entities=filtered.entities,
                enable_twitter=state.enable_twitter,
                enable_reddit=state.enable_reddit
            )
            
            if progress_callback:
                progress_callback(
                    "generating_config", 70,
                    t('progress.savingConfigFiles'),
                    current=2,
                    total=3
                )
            
            # 保存配置文件
            config_path = os.path.join(sim_dir, "simulation_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(sim_params.to_json())
            
            state.config_generated = True
            state.config_reasoning = sim_params.generation_reasoning
            
            if progress_callback:
                progress_callback(
                    "generating_config", 100,
                    t('progress.configComplete'),
                    current=3,
                    total=3
                )
            
            # 注意：运行脚本保留在 backend/scripts/ 目录，不再复制到模拟目录
            # 启动模拟时，simulation_runner 会从 scripts/ 目录运行脚本
            
            # 更新状态
            state.status = SimulationStatus.READY
            self._save_simulation_state(state)
            
            logger.info(f"模拟准备完成: {simulation_id}, "
                       f"entities={state.entities_count}, profiles={state.profiles_count}")
            
            return state
            
        except Exception as e:
            logger.error(f"模拟准备失败: {simulation_id}, error={str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def prepare_simulation_from_seed(
        self,
        simulation_id: str,
        seed_text: str,
        simulation_requirement: str = "",
        progress_callback: Optional[callable] = None,
    ) -> SimulationState:
        """
        从种子文件准备模拟环境
        
        步骤：
        1. 解析种子文件提取Agent定义
        2. 生成模拟配置
        3. 保存配置文件
        """
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        try:
            state.status = SimulationStatus.PREPARING
            self._save_simulation_state(state)
            
            sim_dir = self._get_simulation_dir(simulation_id)
            
            # ========== 阶段1: 解析种子文件 ==========
            if progress_callback:
                progress_callback("parsing_seed", 0, "正在解析种子文件...")
            
            parser = SeedFileParser(seed_text)
            agents = parser.parse()
            
            if progress_callback:
                progress_callback("parsing_seed", 50, f"解析完成: {len(agents)} 个Agent")
            
            # ========== 阶段2: 生成模拟配置 ==========
            if progress_callback:
                progress_callback("generating_config", 0, "正在生成模拟配置...")
            
            config = parser.to_simulation_config()
            
            # 添加模拟元数据
            full_config = {
                "simulation_id": simulation_id,
                "project_id": state.project_id,
                "graph_id": "seed_based_graph",
                "simulation_requirement": simulation_requirement or "地缘政治模拟",
                "agent_configs": config["agents"],
                "event_config": {
                    "initial_posts": [],
                    "scheduled_events": [],
                    "hot_topics": [
                        "HormuzCrisis",
                        "IsraelLebanon", 
                        "OilPrice",
                        "USIranTension",
                        "ProxyWarfare",
                        "DiplomaticChannels"
                    ],
                    "narrative_direction": "中东地缘政治危机模拟，聚焦霍尔木兹海峡冲突、代理力量博弈和大国角力"
                },
                "time_config": {
                    "total_simulation_hours": 168,
                    "minutes_per_round": 60,
                    "agents_per_hour_min": 8,
                    "agents_per_hour_max": 15,
                    "peak_hours": [19, 20, 21, 22],
                    "peak_activity_multiplier": 1.5,
                    "off_peak_hours": [0, 1, 2, 3, 4, 5],
                    "off_peak_activity_multiplier": 0.05,
                    "morning_hours": [6, 7, 8],
                    "morning_activity_multiplier": 0.4,
                    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
                    "work_activity_multiplier": 0.7
                },
                "twitter_config": {
                    "platform": "twitter",
                    "recency_weight": 0.4,
                    "popularity_weight": 0.3,
                    "relevance_weight": 0.3,
                    "viral_threshold": 10,
                    "echo_chamber_strength": 0.5
                },
                "reddit_config": {
                    "platform": "reddit",
                    "recency_weight": 0.3,
                    "popularity_weight": 0.4,
                    "relevance_weight": 0.3,
                    "viral_threshold": 15,
                    "echo_chamber_strength": 0.6
                },
                "llm_model": os.environ.get("LLM_MODEL_NAME", "qwen-plus"),
                "llm_base_url": os.environ.get("LLM_BASE_URL", ""),
                "generated_at": datetime.now().isoformat(),
                "generation_reasoning": f"基于种子文件解析生成: {len(agents)}个Agent, 包含{len(config['factions'])}个阵营"
            }
            
            # 保存配置
            config_path = os.path.join(sim_dir, "simulation_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, ensure_ascii=False, indent=2)
            
            if progress_callback:
                progress_callback("generating_config", 100, "配置生成完成")
            
            # 生成Profile文件
            if progress_callback:
                progress_callback("generating_profiles", 0, "正在生成Agent Profile...")
            
            self._generate_profiles_from_config(full_config, sim_dir)
            
            if progress_callback:
                progress_callback("generating_profiles", 100, "Profile生成完成")
            
            # 更新状态
            state.entities_count = len(agents)
            state.profiles_count = len(agents)
            state.entity_types = list(set(a.entity_type for a in agents))
            state.config_generated = True
            state.config_reasoning = full_config["generation_reasoning"]
            state.status = SimulationStatus.READY
            self._save_simulation_state(state)
            
            logger.info(f"模拟准备完成: {simulation_id}, agents={len(agents)}")
            return state
            
        except Exception as e:
            logger.error(f"模拟准备失败: {simulation_id}, error={str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def _generate_profiles_from_config(self, config: Dict[str, Any], sim_dir: str):
        """从配置生成Profile文件"""
        agent_configs = config.get("agent_configs", [])
        
        # 初始化 GraphRAG 和增强Profile生成器
        graph_rag = GraphRAGEnhancer()
        profile_generator = EnhancedProfileGenerator(sim_dir, config)
        
        # 初始化双层桥接器（地缘政治 + 社交媒体）
        two_layer_bridge = TwoLayerBridge(sim_dir, config)
        
        print(f"[GraphRAG] 初始化状态: {graph_rag.enabled}")
        print(f"[EnhancedProfile] Profile增强已启用")
        print(f"[TwoLayerBridge] 双层架构已启用: {two_layer_bridge.enabled}")
        
        # 运行初始地缘政治模拟轮次（设置初始状态）
        if two_layer_bridge.geo_simulator:
            two_layer_bridge.geo_simulator.global_tension = 85.0  # 高初始紧张度
            # 添加初始军事事件
            from .three_layer_simulator import MilitaryEvent
            two_layer_bridge.geo_simulator.military_events.append(MilitaryEvent(
                name='美军海湾增兵',
                actors=['usa', 'iran'],
                event_type='DEPLOYMENT',
                description='美国向波斯湾增派航母战斗群',
                tension_increase=15
            ))
            two_layer_bridge.geo_simulator.global_tension = min(100, 100)
        
        # 生成 Reddit Profile (JSON格式) - OASIS要求特定格式
        reddit_profiles = []
        for agent in agent_configs:
            # 获取 GraphRAG 增强的上下文
            agent_context = None
            if graph_rag.enabled:
                try:
                    agent_context = graph_rag.get_agent_context(
                        str(agent["agent_id"]), 
                        agent["entity_name"]
                    )
                except Exception as e:
                    print(f"[GraphRAG] 获取上下文失败 {agent['entity_name']}: {e}")
            
            # 构建增强的 user_profile
            base_description = agent.get("description", "")
            
            # 添加关系上下文
            if agent_context and agent_context.relationships:
                base_description += "\n\n关系网络:\n"
                # 过滤掉 BELONGS_TO 关系
                filtered_rels = [r for r in agent_context.relationships 
                                if r.get("type") != "BELONGS_TO"]
                for rel in filtered_rels[:3]:
                    trust = rel.get("trust", 0) or 0
                    trust_desc = "友好" if trust > 0 else "敌对" if trust < 0 else "中立"
                    base_description += f"- 与{rel['target']}({rel['type']}): {trust_desc}\n"
            
            # 添加阵营上下文
            if agent_context and agent_context.faction_info:
                faction = agent_context.faction_info
                base_description += f"\n阵营: {faction.get('name', '未知')}\n"
                base_description += f"立场: {faction.get('stance', '中立')}\n"
            
            # 从 agent_configs 获取 key_attributes
            key_attrs = agent.get("key_attributes", {})
            faction_from_attrs = key_attrs.get("faction", "")
            
            # 获取地缘政治上下文（双层桥接器）
            geo_context = ""
            if two_layer_bridge.geo_simulator:
                geo_context = two_layer_bridge.build_context_prompt(
                    str(agent["agent_id"]),
                    agent["entity_name"]
                )
            
            # 构建增强 persona（包含 GraphRAG 关系 + 阵营信息 + 地缘政治上下文）
            enhanced_persona = profile_generator.build_enhanced_persona(
                agent_id=str(agent["agent_id"]),
                agent_name=agent["entity_name"],
                base_description=base_description,
                faction=faction_from_attrs,
                stance=agent.get("stance", "neutral")
            )
            
            # 添加地缘政治上下文
            if geo_context:
                enhanced_persona += "\n\n" + geo_context
            
            profile = {
                "id": agent["agent_id"],
                "username": f"u_{agent['entity_name'].lower().replace(' ', '_')}",
                "bio": agent.get("description", ""),
                "persona": enhanced_persona[:800],  # 限制长度
                "mbti": key_attrs.get("mbti", "INTJ"),
                "gender": key_attrs.get("gender", "other"),
                "age": key_attrs.get("age", 45),
                "country": agent.get("parent_entity", "Global"),
                "name": agent["entity_name"],
                "type": agent["entity_type"],
                "description": agent.get("description", ""),
                "activity_level": agent["activity_level"],
                "influence": agent["influence_weight"],
                "stance": agent["stance"],
                "role": agent.get("role", ""),
                "parent_entity": agent.get("parent_entity", None),
                "key_attributes": key_attrs,
                "graph_enhanced": graph_rag.enabled and agent_context is not None,
                "graph_relationships": len(agent_context.relationships) if agent_context else 0,
                "geo_context": geo_context[:200] if geo_context else ""
            }
            reddit_profiles.append(profile)
        
        # 保存 Reddit Profile
        reddit_path = os.path.join(sim_dir, "reddit_profiles.json")
        with open(reddit_path, 'w', encoding='utf-8') as f:
            json.dump(reddit_profiles, f, ensure_ascii=False, indent=2)
        
        # 生成 Twitter Profile (CSV格式) - OASIS要求特定格式
        import csv
        twitter_path = os.path.join(sim_dir, "twitter_profiles.csv")
        with open(twitter_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # OASIS要求的列
            writer.writerow([
                "user_id", "name", "username", "description",
                "created_at", "location", "url",
                "followers_count", "friends_count", "statuses_count",
                "verified", "profile_image_url",
                "user_char"  # OASIS必需列
            ])
            for agent in agent_configs:
                writer.writerow([
                    agent["agent_id"],
                    agent["entity_name"],
                    f"@{agent['entity_name'].lower().replace(' ', '_')}",
                    agent.get("description", ""),
                    "2024-01-01",
                    "Global",
                    "",
                    int(agent["influence_weight"] * 1000),  # followers
                    int(agent["activity_level"] * 100),      # friends
                    int(agent["activity_level"] * 500),       # statuses
                    "True" if agent["influence_weight"] > 3 else "False",
                    "",
                    agent.get("description", "")  # user_char - OASIS必需
                ])
        
        logger.info(f"已生成 {len(agent_configs)} 个Agent的Profile文件")
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """获取模拟状态"""
        return self._load_simulation_state(simulation_id)
    
    def list_simulations(self, project_id: Optional[str] = None) -> List[SimulationState]:
        """列出所有模拟"""
        simulations = []
        
        if os.path.exists(self.SIMULATION_DATA_DIR):
            for sim_id in os.listdir(self.SIMULATION_DATA_DIR):
                # 跳过隐藏文件（如 .DS_Store）和非目录文件
                sim_path = os.path.join(self.SIMULATION_DATA_DIR, sim_id)
                if sim_id.startswith('.') or not os.path.isdir(sim_path):
                    continue
                
                state = self._load_simulation_state(sim_id)
                if state:
                    if project_id is None or state.project_id == project_id:
                        simulations.append(state)
        
        return simulations
    
    def get_profiles(self, simulation_id: str, platform: str = "reddit") -> List[Dict[str, Any]]:
        """获取模拟的Agent Profile"""
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        sim_dir = self._get_simulation_dir(simulation_id)
        profile_path = os.path.join(sim_dir, f"{platform}_profiles.json")
        
        if not os.path.exists(profile_path):
            return []
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_simulation_config(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """获取模拟配置"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_run_instructions(self, simulation_id: str) -> Dict[str, str]:
        """获取运行说明"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        return {
            "simulation_dir": sim_dir,
            "scripts_dir": scripts_dir,
            "config_file": config_path,
            "commands": {
                "twitter": f"python {scripts_dir}/run_twitter_simulation.py --config {config_path}",
                "reddit": f"python {scripts_dir}/run_reddit_simulation.py --config {config_path}",
                "parallel": f"python {scripts_dir}/run_parallel_simulation.py --config {config_path}",
            },
            "instructions": (
                f"1. 激活conda环境: conda activate MiroFish\n"
                f"2. 运行模拟 (脚本位于 {scripts_dir}):\n"
                f"   - 单独运行Twitter: python {scripts_dir}/run_twitter_simulation.py --config {config_path}\n"
                f"   - 单独运行Reddit: python {scripts_dir}/run_reddit_simulation.py --config {config_path}\n"
                f"   - 并行运行双平台: python {scripts_dir}/run_parallel_simulation.py --config {config_path}"
            )
        }
