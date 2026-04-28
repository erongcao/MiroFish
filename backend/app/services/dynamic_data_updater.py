"""
Dynamic Data Updater - 动态数据更新器
定期更新GDP、军费、贸易等数据
"""

import json
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class DataSnapshot:
    """年度数据快照"""
    year: int
    country_id: str
    gdp_usd: float
    gdp_growth: float
    military_spending_usd: float
    population_millions: float
    inflation_rate: float = 0.0
    unemployment_rate: float = 0.0
    debt_to_gdp: float = 0.0
    timestamp: str = ""

# 历史数据快照 (2020-2024)
HISTORICAL_SNAPSHOTS: Dict[int, Dict[str, Dict]] = {
    2020: {
        "usa": {"gdp_usd": 21.06, "gdp_growth": -2.2, "military_spending_usd": 778.0, "population_millions": 331.0},
        "china": {"gdp_usd": 14.72, "gdp_growth": 2.2, "military_spending_usd": 252.0, "population_millions": 1411.0},
        "russia": {"gdp_usd": 1.48, "gdp_growth": -2.7, "military_spending_usd": 65.0, "population_millions": 144.0},
        "eu": {"gdp_usd": 15.29, "gdp_growth": -6.1, "military_spending_usd": 225.0, "population_millions": 447.0},
        "iran": {"gdp_usd": 0.23, "gdp_growth": 1.3, "military_spending_usd": 15.0, "population_millions": 84.0},
        "japan": {"gdp_usd": 5.04, "gdp_growth": -4.1, "military_spending_usd": 47.0, "population_millions": 126.0},
        "india": {"gdp_usd": 2.67, "gdp_growth": -5.8, "military_spending_usd": 64.0, "population_millions": 1380.0},
        "uk": {"gdp_usd": 2.76, "gdp_growth": -11.0, "military_spending_usd": 59.0, "population_millions": 67.0},
        "germany": {"gdp_usd": 3.89, "gdp_growth": -3.7, "military_spending_usd": 48.0, "population_millions": 83.0},
        "brazil": {"gdp_usd": 1.44, "gdp_growth": -3.3, "military_spending_usd": 18.0, "population_millions": 212.0},
        "france": {"gdp_usd": 2.63, "gdp_growth": -7.5, "military_spending_usd": 47.0, "population_millions": 67.0},
        "south_korea": {"gdp_usd": 1.64, "gdp_growth": -0.7, "military_spending_usd": 38.0, "population_millions": 51.0},
        "israel": {"gdp_usd": 0.40, "gdp_growth": -1.9, "military_spending_usd": 18.0, "population_millions": 9.2},
        "saudi_arabia": {"gdp_usd": 0.70, "gdp_growth": -4.1, "military_spending_usd": 56.0, "population_millions": 35.0},
        "turkey": {"gdp_usd": 0.72, "gdp_growth": 1.9, "military_spending_usd": 15.0, "population_millions": 84.0},
    },
    2021: {
        "usa": {"gdp_usd": 23.32, "gdp_growth": 5.9, "military_spending_usd": 801.0, "population_millions": 332.0},
        "china": {"gdp_usd": 17.73, "gdp_growth": 8.4, "military_spending_usd": 270.0, "population_millions": 1412.0},
        "russia": {"gdp_usd": 1.78, "gdp_growth": 5.6, "military_spending_usd": 66.0, "population_millions": 145.0},
        "eu": {"gdp_usd": 17.09, "gdp_growth": 7.0, "military_spending_usd": 230.0, "population_millions": 447.0},
        "iran": {"gdp_usd": 0.36, "gdp_growth": 4.3, "military_spending_usd": 17.0, "population_millions": 85.0},
        "japan": {"gdp_usd": 4.94, "gdp_growth": 2.1, "military_spending_usd": 48.0, "population_millions": 125.0},
        "india": {"gdp_usd": 3.18, "gdp_growth": 9.7, "military_spending_usd": 71.0, "population_millions": 1396.0},
        "uk": {"gdp_usd": 3.13, "gdp_growth": 7.6, "military_spending_usd": 62.0, "population_millions": 67.0},
        "germany": {"gdp_usd": 4.26, "gdp_growth": 3.2, "military_spending_usd": 50.0, "population_millions": 83.0},
        "brazil": {"gdp_usd": 1.61, "gdp_growth": 5.0, "military_spending_usd": 19.0, "population_millions": 214.0},
        "france": {"gdp_usd": 2.96, "gdp_growth": 6.4, "military_spending_usd": 48.0, "population_millions": 67.0},
        "south_korea": {"gdp_usd": 1.80, "gdp_growth": 4.3, "military_spending_usd": 40.0, "population_millions": 51.0},
        "israel": {"gdp_usd": 0.48, "gdp_growth": 8.6, "military_spending_usd": 19.0, "population_millions": 9.4},
        "saudi_arabia": {"gdp_usd": 0.87, "gdp_growth": 3.9, "military_spending_usd": 58.0, "population_millions": 35.0},
        "turkey": {"gdp_usd": 0.82, "gdp_growth": 11.4, "military_spending_usd": 17.0, "population_millions": 85.0},
    },
    2022: {
        "usa": {"gdp_usd": 25.46, "gdp_growth": 2.1, "military_spending_usd": 821.0, "population_millions": 333.0},
        "china": {"gdp_usd": 17.96, "gdp_growth": 3.0, "military_spending_usd": 292.0, "population_millions": 1411.0},
        "russia": {"gdp_usd": 2.24, "gdp_growth": -2.1, "military_spending_usd": 86.0, "population_millions": 145.0},
        "eu": {"gdp_usd": 16.74, "gdp_growth": 3.5, "military_spending_usd": 240.0, "population_millions": 447.0},
        "iran": {"gdp_usd": 0.34, "gdp_growth": 4.2, "military_spending_usd": 20.0, "population_millions": 86.0},
        "japan": {"gdp_usd": 4.23, "gdp_growth": 1.0, "military_spending_usd": 49.0, "population_millions": 125.0},
        "india": {"gdp_usd": 3.39, "gdp_growth": 7.0, "military_spending_usd": 76.0, "population_millions": 1417.0},
        "uk": {"gdp_usd": 3.07, "gdp_growth": 4.3, "military_spending_usd": 63.0, "population_millions": 67.0},
        "germany": {"gdp_usd": 4.08, "gdp_growth": 1.9, "military_spending_usd": 51.0, "population_millions": 84.0},
        "brazil": {"gdp_usd": 1.92, "gdp_growth": 2.9, "military_spending_usd": 19.0, "population_millions": 215.0},
        "france": {"gdp_usd": 2.78, "gdp_growth": 2.5, "military_spending_usd": 49.0, "population_millions": 68.0},
        "south_korea": {"gdp_usd": 1.67, "gdp_growth": 2.6, "military_spending_usd": 42.0, "population_millions": 52.0},
        "israel": {"gdp_usd": 0.50, "gdp_growth": 6.5, "military_spending_usd": 21.0, "population_millions": 9.5},
        "saudi_arabia": {"gdp_usd": 1.01, "gdp_growth": 8.7, "military_spending_usd": 62.0, "population_millions": 36.0},
        "turkey": {"gdp_usd": 0.91, "gdp_growth": 5.5, "military_spending_usd": 18.0, "population_millions": 85.0},
    },
    2023: {
        "usa": {"gdp_usd": 27.36, "gdp_growth": 2.5, "military_spending_usd": 886.0, "population_millions": 335.0},
        "china": {"gdp_usd": 17.79, "gdp_growth": 5.2, "military_spending_usd": 296.0, "population_millions": 1412.0},
        "russia": {"gdp_usd": 2.02, "gdp_growth": 3.6, "military_spending_usd": 109.0, "population_millions": 144.0},
        "eu": {"gdp_usd": 18.35, "gdp_growth": 1.8, "military_spending_usd": 300.0, "population_millions": 448.0},
        "iran": {"gdp_usd": 0.40, "gdp_growth": 3.0, "military_spending_usd": 25.0, "population_millions": 87.0},
        "japan": {"gdp_usd": 4.23, "gdp_growth": 1.9, "military_spending_usd": 50.0, "population_millions": 125.0},
        "india": {"gdp_usd": 3.73, "gdp_growth": 6.3, "military_spending_usd": 81.0, "population_millions": 1428.0},
        "uk": {"gdp_usd": 3.33, "gdp_growth": 0.5, "military_spending_usd": 65.0, "population_millions": 67.0},
        "germany": {"gdp_usd": 4.46, "gdp_growth": -0.3, "military_spending_usd": 55.0, "population_millions": 84.0},
        "brazil": {"gdp_usd": 2.13, "gdp_growth": 2.9, "military_spending_usd": 20.0, "population_millions": 216.0},
        "france": {"gdp_usd": 3.05, "gdp_growth": 0.9, "military_spending_usd": 53.0, "population_millions": 68.0},
        "south_korea": {"gdp_usd": 1.71, "gdp_growth": 3.1, "military_spending_usd": 45.0, "population_millions": 52.0},
        "israel": {"gdp_usd": 0.52, "gdp_growth": 3.0, "military_spending_usd": 24.0, "population_millions": 9.8},
        "saudi_arabia": {"gdp_usd": 1.06, "gdp_growth": 0.8, "military_spending_usd": 75.0, "population_millions": 36.0},
        "turkey": {"gdp_usd": 1.15, "gdp_growth": 4.5, "military_spending_usd": 20.0, "population_millions": 85.0},
    },
    2024: {
        # 估计值 (实际数据可能略有差异)
        "usa": {"gdp_usd": 28.0, "gdp_growth": 2.8, "military_spending_usd": 920.0, "population_millions": 336.0},
        "china": {"gdp_usd": 18.3, "gdp_growth": 4.8, "military_spending_usd": 310.0, "population_millions": 1410.0},
        "russia": {"gdp_usd": 2.1, "gdp_growth": 3.6, "military_spending_usd": 140.0, "population_millions": 144.0},
        "eu": {"gdp_usd": 19.0, "gdp_growth": 1.5, "military_spending_usd": 320.0, "population_millions": 450.0},
        "iran": {"gdp_usd": 0.42, "gdp_growth": 3.5, "military_spending_usd": 28.0, "population_millions": 88.0},
        "japan": {"gdp_usd": 4.3, "gdp_growth": 1.2, "military_spending_usd": 52.0, "population_millions": 124.0},
        "india": {"gdp_usd": 4.0, "gdp_growth": 6.5, "military_spending_usd": 86.0, "population_millions": 1440.0},
        "uk": {"gdp_usd": 3.4, "gdp_growth": 0.7, "military_spending_usd": 68.0, "population_millions": 68.0},
        "germany": {"gdp_usd": 4.5, "gdp_growth": 0.2, "military_spending_usd": 58.0, "population_millions": 84.0},
        "brazil": {"gdp_usd": 2.2, "gdp_growth": 3.2, "military_spending_usd": 21.0, "population_millions": 218.0},
        "france": {"gdp_usd": 3.1, "gdp_growth": 1.0, "military_spending_usd": 55.0, "population_millions": 68.0},
        "south_korea": {"gdp_usd": 1.8, "gdp_growth": 2.5, "military_spending_usd": 48.0, "population_millions": 52.0},
        "israel": {"gdp_usd": 0.55, "gdp_growth": 2.5, "military_spending_usd": 27.0, "population_millions": 10.0},
        "saudi_arabia": {"gdp_usd": 1.1, "gdp_growth": 1.5, "military_spending_usd": 78.0, "population_millions": 37.0},
        "turkey": {"gdp_usd": 1.2, "gdp_growth": 3.2, "military_spending_usd": 22.0, "population_millions": 86.0},
    },
}


