"""
Agents 模組
包含所有特定功能的 Agent 實作

此模組包含重構後的專業 Agent 類別，每個 Agent 負責特定功能領域：
- WeatherAgent: 天氣查詢和預報
- TimeAgent: 時間查詢功能
- KnowledgeAgent: 知識庫查詢服務（hihi先生、SET三立）

使用方式：
    from multi_tool_agent.agents import WeatherAgent, TimeAgent, KnowledgeAgent

    # 建立 agent 實例
    weather_agent = WeatherAgent()
    result = await weather_agent.get_weather("台北")
"""

# 匯入重構後的 Agent 類別
from .weather_agent import WeatherAgent
from .time_agent import TimeAgent
from .knowledge_agent import KnowledgeAgent

# 定義公開的 Agent 類別
__all__ = [
    'WeatherAgent',
    'TimeAgent',
    'KnowledgeAgent'
]