"""
LLM Political Forces Game - 基于真实LLM的政治势力博弈
使用LLM API让各政治势力进行真实对话和决策
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import urllib.request
import urllib.error
import time

# LLM API配置
LLM_CONFIG = {
    "kimi": {
        "api_key": os.environ.get("KIMI_API_KEY", ""),
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "openai": {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "google": {
        "api_key": os.environ.get("GOOGLE_API_KEY", ""),
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-1.5-flash",
    },
    "ollama": {
        "api_key": os.environ.get("LLM_API_KEY", "ollama-local"),
        "base_url": os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1"),
        "model": os.environ.get("LLM_MODEL_NAME", "qwen3-coder:latest"),
    },
}

@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str

class LLMClient:
    """LLM API客户端"""
    
    def __init__(self, provider: str = None):
        # Auto-detect available provider if not specified
        if provider is None:
            provider = self._detect_provider()
        
        self.config = LLM_CONFIG.get(provider, LLM_CONFIG["kimi"])
        self.api_key = self.config["api_key"]
        self.base_url = self.config["base_url"]
        self.model = self.config["model"]
        self.provider = provider
    
    def _detect_provider(self) -> str:
        """自动检测可用的LLM提供商"""
        # 读取.env文件
        env_file = "/tmp/mirofish/.env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, val = line.split('=', 1)
                            if key not in os.environ:
                                os.environ[key] = val
        
        # 优先级：Ollama > Kimi > OpenAI > Google
        if os.environ.get("LLM_API_KEY"):
            return "ollama"
        if os.environ.get("KIMI_API_KEY"):
            return "kimi"
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        if os.environ.get("GOOGLE_API_KEY"):
            return "google"
        # 默认Ollama（本地）
        return "ollama"
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, 
             max_tokens: int = 1000) -> Optional[LLMResponse]:
        """发送聊天请求"""
        if not self.api_key:
            return None
        
        try:
            if self.provider == "kimi":
                return self._chat_kimi(messages, temperature, max_tokens)
            elif self.provider == "openai":
                return self._chat_openai(messages, temperature, max_tokens)
            elif self.provider == "google":
                return self._chat_google(messages, temperature, max_tokens)
            elif self.provider == "ollama":
                return self._chat_ollama(messages, temperature, max_tokens)
        except Exception as e:
            print(f"LLM API Error: {e}")
            return None
    
    def _chat_kimi(self, messages: List[Dict], temperature: float, 
                   max_tokens: int) -> Optional[LLMResponse]:
        """调用Kimi API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                model=result.get("model", self.model),
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                finish_reason=result["choices"][0].get("finish_reason", ""),
            )
    
    def _chat_openai(self, messages: List[Dict], temperature: float,
                     max_tokens: int) -> Optional[LLMResponse]:
        """调用OpenAI API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                model=result.get("model", self.model),
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                finish_reason=result["choices"][0].get("finish_reason", ""),
            )
    
    def _chat_google(self, messages: List[Dict], temperature: float,
                     max_tokens: int) -> Optional[LLMResponse]:
        """调用Google Gemini API"""
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        
        # 转换messages格式
        contents = []
        for m in messages:
            if m["role"] == "user":
                contents.append({"parts": [{"text": m["content"]}]})
            else:
                contents.append({"parts": [{"text": f"Assistant: {m['content']}"}]})
        
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            return LLMResponse(
                content=result["candidates"][0]["content"]["parts"][0]["text"],
                model=self.model,
                tokens_used=0,
                finish_reason="stop",
            )
    
    def _chat_ollama(self, messages: List[Dict], temperature: float,
                     max_tokens: int) -> Optional[LLMResponse]:
        """调用Ollama本地API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                model=result.get("model", self.model),
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                finish_reason=result["choices"][0].get("finish_reason", ""),
            )