class DynamicDataUpdater:
    """动态数据更新器"""
    
    def __init__(self, update_callback: Optional[Callable] = None):
        self.current_year = 2024
        self.historical_data = HISTORICAL_SNAPSHOTS
        self.update_callback = update_callback  # 数据更新回调
        
        # 跟踪数据变化
        self.changes_log: List[Dict] = []
    
    def get_year(self, country_id: str, year: int) -> Optional[Dict]:
        """获取特定国家在特定年份的数据"""
        if year in self.historical_data:
            return self.historical_data[year].get(country_id)
        return None
    
    def get_latest(self, country_id: str) -> Dict:
        """获取最新数据"""
        return self.get_year(country_id, self.current_year) or {}
    
    def get_historical(self, country_id: str, start_year: int, end_year: int) -> List[Dict]:
        """获取历史数据"""
        result = []
        for year in range(start_year, end_year + 1):
            data = self.get_year(country_id, year)
            if data:
                result.append({"year": year, **data})
        return result
    
    def calculate_trend(self, country_id: str, metric: str, years: int = 5) -> float:
        """计算某个指标的趋势"""
        data = self.get_historical(country_id, self.current_year - years, self.current_year)
        if len(data) < 2:
            return 0.0
        
        values = [d.get(metric, 0) for d in data]
        if values[-1] == 0:
            return 0.0
        
        # 年均增长率
        growth = (values[-1] - values[0]) / values[0] / len(values)
        return growth
    
    def update_to_year(self, year: int, countries: List[str]) -> Dict[str, Dict]:
        """将数据更新到指定年份"""
        if year not in self.historical_data:
            print(f"[DynamicUpdater] 警告: {year}年数据不存在，使用最近可用年份")
            year = max(self.historical_data.keys())
        
        updates = {}
        for country_id in countries:
            old_data = self.get_latest(country_id)
            new_data = self.get_year(country_id, year) or old_data
            
            if old_data and new_data:
                # 计算变化
                change = {
                    "gdp_change": new_data.get("gdp_usd", 0) - old_data.get("gdp_usd", 0),
                    "military_change": new_data.get("military_spending_usd", 0) - old_data.get("military_spending_usd", 0),
                    "gdp_growth_change": new_data.get("gdp_growth", 0) - old_data.get("gdp_growth", 0),
                }
                
                # 记录变化
                self.changes_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "from_year": self.current_year,
                    "to_year": year,
                    "country_id": country_id,
                    "change": change,
                })
                
                updates[country_id] = {
                    "old": old_data,
                    "new": new_data,
                    "change": change,
                }
        
        self.current_year = year
        
        # 触发回调
        if self.update_callback:
            self.update_callback(updates)
        
        return updates
    
    def simulate_future(self, country_id: str, years_ahead: int, 
                       growth_scenario: str = "baseline") -> Dict:
        """模拟未来数据"""
        current = self.get_latest(country_id)
        if not current:
            return {}
        
        # 增长情景
        scenarios = {
            "baseline": 0.03,      # 基准 3%
            "optimistic": 0.05,   # 乐观 5%
            "pessimistic": 0.01,  # 悲观 1%
            "crisis": -0.02,      # 危机 -2%
        }
        
        growth_rate = scenarios.get(growth_scenario, 0.03)
        
        future = {
            "year": self.current_year + years_ahead,
            "country_id": country_id,
            "gdp_usd": current.get("gdp_usd", 0) * (1 + growth_rate) ** years_ahead,
            "gdp_growth": growth_rate * 100,
            "military_spending_usd": current.get("military_spending_usd", 0) * (1 + growth_rate * 0.8) ** years_ahead,
            "population_millions": current.get("population_millions", 0) * (1 + 0.01) ** years_ahead,
            "scenario": growth_scenario,
        }
        
        return future
    
    def export_history(self, country_id: str) -> str:
        """导出某个国家的完整历史数据"""
        data = self.get_historical(country_id, 2020, self.current_year)
        return json.dumps(data, indent=2)
    
    def get_statistics(self) -> Dict:
        """获取数据统计"""
        stats = {
            "current_year": self.current_year,
            "available_years": list(self.historical_data.keys()),
            "countries_tracked": len(self.historical_data.get(self.current_year, {})),
            "total_changes_logged": len(self.changes_log),
        }
        
        # 计算全球GDP
        if self.current_year in self.historical_data:
            total_gdp = sum(
                d.get("gdp_usd", 0) 
                for d in self.historical_data[self.current_year].values()
            )
            total_military = sum(
                d.get("military_spending_usd", 0) 
                for d in self.historical_data[self.current_year].values()
            )
            stats["total_global_gdp"] = total_gdp
            stats["total_global_military_spending"] = total_military
        
        return stats


