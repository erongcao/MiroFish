#!/usr/bin/env python3
"""
安全集成增强模块到 run_parallel_simulation.py
使用行号精确定位，避免字符串匹配错误
"""

import ast

def main():
    script = "/tmp/mirofish/backend/scripts/run_parallel_simulation.py"
    
    with open(script, 'r') as f:
        lines = f.readlines()
    
    print(f"原始文件: {len(lines)} 行")
    
    # 1. 在导入部分后添加增强模块导入（找到 "import argparse" 行）
    import_idx = None
    for i, line in enumerate(lines):
        if 'import argparse' in line:
            import_idx = i
            break
    
    if import_idx is None:
        print("❌ 无法找到导入位置")
        return False
    
    # 在第一个 import 前添加增强模块导入
    enhanced_import = [
        '# 增强模拟模块导入\n',
        'try:\n',
        '    import sys\n',
        '    sys.path.insert(0, os.path.join(os.path.dirname(__file__), \'..\'))\n',
        '    from app.services.enhanced_simulation import (\n',
        '        EnhancedSimulationIntegrator,\n',
        '        ENHANCED_MODE,\n',
        '        classify_action_type\n',
        '    )\n',
        '    print(f"[Enhanced] 增强模拟模块已加载 (ENHANCED_MODE={ENHANCED_MODE})")\n',
        'except ImportError as e:\n',
        '    print(f"[Enhanced] 增强模拟模块导入失败: {e}")\n',
        '    ENHANCED_MODE = False\n',
        '    EnhancedSimulationIntegrator = None\n',
        '    classify_action_type = lambda x: "NEUTRAL"\n',
        '\n',
        '# 辅助函数\n',
        'def fetch_all_posts_from_db(db_path, platform="twitter"):\n',
        '    """从数据库获取所有帖子"""\n',
        '    posts = []\n',
        '    try:\n',
        '        import sqlite3\n',
        '        conn = sqlite3.connect(db_path)\n',
        '        cursor = conn.cursor()\n',
        '        tables = ["posts", "tweets", "reddit_posts"]\n',
        '        for table in tables:\n',
        '            try:\n',
        '                cursor.execute(f"SELECT * FROM {table} LIMIT 1")\n',
        '                cursor.execute(f"SELECT * FROM {table}")\n',
        '                rows = cursor.fetchall()\n',
        '                columns = [description[0] for description in cursor.description]\n',
        '                for row in rows:\n',
        '                    post = dict(zip(columns, row))\n',
        '                    post["platform"] = platform\n',
        '                    posts.append(post)\n',
        '                break\n',
        '            except:\n',
        '                continue\n',
        '        conn.close()\n',
        '    except Exception as e:\n',
        '        print(f"[Enhanced] 获取帖子失败: {e}")\n',
        '    return posts\n',
        '\n'
    ]
    
    # 插入到文件开头（在所有 import 之前）
    lines = enhanced_import + lines
    
    # 重新计算行号（增加了 37 行）
    offset = 37
    
    print(f"添加导入后: {len(lines)} 行")
    
    # 2. 找到 Twitter 模拟函数中的初始化位置
    # 查找 "if action_logger:" 在 run_twitter_simulation 中的位置
    twitter_start = None
    for i, line in enumerate(lines):
        if 'async def run_twitter_simulation(' in line:
            twitter_start = i
            break
    
    if twitter_start is None:
        print("❌ 无法找到 Twitter 模拟函数")
        return False
    
    # 在 Twitter 函数中找到 "if action_logger:" 行
    twitter_logger_idx = None
    for i in range(twitter_start, min(twitter_start + 200, len(lines))):
        if 'if action_logger:' in lines[i] and 'log_simulation_start' in lines[i+1]:
            twitter_logger_idx = i
            break
    
    if twitter_logger_idx is None:
        print("❌ 无法找到 Twitter action_logger 位置")
        return False
    
    # 在 action_logger 前插入增强模块初始化
    twitter_init = [
        '    # 增强模拟模块初始化\n',
        '    enhanced_integrator = None\n',
        '    enhanced_integrator_reddit = None\n',
        '    if ENHANCED_MODE:\n',
        '        try:\n',
        '            import csv\n',
        '            twitter_profiles_path = os.path.join(simulation_dir, "twitter_profiles.csv")\n',
        '            agent_configs = []\n',
        '            if os.path.exists(twitter_profiles_path):\n',
        '                with open(twitter_profiles_path, "r", encoding="utf-8") as f:\n',
        '                    reader = csv.DictReader(f)\n',
        '                    for i, row in enumerate(reader):\n',
        '                        agent_configs.append({\n',
        '                            "agent_id": str(row.get("user_id", i)),\n',
        '                            "name": row.get("name", f"Agent_{i}"),\n',
        '                            "platform": "twitter"\n',
        '                        })\n',
        '            \n',
        '            if agent_configs:\n',
        '                enhanced_config = {\n',
        '                    "initial_tension": 40.0,\n',
        '                    "event_injector": {\n',
        '                        "base_probability": 0.05,\n',
        '                        "min_rounds_between_events": 3\n',
        '                    },\n',
        '                    "cross_agent": {\n',
        '                        "min_comments_per_round": 1,\n',
        '                        "max_posts_in_feed": 10\n',
        '                    }\n',
        '                }\n',
        '                enhanced_integrator = EnhancedSimulationIntegrator(\n',
        '                    simulation_dir,\n',
        '                    enhanced_config\n',
        '                )\n',
        '                enhanced_integrator.initialize(agent_configs)\n',
        '                log_info("增强模拟模块已初始化")\n',
        '        except Exception as e:\n',
        '            log_info(f"增强模拟初始化失败: {e}")\n',
        '            enhanced_integrator = None\n',
        '    \n'
    ]
    
    lines = lines[:twitter_logger_idx] + twitter_init + lines[twitter_logger_idx:]
    offset += len(twitter_init)
    
    print(f"添加 Twitter 初始化后: {len(lines)} 行")
    
    # 3. 找到 Reddit 模拟函数
    reddit_start = None
    for i, line in enumerate(lines):
        if 'async def run_reddit_simulation(' in line:
            reddit_start = i
            break
    
    if reddit_start is None:
        print("❌ 无法找到 Reddit 模拟函数")
        return False
    
    # 找到 Reddit 中的 "if action_logger:" 行
    reddit_logger_idx = None
    for i in range(reddit_start, min(reddit_start + 200, len(lines))):
        if 'if action_logger:' in lines[i] and 'log_simulation_start' in lines[i+1]:
            reddit_logger_idx = i
            break
    
    if reddit_logger_idx is None:
        print("❌ 无法找到 Reddit action_logger 位置")
        return False
    
    # 在 Reddit action_logger 前插入初始化
    reddit_init = [
        '    # 增强模拟模块初始化\n',
        '    enhanced_integrator = None\n',
        '    enhanced_integrator_reddit = None\n',
        '    if ENHANCED_MODE:\n',
        '        try:\n',
        '            import csv\n',
        '            reddit_profiles_path = os.path.join(simulation_dir, "reddit_profiles.csv")\n',
        '            agent_configs_reddit = []\n',
        '            if os.path.exists(reddit_profiles_path):\n',
        '                with open(reddit_profiles_path, "r", encoding="utf-8") as f:\n',
        '                    reader = csv.DictReader(f)\n',
        '                    for i, row in enumerate(reader):\n',
        '                        agent_configs_reddit.append({\n',
        '                            "agent_id": str(row.get("user_id", i)),\n',
        '                            "name": row.get("name", f"Agent_{i}"),\n',
        '                            "platform": "reddit"\n',
        '                        })\n',
        '            \n',
        '            if agent_configs_reddit:\n',
        '                enhanced_config = {\n',
        '                    "initial_tension": 40.0,\n',
        '                    "event_injector": {\n',
        '                        "base_probability": 0.05,\n',
        '                        "min_rounds_between_events": 3\n',
        '                    },\n',
        '                    "cross_agent": {\n',
        '                        "min_comments_per_round": 1,\n',
        '                        "max_posts_in_feed": 10\n',
        '                    }\n',
        '                }\n',
        '                enhanced_integrator_reddit = EnhancedSimulationIntegrator(\n',
        '                    simulation_dir,\n',
        '                    enhanced_config\n',
        '                )\n',
        '                enhanced_integrator_reddit.initialize(agent_configs_reddit)\n',
        '                log_info("增强模拟模块已初始化 (Reddit)")\n',
        '        except Exception as e:\n',
        '            log_info(f"增强模拟初始化失败: {e}")\n',
        '            enhanced_integrator_reddit = None\n',
        '    \n'
    ]
    
    lines = lines[:reddit_logger_idx] + reddit_init + lines[reddit_logger_idx:]
    
    print(f"添加 Reddit 初始化后: {len(lines)} 行")
    
    # 保存文件
    with open(script, 'w') as f:
        f.writelines(lines)
    
    # 验证语法
    try:
        ast.parse(open(script).read())
        print("\n✅ 语法检查通过")
        print(f"最终文件: {len(lines)} 行")
        return True
    except SyntaxError as e:
        print(f"\n❌ 语法错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