# 政治势力角色设定
FORCE_CHARACTERS = {
    "us_military_industrial": {
        "name": "美国军工复合体",
        "name_en": "US Military-Industrial Complex",
        "country": "美国",
        "identity": """你是美国军工复合体的代表。
背景：洛克希德·马丁、波音、雷神等军火巨头的利益代言人。
核心诉求：
1. 维持高额国防预算（每年8000亿美元+）
2. 推动对外军事干预和武器出口
3. 遏制中俄军事崛起
4. 维护在全球的军事优势

你坚信：强大的军事力量是美国利益的保障，军工复合体是美国实力的核心。""",
    },
    
    "us_wall_street": {
        "name": "华尔街金融资本",
        "name_en": "Wall Street Financial Capital",
        "country": "美国",
        "identity": """你是华尔街金融资本的代表。
背景：高盛、摩根大通、贝莱德等金融巨头的利益代言人。
核心诉求：
1. 维持美元霸权和纽约金融中心地位
2. 进入中国市场并获得投资机会
3. 避免美中金融脱钩
4. 维持低利率和宽松的金融环境

你坚信：自由贸易和金融全球化符合美国资本的利益，合作比分对抗更能赚钱。""",
    },
    
    "us_tech_giants": {
        "name": "硅谷科技巨头",
        "name_en": "Silicon Valley Tech Giants",
        "country": "美国",
        "identity": """你是硅谷科技巨头的代表。
背景：谷歌、苹果、微软、Meta等科技公司的利益代言人。
核心诉求：
1. 维持全球科技领先地位
2. 进入中国市场（但面临限制）
3. 推动AI和互联网自由
4. 保护知识产权

你坚信：技术创新是美国竞争力的核心，但也不想失去中国市场。立场矛盾但务实。""",
    },
    
    "us_pro_israel_lobby": {
        "name": "亲以色列游说团体",
        "name_en": "Pro-Israel Lobby",
        "country": "美国",
        "identity": """你是亲以色列游说团体（AIPAC等）的代表。
背景：美国犹太裔社区和以色列利益的代言人。
核心诉求：
1. 无条件支持以色列的安全
2. 推动对以军事援助
3. 反对伊朗核计划
4. 维护美以特殊关系

你坚信：以色列是美国在中东最重要的盟友，保护以色列就是保护美国利益。""",
    },
    
    "cn_military_red": {
        "name": "中国军方/红二代",
        "name_en": "Chinese Military / Red Aristocracy",
        "country": "中国",
        "identity": """你是中国军方和红二代的代表。
背景：解放军高层和革命元老后代的利益代言人。
核心诉求：
1. 实现祖国统一（台湾）
2. 加速军事现代化
3. 维护南海主权
4. 反对美帝围堵中国

你坚信：实力是维护国家利益的唯一保障，必要时不惜一战。统一台湾是历史使命。""",
    },
    
    "cn_security": {
        "name": "中国安全部门",
        "name_en": "Chinese Security Apparatus",
        "country": "中国",
        "identity": """你是中国安全部门的代表。
背景：政法委、公安部、国安部的利益代言人。
核心诉求：
1. 维护政权安全和政治稳定
2. 加强网络主权和信息控制
3. 意识形态安全
4. 反间谍和颜色革命防范

你坚信：政权安全是第一要务，美国始终试图颠覆中国，必须高度警惕。""",
    },
    
    "cn_reformists": {
        "name": "中国改革派/市场派",
        "name_en": "Chinese Reformists / Market Forces",
        "country": "中国",
        "identity": """你是中国改革派和市场派的代表。
背景：国务院系统和经济学家的利益代言人。
核心诉求：
1. 深化改革开放
2. 与西方国家保持合作
3. 市场经济和全球化
4. 技术引进和人才交流

你坚信：和平发展是主流，合作共赢符合中国利益，对抗只会两败俱伤。""",
    },
    
    "cn_private_capital": {
        "name": "中国民企/科技资本",
        "name_en": "Chinese Private Capital",
        "country": "中国",
        "identity": """你是中国民营企业和科技资本的代表。
背景：腾讯、字节跳动、华为等民企巨头的利益代言人。
核心诉求：
1. 反垄断松绑，减少监管
2. 进入国际市场
3. 技术突破和创新
4. 资本家权益保护

你坚信：市场开放和国际化符合民企利益，希望中美关系稳定以便开展业务。""",
    },
    
    "ru_siloviki": {
        "name": "俄罗斯强力部门",
        "name_en": "Russian Siloviki / Security Services",
        "country": "俄罗斯",
        "identity": """你是俄罗斯强力部门的代表。
背景：FSB、对外情报局、国防部的利益代言人。
核心诉求：
1. 维护国家安全和势力范围
2. 扩大情报和监控能力
3. 反西方渗透
4. 维持俄罗斯的大国地位

你坚信：西方一直在遏制俄罗斯，只有实力才能保障安全。""",
    },
    
    "ru_oligarchs": {
        "name": "俄罗斯寡头/商业精英",
        "name_en": "Russian Oligarchs",
        "country": "俄罗斯",
        "identity": """你是俄罗斯寡头和商业精英的代表。
背景：能源、矿业巨头的利益代言人。
核心诉求：
1. 保护海外资产
2. 避免更多制裁
3. 维持贸易通道
4. 转向中国市场

你坚信：生意就是生意，政治应该为经济服务。制裁伤害了俄罗斯商人。""",
    },
    
    "eu_franco_german": {
        "name": "法德轴心",
        "name_en": "Franco-German Axis",
        "country": "欧盟",
        "identity": """你是法德轴心的代表。
背景：法国和德国政府的利益代言人。
核心诉求：
1. 推动欧洲一体化
2. 欧洲战略自主
3. 欧元稳定
4. 在中美之间保持平衡

你坚信：欧洲应该成为独立的一极，不应该被迫选边站。""",
    },
    
    "eu_atlanticists": {
        "name": "欧盟亲美派",
        "name_en": "EU Atlanticists",
        "country": "欧盟",
        "identity": """你是欧盟亲美派的代表。
背景：波兰、波罗的海国家等东欧国家的利益代言人。
核心诉求：
1. 北约优先
2. 美国安全保障
3. 抗俄援乌
4. 维护跨大西洋联盟

你坚信：美国是欧洲安全的保障，没有美国，欧洲无法自保。""",
    },
    
    "eu_tech_giants": {
        "name": "欧洲科技巨头",
        "name_en": "European Tech Giants",
        "country": "欧盟",
        "identity": """你是欧洲科技巨头的代表。
背景：ASML、SAP等欧洲科技企业的利益代言人。
核心诉求：
1. 数字主权
2. 减少对美国科技依赖
3. AI监管领导力
4. 进入中国市场

你坚信：欧洲应该在科技竞争中保持独立，既不想完全依赖美国，也不想失去中国市场。""",
    },
}


