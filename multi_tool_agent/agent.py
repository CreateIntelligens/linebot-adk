# =============================================================================
# 多功能 Agent 工具函數模組
# 提供天氣查詢、時間查詢和短網址生成功能
# 所有函數都是異步的，使用 aiohttp 進行網路請求
# =============================================================================

import os
import datetime
from zoneinfo import ZoneInfo
import aiohttp
import asyncio
from typing import Optional
# 移除不必要的 ToolContext 導入

# 簡單的工具函數，專注於核心功能


async def get_weather(city: str) -> dict:
    """
    獲取指定城市的當前天氣資訊

    使用 wttr.in API 服務查詢指定城市的即時天氣狀況。
    該 API 提供簡潔的天氣格式，包含溫度、濕度、風速等資訊。

    Args:
        city (str): 要查詢天氣的城市名稱（支援中文和英文）

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的天氣報告文字（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await get_weather("台北")
        >>> print(result)
        {"status": "success", "report": "🌤️ 台北: 🌦 +19°C"}
    """
    try:
        # 建構 wttr.in API 請求 URL
        # format=3: 簡潔格式，m: 公制單位，lang=zh-tw: 繁體中文
        api_url = f"https://wttr.in/{city}?format=3&m&lang=zh-tw"

        # 使用 aiohttp 非同步 HTTP 客戶端發送請求
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    # 成功取得回應，讀取文字內容
                    weather_text = await response.text()
                    weather_text = weather_text.strip()  # 移除前後空白字元

                    # 返回成功結果，包含表情符號和天氣資訊
                    return {
                        "status": "success",
                        "report": f"🌤️ {weather_text}"
                    }
                else:
                    # API 回應狀態碼不是 200，可能是城市名稱錯誤
                    return {
                        "status": "error",
                        "error_message": f"無法取得 {city} 的天氣資訊，請確認城市名稱正確。"
                    }

    except Exception as e:
        # 捕獲所有異常，包括網路錯誤、解析錯誤等
        return {
            "status": "error",
            "error_message": f"查詢天氣時發生錯誤：{str(e)}"
        }


async def get_weather_forecast(city: str, days: str) -> dict:
    """
    獲取指定城市的天氣預報資訊

    使用 wttr.in API 服務查詢指定城市未來數天的天氣預報。
    支援 1-3 天的預報查詢，預設為 3 天。

    Args:
        city (str): 要查詢預報的城市名稱（支援中文和英文）
        days (str): 預報天數，可選值："1", "2", "3"，預設為 "3"

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的預報報告文字（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await get_weather_forecast("東京", "2")
        >>> print(result["report"])
        🔮 未來2天天氣預報：
        東京: ⛅ +15°C +3 km/h
        東京: 🌦 +12°C +5 km/h
    """
    try:
        # 驗證和設定預設值
        if not days or days not in ["1", "2", "3"]:
            days = "3"  # 預設 3 天預報

        # 建構 wttr.in API 請求 URL
        # {days}: 預報天數，m: 公制單位，lang=zh-tw: 繁體中文
        # format: 自訂格式，包含地點、天氣、溫度、風速等
        api_url = f"https://wttr.in/{city}?{days}&m&lang=zh-tw&format=%l:+%c+%t+%w+%p\n"

        # 使用 aiohttp 發送請求，設定 10 秒超時
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    # 成功取得回應
                    forecast_text = await response.text()
                    forecast_text = forecast_text.strip()

                    # 處理多行輸出，只保留指定天數的預報
                    lines = forecast_text.split('\n')[:int(days)]
                    simplified_forecast = '\n'.join(lines)

                    return {
                        "status": "success",
                        "report": f"🔮 未來{days}天天氣預報：\n{simplified_forecast}"
                    }
                else:
                    # API 回應錯誤，可能是城市名稱有誤
                    return {
                        "status": "error",
                        "error_message": f"無法取得 {city} 的天氣預報，請確認城市名稱正確。"
                    }

    except Exception as e:
        # 捕獲所有異常，包括網路超時、解析錯誤等
        return {
            "status": "error",
            "error_message": f"查詢天氣預報時發生錯誤：{str(e)}"
        }


