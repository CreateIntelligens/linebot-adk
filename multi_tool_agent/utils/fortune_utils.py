# =============================================================================
# fortune_utils.py - 運勢相關工具模組
# 提供基於 API Ninjas 的星座運勢查詢功能，包含確定性星座選擇演算法
# 依賴項目：aiohttp, hashlib, os, datetime
# 主要功能：每日運勢取得、星座對應、時段化運勢計算
# =============================================================================

import aiohttp
import logging
import hashlib
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# API 設定 - API Ninjas Horoscope API 相關配置
# API 端點 URL，用於取得星座運勢資料
HOROSCOPE_API_URL = "https://api.api-ninjas.com/v1/horoscope"
# API 金鑰，從環境變數取得，預設空字串
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY", "")

# 星座資料 - 支援的 12 個西洋星座
# 英文名稱列表，用於 API 請求參數
ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

# 星座中英文對照表 - 用於顯示中文星座名稱
# key: 英文星座名稱, value: 中文星座名稱
ZODIAC_NAMES_ZH = {
    "aries": "牡羊座",
    "taurus": "金牛座",
    "gemini": "雙子座",
    "cancer": "巨蟹座",
    "leo": "獅子座",
    "virgo": "處女座",
    "libra": "天秤座",
    "scorpio": "天蠍座",
    "sagittarius": "射手座",
    "capricorn": "摩羯座",
    "aquarius": "水瓶座",
    "pisces": "雙魚座"
}


async def get_fortune_cookie(user_id: str, category: str = "cookie") -> dict:
    """
    取得每日運勢（基於用戶 ID + 日期 + 時段的確定性星座選擇演算法）。

    實作確定性星座選擇機制，確保同一用戶在相同時段內獲得一致的運勢結果。
    演算法細節：
    - 將 24 小時分割為 12 個時段（每時段 2 小時）
    - 使用 MD5 hash(user_id + date + time_slot) % 12 計算星座索引
    - 透過 API Ninjas 取得對應星座的運勢內容

    Args:
        user_id (str): 用戶唯一識別碼，用於運勢計算的種子值
        category (str, optional): 保留參數以維持 API 相容性，預設值為 "cookie"

    Returns:
        dict: 運勢查詢結果
            成功時: {"status": "success", "report": "格式化的運勢內容"}
            失敗時: {"status": "error", "error_message": "錯誤描述訊息"}

    Raises:
        無直接拋出異常，所有錯誤均以字典形式返回

    Example:
        >>> result = await get_fortune_cookie("user123")
        >>> print(result["status"])
        success
        >>> print(result["report"])  # doctest: +SKIP
        🔮 現在運勢
        <BLANKLINE>
        貴人：獅子座
        <BLANKLINE>
        [運勢內容...]

    Note:
        - 需要設定 API_NINJAS_KEY 環境變數
        - 使用台北時區 (UTC+8) 作為時間基準
        - 運勢結果在同一時段內對同一用戶保持一致
    """
    try:
        # 檢查 API Key
        if not API_NINJAS_KEY:
            logger.error("未設定 API_NINJAS_KEY 環境變數")
            return {
                "status": "error",
                "error_message": "運勢服務未正確配置"
            }

        # 取得台北時區當前時間
        taipei_tz = timezone(timedelta(hours=8))
        now = datetime.now(taipei_tz)
        today = now.strftime('%Y-%m-%d')
        current_hour = now.hour

        # 計算時段 (0-11)：每 2 小時一個時段
        time_slot = current_hour // 2

        # 使用 user_id + date + time_slot 計算 hash
        hash_input = f"{user_id}{today}{time_slot}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        zodiac_index = hash_value % 12

        # 選擇星座
        zodiac_sign = ZODIAC_SIGNS[zodiac_index]
        zodiac_name_zh = ZODIAC_NAMES_ZH.get(zodiac_sign, zodiac_sign)

        logger.info(f"用戶 {user_id[:8]}... 時段 {time_slot} ({current_hour}:xx) → {zodiac_name_zh} ({zodiac_sign})")

        # 呼叫 API Ninjas Horoscope API
        headers = {"X-Api-Key": API_NINJAS_KEY}
        params = {"zodiac": zodiac_sign}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                HOROSCOPE_API_URL,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    horoscope_text = data.get("horoscope", "")
                    date = data.get("date", "")

                    if horoscope_text:
                        logger.info(f"成功取得 {zodiac_name_zh} 運勢")
                        return {
                            "status": "success",
                            "report": f"🔮 現在運勢\n\n貴人：{zodiac_name_zh}\n\n{horoscope_text}"
                        }
                    else:
                        logger.error("API 回應中沒有運勢內容")
                        return {
                            "status": "error",
                            "error_message": "無法取得運勢內容"
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"API 請求失敗: HTTP {response.status}, {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"運勢 API 請求失敗 (HTTP {response.status})"
                    }

    except aiohttp.ClientError as e:
        logger.error(f"網路請求錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"網路連線錯誤：{str(e)}"
        }
    except Exception as e:
        logger.error(f"取得運勢時發生未預期的錯誤: {e}", exc_info=True)
        return {
            "status": "error",
            "error_message": f"取得運勢時發生錯誤：{str(e)}"
        }
