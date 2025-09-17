# =============================================================================
# 多功能 Agent 工具函數模組 - 簡化版本
# =============================================================================

import os
import logging

# 設定 logger
logger = logging.getLogger(__name__)

# 全域變數：當前用戶 ID（由 main.py 設定）
current_user_id = None

# =============================================================================
# 阿美族語每日一字功能
# =============================================================================


async def get_amis_word_of_the_day() -> dict:
    """阿美族語每日一字功能 (Utils - 詞典查詢)"""
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
    """網路搜尋功能"""
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
    """獲取指定城市的當前天氣資訊"""
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
        return result.to_dict()
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
        return result.to_dict()
    except Exception as e:
        logger.error(f"查詢 SET 知識庫時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢 SET 知識庫時發生錯誤：{str(e)}"}

# =============================================================================
# 其他功能（需要時再實現）
# =============================================================================


async def video_transcriber(url: str, language: str) -> dict:
    """影片轉錄功能"""
    try:
        from .utils.http_utils import process_video_request
        return await process_video_request(url, language)
    except Exception as e:
        logger.error(f"影片轉錄處理時發生錯誤: {e}")
        return {"status": "error", "error_message": f"影片轉錄處理時發生錯誤：{str(e)}"}


async def call_legal_ai(question: str) -> dict:
    """法律諮詢功能"""
    try:
        from .agents.legal_agent import LegalAgent
        legal_agent = LegalAgent()
        result = await legal_agent.execute(question=question, user_id=current_user_id or "anonymous")
        return result.to_dict()
    except Exception as e:
        logger.error(f"法律諮詢時發生錯誤: {e}")
        return {"status": "error", "error_message": f"法律諮詢時發生錯誤：{str(e)}"}


async def generate_meme(text: str) -> dict:
    """Meme 生成功能"""
    try:
        from .agents.meme_agent import MemeAgent
        meme_agent = MemeAgent()
        result = await meme_agent.execute(meme_idea=text, user_id=current_user_id or "anonymous")
        return result.to_dict()
    except Exception as e:
        logger.error(f"Meme 生成時發生錯誤: {e}")
        return {"status": "error", "error_message": f"Meme 生成時發生錯誤：{str(e)}"}


async def generate_ai_video(prompt: str) -> dict:
    """AI 影片生成功能"""
    try:
        from .agents.comfyui_agent import ComfyUIAgent
        comfyui_agent = ComfyUIAgent()
        result = await comfyui_agent.execute(ai_response=prompt, user_id=current_user_id or "anonymous")
        return result.to_dict()
    except Exception as e:
        logger.error(f"AI 影片生成時發生錯誤: {e}")
        return {"status": "error", "error_message": f"AI 影片生成時發生錯誤：{str(e)}"}


async def get_task_status(task_id: str) -> dict:
    """任務狀態查詢功能"""
    try:
        from .utils.video_utils import process_video_task
        return await process_video_task(task_id)
    except Exception as e:
        logger.error(f"查詢任務狀態時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢任務狀態時發生錯誤：{str(e)}"}


def before_reply_display_loading_animation(user_id: str, loading_seconds: int = 5):
    """載入動畫功能"""
    try:
        from .utils.line_utils import display_loading_animation
        display_loading_animation(
            line_user_id=user_id, loading_seconds=loading_seconds)
    except Exception as e:
        logger.error(f"載入動畫顯示失敗: {e}")
