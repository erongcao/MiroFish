"""
构建完整的 GraphRAG 图谱
包含：Agent节点、Faction节点、Event节点、关系属性
"""

from app.services.neo4j_adapter import get_neo4j_adapter

def build_complete_graph():
    """构建完整的图谱结构"""
    neo4j = get_neo4j_adapter()
    
    if not neo4j.is_connected():
        print("[GraphBuilder] Neo4j 未连接")
        return False
    
    with neo4j.driver.session() as session:
        # 1. 创建阵营节点 (Faction)
        factions = [
            {"name": "伊朗阵营", "stance": "opposing", "description": "以伊朗为核心的反美阵营，包括伊朗政府、革命卫队、代理力量"},
            {"name": "美国阵营", "stance": "supportive", "description": "以美国为核心的西方阵营，包括美国政府、盟友"},
            {"name": "代理力量", "stance": "opposing", "description": "伊朗支持的地区武装组织"},
            {"name": "独立大国", "stance": "neutral", "description": "在地缘政治中保持相对独立的大国"},
            {"name": "欧盟", "stance": "neutral", "description": "欧洲联盟，表面劝和但担忧油价"}
        ]
        
        for faction in factions:
            session.run("""
                CREATE (f:Faction {
                    name: $name,
                    stance: $stance,
                    description: $description
                })
            """, name=faction["name"], stance=faction["stance"], 
                description=faction["description"])
        
        print("[GraphBuilder] 已创建 5 个阵营节点")
        
        # 2. 创建 Agent 节点 (详细角色)
        agents = [
            # 伊朗阵营
            {"id": "iran_supreme_leader", "name": "哈梅内伊", "type": "Person", 
             "role": "精神最高领袖", "faction": "伊朗阵营",
             "description": "反美、宗教领导、意识形态优先、谨慎决策", "influence": 4.5},
            {"id": "iran_president", "name": "伊朗总统", "type": "Person", 
             "role": "总统", "faction": "伊朗阵营",
             "description": "务实派、推进谈判、寻求解除制裁", "influence": 3.5},
            {"id": "iran_foreign_minister", "name": "伊朗外交部长", "type": "Person", 
             "role": "外交部长", "faction": "伊朗阵营",
             "description": "专业外交官、穿梭外交、与欧盟中国保持沟通", "influence": 3.0},
            {"id": "iran_revolutionary_guard", "name": "伊朗革命卫队", "type": "Organization", 
             "role": "革命卫队", "faction": "伊朗阵营",
             "description": "强硬路线、控制霍尔木兹海峡、威胁封锁", "influence": 4.0},
            
            # 代理力量
            {"id": "hezbollah", "name": "真主党", "type": "Organization", 
             "role": "黎巴嫩什叶派武装", "faction": "代理力量",
             "description": "反以反美、黎巴嫩政治力量、持续火箭弹袭击", "influence": 3.5},
            {"id": "houthi", "name": "胡塞武装", "type": "Organization", 
             "role": "也门武装组织", "faction": "代理力量",
             "description": "反沙特反美、封锁红海航运", "influence": 3.0},
            {"id": "hamas", "name": "哈马斯", "type": "Organization", 
             "role": "加沙控制者", "faction": "代理力量",
             "description": "反以色列、加沙控制、激进路线", "influence": 2.5},
            {"id": "plo", "name": "巴解组织", "type": "Organization", 
             "role": "约旦河西岸控制者", "faction": "代理力量",
             "description": "温和派、和谈路线、与哈马斯竞争", "influence": 2.0},
            
            # 以色列
            {"id": "israel", "name": "以色列", "type": "Country", 
             "role": "国家", "faction": "美国阵营",
             "description": "强硬安全立场、打击恐怖主义、威胁扩大地面行动", "influence": 4.0},
            
            # 独立大国
            {"id": "china", "name": "中国", "type": "Country", 
             "role": "域外大国", "faction": "独立大国",
             "description": "表面劝和促谈，实际暗中支持伊朗、对抗美国印太战略", "influence": 4.5},
            {"id": "russia", "name": "俄罗斯", "type": "Country", 
             "role": "域外大国", "faction": "独立大国",
             "description": "公开支持伊朗、提供武器、在叙利亚有军事基地", "influence": 4.0},
            {"id": "india", "name": "印度", "type": "Country", 
             "role": "域外大国", "faction": "独立大国",
             "description": "QUAD同盟、不想选边、从伊朗进口能源", "influence": 3.0},
            {"id": "pakistan", "name": "巴基斯坦", "type": "Country", 
             "role": "域外大国", "faction": "独立大国",
             "description": "伊斯兰国家、美国盟友、可能支持决议但不会出兵", "influence": 2.5},
            
            # 欧盟
            {"id": "eu", "name": "欧盟", "type": "Organization", 
             "role": "国际组织", "faction": "欧盟",
             "description": "表面劝和、担忧油价、人道主义立场", "influence": 3.5},
            
            # 美国阵营
            {"id": "trump", "name": "特朗普", "type": "Person", 
             "role": "总统", "faction": "美国阵营",
             "description": "极限施压、TACO风格、交易外交、不想真开战", "influence": 4.5},
            {"id": "vance", "name": "万斯", "type": "Person", 
             "role": "副总统", "faction": "美国阵营",
             "description": "孤立主义、美国优先、不愿海外军事介入", "influence": 2.5},
            {"id": "rubio", "name": "卢比奥", "type": "Person", 
             "role": "国务卿", "faction": "美国阵营",
             "description": "对伊朗强硬派、支持最大压力制裁", "influence": 3.0},
            {"id": "hegseth", "name": "海格塞斯", "type": "Person", 
             "role": "国防部长", "faction": "美国阵营",
             "description": "支持军事选项、加强中东军事部署", "influence": 3.0},
            {"id": "carlson", "name": "塔克·卡尔森", "type": "Person", 
             "role": "媒体评论员", "faction": "美国阵营",
             "description": "反建制派、质疑对外援助、呼吁减少干预", "influence": 2.5},
            {"id": "newsom", "name": "纽森", "type": "Person", 
             "role": "加州州长", "faction": "美国阵营",
             "description": "民主党温和派、批评特朗普中东政策", "influence": 2.0}
        ]
        
        for agent in agents:
            session.run("""
                CREATE (a:Agent {
                    id: $id,
                    name: $name,
                    type: $type,
                    role: $role,
                    faction: $faction,
                    description: $description,
                    influence: $influence
                })
            """, id=agent["id"], name=agent["name"], type=agent["type"],
                role=agent["role"], faction=agent["faction"],
                description=agent["description"], influence=agent["influence"])
        
        print(f"[GraphBuilder] 已创建 {len(agents)} 个 Agent 节点")
        
        # 3. 创建 BELONGS_TO 关系
        for agent in agents:
            session.run("""
                MATCH (a:Agent {id: $agent_id})
                MATCH (f:Faction {name: $faction_name})
                CREATE (a)-[:BELONGS_TO]->(f)
            """, agent_id=agent["id"], faction_name=agent["faction"])
        
        print("[GraphBuilder] 已创建 BELONGS_TO 关系")
        
        # 4. 创建关系网络 (带信任度)
        relationships = [
            # 伊朗阵营内部 (高度信任)
            ("iran_supreme_leader", "iran_president", "GUIDES", 0.7, "精神领袖指导总统"),
            ("iran_supreme_leader", "iran_revolutionary_guard", "CONTROLS", 0.9, "直接控制革命卫队"),
            ("iran_president", "iran_foreign_minister", "WORKS_WITH", 0.8, "总统与外长协作"),
            
            # 伊朗与代理力量 (支持关系)
            ("iran_supreme_leader", "hezbollah", "SUPPORTS", 0.8, "支持真主党对抗以色列"),
            ("iran_supreme_leader", "houthi", "SUPPORTS", 0.7, "支持胡塞武装封锁红海"),
            ("iran_supreme_leader", "hamas", "SUPPORTS", 0.6, "支持哈马斯对抗以色列"),
            
            # 代理力量之间 (松散联盟)
            ("hezbollah", "hamas", "ALLIES", 0.5, "共同对抗以色列"),
            ("houthi", "hezbollah", "ALLIES", 0.4, "伊朗支持的盟友"),
            
            # 美国阵营内部 (高度信任)
            ("trump", "vance", "WORKS_WITH", 0.6, "总统与副总统"),
            ("trump", "rubio", "WORKS_WITH", 0.7, "总统与国务卿"),
            ("trump", "hegseth", "WORKS_WITH", 0.7, "总统与国防部长"),
            
            # 美国与以色列 (盟友)
            ("trump", "israel", "ALLIES", 0.9, "美国支持以色列"),
            ("israel", "trump", "ALLIES", 0.9, "以色列依赖美国"),
            
            # 敌对关系 (负信任度)
            ("iran_supreme_leader", "trump", "OPPOSES", -0.9, "伊朗反对美国极限施压"),
            ("trump", "iran_supreme_leader", "OPPOSES", -0.9, "美国反对伊朗核计划"),
            ("israel", "iran_supreme_leader", "OPPOSES", -0.9, "以色列视伊朗为最大威胁"),
            ("israel", "hezbollah", "OPPOSES", -0.9, "以色列与真主党敌对"),
            ("israel", "hamas", "OPPOSES", -0.9, "以色列与哈马斯敌对"),
            
            # 中国关系 (复杂)
            ("china", "iran_supreme_leader", "SUPPORTS", 0.3, "暗中支持伊朗对抗美国"),
            ("china", "trump", "OPPOSES", -0.5, "中美战略竞争"),
            ("china", "russia", "ALLIES", 0.6, "中俄战略协作"),
            
            # 俄罗斯关系
            ("russia", "iran_supreme_leader", "SUPPORTS", 0.5, "俄罗斯支持伊朗"),
            ("russia", "trump", "OPPOSES", -0.7, "俄美敌对"),
            
            # 欧盟关系 (中立偏美)
            ("eu", "iran_supreme_leader", "OPPOSES", -0.2, "欧盟对伊朗制裁"),
            ("eu", "trump", "ALLIES", 0.5, "欧盟与美国同盟"),
            
            # 印度关系 (平衡)
            ("india", "trump", "ALLIES", 0.3, "印度与美国QUAD同盟"),
            ("india", "iran_supreme_leader", "NEUTRAL", 0.0, "印度与伊朗能源合作"),
            
            # 巴基斯坦关系 (复杂)
            ("pakistan", "trump", "ALLIES", 0.2, "巴基斯坦与美国盟友"),
            ("pakistan", "iran_supreme_leader", "NEUTRAL", 0.1, "同为伊斯兰国家"),
            
            # 美国内部矛盾
            ("carlson", "trump", "CRITICIZES", -0.2, "塔克·卡尔森质疑特朗普政策"),
            ("newsom", "trump", "OPPOSES", -0.5, "纽森批评特朗普"),
        ]
        
        for rel in relationships:
            session.run("""
                MATCH (a:Agent {id: $source_id})
                MATCH (b:Agent {id: $target_id})
                CREATE (a)-[:%s {
                    trust_level: $trust,
                    description: $description,
                    created_at: datetime()
                }]->(b)
            """ % rel[2], source_id=rel[0], target_id=rel[1], 
                trust=rel[3], description=rel[4])
        
        print(f"[GraphBuilder] 已创建 {len(relationships)} 个关系")
        
        # 5. 创建事件节点
        events = [
            {"name": "霍尔木兹海峡危机", "description": "伊朗扣押商船，美伊军事对峙", 
             "severity": "high", "affected": ["iran_supreme_leader", "trump", "israel", "eu"]},
            {"name": "以色列-黎巴嫩停火", "description": "停火三周但脆弱，真主党持续袭击", 
             "severity": "medium", "affected": ["israel", "hezbollah", "trump"]},
            {"name": "加沙人道主义危机", "description": "以军空袭造成平民伤亡", 
             "severity": "high", "affected": ["israel", "hamas", "plo", "eu"]},
            {"name": "俄乌能源设施打击", "description": "乌克兰无人机袭击俄炼油厂", 
             "severity": "medium", "affected": ["russia", "trump", "eu"]},
            {"name": "台海军演", "description": "解放军联合利剑-2026B演习", 
             "severity": "medium", "affected": ["china", "trump", "india"]},
            {"name": "朝鲜导弹试射", "description": "新型中程弹道导弹试射", 
             "severity": "medium", "affected": ["trump", "china", "russia"]},
        ]
        
        for event in events:
            session.run("""
                CREATE (e:Event {
                    name: $name,
                    description: $description,
                    severity: $severity,
                    timestamp: datetime()
                })
            """, name=event["name"], description=event["description"],
                severity=event["severity"])
            
            # 创建 INVOLVES 关系
            for agent_id in event["affected"]:
                session.run("""
                    MATCH (e:Event {name: $event_name})
                    MATCH (a:Agent {id: $agent_id})
                    CREATE (e)-[:INVOLVES]->(a)
                """, event_name=event["name"], agent_id=agent_id)
        
        print(f"[GraphBuilder] 已创建 {len(events)} 个事件")
        
        # 6. 验证图谱
        result = session.run("""
            MATCH (n) RETURN labels(n) as labels, count(n) as count
        """)
        
        print("\n[GraphBuilder] 图谱统计:")
        for record in result:
            print(f"  {record['labels']}: {record['count']} 个")
        
        # 关系统计
        rel_result = session.run("""
            MATCH ()-[r]->() RETURN type(r) as type, count(r) as count
        """)
        
        print("\n[GraphBuilder] 关系统计:")
        for record in rel_result:
            print(f"  {record['type']}: {record['count']} 个")
    
    return True


if __name__ == "__main__":
    build_complete_graph()
