"""
Multi-Tool Agent 模組
包含所有功能工具和重構後的 Agent 類別

此模組提供向後相容的匯入介面，確保 main.py 中的所有匯入仍然有效。
同時也提供對新重構 Agent 類別的統一存取點。

使用方式：
    # 向後相容的函數匯入（main.py 使用）
    from multi_tool_agent.agent import get_weather, get_current_time, ...

    # 新的 Agent 類別匯入（進階使用）
    from multi_tool_agent import WeatherAgent, TimeAgent, KnowledgeAgent

    # 或者從子模組匯入
    from multi_tool_agent.agents import WeatherAgent, TimeAgent, KnowledgeAgent
"""

# 匯入所有重構後的 Agent 類別 (暫時註解，等BaseAgent移除完成)
# from .agents.weather_agent import WeatherAgent
# from .agents.time_agent import TimeAgent
# from .agents.knowledge_agent import KnowledgeAgent

# 匯入原有的工具函數（向後相容性）
from .agent import (
    # 天氣相關功能
    get_weather,
    get_weather_forecast,

    # 時間查詢功能
    get_current_time,

    # 網址工具
    create_short_url,

    # 知識庫查詢功能
    query_knowledge_base,
    query_set_knowledge_base,

    # 影片處理功能
    video_transcriber,

    # AI 服務功能
    call_legal_ai,
    generate_meme,
    generate_ai_video,

    # 使用者體驗功能
    before_reply_display_loading_animation,
)

# 匯入其他已存在的 agent 模組 (暫時註解，等BaseAgent移除完成)
# from .agents.legal_agent import LegalAgent
# from .agents.meme_agent import MemeAgent
# from .agents.comfyui_agent import ComfyUIAgent

# 定義公開的 API
__all__ = [
    # 重構後的 Agent 類別
    'WeatherAgent',
    'TimeAgent',
    'KnowledgeAgent',
    'LegalAgent',
    'MemeAgent',
    'ComfyUIAgent',

    # 向後相容的工具函數
    'get_weather',
    'get_weather_forecast',
    'get_current_time',
    'create_short_url',
    'query_knowledge_base',
    'query_set_knowledge_base',
    'video_transcriber',
    'call_legal_ai',
    'generate_meme',
    'generate_ai_video',
    'before_reply_display_loading_animation',
]
