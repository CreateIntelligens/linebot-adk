# =============================================================================
# 多功能 Agent 工具函數模組 - 簡化版本
# 直接實現各種功能，不依賴複雜的類別架構
# =============================================================================

import os
import datetime
from zoneinfo import ZoneInfo
import aiohttp
import asyncio
import requests
import json
import logging
import random

# 設定 logger
logger = logging.getLogger(__name__)

# 全域變數：當前用戶 ID（由 main.py 設定）
current_user_id = None

# =============================================================================
# 阿美族語每日一字功能
# =============================================================================


async def get_amis_word_of_the_day() -> dict:
    """阿美族語每日一字功能"""
    try:
        from .agents.amis_agent import AmisAgent
        amis_agent = AmisAgent()
        result = await amis_agent.execute(user_id=current_user_id or "anonymous")
        return result
    except Exception as e:
        logger.error(f"呼叫 AmisAgent 時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"呼叫 AmisAgent 時發生錯誤：{str(e)}"
        }


# =============================================================================
# 天氣功能
# =============================================================================

async def get_weather(city: str) -> dict:
    """獲取指定城市的當前天氣資訊"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://wttr.in/{city}?format=%l:+%c+%t+%h+%w"
            async with session.get(url) as response:
                if response.status == 200:
                    weather_text = await response.text()
                    return {
                        "status": "success",
                        "report": f"🌤️ {weather_text.strip()}",
                        "data": {"city": city}
                    }
                else:
                    return {
                        "status": "error",
                        "error_message": f"無法獲取 {city} 的天氣資訊"
                    }
    except Exception as e:
        logger.error(f"查詢天氣時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"查詢天氣時發生錯誤：{str(e)}"
        }


async def get_weather_forecast(city: str, days: str) -> dict:
    """獲取指定城市的天氣預報"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://wttr.in/{city}?format=%l:+%c+%t+%h+%w&lang=zh"
            async with session.get(url) as response:
                if response.status == 200:
                    weather_text = await response.text()
                    return {
                        "status": "success",
                        "report": f"🔮 未來{days}天天氣預報：\n{weather_text.strip()}",
                        "data": {"city": city, "days": days}
                    }
                else:
                    return {
                        "status": "error",
                        "error_message": f"無法獲取 {city} 的天氣預報"
                    }
    except Exception as e:
        logger.error(f"查詢天氣預報時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"查詢天氣預報時發生錯誤：{str(e)}"
        }

# =============================================================================
# 時間功能
# =============================================================================


async def get_current_time(city: str) -> dict:
    """獲取指定城市的當前時間"""
    try:
        # 城市到時區的映射
        timezone_map = {
            "台北": "Asia/Taipei",
            "東京": "Asia/Tokyo",
            "首爾": "Asia/Seoul",
            "北京": "Asia/Shanghai",
            "香港": "Asia/Hong_Kong",
            "新加坡": "Asia/Singapore",
            "紐約": "America/New_York",
            "洛杉磯": "America/Los_Angeles",
            "倫敦": "Europe/London",
            "巴黎": "Europe/Paris"
        }

        timezone = timezone_map.get(city, "Asia/Taipei")
        tz = ZoneInfo(timezone)
        current_time = datetime.datetime.now(tz)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %z")

        return {
            "status": "success",
            "report": f"{city} 目前時間：{formatted_time}",
            "data": {"city": city, "time": formatted_time}
        }
    except Exception as e:
        logger.error(f"查詢時間時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"查詢時間時發生錯誤：{str(e)}"
        }

# =============================================================================
# 短網址功能
# =============================================================================


async def create_short_url(original_url: str, custom_slug: str) -> dict:
    """建立短網址"""
    try:
        api_token = os.getenv("AIURL_API_TOKEN")
        if not api_token:
            return {
                "status": "error",
                "error_message": "建立短網址時發生錯誤：未設定 API Token"
            }

        api_url = "https://aiurl.tw/api/shorten"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        data = {"url": original_url}
        if custom_slug:
            data["slug"] = custom_slug

        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    short_url = result.get("short_url", "")
                    return {
                        "status": "success",
                        "report": f"短網址建立成功：{short_url}",
                        "data": {"short_url": short_url, "original_url": original_url}
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error_message": f"建立短網址失敗：{error_text}"
                    }
    except Exception as e:
        logger.error(f"建立短網址時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"建立短網址時發生錯誤：{str(e)}"
        }

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
        return {
            "status": "error",
            "error_message": f"查詢 hihi 知識庫時發生錯誤：{str(e)}"
        }


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
        return {
            "status": "error",
            "error_message": f"查詢 SET 知識庫時發生錯誤：{str(e)}"
        }

# =============================================================================
# 其他功能（需要時再實現）
# =============================================================================


async def process_video(url: str, language: str) -> dict:
    """影片處理功能"""
    try:
        from .utils.http_utils import process_video_request
        return await process_video_request(url, language)
    except Exception as e:
        logger.error(f"影片處理時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"影片處理時發生錯誤：{str(e)}"
        }


async def call_legal_ai(question: str) -> dict:
    """法律諮詢功能"""
    try:
        from .agents.legal_agent import LegalAgent
        legal_agent = LegalAgent()
        result = await legal_agent.execute(question=question, user_id=current_user_id or "anonymous")
        return result.to_dict()
    except Exception as e:
        logger.error(f"法律諮詢時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"法律諮詢時發生錯誤：{str(e)}"
        }


async def generate_meme(text: str) -> dict:
    """Meme 生成功能"""
    try:
        from .agents.meme_agent import MemeAgent
        meme_agent = MemeAgent()
        result = await meme_agent.execute(meme_idea=text, user_id=current_user_id or "anonymous")
        return result.to_dict()
    except Exception as e:
        logger.error(f"Meme 生成時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"Meme 生成時發生錯誤：{str(e)}"
        }


async def generate_ai_video(prompt: str) -> dict:
    """AI 影片生成功能"""
    try:
        from .agents.comfyui_agent import ComfyUIAgent
        comfyui_agent = ComfyUIAgent()
        result = await comfyui_agent.execute(ai_response=prompt, user_id=current_user_id or "anonymous")
        return result.to_dict()
    except Exception as e:
        logger.error(f"AI 影片生成時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"AI 影片生成時發生錯誤：{str(e)}"
        }


async def get_task_status(task_id: str) -> dict:
    """任務狀態查詢功能"""
    try:
        from .utils.video_utils import process_video_task
        return await process_video_task(task_id)
    except Exception as e:
        logger.error(f"查詢任務狀態時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"查詢任務狀態時發生錯誤：{str(e)}"
        }


def before_reply_display_loading_animation(user_id: str, loading_seconds: int = 5):
    """載入動畫功能"""
    try:
        import os
        import requests

        channel_access_token = os.getenv("ChannelAccessToken")
        if not channel_access_token:
            logger.warning("載入動畫功能需要 ChannelAccessToken")
            return

        url = f"https://api.line.me/v2/bot/chat/loading/start"
        headers = {
            "Authorization": f"Bearer {channel_access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "chatId": user_id,
            "loadingSeconds": loading_seconds
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 202]:
            logger.info(f"載入動畫啟動成功: 用戶 {user_id}, {loading_seconds} 秒")
        else:
            logger.warning(f"載入動畫啟動失敗: {response.status_code}")

    except Exception as e:
        logger.error(f"載入動畫顯示失敗: {e}")
