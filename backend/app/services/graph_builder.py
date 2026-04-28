"""
图谱构建服务
使用 Neo4j 本地数据库构建知识图谱
"""

import os
import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from .neo4j_adapter import get_neo4j_adapter, Neo4jGraphAdapter
from ..config import Config
from ..models.task import TaskManager, TaskStatus
from .text_processor import TextProcessor
from ..utils.locale import t, get_locale, set_locale

# Zep 相关导入（仅在需要时导入）
try:
    from zep_cloud.client import Zep
    from zep_cloud import EpisodeData, EntityEdgeSourceTarget
    ZEP_AVAILABLE = True
except ImportError:
    ZEP_AVAILABLE = False
    EpisodeData = None
    EntityEdgeSourceTarget = None


@dataclass
class GraphInfo:
    """图谱信息"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    图谱构建服务
    使用 Neo4j 本地数据库构建知识图谱
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # 注意：不在这里初始化 neo4j_adapter，因为在 Config 类加载前 .env 可能还没被 load_dotenv
        # 而是延迟到第一次使用时初始化
        self._neo4j_adapter = None
        self._use_neo4j = None
        self.api_key = api_key
        
        self.task_manager = TaskManager()
    
    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "MiroFish Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3
    ) -> str:
        """
        异步构建图谱
        
        Args:
            text: 输入文本
            ontology: 本体定义（来自接口1的输出）
            graph_name: 图谱名称
            chunk_size: 文本块大小
            chunk_overlap: 块重叠大小
            batch_size: 每批发送的块数量
            
        Returns:
            任务ID
        """
        # 创建任务
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )
        
        # Capture locale before spawning background thread
        current_locale = get_locale()

        # 在后台线程中执行构建
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size, current_locale)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    @property
    def neo4j_adapter(self):
        """延迟初始化 Neo4j 适配器"""
        if self._neo4j_adapter is None:
            self._neo4j_adapter = get_neo4j_adapter()
        return self._neo4j_adapter
    
    @property
    def use_neo4j(self) -> bool:
        """延迟判断是否使用 Neo4j"""
        if self._use_neo4j is None:
            self._use_neo4j = self.neo4j_adapter.is_connected()
            if not self._use_neo4j:
                print("[GraphBuilder] Neo4j 未连接，尝试使用 Zep...")
                # 回退到 Zep
                self.api_key = self.api_key or Config.ZEP_API_KEY
                if self.api_key:
                    try:
                        from zep_cloud.client import Zep
                        self.client = Zep(api_key=self.api_key)
                        self._use_neo4j = False
                    except Exception as e:
                        print(f"[GraphBuilder] Zep 也失败: {e}")
                        raise ValueError("Neo4j 和 Zep 都不可用")
                else:
                    raise ValueError("Neo4j 未连接且 ZEP_API_KEY 未配置")
        return self._use_neo4j
    
    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int,
        locale: str = 'zh'
    ):
        """图谱构建工作线程 - 使用 Neo4j"""
        set_locale(locale)
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message=t('progress.startBuildingGraph')
            )
            
            if self.use_neo4j:
                # 使用 Neo4j 构建
                self._build_with_neo4j(task_id, text, ontology, graph_name)
            else:
                # 使用 Zep 构建
                self._build_with_zep(task_id, text, ontology, graph_name, 
                                   chunk_size, chunk_overlap, batch_size)
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)
    
    def _build_with_neo4j(self, task_id: str, text: str, 
                         ontology: Dict[str, Any], graph_name: str):
        """使用 Neo4j + LLM 构建图谱"""
        import asyncio
        adapter = self.neo4j_adapter
        
        # 清空旧数据
        adapter.clear_graph()
        self.task_manager.update_task(task_id, progress=5, 
                                      message="已清空旧图谱，准备 LLM 提取...")
        
        self.task_manager.update_task(task_id, progress=10, 
                                      message="正在使用 LLM 提取实体和关系...")
        
        # 获取 LLM 模型名称
        llm_model = os.environ.get("LLM_MODEL_NAME", "qwen-plus")
        
        # 调用 LLM 提取实体（同步版本）
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            extraction_result = loop.run_until_complete(
                extract_entities_with_llm(text[:8000], llm_model)
            )
            loop.close()
        except Exception as e:
            print(f"[GraphBuilder] LLM 提取失败: {e}")
            extraction_result = {"entities": [], "relations": []}
        
        entities = extraction_result.get("entities", [])
        relations = extraction_result.get("relations", [])
        
        self.task_manager.update_task(task_id, progress=30, 
                                      message=f"LLM 提取完成: {len(entities)} 个实体, {len(relations)} 个关系")
        
        # 存储实体到 Neo4j
        from neo4j_adapter import store_entities_in_neo4j
        success = store_entities_in_neo4j(adapter, entities, relations)
        
        if success:
            self.task_manager.update_task(task_id, progress=80, 
                                          message=f"已存入 Neo4j: {len(entities)} 实体, {len(relations)} 关系")
        else:
            self.task_manager.update_task(task_id, progress=80, 
                                          message="存入 Neo4j 失败，但继续")
        
        # 获取图谱信息
        graph_info = adapter.get_graph_info()
        
        self.task_manager.update_task(task_id, progress=90, 
                                      message="正在完成...")
        
        # 完成
        self.task_manager.complete_task(task_id, {
            "graph_id": "neo4j_graph",
            "graph_info": graph_info,
            "entities_extracted": len(entities),
            "relations_extracted": len(relations),
            "method": "neo4j_llm"
        })
    
    def _build_with_zep(self, task_id: str, text: str, ontology: Dict[str, Any],
                       graph_name: str, chunk_size: int, chunk_overlap: int,
                       batch_size: int):
        """使用 Zep 构建图谱（原有逻辑）"""
        # 1. 创建图谱
        graph_id = self.create_graph(graph_name)
        self.task_manager.update_task(task_id, progress=10,
                                      message=t('progress.graphCreated', graphId=graph_id))
        
        # 2. 设置本体
        self.set_ontology(graph_id, ontology)
        self.task_manager.update_task(task_id, progress=15,
                                      message=t('progress.ontologySet'))
        
        # 3. 文本分块
        chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
        total_chunks = len(chunks)
        self.task_manager.update_task(task_id, progress=20,
                                      message=t('progress.textSplit', count=total_chunks))
        
        # 4. 分批发送数据
        episode_uuids = self.add_text_batches(
            graph_id, chunks, batch_size,
            lambda msg, prog: self.task_manager.update_task(
                task_id,
                progress=20 + int(prog * 0.4),
                message=msg
            )
        )
        
        # 5. 等待Zep处理完成
        self.task_manager.update_task(task_id, progress=60,
                                      message=t('progress.waitingZepProcess'))
        
        self._wait_for_episodes(
            episode_uuids,
            lambda msg, prog: self.task_manager.update_task(
                task_id,
                progress=60 + int(prog * 0.3),
                message=msg
            )
        )
        
        # 6. 获取图谱信息
        self.task_manager.update_task(task_id, progress=90,
                                      message=t('progress.fetchingGraphInfo'))
        
        graph_info = self._get_graph_info(graph_id)
        
        # 完成
        self.task_manager.complete_task(task_id, {
            "graph_id": graph_id,
            "graph_info": graph_info.to_dict(),
            "chunks_processed": total_chunks,
        })
    
    def create_graph(self, name: str) -> str:
        """创建图谱"""
        if self.use_neo4j:
            # Neo4j 不需要显式创建图谱，直接返回标识
            return "neo4j_graph"
        else:
            # Zep 方式
            if not hasattr(self, 'client') or self.client is None:
                raise RuntimeError("Zep 客户端未初始化")
            graph_id = f"mirofish_{uuid.uuid4().hex[:16]}"
            self.client.graph.create(
                graph_id=graph_id,
                name=name,
                description="MiroFish Social Simulation Graph"
            )
            return graph_id
    
    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """获取图谱信息"""
        if self.use_neo4j:
            info = self.neo4j_adapter.get_graph_info()
            return GraphInfo(
                graph_id=graph_id,
                node_count=info.get("node_count", 0),
                edge_count=info.get("edge_count", 0),
                entity_types=info.get("labels", [])
            )
        else:
            # Zep 方式
            try:
                from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges
                nodes = fetch_all_nodes(self.client, graph_id)
                edges = fetch_all_edges(self.client, graph_id)
                
                entity_types = set()
                for node in nodes:
                    entity_types.update(node.get("labels", []))
                
                return GraphInfo(
                    graph_id=graph_id,
                    node_count=len(nodes),
                    edge_count=len(edges),
                    entity_types=list(entity_types)
                )
            except Exception as e:
                print(f"[GraphBuilder] 获取 Zep 图谱信息失败: {e}")
                return GraphInfo(graph_id=graph_id, node_count=0, edge_count=0, entity_types=[])
    
    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """设置图谱本体"""
        if self.use_neo4j:
            # Neo4j 不需要显式设置本体，实体和关系在创建时动态定义
            print(f"[GraphBuilder] Neo4j 模式：跳过本体设置")
            return
        
        # Zep 模式下的原有逻辑
        if not ZEP_AVAILABLE:
            raise RuntimeError("Zep 模块不可用")
        
        import warnings
        from typing import Optional
        from pydantic import Field
        from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel
        
        # 抑制 Pydantic v2 关于 Field(default=None) 的警告
        warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')
        
        # Zep 保留名称，不能作为属性名
        RESERVED_NAMES = {'uuid', 'name', 'group_id', 'name_embedding', 'summary', 'created_at'}
        
        def safe_attr_name(attr_name: str) -> str:
            """将保留名称转换为安全名称"""
            if attr_name.lower() in RESERVED_NAMES:
                return f"entity_{attr_name}"
            return attr_name
        
        # 动态创建实体类型
        entity_types = {}
        for entity_def in ontology.get("entity_types", []):
            name = entity_def["name"]
            description = entity_def.get("description", f"A {name} entity.")
            
            # 创建属性字典和类型注解（Pydantic v2 需要）
            attrs = {"__doc__": description}
            annotations = {}
            
            for attr_def in entity_def.get("attributes", []):
                attr_name = safe_attr_name(attr_def["name"])  # 使用安全名称
                attr_desc = attr_def.get("description", attr_name)
                # Zep API 需要 Field 的 description，这是必需的
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[EntityText]  # 类型注解
            
            attrs["__annotations__"] = annotations
            
            # 动态创建类
            entity_class = type(name, (EntityModel,), attrs)
            entity_class.__doc__ = description
            entity_types[name] = entity_class
        
        # 动态创建边类型
        edge_definitions = {}
        for edge_def in ontology.get("edge_types", []):
            name = edge_def["name"]
            description = edge_def.get("description", f"A {name} relationship.")
            
            # 创建属性字典和类型注解
            attrs = {"__doc__": description}
            annotations = {}
            
            for attr_def in edge_def.get("attributes", []):
                attr_name = safe_attr_name(attr_def["name"])  # 使用安全名称
                attr_desc = attr_def.get("description", attr_name)
                # Zep API 需要 Field 的 description，这是必需的
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[str]  # 边属性用str类型
            
            attrs["__annotations__"] = annotations
            
            # 动态创建类
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            edge_class = type(class_name, (EdgeModel,), attrs)
            edge_class.__doc__ = description
            
            # 构建source_targets
            source_targets = []
            for st in edge_def.get("source_targets", []):
                source_targets.append(
                    EntityEdgeSourceTarget(
                        source=st.get("source", "Entity"),
                        target=st.get("target", "Entity")
                    )
                )
            
            if source_targets:
                edge_definitions[name] = (edge_class, source_targets)
        
        # 调用Zep API设置本体
        if entity_types or edge_definitions:
            self.client.graph.set_ontology(
                graph_id=graph_id,
                entity_types=entity_types,
                edge_definitions=edge_definitions
            )
    
    def add_text_batches(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """分批添加文本到图谱，返回所有 episode 的 uuid 列表"""
        # Neo4j 模式：文本直接存储，不需要调用此方法
        # 返回空列表，让调用者知道这是 Neo4j 模式
        if self.use_neo4j:
            # 存储文本到 Neo4j（简化处理）
            adapter = self.neo4j_adapter
            for i, chunk in enumerate(chunks):
                adapter.create_node(
                    node_id=f"chunk_{i}",
                    labels=["Chunk"],
                    properties={
                        "text": chunk[:500],  # 截断存储
                        "index": i,
                        "type": "text_chunk"
                    }
                )
            return []  # Neo4j 不返回 episode uuid
        
        episode_uuids = []
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            if progress_callback:
                progress = (i + len(batch_chunks)) / total_chunks
                progress_callback(
                    t('progress.sendingBatch', current=batch_num, total=total_batches, chunks=len(batch_chunks)),
                    progress
                )
            
            # 构建episode数据
            episodes = [
                EpisodeData(data=chunk, type="text")
                for chunk in batch_chunks
            ]
            
            # 发送到Zep
            try:
                batch_result = self.client.graph.add_batch(
                    graph_id=graph_id,
                    episodes=episodes
                )
                
                # 收集返回的 episode uuid
                if batch_result and isinstance(batch_result, list):
                    for ep in batch_result:
                        ep_uuid = getattr(ep, 'uuid_', None) or getattr(ep, 'uuid', None)
                        if ep_uuid:
                            episode_uuids.append(ep_uuid)
                
                # 避免请求过快
                time.sleep(1)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(t('progress.batchFailed', batch=batch_num, error=str(e)), 0)
                raise
        
        return episode_uuids
    
    def _wait_for_episodes(
        self,
        episode_uuids: List[str],
        progress_callback: Optional[Callable] = None,
        timeout: int = 600
    ):
        """等待所有 episode 处理完成（通过查询每个 episode 的 processed 状态）"""
        if not episode_uuids:
            if progress_callback:
                progress_callback(t('progress.noEpisodesWait'), 1.0)
            return
        
        start_time = time.time()
        pending_episodes = set(episode_uuids)
        completed_count = 0
        total_episodes = len(episode_uuids)
        
        if progress_callback:
            progress_callback(t('progress.waitingEpisodes', count=total_episodes), 0)
        
        while pending_episodes:
            if time.time() - start_time > timeout:
                if progress_callback:
                    progress_callback(
                        t('progress.episodesTimeout', completed=completed_count, total=total_episodes),
                        completed_count / total_episodes
                    )
                break
            
            # 检查每个 episode 的处理状态
            for ep_uuid in list(pending_episodes):
                try:
                    episode = self.client.graph.episode.get(uuid_=ep_uuid)
                    is_processed = getattr(episode, 'processed', False)
                    
                    if is_processed:
                        pending_episodes.remove(ep_uuid)
                        completed_count += 1
                        
                except Exception as e:
                    # 忽略单个查询错误，继续
                    pass
            
            elapsed = int(time.time() - start_time)
            if progress_callback:
                progress_callback(
                    t('progress.zepProcessing', completed=completed_count, total=total_episodes, pending=len(pending_episodes), elapsed=elapsed),
                    completed_count / total_episodes if total_episodes > 0 else 0
                )
            
            if pending_episodes:
                time.sleep(3)  # 每3秒检查一次
        
        if progress_callback:
            progress_callback(t('progress.processingComplete', completed=completed_count, total=total_episodes), 1.0)
    
    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """获取图谱信息"""
        if self.use_neo4j:
            info = self.neo4j_adapter.get_graph_info()
            return GraphInfo(
                graph_id=graph_id,
                node_count=info.get("node_count", 0),
                edge_count=info.get("edge_count", 0),
                entity_types=info.get("labels", [])
            )
        else:
            # Zep 方式
            try:
                from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges
                nodes = fetch_all_nodes(self.client, graph_id)
                edges = fetch_all_edges(self.client, graph_id)
                
                entity_types = set()
                for node in nodes:
                    if node.labels:
                        for label in node.labels:
                            if label not in ["Entity", "Node"]:
                                entity_types.add(label)
                
                return GraphInfo(
                    graph_id=graph_id,
                    node_count=len(nodes),
                    edge_count=len(edges),
                    entity_types=list(entity_types)
                )
            except Exception as e:
                print(f"[GraphBuilder] 获取 Zep 图谱信息失败: {e}")
                return GraphInfo(graph_id=graph_id, node_count=0, edge_count=0, entity_types=[])
    
    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """
        获取完整图谱数据（包含详细信息）
        """
        if self.use_neo4j:
            # Neo4j 模式
            return self._get_neo4j_graph_data(graph_id)
        else:
            # Zep 模式
            return self._get_zep_graph_data(graph_id)
    
    def _get_neo4j_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """获取 Neo4j 图谱数据"""
        adapter = self.neo4j_adapter
        
        try:
            with adapter.driver.session() as session:
                # 获取所有节点
                node_result = session.run("MATCH (n) RETURN n, labels(n) as labels, id(n) as node_id")
                nodes_data = []
                node_map = {}
                
                for record in node_result:
                    node = record["n"]
                    labels = record["labels"]
                    node_id = record["node_id"]
                    
                    node_map[node_id] = node.get("name", "")
                    nodes_data.append({
                        "uuid": str(node_id),
                        "name": node.get("name", ""),
                        "labels": labels or [],
                        "summary": node.get("description", ""),
                        "attributes": dict(node),
                        "created_at": None,
                    })
                
                # 获取所有关系
                edge_result = session.run("MATCH ()-[r]->() RETURN r, id(r) as edge_id, id(startNode(r)) as source_id, id(endNode(r)) as target_id")
                edges_data = []
                
                for record in edge_result:
                    edge = record["r"]
                    edge_id = record["edge_id"]
                    source_id = record["source_id"]
                    target_id = record["target_id"]
                    
                    edges_data.append({
                        "uuid": str(edge_id),
                        "name": edge.type,
                        "fact": edge.get("description", ""),
                        "fact_type": edge.type,
                        "source_node_uuid": str(source_id),
                        "target_node_uuid": str(target_id),
                        "source_node_name": node_map.get(source_id, ""),
                        "target_node_name": node_map.get(target_id, ""),
                        "attributes": dict(edge),
                        "created_at": None,
                        "valid_at": None,
                        "invalid_at": None,
                        "expired_at": None,
                        "episodes": [],
                    })
                
                return {
                    "graph_id": graph_id,
                    "nodes": nodes_data,
                    "edges": edges_data,
                    "node_count": len(nodes_data),
                    "edge_count": len(edges_data),
                }
        except Exception as e:
            print(f"[GraphBuilder] 获取 Neo4j 图谱数据失败: {e}")
            return {
                "graph_id": graph_id,
                "nodes": [],
                "edges": [],
                "node_count": 0,
                "edge_count": 0,
                "error": str(e)
            }
    
    def _get_zep_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """获取 Zep 图谱数据"""
        try:
            from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges
            nodes = fetch_all_nodes(self.client, graph_id)
            edges = fetch_all_edges(self.client, graph_id)

            # 创建节点映射用于获取节点名称
            node_map = {}
            for node in nodes:
                node_map[node.uuid_] = node.name or ""
            
            nodes_data = []
            for node in nodes:
                # 获取创建时间
                created_at = getattr(node, 'created_at', None)
                if created_at:
                    created_at = str(created_at)
                
                nodes_data.append({
                    "uuid": node.uuid_,
                    "name": node.name,
                    "labels": node.labels or [],
                    "summary": node.summary or "",
                    "attributes": node.attributes or {},
                    "created_at": created_at,
                })
            
            edges_data = []
            for edge in edges:
                # 获取时间信息
                created_at = getattr(edge, 'created_at', None)
                valid_at = getattr(edge, 'valid_at', None)
                invalid_at = getattr(edge, 'invalid_at', None)
                expired_at = getattr(edge, 'expired_at', None)
                
                # 获取 episodes
                episodes = getattr(edge, 'episodes', None) or getattr(edge, 'episode_ids', None)
                if episodes and not isinstance(episodes, list):
                    episodes = [str(episodes)]
                elif episodes:
                    episodes = [str(e) for e in episodes]
                
                # 获取 fact_type
                fact_type = getattr(edge, 'fact_type', None) or edge.name or ""
                
                edges_data.append({
                    "uuid": edge.uuid_,
                    "name": edge.name or "",
                    "fact": edge.fact or "",
                    "fact_type": fact_type,
                    "source_node_uuid": edge.source_node_uuid,
                    "target_node_uuid": edge.target_node_uuid,
                    "source_node_name": node_map.get(edge.source_node_uuid, ""),
                    "target_node_name": node_map.get(edge.target_node_uuid, ""),
                    "attributes": edge.attributes or {},
                    "created_at": str(created_at) if created_at else None,
                    "valid_at": str(valid_at) if valid_at else None,
                    "invalid_at": str(invalid_at) if invalid_at else None,
                    "expired_at": str(expired_at) if expired_at else None,
                    "episodes": episodes or [],
                })
            
            return {
                "graph_id": graph_id,
                "nodes": nodes_data,
                "edges": edges_data,
                "node_count": len(nodes_data),
                "edge_count": len(edges_data),
            }
        except Exception as e:
            print(f"[GraphBuilder] 获取 Zep 图谱数据失败: {e}")
            return {
                "graph_id": graph_id,
                "nodes": [],
                "edges": [],
                "node_count": 0,
                "edge_count": 0,
                "error": str(e)
            }
    
    def delete_graph(self, graph_id: str):
        """删除图谱"""
        self.client.graph.delete(graph_id=graph_id)

