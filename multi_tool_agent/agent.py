# =============================================================================
# agent.py - 工具函數統一接口模組
# 提供統一的工具函數介面，整合 agents 和 utils
# =============================================================================

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全域變數：當前用戶 ID（由 main.py 設定）
current_user_id = None

# =============================================================================
# 簡單工具 - 直接從 utils 導入（無需包裝）
# =============================================================================

from .utils.weather_utils import get_weather, get_weather_forecast
from .utils.time_utils import get_current_time
from .utils.amis_utils import get_amis_word_of_the_day
from line import display_loading_animation as before_reply_display_loading_animation

# 短網址需要重新映射參數名稱，所以保留包裝
async def create_short_url(original_url: str, custom_slug: str) -> dict:
    """建立短網址"""
    try:
        from .utils.http_utils import create_short_url as create_short_url_util
        return await create_short_url_util(url=original_url, slug=custom_slug)
    except Exception as e:
        logger.error(f"建立短網址時發生錯誤: {e}")
        return {"status": "error", "error_message": f"建立短網址時發生錯誤：{str(e)}"}

# =============================================================================
# Agent 包裝函數 - 隱藏 Agent 實例化和 user_id 處理
# =============================================================================

async def search_web(query: str) -> dict:
    """執行網路搜尋"""
    try:
        from .agents.search_agent import SearchAgent
        agent = SearchAgent()
        return await agent.execute(query=query, max_results=5)
    except Exception as e:
        logger.error(f"網路搜尋時發生錯誤: {e}")
        return {"status": "error", "error_message": f"搜尋時發生錯誤：{str(e)}"}


async def query_knowledge_base(question: str) -> dict:
    """查詢 hihi 導覽先生知識庫"""
    try:
        from .agents.knowledge_agent import KnowledgeAgent
        agent = KnowledgeAgent()
        return await agent.execute(
            knowledge_type="hihi",
            question=question,
            user_id=current_user_id or "anonymous"
        )
    except Exception as e:
        logger.error(f"查詢 hihi 知識庫時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢 hihi 知識庫時發生錯誤：{str(e)}"}


async def query_set_knowledge_base(question: str) -> dict:
    """查詢 SET 三立電視知識庫"""
    try:
        from .agents.knowledge_agent import KnowledgeAgent
        agent = KnowledgeAgent()
        return await agent.execute(
            knowledge_type="set",
            question=question,
            user_id=current_user_id or "anonymous"
        )
    except Exception as e:
        logger.error(f"查詢 SET 知識庫時發生錯誤: {e}")
        return {"status": "error", "error_message": f"查詢 SET 知識庫時發生錯誤：{str(e)}"}


async def call_legal_ai(question: str) -> dict:
    """法律諮詢功能"""
    try:
        from .agents.legal_agent import LegalAgent
        agent = LegalAgent()
        return await agent.execute(
            question=question,
            user_id=current_user_id or "anonymous"
        )
    except Exception as e:
        logger.error(f"法律諮詢時發生錯誤: {e}")
        return {"status": "error", "error_message": f"法律諮詢時發生錯誤：{str(e)}"}


async def generate_meme(text: str) -> dict:
    """Meme 生成功能"""
    try:
        from .agents.meme_agent import MemeAgent
        agent = MemeAgent()
        return await agent.execute(
            meme_idea=text,
            user_id=current_user_id or "anonymous"
        )
    except Exception as e:
        logger.error(f"Meme 生成時發生錯誤: {e}")
        return {"status": "error", "error_message": f"Meme 生成時發生錯誤：{str(e)}"}


async def draw_tarot_cards(question: str) -> dict:
    """
    執行塔羅牌占卜,抽取三張牌(過去、現在、未來)並提供專業解讀。

    Args:
        question: 使用者想要占卜的問題

    Returns:
        dict: 包含占卜結果、牌卡解讀和圖片的字典
    """
    try:
        from .agents.tarot_agent import TarotAgent
        agent = TarotAgent()
        return await agent.execute(
            question=question,
            user_id=current_user_id or "anonymous"
        )
    except Exception as e:
        logger.error(f"塔羅牌占卜時發生錯誤: {e}")
        return {"status": "error", "error_message": f"塔羅牌占卜時發生錯誤：{str(e)}"}

# =============================================================================
# 複雜工具 - 有額外業務邏輯（任務監控、數據處理等）
# =============================================================================

async def video_transcriber(url: str, language: str, summary_words: Optional[int] = None) -> dict:
    """
    影片轉錄功能（帶任務監控）

    處理影片轉錄請求並啟動背景任務監控。
    """
    try:
        from .utils.http_utils import process_video_request
        result = await process_video_request(url, language, summary_words)

        # 額外邏輯：如果成功產生任務，啟動監控
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


async def generate_ai_video(prompt: str) -> dict:
    """
    AI 影片生成功能（帶任務監控）

    生成 AI 影片並啟動背景任務監控。
    """
    try:
        from .agents.comfyui_agent import ComfyUIAgent
        agent = ComfyUIAgent()
        result = await agent.execute(
            ai_response=prompt,
            user_id=current_user_id or "anonymous"
        )

        # 額外邏輯：如果成功產生任務，啟動監控
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
    """
    通用任務狀態查詢功能（帶影片數據處理）

    查詢任務狀態，如果有影片則自動設定供回覆使用。
    """
    try:
        from .agents.id_query_agent import IDQueryAgent
        agent = IDQueryAgent()
        result = await agent.execute(
            task_id=task_id,
            user_id=current_user_id or "anonymous"
        )

        # 額外邏輯：如果結果包含影片數據，設定到 main 模組供回覆使用
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
