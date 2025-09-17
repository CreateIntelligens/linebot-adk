# =============================================================================
# 天氣查詢工具函數
# 使用 wttr.in API 提供天氣資訊
# =============================================================================

import aiohttp
import logging

logger = logging.getLogger(__name__)


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