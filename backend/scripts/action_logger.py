"""
Action Logger - 模拟动作日志记录器
记录每个 Agent 的动作到 JSONL 文件，供后续分析使用
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class PlatformActionLogger:
    """平台动作日志记录器"""

    def __init__(self, simulation_dir: str, platform: str):
        self.simulation_dir = simulation_dir
        self.platform = platform
        self.actions_log_path = os.path.join(simulation_dir, "actions.jsonl")
        self.round_count = 0
        self.action_count = 0
        # 确保目录存在
        os.makedirs(simulation_dir, exist_ok=True)

    def log_simulation_start(self, config: Dict[str, Any]):
        """记录模拟开始"""
        self.round_count = 0
        self.action_count = 0
        with open(self.actions_log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "simulation_start",
                "timestamp": datetime.now().isoformat(),
                "config": {k: v for k, v in config.items() if k != "agent_configs"},
                "agent_count": len(config.get("agent_configs", []))
            }, ensure_ascii=False) + "\n")

    def log_round_start(self, round_num: int, simulated_hour: int):
        """记录回合开始"""
        self.round_count = round_num
        self.action_count = 0

    def log_round_end(self, round_num: int, action_count: int):
        """记录回合结束"""
        self.round_count = round_num
        self.action_count = action_count
        with open(self.actions_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "round_end",
                "timestamp": datetime.now().isoformat(),
                "round": round_num,
                "action_count": action_count
            }, ensure_ascii=False) + "\n")

    def log_action(self, round_num: int, agent_id: Any, agent_name: str,
                   action_type: str, action_args: Dict[str, Any]):
        """记录单个动作"""
        self.action_count += 1
        with open(self.actions_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "action",
                "timestamp": datetime.now().isoformat(),
                "round": round_num,
                "platform": self.platform,
                "agent_id": str(agent_id),
                "agent_name": agent_name,
                "action_type": action_type,
                "action_args": action_args
            }, ensure_ascii=False) + "\n")

    def log_simulation_end(self, total_rounds: int, total_actions: int):
        """记录模拟结束"""
        with open(self.actions_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "simulation_end",
                "timestamp": datetime.now().isoformat(),
                "total_rounds": total_rounds,
                "total_actions": total_actions
            }, ensure_ascii=False) + "\n")


class SimulationLogManager:
    """仿真日志管理器 - 提供平台日志记录器"""

    def __init__(self, simulation_dir: str):
        self.simulation_dir = simulation_dir
        self._twitter_logger: Optional[PlatformActionLogger] = None
        self._reddit_logger: Optional[PlatformActionLogger] = None

    def get_twitter_logger(self) -> PlatformActionLogger:
        if self._twitter_logger is None:
            self._twitter_logger = PlatformActionLogger(
                os.path.join(self.simulation_dir, "twitter"),
                "twitter"
            )
        return self._twitter_logger

    def get_reddit_logger(self) -> PlatformActionLogger:
        if self._reddit_logger is None:
            self._reddit_logger = PlatformActionLogger(
                os.path.join(self.simulation_dir, "reddit"),
                "reddit"
            )
        return self._reddit_logger

    def info(self, msg: str):
        """打印信息日志（打印到标准输出）"""
        print(f"[SimulationLog] {msg}")
