"""
Geopolitical Simulation Persistence Layer
持久化存储层 - 将模拟结果保存到数据库
"""

import os
import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

class GeopoliticalDB:
    """地缘政治模拟数据库"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库和表存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 模拟会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                config TEXT,
                initial_tension REAL,
                final_tension REAL,
                total_rounds INTEGER,
                status TEXT
            )
        ''')
        
        # 国家状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS country_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round INTEGER NOT NULL,
                country_id TEXT NOT NULL,
                name TEXT,
                military_posture TEXT,
                war_intensity TEXT,
                casualties INTEGER,
                public_support REAL,
                international_pressure REAL,
                dominant_faction TEXT,
                government_stability REAL,
                economic_strength REAL,
                UNIQUE(session_id, round, country_id)
            )
        ''')
        
        # 外交事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diplomatic_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round INTEGER NOT NULL,
                event_type TEXT,
                actor TEXT,
                target TEXT,
                description TEXT,
                pressure REAL,
                actor_strategy TEXT,
                target_strategy TEXT
            )
        ''')
        
        # 战争事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS war_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round INTEGER NOT NULL,
                parties TEXT,
                intensity TEXT,
                casualties TEXT,
                description TEXT,
                cause TEXT
            )
        ''')
        
        # UN决议表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS un_resolutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round INTEGER NOT NULL,
                resolution_type TEXT,
                target_countries TEXT,
                support_rate REAL,
                passed INTEGER,
                description TEXT
            )
        ''')
        
        # 社交媒体动作表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_media_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round INTEGER NOT NULL,
                agent_id TEXT,
                agent_name TEXT,
                action_type TEXT,
                content TEXT,
                hardline_signal REAL,
                peace_signal REAL,
                pressure_change REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_session(self, session_id: str, config: Dict[str, Any], 
                     initial_tension: float = 30.0) -> bool:
        """保存模拟会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO simulation_sessions 
            (session_id, created_at, updated_at, config, initial_tension, status)
            VALUES (?, ?, ?, ?, ?, 'running')
        ''', (session_id, now, now, json.dumps(config), initial_tension))
        
        conn.commit()
        conn.close()
        return True
    
    def update_session(self, session_id: str, final_tension: float = None,
                      total_rounds: int = None, status: str = None):
        """更新模拟会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = ["updated_at = ?"]
        values = [datetime.now().isoformat()]
        
        if final_tension is not None:
            updates.append("final_tension = ?")
            values.append(final_tension)
        
        if total_rounds is not None:
            updates.append("total_rounds = ?")
            values.append(total_rounds)
        
        if status is not None:
            updates.append("status = ?")
            values.append(status)
        
        values.append(session_id)
        
        cursor.execute(f'''
            UPDATE simulation_sessions 
            SET {', '.join(updates)}
            WHERE session_id = ?
        ''', values)
        
        conn.commit()
        conn.close()
    
    def save_country_state(self, session_id: str, round_num: int, 
                           country_data: Dict[str, Any]):
        """保存国家状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO country_states
            (session_id, round, country_id, name, military_posture, war_intensity,
             casualties, public_support, international_pressure, dominant_faction,
             government_stability, economic_strength)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, round_num,
            country_data.get('country_id', ''),
            country_data.get('name', ''),
            country_data.get('military_posture', ''),
            country_data.get('war_intensity', ''),
            country_data.get('casualties', 0),
            country_data.get('public_support', 0.5),
            country_data.get('international_pressure', 0),
            country_data.get('dominant_faction', 'moderates'),
            country_data.get('government_stability', 0.8),
            country_data.get('economic_strength', 0.5)
        ))
        
        conn.commit()
        conn.close()
    
    def save_diplomatic_event(self, session_id: str, round_num: int,
                              event_data: Dict[str, Any]):
        """保存外交事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO diplomatic_events
            (session_id, round, event_type, actor, target, description, pressure,
             actor_strategy, target_strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, round_num,
            event_data.get('type', ''),
            event_data.get('actor', ''),
            event_data.get('target', ''),
            event_data.get('description', ''),
            event_data.get('pressure', 0),
            event_data.get('strategy', ''),
            event_data.get('predicted_opponent', '')
        ))
        
        conn.commit()
        conn.close()
    
    def save_war_event(self, session_id: str, round_num: int, event_data: Dict[str, Any]):
        """保存战争事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO war_events
            (session_id, round, parties, intensity, casualties, description, cause)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, round_num,
            json.dumps(event_data.get('parties', [])),
            event_data.get('intensity', ''),
            json.dumps(event_data.get('casualties', {})),
            event_data.get('description', ''),
            event_data.get('cause', '')
        ))
        
        conn.commit()
        conn.close()
    
    def save_un_resolution(self, session_id: str, round_num: int, resolution_data: Dict[str, Any]):
        """保存UN决议"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO un_resolutions
            (session_id, round, resolution_type, target_countries, support_rate,
             passed, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, round_num,
            resolution_data.get('type', ''),
            json.dumps(resolution_data.get('target', [])),
            resolution_data.get('support_rate', 0),
            1 if resolution_data.get('passed') else 0,
            resolution_data.get('description', '')
        ))
        
        conn.commit()
        conn.close()
    
    def save_social_media_action(self, session_id: str, round_num: int,
                                 action_data: Dict[str, Any], 
                                 media_analysis: Dict[str, Any] = None):
        """保存社交媒体动作"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO social_media_actions
            (session_id, round, agent_id, agent_name, action_type, content,
             hardline_signal, peace_signal, pressure_change)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, round_num,
            action_data.get('agent_id', ''),
            action_data.get('agent_name', ''),
            action_data.get('action_type', ''),
            action_data.get('content', ''),
            media_analysis.get('hardline_signal', 0) if media_analysis else 0,
            media_analysis.get('peace_signal', 0) if media_analysis else 0,
            media_analysis.get('pressure_change', 0) if media_analysis else 0
        ))
        
        conn.commit()
        conn.close()
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id, created_at, updated_at, initial_tension, 
                   final_tension, total_rounds, status
            FROM simulation_sessions WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        result = {
            'session_id': row[0],
            'created_at': row[1],
            'updated_at': row[2],
            'initial_tension': row[3],
            'final_tension': row[4],
            'total_rounds': row[5],
            'status': row[6]
        }
        
        # 获取统计
        cursor.execute('SELECT COUNT(*) FROM war_events WHERE session_id = ?', (session_id,))
        result['war_events_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM un_resolutions WHERE session_id = ?', (session_id,))
        result['un_resolutions_count'] = cursor.fetchone()[0]
        
        conn.close()
        return result
    
    def get_tension_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取紧张度历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT round, AVG(international_pressure), 
                   (SELECT war_intensity FROM country_states WHERE session_id = ? AND round = cs.round LIMIT 1)
            FROM country_states cs
            WHERE session_id = ?
            GROUP BY round
            ORDER BY round
        ''', (session_id, session_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {'round': r[0], 'avg_pressure': r[1], 'war_intensity': r[2]}
            for r in rows
        ]


