"""
Real LLM Diplomatic Game - 真实LLM外交博弈
势力之间可以对话、讨价还价、形成联盟
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import time

from llm_political_game import LLMClient, FORCE_CHARACTERS

@dataclass
class DiplomaticMessage:
    """外交消息"""
    from_force: str
    to_force: str  # "all" for public, specific for private
    content: str
    message_type: str  # "public_statement", "private_proposal", "threat", "offer"
    round_num: int

@dataclass
class ForceState:
    """势力状态"""
    force_id: str
    name: str
    country: str
    
    # 动态状态
    trust_level: Dict[str, float] = field(default_factory=dict)  # 对其他势力的信任
    resource_level: float = 1.0  # 资源水平
    public_stance: str = "neutral"
    
    # 关系
    allies: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)

class RealLLMDiplomaticGame:
    """真实LLM外交博弈"""
    
    def __init__(self, llm_provider: str = "ollama"):
        self.llm = LLMClient(llm_provider)
        self.characters = FORCE_CHARACTERS
        self.message_history: List[DiplomaticMessage] = []
        self.force_states: Dict[str, ForceState] = {}
    
    def initialize_forces(self, force_ids: List[str]):
        """初始化势力状态"""
        for fid in force_ids:
            char = self.characters.get(fid, {})
            self.force_states[fid] = ForceState(
                force_id=fid,
                name=char.get("name", fid),
                country=char.get("country", ""),
                trust_level={other: 0.5 for other in force_ids if other != fid},
            )
    
    def generate_public_statement(self, force_id: str, scenario: str, 
                                   context: str, round_num: int) -> str:
        """生成公开声明"""
        char = self.characters.get(force_id, {})
        identity = char.get("identity", "")
        name = char.get("name", force_id)
        
        # 获取历史消息
        recent_messages = [
            f"[{msg.from_force}]: {msg.content}"
            for msg in self.message_history[-10:]
            if msg.message_type == "public_statement"
        ]
        
        prompt = f"""{identity}

当前场景：{scenario}

当前局势：
{context}

历史声明（最近）：
{chr(10).join(recent_messages) if recent_messages else "（无）"}

你是{name}，请发表公开声明。
要求：
1. 表明你的立场和诉求
2. 回应其他势力的声明（如果有）
3. 提出你的条件或警告
4. 50-100字，像真实外交声明一样

直接回复声明内容，不要解释。"""
        
        messages = [
            {"role": "system", "content": "你是一个外交发言人。"},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat(messages, temperature=0.8, max_tokens=200)
        return response.content if response else f"[{name}] 暂无声明"
    
    def generate_private_proposal(self, force_id: str, target_force: str,
                                   scenario: str, context: str) -> Optional[str]:
        """生成私下提议"""
        char = self.characters.get(force_id, {})
        target_char = self.characters.get(target_force, {})
        identity = char.get("identity", "")
        name = char.get("name", force_id)
        target_name = target_char.get("name", target_force)
        
        prompt = f"""{identity}

当前场景：{scenario}

你想向{target_name}发送私下外交提议。

要求：
1. 提出具体的合作或交易条件
2. 说明你能提供什么，想要什么
3. 语气可以是威胁、利诱或真诚合作
4. 30-80字

直接回复提议内容，不要解释。"""
        
        messages = [
            {"role": "system", "content": "你是一个秘密外交使者。"},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat(messages, temperature=0.9, max_tokens=150)
        return response.content if response else None
    
    def generate_response_to_proposal(self, force_id: str, from_force: str,
                                     proposal: str, scenario: str) -> str:
        """回应私下提议"""
        char = self.characters.get(force_id, {})
        from_char = self.characters.get(from_force, {})
        identity = char.get("identity", "")
        name = char.get("name", force_id)
        from_name = from_char.get("name", from_force)
        
        prompt = f"""{identity}

{from_name}向你发送了私下提议：
\"{proposal}\"

请回复：
1. 接受、拒绝还是讨价还价？
2. 你的条件是什么？
3. 30-80字

