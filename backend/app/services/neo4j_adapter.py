"""
Neo4j Graph Adapter - Neo4j 图谱适配器
替代 Zep API，使用本地 Neo4j 数据库 + LLM 实体提取
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from neo4j import GraphDatabase, basic_auth
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("[Neo4jAdapter] neo4j 驱动未安装...")
    import subprocess
    subprocess.run(["pip", "install", "neo4j"], check=True)
    from neo4j import GraphDatabase, basic_auth
    NEO4J_AVAILABLE = True


class Neo4jGraphAdapter:
    """Neo4j 图谱适配器"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", 
                 password: str = "62483180"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        
        if NEO4J_AVAILABLE:
            try:
                # 尝试 Bolt 连接
                self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
                with self.driver.session() as session:
                    result = session.run("RETURN 1 as num")
                    result.single()
                self.connected = True
                print(f"[Neo4jAdapter] 已连接到 {uri}")
            except Exception as e:
                print(f"[Neo4jAdapter] Bolt 连接失败: {e}")
                print(f"[Neo4jAdapter] 尝试 HTTP 协议...")
                # 如果 Bolt 失败，尝试 HTTP
                try:
                    import requests
                    response = requests.get(
                        "http://localhost:7474/db/data/",
                        auth=(user, password),
                        timeout=5
                    )
                    if response.status_code == 200:
                        self.connected = True
                        print(f"[Neo4jAdapter] HTTP 连接成功")
                    else:
                        print(f"[Neo4jAdapter] HTTP 也失败: {response.status_code}")
                except Exception as http_err:
                    print(f"[Neo4jAdapter] HTTP 连接失败: {http_err}")
        else:
            print("[Neo4jAdapter] neo4j 驱动不可用")
    
    def get_entities(self, defined_entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """获取实体列表（兼容 ZepEntityReader 格式）"""
        if not self.is_connected():
            return {"entities": [], "entity_types": set(), "total_count": 0, "filtered_count": 0}
        
        try:
            with self.driver.session() as session:
                # 获取所有非 Chunk 节点
                result = session.run("""
                    MATCH (n)
                    WHERE NOT n:Chunk
                    RETURN n, labels(n) as labels, elementId(n) as node_id
                """)
                
                entities = []
                entity_types = set()
                
                for record in result:
                    node = record["n"]
                    labels = record["labels"]
                    node_id = record["node_id"]
                    
                    # 获取实体类型（排除 Entity）
                    entity_type = None
                    for label in labels:
                        if label not in ["Entity", "Chunk"]:
                            entity_type = label
                            entity_types.add(label)
                    
                    if not entity_type:
                        entity_type = "Entity"
                        entity_types.add("Entity")
                    
                    # 过滤
                    if defined_entity_types and entity_type not in defined_entity_types:
                        continue
                    
                    # 获取属性
                    props = dict(node)
                    name = props.get("name", props.get("id", f"node_{node_id}"))
                    description = props.get("description", "")
                    
                    entities.append({
                        "uuid": str(node_id),
                        "name": name,
                        "labels": labels,
                        "summary": description,
                        "attributes": props,
                        "related_edges": [],
                        "related_nodes": []
                    })
                
                return {
                    "entities": entities,
                    "entity_types": entity_types,
                    "total_count": len(entities),
                    "filtered_count": len(entities)
                }
        except Exception as e:
            print(f"[Neo4jAdapter] 获取实体失败: {e}")
            return {"entities": [], "entity_types": set(), "total_count": 0, "filtered_count": 0}
    
    def is_connected(self) -> bool:
        return self.connected
    
    def create_node(self, node_id: str, labels: List[str], 
                   properties: Dict[str, Any]) -> bool:
        """创建节点"""
        if not self.connected:
            return False
        
        try:
            label_str = ":".join(labels)
            props = {k: v for k, v in properties.items() if v is not None}
            
            with self.driver.session() as session:
                query = f"""
                MERGE (n:{label_str} {{id: $node_id}})
                SET n += $props
                RETURN n
                """
                session.run(query, node_id=node_id, props=props)
            return True
        except Exception as e:
            print(f"[Neo4jAdapter] 创建节点失败: {e}")
            return False
    
    def create_edge(self, edge_type: str, source_id: str, 
                   target_id: str, properties: Dict[str, Any]) -> bool:
        """创建关系"""
        if not self.connected:
            return False
        
        try:
            props = {k: v for k, v in properties.items() if v is not None}
            
            with self.driver.session() as session:
                query = f"""
                MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                MERGE (a)-[r:{edge_type}]->(b)
                SET r += $props
                RETURN r
                """
                session.run(query, source_id=source_id, 
                          target_id=target_id, props=props)
            return True
        except Exception as e:
            print(f"[Neo4jAdapter] 创建关系失败: {e}")
            return False
    
    def get_graph_info(self) -> Dict[str, Any]:
        """获取图谱信息"""
        if not self.connected:
            return {"error": "未连接"}
        
        try:
            with self.driver.session() as session:
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()["count"]
                
                edge_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                edge_count = edge_result.single()["count"]
                
                label_result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
                labels = label_result.single()["labels"]
                
                return {
                    "node_count": node_count,
                    "edge_count": edge_count,
                    "labels": labels or [],
                    "connected": True
                }
        except Exception as e:
            print(f"[Neo4jAdapter] 获取信息失败: {e}")
            return {"error": str(e)}
    
    def get_graph_data(self) -> Dict[str, Any]:
        """获取完整图谱数据"""
        if not self.connected:
            return {"nodes": [], "edges": []}
        
        try:
            with self.driver.session() as session:
                # 获取所有节点
                node_result = session.run("MATCH (n) RETURN n, labels(n) as labels, elementId(n) as node_id")
                nodes = []
                for record in node_result:
                    node = record["n"]
                    labels = record["labels"]
                    node_id = record["node_id"]
                    nodes.append({
                        "uuid": node_id,
                        "name": node.get("name", "unnamed"),
                        "labels": labels or [],
                        "summary": node.get("description", ""),
                        "attributes": dict(node)
                    })
                
                # 获取所有关系
                edge_result = session.run("MATCH ()-[r]->() RETURN r, elementId(startNode(r)) as source_id, elementId(endNode(r)) as target_id")
                edges = []
                for record in edge_result:
                    edge = record["r"]
                    edges.append({
                        "uuid": str(record["source_id"]) + "_" + str(record["target_id"]),
                        "name": edge.type,
                        "source_node_uuid": str(record["source_id"]),
                        "target_node_uuid": str(record["target_id"]),
                        "fact": edge.get("description", ""),
                        "attributes": dict(edge)
                    })
                
                return {
                    "nodes": nodes,
                    "edges": edges,
                    "node_count": len(nodes),
                    "edge_count": len(edges)
                }
        except Exception as e:
            print(f"[Neo4jAdapter] 获取图谱数据失败: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}
    
    def clear_graph(self) -> bool:
        """清空图谱"""
        if not self.connected:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            return True
        except Exception as e:
            print(f"[Neo4jAdapter] 清空失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.connected = False


# 全局适配器实例
_neo4j_adapter = None

def get_neo4j_adapter() -> Neo4jGraphAdapter:
    """获取 Neo4j 适配器实例"""
    global _neo4j_adapter
    if _neo4j_adapter is None:
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "62483180")
        _neo4j_adapter = Neo4jGraphAdapter(uri, user, password)
    
    return _neo4j_adapter


# LLM 实体提取函数
async def extract_entities_with_llm(text: str, llm_model: str = "qwen-plus") -> Dict[str, Any]:
    """
    使用 LLM 从文本中提取实体和关系
    返回格式:
    {
        "entities": [{"id": "iran", "name": "伊朗", "type": "Country", "description": "..."}],
        "relations": [{"source": "iran", "target": "usa", "type": "OPPOSES", "description": "..."}]
    }
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("[EntityExtractor] 需要安装 openai 库")
        return {"entities": [], "relations": []}
    
    # 获取 LLM 配置
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "")
    
    if not api_key or not base_url:
        print("[EntityExtractor] LLM 配置不完整")
        return {"entities": [], "relations": []}
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        prompt = f"""从以下文本中提取所有实体（国家、组织、人）和它们之间的关系。

文本:
{text[:4000]}

请以 JSON 格式返回:
{{
    "entities": [
        {{"id": "实体ID(如iran, usa, china)", "name": "实体名称", "type": "类型(Country/Organization/Person)", "description": "简要描述"}}
    ],
    "relations": [
        {{"source": "实体ID", "target": "实体ID", "type": "关系类型(如ALLIES/OPPOSES/SUPPORT)", "description": "关系描述"}}
    ]
}}

只返回 JSON，不要其他内容。"""

        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": "你是一个实体关系提取专家。只返回有效的JSON格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 清理和解析 JSON
        import re
        
        # 尝试提取 JSON 块（更精确的模式）
        # 查找第一个 { 和最后一个 }
        first_brace = result_text.find('{')
        last_brace = result_text.rfind('}')
        
        if first_brace >= 0 and last_brace > first_brace:
            json_str = result_text[first_brace:last_brace+1]
            
            # 尝试解析 JSON
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError as e:
                print(f"[EntityExtractor] JSON 解析失败: {e}")
                print(f"[EntityExtractor] 问题位置: line {e.lineno}, col {e.colno}")
                
                # 尝试修复：删除注释、修复尾随逗号等
                # 1. 删除 // 注释
                json_str = re.sub(r'//[^\n]*', '', json_str)
                # 2. 删除 /* */ 注释
                json_str = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', json_str, flags=re.DOTALL)
                # 3. 修复对象中的尾随逗号
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                # 4. 修复缺失的逗号（简单情况）
                json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
                
                try:
                    result = json.loads(json_str)
                    print(f"[EntityExtractor] JSON 修复成功")
                    return result
                except:
                    pass
                
                # 如果还是失败，尝试逐行提取实体和关系
                print(f"[EntityExtractor] 尝试逐行提取...")
                entities = []
                relations = []
                
                # 尝试提取 entities 部分
                entities_match = re.search(r'"entities"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                if entities_match:
                    entities_str = entities_match.group(1)
                    # 提取单个实体对象
                    entity_matches = re.finditer(r'\{[^}]*"id"[^}]*\}', entities_str)
                    for match in entity_matches:
                        try:
                            entity = json.loads(match.group())
                            entities.append(entity)
                        except:
                            pass
                
                # 尝试提取 relations 部分
                relations_match = re.search(r'"relations"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                if relations_match:
                    relations_str = relations_match.group(1)
                    relation_matches = re.finditer(r'\{[^}]*"source"[^}]*\}', relations_str)
                    for match in relation_matches:
                        try:
                            relation = json.loads(match.group())
                            relations.append(relation)
                        except:
                            pass
                
                if entities or relations:
                    print(f"[EntityExtractor] 逐行提取成功: {len(entities)} 实体, {len(relations)} 关系")
                    return {"entities": entities, "relations": relations}
                
                print(f"[EntityExtractor] 无法修复 JSON，返回空结果")
                return {"entities": [], "relations": []}
        else:
            print(f"[EntityExtractor] 无法找到 JSON: {result_text[:200]}")
            return {"entities": [], "relations": []}
            
    except Exception as e:
        print(f"[EntityExtractor] LLM 调用失败: {e}")
        return {"entities": [], "relations": []}


def store_entities_in_neo4j(adapter: Neo4jGraphAdapter, entities: List[Dict], relations: List[Dict]) -> bool:
    """将提取的实体和关系存入 Neo4j"""
    if not adapter.is_connected():
        print("[Neo4jAdapter] Neo4j 未连接")
        return False
    
    try:
        # 存储实体
        for entity in entities:
            adapter.create_node(
                node_id=entity.get("id", ""),
                labels=[entity.get("type", "Entity")],
                properties={
                    "name": entity.get("name", ""),
                    "description": entity.get("description", ""),
                    "type": entity.get("type", "Entity")
                }
            )
        
        # 存储关系
        for relation in relations:
            adapter.create_edge(
                edge_type=relation.get("type", "RELATED"),
                source_id=relation.get("source", ""),
                target_id=relation.get("target", ""),
                properties={
                    "description": relation.get("description", "")
                }
            )
        
        print(f"[Neo4jAdapter] 已存储 {len(entities)} 个实体, {len(relations)} 个关系")
        return True
        
    except Exception as e:
        print(f"[Neo4jAdapter] 存储失败: {e}")
        return False