async def get_current_time(city: str) -> dict:
    """
    獲取指定城市的當前時間

    使用 worldtimeapi.org API 服務智慧判斷城市時區並獲取當前時間。
    如果 API 查詢失敗，會降級使用預設的台北時區。

    Args:
        city (str): 要查詢時間的城市名稱（支援中文和英文），預設為 "台北"

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的時間報告文字（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await get_current_time("東京")
        >>> print(result["report"])
        東京 目前時間：2025-01-15 14:30:25 +09
    """
    try:
        # 處理預設值
        if not city:
            city = "台北"

        # 第一階段：獲取所有可用時區列表
        api_url = "http://worldtimeapi.org/api/timezone"

        async with aiohttp.ClientSession() as session:
            # 請求時區列表，設定 5 秒超時
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    timezones = await response.json()

                    # 智慧匹配：將城市名稱轉為小寫進行模糊匹配
                    city_lower = city.lower()
                    matched_timezone = None

                    # 遍歷時區列表，尋找包含城市名稱的時區
                    for tz in timezones:
                        if city_lower in tz.lower():
                            matched_timezone = tz
                            break

                    # 如果找到匹配的時區，獲取該時區的時間
                    if matched_timezone:
                        time_api_url = f"http://worldtimeapi.org/api/timezone/{matched_timezone}"
                        async with session.get(time_api_url, timeout=aiohttp.ClientTimeout(total=5)) as time_response:
                            if time_response.status == 200:
                                time_data = await time_response.json()
                                datetime_str = time_data['datetime']

                                # 解析 ISO 格式時間字串
                                dt = datetime.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))

                                # 格式化輸出時間
                                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
                                return {
                                    "status": "success",
                                    "report": f"{city} 目前時間：{formatted_time}"
                                }

        # 如果 API 查詢失敗或沒有匹配的時區，使用降級方案
        tz = ZoneInfo("Asia/Taipei")  # 預設台北時區
        now = datetime.datetime.now(tz)
        return {
            "status": "success",
            "report": f"{city} 目前時間：{now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        }

    except Exception as e:
        # 第一級異常處理：嘗試使用降級方案
        try:
            tz = ZoneInfo("Asia/Taipei")
            now = datetime.datetime.now(tz)
            return {
                "status": "success",
                "report": f"{city} 目前時間：{now.strftime('%Y-%m-%d %H:%M:%S %Z')} (使用台北時區)"
            }
        except Exception as e2:
            # 最終降級失敗，返回錯誤
            return {
                "status": "error",
                "error_message": f"取得時間時發生錯誤：{str(e2)}"
            }


async def query_knowledge_base(question: str, user_id: str) -> dict:
    """
    查詢 FastGPT 知識庫

    使用 FastGPT API 查詢知識庫內容，支援上下文對話管理。
    透過 OpenAI 相容的 API 介面與 FastGPT 知識庫進行互動。

    Args:
        question (str): 要查詢的問題或內容
        user_id (str): 用戶 ID，用於維持對話上下文

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的回答內容（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await query_knowledge_base("什麼是人工智慧？")
        >>> print(result["report"])
        人工智慧是指讓機器具備類似人類智能的技術...

        >>> result = await query_knowledge_base("更詳細的說明")
        >>> print(result["report"])
        詳細來說，人工智慧包括機器學習、深度學習...
    """
    # 使用 user_id 作為 chatId 維持對話上下文
    print(f"知識庫查詢: {question}, 用戶ID: {user_id}")

    # FastGPT API 配置 - 從環境變數讀取
    api_url = os.getenv("FASTGPT_API_URL") or "http://llm.5gao.ai:1987/api/v1/chat/completions"
    api_key = os.getenv("FASTGPT_API_KEY") or ""

    # 檢查必要的配置
    if not api_key:
        return {
            "status": "error",
            "error_message": "抱歉，目前知識庫服務暫時無法使用，請稍後再試。如果是關於 hihi 先生的問題，建議直接觀看公視節目獲取最新資訊。"
        }

    # 設定請求標頭
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 建構請求資料，包含 chatId 用於會話管理
    data = {
        "messages": [
            {
                "role": "user", 
                "content": question
            }
        ],
        "stream": False,  # 不使用串流模式
        "chatId": user_id  # 使用用戶ID作為對話識別
    }
    
    try:
        # 使用 aiohttp 發送 POST 請求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url, 
                json=data, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)  # 設定 30 秒超時
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # 從回應中提取答案內容
                    choices = result.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return {
                            "status": "success",
                            "report": f"🧠 知識庫回答：\n{content}"
                        }
                    else:
                        return {
                            "status": "error",
                            "error_message": "抱歉，知識庫暫時無法提供回答，請稍後再試。如果是關於 hihi 先生的問題，建議直接觀看公視節目。"
                        }
                else:
                    # API 回應錯誤
                    if response.status == 401:
                        return {
                            "status": "error", 
                            "error_message": "抱歉，知識庫服務認證失效，請稍後再試。建議直接觀看公視 hihi 先生節目獲取最新資訊。"
                        }
                    elif response.status == 403:
                        return {
                            "status": "error",
                            "error_message": "抱歉，知識庫服務暫時無法存取，請稍後再試。"
                        }
                    else:
                        return {
                            "status": "error",
                            "error_message": "抱歉，知識庫服務暫時忙碌中，請稍後再試。如果急需資訊，建議直接觀看公視節目。"
                        }
    
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error_message": "抱歉，知識庫查詢超時了，請稍後再試。如果急需 hihi 先生相關資訊，建議直接觀看公視節目。"
        }
    except Exception as e:
        # 捕獲所有其他異常，避免暴露技術細節
        return {
            "status": "error",
            "error_message": "抱歉，知識庫服務目前遇到一些問題，請稍後再試。如果是關於 hihi 先生的問題，建議直接觀看公視節目獲取最新資訊。"
        }