直接回复，不要解释。"""
        
        messages = [
            {"role": "system", "content": "你是一个外交决策者。"},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat(messages, temperature=0.8, max_tokens=150)
        return response.content if response else "拒绝提议。"
    
    def run_real_game(self, scenario_id: str, force_ids: List[str],
                     scenario: str, context: str, rounds: int = 3) -> Dict:
        """运行真实外交博弈"""
        print(f"\n{'='*60}")
        print(f"真实LLM外交博弈")
        print(f"{'='*60}")
        print(f"场景: {scenario_id}")
        print(f"参与势力: {len(force_ids)}个")
        print(f"博弈轮数: {rounds}")
        print(f"LLM: {self.llm.provider}/{self.llm.model}")
        print(f"{'='*60}\n")
        
        self.initialize_forces(force_ids)
        
        for round_num in range(1, rounds + 1):
            print(f"\n{'='*50}")
            print(f"第 {round_num} 轮")
            print(f"{'='*50}")
            
            # 1. 公开声明阶段
            print("\n📢 公开声明阶段")
            for force_id in force_ids:
                char = self.characters.get(force_id, {})
                name = char.get("name", force_id)
                
                statement = self.generate_public_statement(
                    force_id, scenario, context, round_num
                )
                
                msg = DiplomaticMessage(
                    from_force=force_id,
                    to_force="all",
                    content=statement,
                    message_type="public_statement",
                    round_num=round_num,
                )
                self.message_history.append(msg)
                
                print(f"\n[{name}]:")
                print(f"  \"{statement}\"")
                
                time.sleep(0.3)
            
            # 2. 私下外交阶段（随机配对）
            print("\n🔒 私下外交阶段")
            import random
            random.shuffle(force_ids)
            
            for i in range(0, len(force_ids), 2):
                if i + 1 < len(force_ids):
                    force_a = force_ids[i]
                    force_b = force_ids[i + 1]
                    
                    char_a = self.characters.get(force_a, {})
                    char_b = self.characters.get(force_b, {})
                    name_a = char_a.get("name", force_a)
                    name_b = char_b.get("name", force_b)
                    
                    # A向B提议
                    proposal = self.generate_private_proposal(
                        force_a, force_b, scenario, context
                    )
                    
                    if proposal:
                        print(f"\n💬 {name_a} → {name_b} (私下):")
                        print(f"  \"{proposal}\"")
                        
                        # B回应
                        response = self.generate_response_to_proposal(
                            force_b, force_a, proposal, scenario
                        )
                        
                        print(f"  {name_b} 回应:")
                        print(f"  \"{response}\"")
                        
                        # 记录
                        self.message_history.append(DiplomaticMessage(
                            from_force=force_a,
                            to_force=force_b,
                            content=proposal,
                            message_type="private_proposal",
                            round_num=round_num,
                        ))
                        self.message_history.append(DiplomaticMessage(
                            from_force=force_b,
                            to_force=force_a,
                            content=response,
                            message_type="private_proposal",
                            round_num=round_num,
                        ))
                    
                    time.sleep(0.3)
        
        # 最终结果
        print(f"\n{'='*60}")
        print(f"博弈结束")
        print(f"{'='*60}")
        
        return {
            "scenario": scenario_id,
            "rounds": rounds,
            "total_messages": len(self.message_history),
            "forces": len(force_ids),
        }


# 全局实例
real_game = RealLLMDiplomaticGame()

if __name__ == "__main__":
    print("=== 真实LLM外交博弈系统 ===\n")
    
    game = RealLLMDiplomaticGame()
    
    scenario = "波斯湾战争：伊朗封锁霍尔木兹海峡，全球石油危机"
    forces = [
        'us_military_industrial',
        'us_wall_street',
        'cn_military_red',
        'cn_reformists',
        'ru_siloviki',
        'ru_oligarchs',
        'eu_franco_german',
        'eu_atlanticists',
    ]
    
    context = "油价暴涨300%，美国海军第五舰队待命，沙特请求保护"
    
    result = game.run_real_game('persian_gulf', forces, scenario, context, rounds=2)
    
    print(f"\n总消息数: {result['total_messages']}")