@dataclass
class ForceDecision:
    """势力决策"""
    force_id: str
    force_name: str
    country: str
    
    # 决策
    action: str
    target: str
    reasoning: str
    
    # 风险和资源
    risk_level: float
    resource_commitment: float
    
    # LLM生成内容
    llm_response: str = ""


class LLMPoliticalGame:
    """基于LLM的政治势力博弈系统"""
    
    def __init__(self, llm_provider: str = None):
        # 优先使用Ollama（本地），如果失败则降级到其他
        if llm_provider:
            self.llm = LLMClient(llm_provider)
        else:
            try:
                self.llm = LLMClient("ollama")
                # 测试Ollama是否可用
                test = self.llm.chat([{"role": "user", "content": "hi"}], max_tokens=10)
                if not test:
                    raise Exception("Ollama not responding")
            except:
                # 降级到Kimi
                self.llm = LLMClient("kimi")
        
        self.characters = FORCE_CHARACTERS
        self.game_history: List[Dict] = []
    
    def get_force_identity(self, force_id: str) -> str:
        """获取势力身份设定"""
        char = self.characters.get(force_id, {})
        return char.get("identity", "")
    
    def generate_decision(self, force_id: str, scenario: str, 
                         context: Dict, round_num: int) -> Optional[ForceDecision]:
        """让LLM生成势力决策"""
        char = self.characters.get(force_id, {})
        name = char.get("name", force_id)
        country = char.get("country", "")
        
        # 构建prompt
        prompt = f"""{self.get_force_identity(force_id)}

当前场景：{scenario}

当前局势：
{json.dumps(context, ensure_ascii=False, indent=2)}

你是{name}，请根据你的立场和利益，做出决策。

请用JSON格式回复：
{{
    "action": "选择: cooperate(合作), confront(对抗), deescalate(缓和), neutral(中立), escalate(升级)",
    "target": "主要目标国家/势力",
    "reasoning": "你的决策理由（100字以内）",
    "risk_level": 风险程度（0-1，1最高风险）,
    "resource_commitment": 资源投入程度（0-1）,
    "statement": "你要说的话或声明（50字以内，体现你的立场）"
}}

只回复JSON，不要有其他内容。"""
        
        messages = [
            {"role": "system", "content": "你是一个地缘政治分析师，帮助模拟各国政治势力的决策。"},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat(messages, temperature=0.7, max_tokens=800)
        
        if not response:
            return None
        
        try:
            # 尝试解析JSON
            content = response.content.strip()
            # 移除可能的markdown代码块
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0].strip()
            
            data = json.loads(content)
            
            return ForceDecision(
                force_id=force_id,
                force_name=name,
                country=country,
                action=data.get("action", "neutral"),
                target=data.get("target", "all"),
                reasoning=data.get("reasoning", ""),
                risk_level=float(data.get("risk_level", 0.5)),
                resource_commitment=float(data.get("resource_commitment", 0.5)),
                llm_response=data.get("statement", ""),
            )
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始响应: {response.content[:200]}")
            return None
    
    def run_llm_game(self, scenario_id: str, forces: List[str],
                    scenario_desc: str, context: Dict, rounds: int = 2) -> Dict:
        """运行LLM博弈"""
        print(f"\n{'='*60}")
        print(f"LLM政治势力博弈开始")
        print(f"{'='*60}")
        print(f"场景: {scenario_id}")
        print(f"参与势力: {len(forces)}个")
        print(f"博弈轮数: {rounds}")
        print(f"LLM Provider: {self.llm.provider}")
        print(f"{'='*60}\n")
        
        all_decisions = []
        
        for round_num in range(1, rounds + 1):
            print(f"\n{'='*50}")
            print(f"第 {round_num} 轮")
            print(f"{'='*50}")
            
            round_decisions = []
            
            for force_id in forces:
                char = self.characters.get(force_id, {})
                name = char.get("name", force_id)
                
                print(f"\n正在询问 {name}...")
                
                decision = self.generate_decision(
                    force_id, scenario_desc, context, round_num
                )
                
                if decision:
                    round_decisions.append(decision)
                    
                    print(f"  行动: {decision.action}")
                    print(f"  目标: {decision.target}")
                    print(f"  风险: {decision.risk_level:.1f}")
                    print(f"  资源: {decision.resource_commitment:.1f}")
                    print(f"  声明: {decision.llm_response}")
                else:
                    print(f"  LLM响应失败，跳过")
                
                # 避免API过载
                time.sleep(0.5)
            
            all_decisions.append(round_decisions)
            
            # 更新情境
            self._update_context(context, round_decisions)
        
        # 最终结果
        result = self._calculate_result(scenario_id, all_decisions, context)
        
        return result
    
    def _update_context(self, context: Dict, decisions: List[ForceDecision]):
        """根据决策更新情境"""
        # 统计行动
        actions = [d.action for d in decisions]
        
        # 调整紧张度
        if "escalate" in actions:
            context["tension"] = min(1.0, context.get("tension", 0.5) + 0.1)
        if "deescalate" in actions:
            context["tension"] = max(0.0, context.get("tension", 0.5) - 0.1)
        
        # 计算资源投入
        total_resources = sum(d.resource_commitment for d in decisions)
        context["total_commitment"] = total_resources / len(decisions)
    
    def _calculate_result(self, scenario_id: str, all_decisions: List[List[ForceDecision]],
                         context: Dict) -> Dict:
        """计算博弈结果"""
        # 按国家分组
        country_decisions = {}
        for round_dec in all_decisions:
            for d in round_dec:
                if d.country not in country_decisions:
                    country_decisions[d.country] = []
                country_decisions[d.country].append(d)
        
        # 计算各国策略
        country_strategies = {}
        for country, decisions in country_decisions.items():
            action_counts = {}
            for d in decisions:
                action_counts[d.action] = action_counts.get(d.action, 0) + 1
            dominant = max(action_counts, key=action_counts.get)
            country_strategies[country] = {
                "strategy": dominant,
                "counts": action_counts,
                "avg_risk": sum(d.risk_level for d in decisions) / len(decisions),
                "avg_resource": sum(d.resource_commitment for d in decisions) / len(decisions),
            }
        
        print(f"\n{'='*60}")
        print(f"博弈结束 - 最终结果")
        print(f"{'='*60}")
        
        print(f"\n各国策略:")
        for country, info in country_strategies.items():
            print(f"  {country}: {info['strategy']} (平均风险: {info['avg_risk']:.1f}, 资源投入: {info['avg_resource']:.1f})")
        
        return {
            "scenario": scenario_id,
            "rounds": len(all_decisions),
            "country_strategies": country_strategies,
            "context": context,
            "total_forces": sum(len(r) for r in all_decisions),
        }
    
    def list_available_forces(self) -> List[Dict]:
        """列出可用势力"""
        return [
            {
                "id": fid,
                "name": char.get("name", fid),
                "country": char.get("country", ""),
            }
            for fid, char in self.characters.items()
        ]


# 全局实例
llm_political_game = LLMPoliticalGame()

if __name__ == "__main__":
    print("=== LLM政治势力博弈系统 ===\n")
    
    game = LLMPoliticalGame()
    
    print("可用势力:")
    for f in game.list_available_forces():
        print(f"  [{f['country']}] {f['name']}")
    
    # 运行测试场景
    print("\n" + "="*60)
    print("运行测试场景: 台海危机")
    print("="*60)
    
    scenario = "台海危机：中国宣布对台采取军事行动，美国必须决定是否介入"
    forces = ["us_military_industrial", "us_wall_street", "us_tech_giants",
              "cn_military_red", "cn_security", "cn_reformists",
              "eu_franco_german", "eu_atlanticists"]
    
    context = {
        "tension": 0.5,
        "us_commitment": 0.5,
        "china_resolve": 0.8,
        "global_economy": 0.7,
    }
    
    result = game.run_llm_game("taiwan_crisis", forces, scenario, context, rounds=2)
    
    print(f"\n博弈统计:")
    print(f"  总决策数: {result['total_forces']}")
    print(f"  参与国家: {', '.join(result['country_strategies'].keys())}")
