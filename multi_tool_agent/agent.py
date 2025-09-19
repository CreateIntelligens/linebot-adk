# =============================================================================
# agent.py - 多功能 Agent 工具函數模組
# 提供各種工具函數的統一介面，包括天氣查詢、時間查詢、短網址生成、知識庫查詢、影片處理等功能
# =============================================================================

import os
import logging
from typing import Optional

# 設定 logger
logger = logging.getLogger(__name__)

# 全域變數：當前用戶 ID（由 main.py 設定）
current_user_id = None

# =============================================================================
# 阿美族語每日一字功能
# =============================================================================


async def get_amis_word_of_the_day() -> dict:
    """
    獲取阿美族語每日一字

    從阿美族語詞典服務獲取當天的每日一字資訊，包含阿美族語、漢語翻譯和相關說明。

    Returns:
        dict: 包含每日一字資訊的字典
            - status: 狀態 ("success" 或 "error")
            - word: 阿美族語單字 (成功時)
            - translation: 漢語翻譯 (成功時)
            - error_message: 錯誤訊息 (失敗時)
    """
    try:
        from .utils.amis_utils import get_amis_word_of_the_day as get_amis_word_util
        return await get_amis_word_util()
    except Exception as e:
        logger.error(f"阿美族語詞典查詢時發生錯誤: {e}")
        return {"status": "error", "error_message": f"阿美族語詞典查詢時發生錯誤：{str(e)}"}

# =============================================================================
# 搜尋功能
# =============================================================================


# =============================================================================
# 智能搜尋功能 (Agent)
# =============================================================================

async def search_web(query: str) -> dict:
    """
    執行網路搜尋

    使用搜尋代理程式在網路上搜尋相關資訊，提供前5個最相關的結果。

    Args:
        query (str): 搜尋查詢字串

    Returns:
        dict: 搜尋結果字典
            - status: 狀態 ("success" 或 "error")
            - results: 搜尋結果列表 (成功時)
            - error_message: 錯誤訊息 (失敗時)
    """
    try:
        from .agents.search_agent import SearchAgent
        search_agent = SearchAgent()
        result = await search_agent.execute(query=query, max_results=5)
        return result
    except Exception as e:
        logger.error(f"呼叫 SearchAgent 時發生錯誤: {e}")
        return {"status": "error", "error_message": f"搜尋時發生錯誤：{str(e)}"}

# =============================================================================
# 天氣功能 (Utils - 簡單API調用)
# =============================================================================

async def get_weather(city: str) -> dict:
    """
    獲取指定城市的當前天氣資訊

    從天氣API獲取指定城市的即時天氣資料，包括溫度、濕度、風速等資訊。

    Args:
        city (str): 城市名稱，例如 "台北" 或 "Taipei"

    Returns:
        dict: 天氣資訊字典
            - status: 狀態 ("success" 或 "error")
            - temperature: 溫度 (成功時)
            - humidity: 濕度 (成功時)
            - wind_speed: 風速 (成功時)
            - error_message: 錯誤訊息 (失敗時)
    """
    try:
        from .utils.weather_utils import get_weather as get_weather_util
        return await get_weather_util(city)
    except Exception as e:
        logger.error(f"天氣查詢時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢天氣時發生錯誤：{str(e)}"}

async def get_weather_forecast(city: str, days: str) -> dict:
    """獲取指定城市的天氣預報"""
    try:
        from .utils.weather_utils import get_weather_forecast as get_weather_forecast_util
        return await get_weather_forecast_util(city, days)
    except Exception as e:
        logger.error(f"天氣預報查詢時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢天氣預報時發生錯誤：{str(e)}"}

# =============================================================================
# 時間功能 (Utils - 簡單時區映射)
# =============================================================================

async def get_current_time(city: str) -> dict:
    """獲取指定城市的當前時間"""
    try:
        from .utils.time_utils import get_current_time as get_current_time_util
        return await get_current_time_util(city)
    except Exception as e:
        logger.error(f"時間查詢時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢時間時發生錯誤：{str(e)}"}

# =============================================================================
# 短網址功能 (Utils - 純HTTP API調用)
# =============================================================================

async def create_short_url(original_url: str, custom_slug: str) -> dict:
    """建立短網址"""
    try:
        from .utils.http_utils import create_short_url as create_short_url_util
        return await create_short_url_util(url=original_url, slug=custom_slug)
    except Exception as e:
        logger.error(f"建立短網址時發生錯誤: {e}")
        return {"status": "error", "error_message": f"建立短網址時發生錯誤：{str(e)}"}

# =============================================================================
# 知識庫功能
# =============================================================================


