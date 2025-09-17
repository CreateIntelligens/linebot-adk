# =============================================================================
# 時間查詢工具函數
# 提供世界各城市的當前時間查詢
# =============================================================================

import datetime
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


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
            "report": f"🕐 {city} 目前時間：{formatted_time}",
            "data": {"city": city, "time": formatted_time}
        }
    except Exception as e:
        logger.error(f"查詢時間時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"查詢時間時發生錯誤：{str(e)}"
        }