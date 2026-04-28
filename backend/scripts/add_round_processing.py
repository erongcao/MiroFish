#!/usr/bin/env python3
"""
添加轮次处理和动作记录到 run_parallel_simulation.py
"""

import ast

def add_round_processing():
    script = "/tmp/mirofish/backend/scripts/run_parallel_simulation.py"
    
    with open(script, 'r') as f:
        lines = f.readlines()
    
    print(f"当前文件: {len(lines)} 行")
    
    # 找到 Twitter 循环中的关键位置
    # 1. 在 "# 无论是否有活跃agent，都记录round开始" 前添加轮次前处理
    twitter_preround_idx = None
    for i, line in enumerate(lines):
        if '# 无论是否有活跃agent，都记录round开始' in line and i > 1200 and i < 1400:
            twitter_preround_idx = i
            break
    
    if twitter_preround_idx:
        twitter_preround = [
            '        # 增强模拟轮次前处理\n',
            '        enhanced_round_context = None\n',
            '        if enhanced_integrator:\n',
            '            try:\n',
            '                all_posts = fetch_all_posts_from_db(db_path, "twitter")\n',
            '                enhanced_round_context = enhanced_integrator.pre_round_processing(\n',
            '                    round_num=round_num + 1,\n',
            '                    agent_configs=agent_configs,\n',
            '                    all_posts=all_posts\n',
            '                )\n',
            '                if enhanced_round_context.active_events:\n',
            '                    for event in enhanced_round_context.active_events:\n',
            '                        log_info(f"【事件】{event.description}")\n',
            '            except Exception as e:\n',
            '                pass\n',
            '\n'
        ]
        lines = lines[:twitter_preround_idx] + twitter_preround + lines[twitter_preround_idx:]
        print(f"✅ 添加 Twitter 轮次前处理 (行 {twitter_preround_idx})")
    
    # 2. 找到 Reddit 循环中的相同位置
    reddit_preround_idx = None
    for i, line in enumerate(lines):
        if '# 无论是否有活跃agent，都记录round开始' in line and i > 1400:
            reddit_preround_idx = i
            break
    
    if reddit_preround_idx:
        reddit_preround = [
            '        # 增强模拟轮次前处理\n',
            '        enhanced_round_context_reddit = None\n',
            '        if enhanced_integrator_reddit:\n',
            '            try:\n',
            '                all_posts = fetch_all_posts_from_db(db_path, "reddit")\n',
            '                enhanced_round_context_reddit = enhanced_integrator_reddit.pre_round_processing(\n',
            '                    round_num=round_num + 1,\n',
            '                    agent_configs=agent_configs_reddit,\n',
            '                    all_posts=all_posts\n',
            '                )\n',
            '                if enhanced_round_context_reddit.active_events:\n',
            '                    for event in enhanced_round_context_reddit.active_events:\n',
            '                        log_info(f"【Reddit事件】{event.description}")\n',
            '            except Exception as e:\n',
            '                pass\n',
            '\n'
        ]
        lines = lines[:reddit_preround_idx] + reddit_preround + lines[reddit_preround_idx:]
        print(f"✅ 添加 Reddit 轮次前处理 (行 {reddit_preround_idx})")
    
    # 3. 添加 Twitter 动作记录（在 "if action_logger:" 的 "log_round_end" 之后）
    # 找到 Twitter 的 log_round_end 后的位置
    twitter_action_idx = None
    for i, line in enumerate(lines):
        if 'log_round_end(round_num + 1, round_action_count)' in line and i > 1200 and i < 1500:
            # 找到下一个空行或 if 语句
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].strip() == '' or 'if (round_num + 1) % 20 == 0' in lines[j]:
                    twitter_action_idx = j
                    break
            break
    
    if twitter_action_idx:
        twitter_action = [
            '\n',
            '        # 增强模拟动作记录\n',
            '        if enhanced_integrator and enhanced_round_context:\n',
            '            try:\n',
            '                for action_data in actual_actions:\n',
            '                    agent_id = str(action_data.get("agent_id", ""))\n',
            '                    action_args = action_data.get("action_args", {})\n',
            '                    inferred_type = classify_action_type(action_args.get("content", ""))\n',
            '                    enhanced_integrator.record_action(\n',
            '                        agent_id=agent_id,\n',
            '                        action_type=inferred_type,\n',
            '                        action_args=action_args,\n',
            '                        round_context=enhanced_round_context\n',
            '                    )\n',
            '            except Exception as e:\n',
            '                pass\n'
        ]
        lines = lines[:twitter_action_idx] + twitter_action + lines[twitter_action_idx:]
        print(f"✅ 添加 Twitter 动作记录 (行 {twitter_action_idx})")
    
    # 4. 添加 Reddit 动作记录
    reddit_action_idx = None
    for i, line in enumerate(lines):
        if 'log_round_end(round_num + 1, round_action_count)' in line and i > 1500:
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].strip() == '' or 'if (round_num + 1) % 20 == 0' in lines[j]:
                    reddit_action_idx = j
                    break
            break
    
    if reddit_action_idx:
        reddit_action = [
            '\n',
            '        # 增强模拟动作记录\n',
            '        if enhanced_integrator_reddit and enhanced_round_context_reddit:\n',
            '            try:\n',
            '                for action_data in actual_actions:\n',
            '                    agent_id = str(action_data.get("agent_id", ""))\n',
            '                    action_args = action_data.get("action_args", {})\n',
            '                    inferred_type = classify_action_type(action_args.get("content", ""))\n',
            '                    enhanced_integrator_reddit.record_action(\n',
            '                        agent_id=agent_id,\n',
            '                        action_type=inferred_type,\n',
            '                        action_args=action_args,\n',
            '                        round_context=enhanced_round_context_reddit\n',
            '                    )\n',
            '            except Exception as e:\n',
            '                pass\n'
        ]
        lines = lines[:reddit_action_idx] + reddit_action + lines[reddit_action_idx:]
        print(f"✅ 添加 Reddit 动作记录 (行 {reddit_action_idx})")
    
    # 5. 添加 Twitter 轮次后处理（在 return result 前）
    twitter_post_idx = None
    for i, line in enumerate(lines):
        if 'return result' in line and i > 1200 and i < 1600:
            # 向前找到空行
            for j in range(i-1, max(i-20, 0), -1):
                if 'log_info(f"模拟循环完成!' in lines[j]:
                    twitter_post_idx = j
                    break
            break
    
    if twitter_post_idx:
        twitter_post = [
            '    # 增强模拟轮次后处理\n',
            '    if enhanced_integrator and enhanced_round_context:\n',
            '        try:\n',
            '            enhanced_integrator.post_round_processing(enhanced_round_context)\n',
            '        except Exception as e:\n',
            '            pass\n',
            '\n'
        ]
        lines = lines[:twitter_post_idx] + twitter_post + lines[twitter_post_idx:]
        print(f"✅ 添加 Twitter 轮次后处理 (行 {twitter_post_idx})")
    
    # 6. 添加 Reddit 轮次后处理
    reddit_post_idx = None
    for i, line in enumerate(lines):
        if 'return result' in line and i > 1600:
            for j in range(i-1, max(i-20, 0), -1):
                if 'log_info(f"模拟循环完成!' in lines[j]:
                    reddit_post_idx = j
                    break
            break
    
    if reddit_post_idx:
        reddit_post = [
            '    # 增强模拟轮次后处理\n',
            '    if enhanced_integrator_reddit and enhanced_round_context_reddit:\n',
            '        try:\n',
            '            enhanced_integrator_reddit.post_round_processing(enhanced_round_context_reddit)\n',
            '        except Exception as e:\n',
            '            pass\n',
            '\n'
        ]
        lines = lines[:reddit_post_idx] + reddit_post + lines[reddit_post_idx:]
        print(f"✅ 添加 Reddit 轮次后处理 (行 {reddit_post_idx})")
    
    # 保存文件
    with open(script, 'w') as f:
        f.writelines(lines)
    
    # 验证语法
    try:
        ast.parse(open(script).read())
        print(f"\n✅ 语法检查通过")
        print(f"最终文件: {len(lines)} 行")
        return True
    except SyntaxError as e:
        print(f"\n❌ 语法错误: {e}")
        return False

if __name__ == "__main__":
    success = add_round_processing()
    exit(0 if success else 1)