async def query_knowledge_base(question: str) -> dict:
    """查詢 hihi 導覽先生知識庫"""
    try:
        from .agents.knowledge_agent import KnowledgeAgent
        knowledge_agent = KnowledgeAgent()
        result = await knowledge_agent.execute(
            knowledge_type="hihi",
            question=question,
            user_id=current_user_id or "anonymous"
        )
        return result
    except Exception as e:
        logger.error(f"查詢 hihi 知識庫時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢 hihi 知識庫時發生錯誤：{str(e)}"}


async def query_set_knowledge_base(question: str) -> dict:
    """查詢 SET 三立電視知識庫"""
    try:
        from .agents.knowledge_agent import KnowledgeAgent
        knowledge_agent = KnowledgeAgent()
        result = await knowledge_agent.execute(
            knowledge_type="set",
            question=question,
            user_id=current_user_id or "anonymous"
        )
        return result
    except Exception as e:
        logger.error(f"查詢 SET 知識庫時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢 SET 知識庫時發生錯誤：{str(e)}"}

# =============================================================================
# 其他功能（需要時再實現）
# =============================================================================


async def video_transcriber(url: str, language: str, summary_words: Optional[int] = None) -> dict:
    """影片轉錄功能"""
    try:
        from .utils.http_utils import process_video_request
        result = await process_video_request(url, language, summary_words)

        # 如果成功產生任務，啟動監控
        if result.get("status") == "success" and "task_id" in result:
            from main import start_task_monitoring
            task_id = result["task_id"]
            user_id = current_user_id or "anonymous"
            start_task_monitoring(task_id, user_id, url)
            logger.info(f"已啟動影片轉錄任務監控: {task_id}")

        return result
    except Exception as e:
        logger.error(f"影片轉錄處理時發生錯誤: {e}")
        return {"status": "error", "error_message": f"影片轉錄處理時發生錯誤：{str(e)}"}


async def call_legal_ai(question: str) -> dict:
    """法律諮詢功能"""
    try:
        from .agents.legal_agent import LegalAgent
        legal_agent = LegalAgent()
        result = await legal_agent.execute(question=question, user_id=current_user_id or "anonymous")
        return result
    except Exception as e:
        logger.error(f"法律諮詢時發生錯誤: {e}")
        return {"status": "error", "error_message": f"法律諮詢時發生錯誤：{str(e)}"}


async def generate_meme(text: str) -> dict:
    """Meme 生成功能"""
    try:
        from .agents.meme_agent import MemeAgent
        meme_agent = MemeAgent()
        result = await meme_agent.execute(meme_idea=text, user_id=current_user_id or "anonymous")
        return result
    except Exception as e:
        logger.error(f"Meme 生成時發生錯誤: {e}")
        return {"status": "error", "error_message": f"Meme 生成時發生錯誤：{str(e)}"}


async def generate_ai_video(prompt: str) -> dict:
    """AI 影片生成功能"""
    try:
        from .agents.comfyui_agent import ComfyUIAgent
        comfyui_agent = ComfyUIAgent()
        result = await comfyui_agent.execute(ai_response=prompt, user_id=current_user_id or "anonymous")

        # 如果成功產生任務，啟動監控
        if result.get("status") == "success" and result.get("data") and "prompt_id" in result["data"]:
            from main import start_task_monitoring
            task_id = result["data"]["prompt_id"]
            user_id = current_user_id or "anonymous"
            start_task_monitoring(task_id, user_id)
            logger.info(f"已啟動 ComfyUI 任務監控: {task_id}")

        return result
    except Exception as e:
        logger.error(f"AI 影片生成時發生錯誤: {e}")
        return {"status": "error", "error_message": f"AI 影片生成時發生錯誤：{str(e)}"}


async def get_task_status(task_id: str) -> dict:
    """通用任務狀態查詢功能 - 調用 ID 查詢 Agent"""
    try:
        from .agents.id_query_agent import IDQueryAgent
        id_query_agent = IDQueryAgent()

        result = await id_query_agent.execute(task_id=task_id, user_id=current_user_id or "anonymous")

        # 如果結果包含影片數據，設定到 main 模組供回覆使用
        if result and result.get("has_video"):
            try:
                import sys
                main_module = sys.modules.get('main')
                if main_module and hasattr(main_module, 'call_agent_async'):
                    main_module.call_agent_async._last_query_result = result
                    logger.info(f"影片數據已設定供回覆使用: {task_id}")
            except Exception as set_error:
                logger.error(f"設定影片數據時發生錯誤: {set_error}")

        return result
    except Exception as e:
        logger.error(f"調用 ID 查詢 Agent 時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢任務狀態時發生錯誤：{str(e)}"}


def before_reply_display_loading_animation(user_id: str, loading_seconds: int = 5):
    """載入動畫功能"""
    try:
        from .utils.line_utils import display_loading_animation
        display_loading_animation(
            line_user_id=user_id, loading_seconds=loading_seconds)
    except Exception as e:
        logger.error(f"載入動畫顯示失敗: {e}")
