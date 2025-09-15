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
    查詢公視hihi導覽先生知識庫

    使用 FastGPT API 查詢公視台語節目「hihi導覽先生」相關內容，支援上下文對話管理。
    可回答節目介紹、角色資訊、內容摘要等相關問題。

    Args:
        question (str): 要查詢的問題或內容
        user_id (str): 用戶 ID，用於維持對話上下文

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - report (str): 成功時的回答內容（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await query_knowledge_base("hihi先生是誰？", "user123")
        >>> print(result["report"])
        🧠 知識庫回答：
        hihi先生是公視台語節目的主角...

        >>> result = await query_knowledge_base("節目內容是什麼？", "user123")
        >>> print(result["report"])
        🧠 知識庫回答：
        hihi先生導覽節目主要介紹台灣各地景點...
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
        "authorization": f"Bearer {os.getenv('AIURL_API_TOKEN', 'OtwD-9Gk-dn1')}",  # API 認證 token
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


async def call_legal_ai(question: str, user_id: str) -> dict:
    """
    呼叫法律問題 AI API

    使用支援思考模式的 AI API 回答法律相關問題。

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
        🏛️ 法律諮詢回答：
        合約糾紛的處理方式...
    """
    # 法律 AI API 配置
    api_url = os.getenv("LEGAL_AI_API_URL") or "https://taiwan-law-bot-dev.onrender.com/chat"
    api_key = os.getenv("LEGAL_AI_API_KEY") or ""

    # 設定請求標頭，模擬瀏覽器請求
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/event-stream, application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Origin": "https://taiwan-law-bot-dev.onrender.com",
        "Referer": "https://taiwan-law-bot-dev.onrender.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    # 建構請求資料 - 使用最快的設定
    data = {
        "messages": [{"role": "user", "content": question}],
        "stream": False,
        "is_paid_user": True,
        "is_thinking_mode": False,  # 關閉思考模式
        "general_public_mode": True,  # 使用一般大眾模式，回答更簡潔
        "writing_mode": False,
        "ai_high_court_only": False,  # 包含所有層級法院判決
        "model": "gpt-4.1"  # 使用 4.1 版本
    }

    # 檢查是否有有效的 user_id
    if user_id == "unknown" or user_id == "user123" or len(user_id) < 20:
        # 如果沒有有效的 user_id，直接同步處理
        try:
            # 設定較大的緩衝區以處理大型回應
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(
                connector=connector,
                read_bufsize=2**16  # 64KB buffer
            ) as session:
                async with session.post(
                    api_url,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        # API 即使設定 stream: false 也回傳事件流格式，先取得全部內容
                        import json
                        response_text = await response.text()
                        print(f"[法律AI] 收到回應，長度: {len(response_text)} 字元")
                        print(f"[法律AI] 回應前100字元: {response_text[:100]}")
                        
                        content_parts = []
                        final_reply = ""
                        line_count = 0
                        
                        # 處理事件流格式的回應
                        for line in response_text.split('\n'):
                            line_text = line.strip()
                            line_count += 1
                            if line_text.startswith('data: '):
                                print(f"[法律AI] 第{line_count}行 data: {line_text[:50]}...")
                                try:
                                    json_data = json.loads(line_text[6:])
                                    print(f"[法律AI] JSON解析成功，keys: {list(json_data.keys())}")
                                    
                                    # 處理台灣法律 AI 的回應格式
                                    if 'content' in json_data:
                                        content_parts.append(json_data['content'])
                                        print(f"[法律AI] 收集 content，目前總數: {len(content_parts)}")
                                    
                                    # 檢查是否完成
                                    if json_data.get('done', False) and 'reply' in json_data:
                                        final_reply = json_data['reply']
                                        print(f"[法律AI] 找到 final_reply，長度: {len(final_reply)} 字元")
                                        break
                                except Exception as e:
                                    print(f"[法律AI] JSON解析失敗: {e}")
                                    continue
                        
                        # 使用最終回應或組合的內容
                        full_content = final_reply if final_reply else ''.join(content_parts)
                        print(f"[法律AI] 最終內容長度: {len(full_content)} 字元")
                        print(f"[法律AI] 使用 final_reply: {bool(final_reply)}, content_parts數量: {len(content_parts)}")
                        
                        if full_content:
                            print(f"[法律AI] 成功回傳，內容前50字元: {full_content[:50]}")
                            return {
                                "status": "success",
                                "report": f"🏛️ 法律諮詢回答：\n\n{full_content}"
                            }
                        else:
                            return {
                                "status": "error",
                                "error_message": "法律 AI 沒有回應內容。"
                            }
                    else:
                        error_text = await response.text()
                        print(f"[法律AI] HTTP錯誤 {response.status}")
                        print(f"[法律AI] 錯誤內容: {error_text[:200]}...")
                        return {
                            "status": "error",
                            "error_message": f"法律諮詢服務回應錯誤：{response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"法律諮詢服務發生錯誤：{str(e)}"
            }
    else:
        # 有有效的 user_id，使用背景處理
        import uuid
        task_id = str(uuid.uuid4())
        
        # 啟動背景查詢任務
        asyncio.create_task(process_legal_query_async(task_id, question, user_id, api_url, data, headers))
        
        return {
            "status": "success",
            "report": f"📋 法律諮詢查詢中... 請稍候\n查詢ID: {task_id[:8]}",
            "task_id": task_id
        }


async def process_legal_query_async(task_id: str, question: str, user_id: str, api_url: str, data: dict, headers: dict):
    """
    背景處理法律諮詢查詢
    
    Args:
        task_id (str): 任務 ID
        question (str): 法律問題
        user_id (str): 用戶 ID
        api_url (str): API URL
        data (dict): 請求資料
        headers (dict): 請求標頭
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)  # 延長到 2 分鐘
            ) as response:
                if response.status == 200:
                    # 處理台灣法律 AI 的串流回應格式
                    content_parts = []
                    final_reply = ""
                    
                    async for line in response.content:
                        line_text = line.decode('utf-8').strip()
                        if line_text.startswith('data: '):
                            try:
                                import json
                                json_data = json.loads(line_text[6:])
                                
                                # 處理台灣法律 AI 的回應格式
                                if 'content' in json_data:
                                    content_parts.append(json_data['content'])
                                
                                # 檢查是否完成
                                if json_data.get('done', False) and 'reply' in json_data:
                                    final_reply = json_data['reply']
                                    break
                            except Exception as e:
                                continue

                    # 使用最終回應或組合的內容
                    full_content = final_reply if final_reply else ''.join(content_parts)
                    
                    if full_content:
                        # 推送完成結果
                        message = f"🏛️ 法律諮詢結果：\n\n{full_content}\n\n查詢ID: {task_id[:8]}"
                        await push_legal_result(user_id, message)
                    else:
                        await push_legal_result(user_id, f"❌ 法律諮詢查詢失敗：AI 沒有回應內容\n查詢ID: {task_id[:8]}")
                else:
                    await push_legal_result(user_id, f"❌ 法律諮詢查詢失敗：服務回應錯誤 {response.status}\n查詢ID: {task_id[:8]}")

    except Exception as e:
        await push_legal_result(user_id, f"❌ 法律諮詢查詢失敗：{str(e)}\n查詢ID: {task_id[:8]}")


async def push_legal_result(user_id: str, message: str):
    """
    推送法律諮詢結果給用戶
    
    Args:
        user_id (str): LINE 用戶 ID
        message (str): 要推送的訊息內容
    """
    try:
        # 直接使用 HTTP API 推送訊息
        import aiohttp
        import json
        
        channel_access_token = os.getenv("ChannelAccessToken", None)
        if not channel_access_token:
            print(f"無法推送法律諮詢結果：缺少 ChannelAccessToken")
            return
            
        headers = {
            'Authorization': f'Bearer {channel_access_token}',
            'Content-Type': 'application/json'
        }
        
        # 限制訊息長度（LINE 訊息上限 5000 字符）
        if len(message) > 4800:
            message = message[:4800] + "\n...\n（回應內容過長，已截斷）"
        
        data = {
            'to': user_id,
            'messages': [
                {
                    'type': 'text',
                    'text': message
                }
            ]
        }
        
        print(f"準備推送給用戶: {user_id}, 訊息長度: {len(message)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.line.me/v2/bot/message/push',
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    print(f"推送法律諮詢結果給用戶 {user_id}: {message[:50]}...")
                else:
                    error_text = await response.text()
                    print(f"推送法律諮詢結果失敗: {response.status} - {error_text}")
                    print(f"請求資料: {data}")
                    print(f"用戶ID: '{user_id}' (type: {type(user_id)}, len: {len(user_id)})")
                    
    except Exception as e:
        print(f"推送法律諮詢結果失敗: {e}")