# 全局实例
dynamic_updater = DynamicDataUpdater()

if __name__ == "__main__":
    updater = DynamicDataUpdater()
    
    print("=== 动态数据更新器测试 ===\n")
    
    # 统计
    stats = updater.get_statistics()
    print(f"当前年份: {stats['current_year']}")
    print(f"可用年份: {stats['available_years']}")
    print(f"追踪国家数: {stats['countries_tracked']}")
    print(f"总全球GDP: ${stats['total_global_gdp']:.2f}T")
    print(f"总军费: ${stats['total_global_military_spending']:.2f}B")
    
    print("\n=== GDP趋势 (2020-2024) ===")
    for country_id in ["usa", "china", "russia", "india"]:
        trend = updater.calculate_trend(country_id, "gdp_usd")
        print(f"{country_id}: {trend*100:.1f}%/年")
    
    print("\n=== 军费增长 ===")
    for country_id in ["usa", "china", "russia"]:
        trend = updater.calculate_trend(country_id, "military_spending_usd")
        print(f"{country_id}: {trend*100:.1f}%/年")
    
    print("\n=== 美国未来5年预测 ===")
    future = updater.simulate_future("usa", 5, "baseline")
    print(f"GDP: ${future.get('gdp_usd', 0):.2f}T (年增长 {future.get('gdp_growth', 0):.1f}%)")
    
    print("\n=== 历史数据导出 (俄罗斯) ===")
    print(updater.export_history("russia"))
    
    print("\n=== 数据变化日志 ===")
    updater.update_to_year(2022, ["usa", "china"])
    for log in updater.changes_log[-2:]:
        print(f"  {log['country_id']}: GDP变化 ${log['change']['gdp_change']:.2f}T")
