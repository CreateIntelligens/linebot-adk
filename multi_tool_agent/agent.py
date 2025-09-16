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
import requests
import json
import logging

# 設定 logger
logger = logging.getLogger(__name__)

# 全域變數：當前用戶 ID（由 main.py 設定）
current_user_id = None

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
                                dt = datetime.datetime.fromisoformat(
                                    datetime_str.replace('Z', '+00:00'))

                                # 格式化輸出時間
                                formatted_time = dt.strftime(
                                    "%Y-%m-%d %H:%M:%S %Z")
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
    查詢公視hihi導覽先生知識庫

    使用 FastGPT API 查詢公視台語節目「hihi導覽先生」相關內容，支援上下文對話管理。
    可回答節目介紹、角色資訊、內容摘要等相關問題。

    Args:
        question (str): 要查詢的問題或內容
        user_id (str): 必須傳入用戶的真實 ID，用於維持每個用戶的獨立對話上下文

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的回答內容（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await query_knowledge_base("hihi先生是誰？", user_id)
        >>> print(result["report"])
        🧠 知識庫回答：hihi先生是公視台語節目的主角...
    """
    # 使用真實的用戶 ID，不依賴 ADK 傳入的參數
    real_user_id = current_user_id or user_id
    print(f"hihi導覽先生知識庫查詢: {question}, 用戶ID: {real_user_id} (ADK傳入: {user_id})")

    # FastGPT API 配置 - 從環境變數讀取
    api_url = os.getenv(
        "FASTGPT_API_URL") or "http://llm.5gao.ai:1987/api/v1/chat/completions"
    api_key = os.getenv("FASTGPT_HIHI_API_KEY") or ""

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
        "chatId": real_user_id  # 使用真實用戶ID作為對話識別
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
                        content = choices[0].get(
                            "message", {}).get("content", "")

                        # 檢查回答是否包含「不知道」、「無法回答」等關鍵詞
                        no_answer_keywords = ["不知道", "無法回答", "沒有相關", "找不到", "不清楚", "無相關資訊"]
                        if any(keyword in content for keyword in no_answer_keywords):
                            return {
                                "status": "not_relevant",
                                "report": "知識庫中沒有找到相關資訊"
                            }

                        return {
                            "status": "success",
                            "report": f"{content}"
                        }
                    else:
                        return {
                            "status": "not_relevant",
                            "report": "知識庫沒有回應"
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


async def query_set_knowledge_base(question: str, user_id: str) -> dict:
    """
    查詢SET三立電視知識庫

    使用 FastGPT API 查詢三立電視相關內容，支援上下文對話管理。
    可回答三立電視台節目介紹、藝人資訊、節目內容等相關問題。

    Args:
        question (str): 要查詢的問題或內容
        user_id (str): 必須傳入用戶的真實 ID，用於維持每個用戶的獨立對話上下文

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的回答內容（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await query_set_knowledge_base("三立有什麼節目？", user_id)
        >>> print(result["report"])
        📺 SET三立電視回答：三立電視台有多個頻道，包含戲劇、綜藝、新聞等節目...
    """
    # 使用真實的用戶 ID，不依賴 ADK 傳入的參數
    real_user_id = current_user_id or user_id
    print(f"SET三立知識庫查詢: {question}, 用戶ID: {real_user_id} (ADK傳入: {user_id})")

    # FastGPT API 配置 - 從環境變數讀取
    api_url = os.getenv(
        "FASTGPT_API_URL") or "http://llm.5gao.ai:1987/api/v1/chat/completions"
    api_key = os.getenv("FASTGPT_SET_API_KEY") or ""

    # 檢查必要的配置
    if not api_key:
        return {
            "status": "error",
            "error_message": "抱歉，目前SET三立電視知識庫服務暫時無法使用，請稍後再試。如果是關於三立節目的問題，建議直接查看三立電視官網獲取最新資訊。"
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
        "chatId": f"set_{real_user_id}"  # 使用真實用戶ID和 set_ 前綴區分對話
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
                        content = choices[0].get(
                            "message", {}).get("content", "")

                        # 檢查回答是否包含「不知道」、「無法回答」等關鍵詞
                        no_answer_keywords = ["不知道", "無法回答", "沒有相關", "找不到", "不清楚", "無相關資訊"]
                        if any(keyword in content for keyword in no_answer_keywords):
                            return {
                                "status": "not_relevant",
                                "report": "知識庫中沒有找到相關資訊"
                            }

                        return {
                            "status": "success",
                            "report": f"{content}"
                        }
                    else:
                        return {
                            "status": "not_relevant",
                            "report": "知識庫沒有回應"
                        }
                else:
                    # API 回應錯誤
                    if response.status == 401:
                        return {
                            "status": "error",
                            "error_message": "抱歉，SET三立電視知識庫服務認證失效，請稍後再試。建議直接查看三立電視官網獲取最新資訊。"
                        }
                    elif response.status == 403:
                        return {
                            "status": "error",
                            "error_message": "抱歉，SET三立電視知識庫服務暫時無法存取，請稍後再試。"
                        }
                    else:
                        return {
                            "status": "error",
                            "error_message": "抱歉，SET三立電視知識庫服務暫時忙碌中，請稍後再試。如果急需資訊，建議直接查看三立電視官網。"
                        }

    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error_message": "抱歉，SET三立電視知識庫查詢超時了，請稍後再試。如果急需節目資訊，建議直接查看三立電視官網。"
        }
    except Exception as e:
        # 捕獲所有其他異常，避免暴露技術細節
        return {
            "status": "error",
            "error_message": "抱歉，SET三立電視知識庫服務目前遇到一些問題，請稍後再試。如果是關於三立節目的問題，建議直接查看三立電視官網獲取最新資訊。"
        }


async def create_short_url(url: str, slug: str) -> dict:
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
        # API 認證 token
        "authorization": f"Bearer {os.getenv('AIURL_API_TOKEN', 'OtwD-9Gk-dn1')}",
        "content-type": "application/json"   # 請求內容類型
    }

    # 處理預設值 - 如果用戶說隨意/隨便等，設為空字串讓系統自動生成
    if slug is None or slug.lower() in ["隨意", "隨便", "你決定", "自動", "random"]:
        slug = ""

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


async def process_video(url: str, summary_language: str) -> dict:
    """
    處理影片並生成摘要

    使用 AI 影片轉錄器 API 處理指定的影片 URL，生成文字轉錄和摘要。
    支援指定摘要語言，預設為繁體中文。

    Args:
        url (str): 要處理的影片 URL
        summary_language (str): 摘要語言，預設為 "zh"（繁體中文）

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的處理結果報告（僅在成功時存在）
            - task_id (str): 任務 ID（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await process_video("https://example.com/video.mp4")
        >>> print(result["report"])
        影片摘要中，任務ID: abc123
    """
    # AI 影片轉錄器 API 端點
    api_base_url = os.getenv("VIDEO_API_BASE_URL") or "http://10.9.0.32:8893"
    process_url = f"{api_base_url}/api/process-video"

    # 處理預設值
    if not summary_language:
        summary_language = "zh"

    # 建構請求資料
    data = {
        "url": url,
        "summary_language": summary_language
    }

    try:
        # 使用 aiohttp 發送 POST 請求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                process_url,
                data=data,  # 使用 form data
                timeout=aiohttp.ClientTimeout(total=20)  # 設定 60 秒超時
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # 從回應中提取任務 ID
                    task_id = result.get("task_id", "unknown")

                    # 任務ID將在 main.py 中記錄到用戶活躍任務列表

                    return {
                        "status": "success",
                        "report": f"摘要擷取中... 任務ID: {task_id}",
                        "task_id": task_id
                    }
                else:
                    # API 回應錯誤
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error_message": f"影片處理請求失敗：{response.status} - {error_text}"
                    }

    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error_message": "影片處理請求超時，請稍後再試。"
        }
    except Exception as e:
        # 捕獲所有異常
        return {
            "status": "error",
            "error_message": f"處理影片時發生錯誤：{str(e)}"
        }


async def get_task_status(task_id: str) -> dict:
    """
    查詢影片處理任務狀態

    根據任務 ID 查詢影片處理的當前狀態和進度。

    Args:
        task_id (str): 影片處理任務的 ID

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的任務狀態報告（僅在成功時存在）
            - task_status (str): 任務狀態（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await get_task_status("abc123")
        >>> print(result["report"])
        任務狀態: 處理中... 進度: 50%
    """
    # AI 影片轉錄器 API 端點
    api_base_url = os.getenv("VIDEO_API_BASE_URL") or "http://10.9.0.32:8893"
    status_url = f"{api_base_url}/api/task-status/{task_id}"

    try:
        # 使用 aiohttp 發送 GET 請求
        async with aiohttp.ClientSession() as session:
            async with session.get(
                status_url,
                timeout=aiohttp.ClientTimeout(total=30)  # 設定 30 秒超時
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # 提取任務狀態資訊
                    task_status = result.get("status", "unknown")
                    progress = result.get("progress", 0)
                    message = result.get("message", "")
                    summary = result.get("summary", "")

                    # 格式化狀態報告
                    if task_status == "completed":
                        # 如果有摘要內容，顯示摘要；否則顯示訊息
                        content = summary if summary else message
                        report = content if content else "任務已完成"
                    elif task_status == "processing":
                        report = f"🔄 處理中... 進度: {progress}%\n{message}"
                    elif task_status == "failed":
                        report = f"❌ 任務失敗\n{message}"
                    else:
                        report = f"📋 任務狀態: {task_status}\n{message}"

                    return {
                        "status": "success",
                        "report": report,
                        "task_status": task_status
                    }
                else:
                    # API 回應錯誤
                    if response.status == 404:
                        return {
                            "status": "error",
                            "error_message": f"找不到任務 ID: {task_id}"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "error_message": f"查詢任務狀態失敗：{response.status} - {error_text}"
                        }

    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error_message": "查詢任務狀態超時，請稍後再試。"
        }
    except Exception as e:
        # 捕獲所有異常
        return {
            "status": "error",
            "error_message": f"查詢任務狀態時發生錯誤：{str(e)}"
        }

# 法律問題分類函數已移到 legal_agent.py


async def call_legal_ai(question: str, user_id: str) -> dict:
    """
    呼叫專業 AI 法律諮詢服務

    使用多專業 AI Agent 團隊回答法律相關問題，根據問題類型自動選擇合適的專業領域。
    基於 awesome-llm-apps 的 Legal Agent Team 概念，整合契約分析師、法律策略師、
    法律研究員等多個專業角色。

    Args:
        question (str): 法律相關問題
        user_id (str): 用戶 ID，用於維持對話上下文

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的回答內容（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await call_legal_ai("合約糾紛如何處理？", "user123")
        >>> print(result["report"])
        📑 **契約分析師** 專業分析：
        [詳細的契約糾紛處理建議]
    """
    try:
        # 導入法律諮詢功能
        from .legal_agent import legal_ai, fallback_legal

        # 嘗試使用主要法律諮詢服務
        try:
            result = await legal_ai(question, user_id)
            if result["status"] == "success":
                return result
        except Exception as e:
            print(f"[法律諮詢] 主要服務失敗: {e}")

        # 主要服務失敗時，使用備用服務
        return await fallback_legal(question, user_id)

    except Exception as e:
        print(f"[法律諮詢] 系統錯誤: {e}")
        return {
            "status": "error",
            "error_message": "抱歉，法律諮詢服務暫時無法使用，請稍後再試。"
        }


async def generate_meme(meme_idea: str, user_id: str) -> dict:
    """
    生成 Meme 圖片

    根據用戶的想法，使用 AI 生成合適的 meme 文字，然後調用 ImgFlip API 創建 meme。

    Args:
        meme_idea (str): 用戶的 meme 想法或描述
        user_id (str): 用戶 ID

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - meme_url (str): 生成的 meme 圖片 URL（僅在成功時存在）
            - report (str): 成功時的報告文字（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await generate_meme("老闆說要加班但薪水沒有增加", "user123")
        >>> print(result["meme_url"])
        https://i.imgflip.com/abc123.jpg
    """
    try:
        # 導入 meme 生成功能
        from .meme_agent import generate_meme as meme_gen, fallback_meme_generator

        # 嘗試使用主要 meme 生成服務
        try:
            result = await meme_gen(meme_idea, user_id)
            if result["status"] == "success":
                return result
        except Exception as e:
            print(f"[Meme 生成] 主要服務失敗: {e}")

        # 主要服務失敗時，使用備用服務
        return await fallback_meme_generator(meme_idea, user_id)

    except Exception as e:
        print(f"[Meme 生成] 系統錯誤: {e}")
        return {
            "status": "error",
            "error_message": "抱歉，Meme 生成服務暫時無法使用，請稍後再試。"
        }


async def generate_ai_video(text_content: str, user_id: str) -> dict:
    """
    使用 ComfyUI 生成 AI 影片

    根據提供的文字內容，使用 ComfyUI 生成對應的 AI 影片。
    此功能會先回覆用戶文字內容，然後在背景生成影片，完成後推送給用戶。

    Args:
        text_content (str): 要轉換成影片的文字內容
        user_id (str): 必須傳入用戶的真實 ID，用於推送影片

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "submitted" 或 "error"
            - report (str): 成功時的說明（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await generate_ai_video("你好！歡迎使用 AI 服務", user_id)
        >>> print(result["report"])
        文字內容已送出，影片正在生成中，完成後會自動推送給您！
    """
    try:
        # 使用真實的用戶 ID，不依賴 ADK 傳入的參數
        real_user_id = current_user_id or user_id
        print(f"AI影片生成: {text_content[:50]}..., 用戶ID: {real_user_id} (ADK傳入: {user_id})")

        # 導入 ComfyUI 相關功能
        from .comfyui_agent import generate_ai_video as comfy_generate

        # 提交影片生成工作
        result = await comfy_generate(text_content, real_user_id)

        if result["status"] == "submitted":
            # 成功提交，啟動背景監控任務
            prompt_id = result["prompt_id"]
            print(f"影片生成工作已提交: {prompt_id}")

            # 在背景執行影片監控和推送
            asyncio.create_task(monitor_and_push_video(prompt_id, real_user_id, text_content))

            return {
                "status": "success",
                "report": f"\n\n文字內容：{text_content}\n\n影片正在生成中，完成後會自動推送給您！"
            }
        elif result["status"] == "service_unavailable":
            return {
                "status": "error",
                "error_message": f"🚫 影片生成服務暫時無法使用\n\n{result.get('error_message', '')}\n\nTTS 服務狀態：正常 ✅\nComfyUI 服務狀態：無法連接 ❌"
            }
        else:
            return {
                "status": "error",
                "error_message": result.get("error_message", "影片生成提交失敗")
            }

    except Exception as e:
        print(f"[AI影片生成] 系統錯誤: {e}")
        return {
            "status": "error",
            "error_message": "抱歉，AI 影片生成服務暫時無法使用，請稍後再試。"
        }


async def monitor_and_push_video(prompt_id: str, user_id: str, text_content: str):
    """
    監控影片生成進度並在完成後推送給用戶

    這是一個背景任務，會持續監控 ComfyUI 的工作進度，
    當影片生成完成後，會自動推送給指定用戶。
    """
    try:
        print(f"開始監控影片生成: {prompt_id}")

        # 導入相關模組
        from .comfyui_agent import check_comfyui_status, extract_video_info, download_comfyui_video
        import asyncio

        # 設定監控參數
        max_attempts = 120  # 最多檢查 120 次（2分鐘）
        check_interval = 1   # 每 1 秒檢查一次
        initial_delay = 5    # 初始等待 5 秒讓工作開始

        # 初始等待，讓 ComfyUI 有時間開始處理
        print(f"等待 {initial_delay} 秒讓 ComfyUI 開始處理...")
        await asyncio.sleep(initial_delay)

        # 持續監控工作狀態
        for attempt in range(max_attempts):
            try:
                print(f"檢查影片狀態（{attempt + 1}/{max_attempts}）: {prompt_id}")

                result = await check_comfyui_status(prompt_id)
                if result:
                    print(f"工作狀態檢查成功: {prompt_id}")
                    video_info = extract_video_info(result)
                    if video_info:
                        print(f"找到影片檔案資訊: {video_info['filename']}")

                        # 下載影片檔案
                        video_data = await download_comfyui_video(video_info)

                        if video_data and len(video_data) > 0:
                            print(f"影片下載成功，大小: {len(video_data)} bytes")

                            # 影片下載成功，推送給用戶
                            await push_video_to_user(user_id, video_data, text_content, video_info)
                            print(f"[PUSH] ✅ 影片已成功推送給用戶: {user_id}")
                            return  # 成功完成
                        else:
                            print(f"影片下載失敗或檔案為空")
                    else:
                        print(f"無法取得影片檔案資訊")
                else:
                    print(f"工作狀態檢查返回 None")

                # 等待後再次檢查
                if attempt < max_attempts - 1:
                    print(f"等待 {check_interval} 秒後再次檢查...")
                    await asyncio.sleep(check_interval)

            except Exception as e:
                print(f"檢查影片狀態時發生錯誤（嘗試 {attempt + 1}/{max_attempts}）: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(check_interval)

        # 所有嘗試都失敗了，只記錄日誌，不推送錯誤訊息給用戶
        print(f"❌ 影片監控失敗，已達最大嘗試次數: {prompt_id}")
        print(f"工作 ID: {prompt_id}，用戶 ID: {user_id}")
        print(f"影片內容: {text_content[:50]}...")

    except Exception as e:
        print(f"監控影片生成時發生系統錯誤: {e}")
        try:
            await push_error_message_to_user(user_id, "影片生成監控過程中發生系統錯誤。")
        except:
            pass


async def push_video_to_user(user_id: str, video_data: bytes, text_content: str, video_info: dict = None):
    """
    推送影片給用戶
    """
    try:
        # 導入 LINE Bot API
        from linebot import AsyncLineBotApi
        from linebot.models import VideoSendMessage, TextSendMessage
        from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
        import os
        import aiohttp
        import requests

        # 初始化 LINE Bot API
        async with aiohttp.ClientSession() as session:
            async_http_client = AiohttpAsyncHttpClient(session)
            line_bot_api = AsyncLineBotApi(
                channel_access_token=os.getenv("ChannelAccessToken"),
                async_http_client=async_http_client
            )

            if video_data and len(video_data) > 0:
                try:
                    # 創建臨時檔案保存影片（使用統一的目錄）
                    import uuid
                    from pathlib import Path

                    # 使用與 main.py 相同的目錄
                    video_dir = Path("/app/upload")
                    video_dir.mkdir(exist_ok=True)

                    temp_filename = f"temp_{uuid.uuid4().hex}.mp4"
                    temp_file_path = video_dir / temp_filename

                    with open(temp_file_path, 'wb') as temp_file:
                        temp_file.write(video_data)

                    print(f"影片已下載到本地，檔案大小: {len(video_data)//1024} KB")
                    print(f"本地檔案路徑: {temp_file_path}")

                    # 上傳影片到 HTTPS 伺服器，然後用 HTTPS URL 推送
                    try:
                        # 上傳影片到你的 HTTPS 伺服器
                        https_url = await upload_video_to_https_server(video_data, video_info['filename'])

                        if https_url:
                            # 用 HTTPS URL 推送影片
                            video_message = VideoSendMessage(
                                original_content_url=https_url,
                                preview_image_url=https_url
                            )
                            await line_bot_api.push_message(user_id, video_message)
                            print(f"[PUSH] ✅ 影片已成功推送給用戶: {https_url}")
                        else:
                            print("❌ 影片上傳到 HTTPS 伺服器失敗")

                    except Exception as e:
                        print(f"❌ 推送影片時發生錯誤: {e}")
                        # 發送錯誤通知
                        fallback_message = TextSendMessage(
                            text=f"🎬 影片生成完成，但推送時發生問題。\n\n📝 內容：{text_content[:50]}..."
                        )
                        await line_bot_api.push_message(user_id, fallback_message)

                    # 清理臨時檔案
                    os.unlink(temp_file_path)

                except Exception as e:
                    print(f"❌ 影片處理失敗: {e}")
                    error_message = TextSendMessage(
                        text=f"🎬 影片生成完成，但推送過程中發生錯誤。\n\n📝 內容：{text_content[:50]}{'...' if len(text_content) > 50 else ''}"
                    )
                    await line_bot_api.push_message(user_id, error_message)
            else:
                error_message = TextSendMessage(
                    text=f"🎬 影片生成完成，但檔案資料無效。\n\n📝 內容：{text_content[:50]}{'...' if len(text_content) > 50 else ''}"
                )
                await line_bot_api.push_message(user_id, error_message)

    except Exception as e:
        print(f"推送影片時發生系統錯誤: {e}")
        try:
            # 最後的錯誤處理
            async with aiohttp.ClientSession() as session:
                async_http_client = AiohttpAsyncHttpClient(session)
                line_bot_api = AsyncLineBotApi(
                    channel_access_token=os.getenv("ChannelAccessToken"),
                    async_http_client=async_http_client
                )
                error_message = TextSendMessage(
                    text="影片推送過程中發生系統錯誤，請稍後再試。"
                )
                await line_bot_api.push_message(user_id, error_message)
        except:
            pass


async def push_error_message_to_user(user_id: str, error_message: str):
    """
    推送錯誤訊息給用戶
    """
    try:
        # 導入 LINE Bot API
        from linebot import AsyncLineBotApi
        from linebot.models import TextSendMessage
        from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
        import os

        # 初始化 LINE Bot API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async_http_client = AiohttpAsyncHttpClient(session)
            line_bot_api = AsyncLineBotApi(
                channel_access_token=os.getenv("ChannelAccessToken"),
                async_http_client=async_http_client
            )

            message = TextSendMessage(text=f"❌ {error_message}")
            await line_bot_api.push_message(user_id, message)
            print(f"[PUSH] ✅ 錯誤訊息已推送給用戶")

    except Exception as e:
        print(f"推送錯誤訊息時發生錯誤: {e}")


async def upload_video_to_https_server(video_data: bytes, filename: str) -> str:
    """
    上傳影片到 HTTPS 伺服器

    Args:
        video_data: 影片檔案的二進制數據
        filename: 影片檔案名稱

    Returns:
        str: 上傳成功後的 HTTPS URL，失敗時返回 None
    """
    try:
        import aiohttp

        # 直接上傳檔案到 HTTPS 伺服器
        upload_url = "https://adkline.147.5gao.ai/upload"
        print(f"上傳檔案到: {upload_url}")

        async with aiohttp.ClientSession() as session:
            # 準備檔案上傳
            data = aiohttp.FormData()
            data.add_field('file',
                          video_data,
                          filename=filename,
                          content_type='video/mp4')

            # 上傳檔案
            async with session.post(upload_url, data=data) as upload_response:
                if upload_response.status == 200:
                    result = await upload_response.json()
                    upload_url = result.get('url', f"https://adkline.147.5gao.ai/files/{filename}")
                    print(f"✅ 檔案上傳成功: {upload_url}")
                    return upload_url
                else:
                    error_text = await upload_response.text()
                    print(f"❌ 檔案上傳失敗: {upload_response.status} - {error_text}")
                    return None

    except Exception as e:
        print(f"❌ 上傳影片時發生錯誤: {e}")
        return None


def before_reply_display_loading_animation(line_user_id, loading_seconds=5):
    """
    在回覆前顯示 LINE Bot 載入動畫

    使用 LINE Messaging API 的 Chat Loading 功能，在處理請求時顯示載入動畫，
    提升用戶體驗，讓用戶知道 Bot 正在處理中。

    Args:
        line_user_id (str): LINE 用戶 ID
        loading_seconds (int): 載入動畫持續秒數，預設 5 秒，最大 60 秒

    Returns:
        None

    Note:
        需要 CHANNEL_ACCESS_TOKEN 環境變數設定正確的 LINE Bot 存取權杖
    """
    api_url = 'https://api.line.me/v2/bot/chat/loading/start'
    headers = {
        'Authorization': 'Bearer ' + os.environ.get("ChannelAccessToken"),
        'Content-Type': 'application/json'
    }
    data = {
        "chatId": line_user_id,
        "loadingSeconds": loading_seconds
    }
    requests.post(api_url, headers=headers, data=json.dumps(data))