async def create_short_url(url: str, slug: Optional[str] = None) -> dict:
    """
    使用 aiurl.tw 服務建立短網址

    將長網址轉換為短網址，使用 aiurl.tw 提供的 URL 縮短服務。
    支援自訂 slug（短網址後綴），如果沒有提供則由服務自動生成。

    Args:
        url (str): 要縮短的原始長網址
        slug (Optional[str]): 自訂的短網址 slug，可選參數

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的結果報告文字（僅在成功時存在）
            - short_url (str): 生成的短網址（僅在成功時存在）
            - original_url (str): 原始網址（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await create_short_url("https://www.example.com/very/long/url")
        >>> print(result["short_url"])
        https://aiurl.tw/abc123

        >>> result = await create_short_url("https://www.example.com", "my-link")
        >>> print(result["short_url"])
        https://aiurl.tw/my-link
    """
    # aiurl.tw API 端點
    api_url = "https://aiurl.tw/api/link/create"

    # 設定請求標頭
    headers = {
        "authorization": "Bearer ToNf.360",  # API 認證 token
        "content-type": "application/json"   # 請求內容類型
    }

    # 建構請求資料
    data = {"url": url}
    if slug:  # 如果提供了自訂 slug，加入請求資料中
        data["slug"] = slug

    try:
        # 使用 aiohttp 發送 POST 請求
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=data, headers=headers) as response:
                if response.status == 201:  # HTTP 201 Created 表示成功建立
                    result = await response.json()

                    # 從回應中提取連結資訊
                    link_info = result.get("link", {})
                    short_url = f"https://aiurl.tw/{link_info.get('slug', '')}"

                    return {
                        "status": "success",
                        "report": f"短網址已建立：{short_url}",
                        "short_url": short_url,
                        "original_url": url
                    }
                else:
                    # API 回應錯誤，讀取錯誤訊息
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error_message": f"建立短網址失敗：{response.status} - {error_text}"
                    }

    except Exception as e:
        # 捕獲所有異常，包括網路錯誤、JSON 解析錯誤等
        return {
            "status": "error",
            "error_message": f"建立短網址時發生錯誤：{str(e)}"
        }
