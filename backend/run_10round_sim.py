#!/usr/bin/env python3
"""
运行多智能体政治模拟 - 集成Neo4j图数据库
每轮结束后自动将Agent关系和博弈结果持久化到Neo4j

更新至 2026年5月 最新国际形势
"""
import sys
import os

# 设置环境变量 - 阿里云 DashScope
os.environ['DASHSCOPE_API_KEY'] = 'sk-00a5136c6276471fa72db5928c613e1a'
os.environ['DASHSCOPE_MODEL'] = 'qwen-plus'
os.environ.pop('LLM_API_KEY', None)
os.environ.pop('KIMI_API_KEY', None)

# 添加路径
sys.path.insert(0, '/tmp/mirofish/backend')
sys.path.insert(0, '/tmp/mirofish/backend/app/services')
os.chdir('/tmp/mirofish/backend')

from multi_agent_political_simulation import MultiAgentPoliticalSimulation

# 使用DashScope + Neo4j
sim = MultiAgentPoliticalSimulation("dashscope")

scenario = '波斯湾战争：伊朗封锁霍尔木兹海峡（2026年5月升级版）'
context = '''【2026年5月1日 最新国际形势】

🔥 当前危机：波斯湾战争全面升级
- 伊朗革命卫队于4月1日封锁霍尔木兹海峡，油价从85美元飙升至380美元/桶
- 美以已启动"蜂巢行动"，对伊朗核设施进行有限打击
- 胡塞武装同步封锁红海，全球航运绕行好望角，运费暴涨500%
- 中国呼吁立即停火谈判，但拒绝谴责伊朗"正当防御行为"
- 俄罗斯向伊朗提供S-300防空系统和电子战装备

🌍 各方态势：
【美国】拜登政府面临大选压力，军工复合体推动扩大打击范围；华尔街警告经济衰退风险；以色列总理已授权地面进攻选项
【伊朗】经济濒临崩溃（GDP损失65%、通胀700%），但民族主义情绪高涨，革命卫队控制决策
【中国】解放军台海巡航常态化；借能源危机加速减持美债；上海合作组织框架下呼吁停火
【俄罗斯】乌克兰东部战线僵持；借油价上涨获利；向伊朗提供武器换取在叙利亚的军事存在
【欧盟】德法主张外交解决；东欧国家支持美国；能源价格导致通胀回温，民众不满上升
【以色列】已对伊朗发动三轮空袭；地面部队在黎巴嫩边境集结；国内政治压力要求彻底摧毁核设施
【沙特】呼吁保护霍尔木兹航道；与以色列关系正常化谈判暂停；被迫增加对华石油出口

📊 经济数据（2026年5月）：
- 布伦特原油：380美元/桶（年初85美元）
- 全球航运指数：飙升至2008年水平
- S&P 500：较年初下跌18%
- 黄金：2450美元/盎司
- 比特币：遭避险抛售，跌至48000美元

⚠️ 联合国安理会陷入僵局，美俄中均否决对方提案

初始状态:
- 伊朗：资源30（经济崩溃边缘）
- 美国：资源82（战争动员中）
- 以色列：资源65（已发动攻击）
- 中国：资源92（战略观望）
- 俄罗斯：资源78（借机获利）
- 欧盟：资源58（能源危机）
- 沙特：资源70（被迫卷入）
- 英国：资源55（追随美国）'''

print('='*60)
print('MiroFish 72智能体 × 博弈论模拟 + Neo4j持久化')
print('（2026年5月最新版背景）')
print('='*60)
print(f'场景: {scenario}')
print(f'LLM: DashScope qwen-plus（阿里云）')
print(f'图数据库: Neo4j (bolt://localhost:7687)')
print('='*60)

sim.run_full_simulation(scenario, context, rounds=5)