class GeopoliticalPersistenceMiddleware:
    """
    地缘政治持久化中间件
    在模拟运行时自动保存数据
    """
    
    def __init__(self, simulation_dir: str):
        self.simulation_dir = simulation_dir
        self.db_path = os.path.join(simulation_dir, 'geopolitical.db')
        self.db = GeopoliticalDB(self.db_path)
        self.current_session_id = None
    
    def start_session(self, session_id: str, config: Dict[str, Any],
                      initial_tension: float = 30.0):
        """开始新的模拟会话"""
        self.current_session_id = session_id
        self.db.save_session(session_id, config, initial_tension)
    
    def end_session(self, final_tension: float = None, total_rounds: int = None,
                   status: str = 'completed'):
        """结束模拟会话"""
        if self.current_session_id:
            self.db.update_session(
                self.current_session_id,
                final_tension=final_tension,
                total_rounds=total_rounds,
                status=status
            )
    
    def save_round_data(self, round_num: int, round_data: Dict[str, Any]):
        """保存单轮数据"""
        if not self.current_session_id:
            return
        
        session_id = self.current_session_id
        
        # 保存国家状态
        for country_data in round_data.get('countries', {}).values():
            country_data['country_id'] = country_data.get('name', '').lower().replace(' ', '_')
            self.db.save_country_state(session_id, round_num, country_data)
        
        # 保存外交事件
        for event in round_data.get('diplomatic_events', []):
            self.db.save_diplomatic_event(session_id, round_num, event)
        
        # 保存战争事件
        for event in round_data.get('war_events', []):
            self.db.save_war_event(session_id, round_num, event)
        
        # 保存UN决议
        for res in round_data.get('un_resolutions', []):
            self.db.save_un_resolution(session_id, round_num, res)
        
        # 保存社交媒体动作
        for action in round_data.get('social_media_actions', []):
            self.db.save_social_media_action(session_id, round_num, action)
    
    def get_summary(self) -> Optional[Dict[str, Any]]:
        """获取当前会话摘要"""
        if not self.current_session_id:
            return None
        return self.db.get_session_summary(self.current_session_id)
    
    def get_timeline(self, session_id: str = None) -> List[Dict[str, Any]]:
        """获取事件时间线"""
        if not session_id:
            session_id = self.current_session_id
        if not session_id:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有事件按时间排序
        events = []
        
        cursor.execute('''
            SELECT round, 'diplomatic', event_type, actor, description
            FROM diplomatic_events WHERE session_id = ?
            ORDER BY round
        ''', (session_id,))
        for row in cursor.fetchall():
            events.append({
                'round': row[0],
                'type': 'diplomatic',
                'action': row[2],
                'actor': row[3],
                'description': row[4]
            })
        
        cursor.execute('''
            SELECT round, 'war', intensity, parties, description
            FROM war_events WHERE session_id = ?
            ORDER BY round
        ''', (session_id,))
        for row in cursor.fetchall():
            events.append({
                'round': row[0],
                'type': 'war',
                'intensity': row[2],
                'parties': json.loads(row[3]),
                'description': row[4]
            })
        
        cursor.execute('''
            SELECT round, 'un', resolution_type, target_countries, passed, description
            FROM un_resolutions WHERE session_id = ?
            ORDER BY round
        ''', (session_id,))
        for row in cursor.fetchall():
            events.append({
                'round': row[0],
                'type': 'un',
                'resolution_type': row[2],
                'target_countries': json.loads(row[3]),
                'passed': bool(row[4]),
                'description': row[5]
            })
        
        conn.close()
        
        # 按round排序
        events.sort(key=lambda x: x['round'])
        return events