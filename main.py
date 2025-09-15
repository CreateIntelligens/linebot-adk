# =============================================================================
# LINE Bot ADK 應用程式主檔案
# 使用 Google ADK (Agent Development Kit) 和 Google Gemini 模型
# 提供天氣查詢、時間查詢和短網址生成功能
# =============================================================================

import os
import sys
import asyncio
from io import BytesIO

import aiohttp
from fastapi import Request, FastAPI, HTTPException
from zoneinfo import ZoneInfo

# LINE Bot SDK 相關匯入
from linebot.models import MessageEvent, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot import AsyncLineBotApi, WebhookParser

# 自訂工具函數匯入
from multi_tool_agent.agent import (
    get_weather,           # 天氣查詢功能
    get_weather_forecast,  # 天氣預報功能
    get_current_time,      # 時間查詢功能
    create_short_url,      # 短網址生成功能
    query_knowledge_base,  # 知識庫查詢功能
    process_video,         # 影片處理功能
    get_task_status,       # 任務狀態查詢功能
    call_legal_ai,         # 法律諮詢功能
)

# Google ADK 相關匯入
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai import types

# =============================================================================
# 環境變數配置和驗證
# =============================================================================

# Google ADK 配置 - 決定使用哪種 Google AI 服務
USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI") or "FALSE"  # 預設使用免費的 Google AI API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""  # Google AI Studio API 金鑰

# LINE Bot 基本配置 - 從環境變數獲取
channel_secret = os.getenv("ChannelSecret", None)  # LINE Channel Secret，用於驗證 Webhook
channel_access_token = os.getenv("ChannelAccessToken", None)  # LINE Channel Access Token，用於發送訊息

# =============================================================================
# 環境變數驗證 - 確保必要的配置都已設定
# =============================================================================

# 驗證 LINE Bot 必要配置
if channel_secret is None:
    print("請設定 ChannelSecret 環境變數。")
    sys.exit(1)
if channel_access_token is None:
    print("請設定 ChannelAccessToken 環境變數。")
    sys.exit(1)

# 驗證 Google ADK 配置
if USE_VERTEX == "True":  # 如果使用 Vertex AI
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
    if not GOOGLE_CLOUD_PROJECT:
        raise ValueError(
            "使用 Vertex AI 時必須設定 GOOGLE_CLOUD_PROJECT 環境變數。"
        )
    if not GOOGLE_CLOUD_LOCATION:
        raise ValueError(
            "使用 Vertex AI 時必須設定 GOOGLE_CLOUD_LOCATION 環境變數。"
        )
elif not GOOGLE_API_KEY:  # 如果使用 Google AI Studio API
    raise ValueError("請設定 GOOGLE_API_KEY 環境變數。")

# =============================================================================
# FastAPI 應用程式初始化
# =============================================================================

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="LINE Bot ADK",  # API 文件標題
    description="使用 Google ADK 的多功能 LINE Bot",  # API 文件描述
    version="1.0.0"  # 版本號
)

# 初始化 HTTP 客戶端和 LINE Bot API
session = aiohttp.ClientSession()  # aiohttp 異步 HTTP 客戶端
async_http_client = AiohttpAsyncHttpClient(session)  # LINE Bot 非同步 HTTP 客戶端
line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)  # LINE Bot API 實例
parser = WebhookParser(channel_secret)  # Webhook 請求解析器，用於驗證請求真實性

# =============================================================================
# Google ADK Agent 初始化
# =============================================================================

# 建立主要 Agent 實例
root_agent = Agent(
    name="multi_tool_agent",  # Agent 唯一識別名稱
    model="gemini-2.5-flash",  # 使用 Google Gemini 2.0 Flash 模型
    description="多功能助手，提供天氣查詢、時間查詢、短網址生成、公視hihi導覽先生資訊查詢、影片處理和專業法律諮詢功能",  # Agent 功能描述
    instruction=(
        "我是專門提供七種服務的助手：天氣、時間、短網址、公視hihi導覽先生資訊查詢、影片處理、任務狀態查詢、法律諮詢。\n"
        "回答要簡潔直接，不要問太多確認問題。\n\n"
        "判斷邏輯順序：\n"
        "1. 法律相關：明確提到「法律」「合約」「糾紛」「法院」「律師」「起訴」「法規」「條文」等法律詞彙 → 使用法律諮詢工具\n"
        "2. 天氣相關：明確提到「天氣」「溫度」「下雨」「晴天」等氣象詞彙 → 使用天氣工具\n"
        "3. 時間相關：明確提到「時間」「幾點」「現在」「今天幾號」等時間詞彙 → 使用時間工具。如果用戶沒有指定城市，請傳入「台北」作為參數\n"
        "4. 網址相關：明確提到「網址」「連結」「短網址」或包含 http/https 但沒有提到影片處理 → 使用短網址工具。沒有指定 slug 時傳入空字串。如果用戶要求「長連結」「長網址」，則生成至少50字符的 slug，主要由 0 和 o 混合組成頭尾由 l跟 ng包覆（如：lo0o0o0oo0oooong0o0o0oo00oo0o0ooong）\n"
        "5. 影片處理相關：明確提到「影片」「轉錄」「摘要」「處理影片」或包含影片URL → 使用影片處理工具，summary_language 參數請傳入 \"zh\"\n"
        "6. 任務狀態相關：明確提到「任務」「狀態」「進度」「查詢任務」或訊息只包含一個任務ID字串（例如：032240I9 或 2d9a32e5-becc-48f8-af37-790ae1f78c11）→ 使用任務狀態查詢工具\n"
        "7. 其他所有問題：\n"
        "   7a. 優先使用 query_knowledge_base 查詢公視hihi導覽先生相關資訊\n"
        "   7b. 如果知識庫回答與用戶問題完全無關或無法提供有用資訊，則直接用AI進行一般回答\n\n"
        "hihi導覽先生是公視台語節目，知識庫包含節目、角色、內容等相關資訊。\n\n"
        "請用繁體中文簡潔回應。"
    ),
    # 註冊可用的工具函數
    tools=[
        get_weather,           # 天氣查詢工具
        get_weather_forecast,  # 天氣預報工具
        get_current_time,      # 時間查詢工具
        create_short_url,      # 短網址生成工具
        query_knowledge_base,  # 知識庫查詢工具
        process_video,         # 影片處理工具
        get_task_status,       # 任務狀態查詢工具
        call_legal_ai,         # 法律諮詢工具
    ],
)

print(f"Agent '{root_agent.name}' 初始化完成。")

# =============================================================================
# 會話管理系統
# 使用 Google ADK 的 InMemorySessionService 來管理對話狀態和歷史
# =============================================================================

# 初始化會話服務 - 儲存對話歷史和狀態資訊
# InMemorySessionService: 簡單的記憶體儲存，應用重啟後資料會遺失
session_service = InMemorySessionService()

# 應用程式識別名稱 - 用於區分不同應用程式的會話
APP_NAME = "linebot_adk_app"

# 全域會話追蹤字典 - 記錄活躍用戶的會話 ID
# 鍵: user_id, 值: session_id
active_sessions = {}

# 全域任務追蹤字典 - 記錄用戶的活躍影片處理任務
# 鍵: user_id, 值: 任務 ID 列表
user_active_tasks = {}

# 任務監控狀態 - 記錄正在監控的任務
# 鍵: task_id, 值: {"user_id": str, "last_status": str, "original_url": str}
monitoring_tasks = {}


async def get_or_create_session(user_id: str) -> str:
    """
    獲取或建立用戶會話

    為每個用戶動態建立專屬會話，如果已存在則重用現有會話。
    這確保了對話的連續性和上下文保持。

    Args:
        user_id (str): LINE 用戶 ID

    Returns:
        str: 會話 ID
    """
    if user_id not in active_sessions:
        # 建立新會話
        session_id = f"session_{user_id}"

        # 在會話服務中建立會話
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        # 記錄到活躍會話字典
        active_sessions[user_id] = session_id
        print(f"建立新會話: App='{APP_NAME}', User='{user_id}', Session='{session_id}'")
    else:
        # 使用現有會話
        session_id = active_sessions[user_id]
        print(f"使用現有會話: App='{APP_NAME}', User='{user_id}', Session='{session_id}'")

    return session_id


async def push_message_to_user(user_id: str, message: str):
    """
    主動推送訊息給用戶
    
    Args:
        user_id (str): LINE 用戶 ID
        message (str): 要推送的訊息內容
    """
    try:
        from linebot.models import TextSendMessage
        push_msg = TextSendMessage(text=message)
        await line_bot_api.push_message(user_id, push_msg)
        print(f"推送訊息給用戶 {user_id}: {message[:50]}...")
    except Exception as e:
        print(f"推送訊息失敗: {e}")


async def monitor_task_status(task_id: str, user_id: str):
    """
    監控單一任務狀態，完成時主動推送
    
    Args:
        task_id (str): 任務 ID
        user_id (str): 用戶 ID
    """
    max_checks = 120  # 最多檢查 120 次 (120 * 30秒 = 1小時)
    check_count = 0
    
    print(f"開始監控任務 {task_id}")
    
    while check_count < max_checks:
        try:
            await asyncio.sleep(30)  # 每 30 秒檢查一次
            check_count += 1
            
            from multi_tool_agent.agent import get_task_status
            status_result = await get_task_status(task_id)
            
            if status_result["status"] == "success":
                task_status = status_result.get("task_status", "unknown")
                
                # 檢查任務是否完成
                if task_status == "completed":
                    # 任務完成，推送通知（包含原始連結和摘要）
                    message = f"✅ 影片摘要完成！\n{status_result['report']}"
                    await push_message_to_user(user_id, message)
                    
                    # 清理任務記錄
                    if user_id in user_active_tasks and task_id in user_active_tasks[user_id]:
                        user_active_tasks[user_id].remove(task_id)
                    if task_id in monitoring_tasks:
                        del monitoring_tasks[task_id]
                    
                    print(f"任務 {task_id} 已完成並推送給用戶")
                    break
                    
                elif task_status == "failed":
                    # 任務失敗，推送通知
                    message = f"❌ 影片處理失敗\n任務 ID: {task_id}\n\n{status_result['report']}"
                    await push_message_to_user(user_id, message)
                    
                    # 清理任務記錄
                    if user_id in user_active_tasks and task_id in user_active_tasks[user_id]:
                        user_active_tasks[user_id].remove(task_id)
                    if task_id in monitoring_tasks:
                        del monitoring_tasks[task_id]
                        
                    print(f"任務 {task_id} 失敗並推送給用戶")
                    break
                    
                # 更新監控狀態
                if task_id in monitoring_tasks:
                    monitoring_tasks[task_id]["last_status"] = task_status
                    
        except Exception as e:
            print(f"監控任務 {task_id} 時發生錯誤: {e}")
            
    # 監控超時清理
    if task_id in monitoring_tasks:
        del monitoring_tasks[task_id]
    print(f"任務 {task_id} 監控結束")


def start_task_monitoring(task_id: str, user_id: str, original_url: str = ""):
    """
    啟動任務監控（非阻塞）
    
    Args:
        task_id (str): 任務 ID  
        user_id (str): 用戶 ID
        original_url (str): 原始影片 URL
    """
    # 記錄監控狀態
    monitoring_tasks[task_id] = {
        "user_id": user_id, 
        "last_status": "processing",
        "original_url": original_url
    }
    
    # 在背景啟動監控任務
    asyncio.create_task(monitor_task_status(task_id, user_id))
    print(f"啟動任務 {task_id} 背景監控")


# =============================================================================
# Agent 執行器初始化
# Runner 負責協調 Agent 的執行流程和事件處理
# =============================================================================

runner = Runner(
    agent=root_agent,        # 要執行的 Agent 實例
    app_name=APP_NAME,       # 應用程式名稱，用於會話區分
    session_service=session_service,  # 會話管理服務
)

print(f"Runner 初始化完成，Agent: '{runner.agent.name}'")


@app.post("/")
async def handle_callback(request: Request) -> str:
    """
    LINE Bot Webhook 回呼處理函數

    處理來自 LINE 平台的 Webhook 請求，驗證請求真實性並處理訊息事件。
    這是 LINE Bot 的主要入口點，負責接收和回應用戶訊息。

    Args:
        request (Request): FastAPI 請求物件，包含 LINE 發送的 Webhook 資料

    Returns:
        str: 處理結果，成功返回 "OK"

    Raises:
        HTTPException: 當請求驗證失敗時拋出 400 錯誤
    """
    # 從請求標頭獲取 LINE 簽章，用於驗證請求真實性
    signature = request.headers["X-Line-Signature"]

    # 獲取請求主體並轉換為字串
    body = await request.body()
    body = body.decode()

    try:
        # 使用 WebhookParser 解析和驗證請求
        # 如果簽章無效會拋出 InvalidSignatureError
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        # 簽章驗證失敗，返回 400 錯誤
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 處理每個事件
    for event in events:
        # 只處理訊息事件，其他事件類型忽略
        if not isinstance(event, MessageEvent):
            continue

        # 處理文字訊息
        if event.message.type == "text":
            # 提取訊息內容和用戶資訊
            msg = event.message.text
            user_id = event.source.user_id
            print(f"收到訊息: {msg} 來自用戶: {user_id}")

            # ToolContext 會自動管理用戶上下文，不需要手動設定

            # 呼叫 Agent 處理用戶查詢
            response = await call_agent_async(msg, user_id)

            # 建立回覆訊息
            reply_msg = TextSendMessage(text=response)

            # 發送回覆給用戶
            await line_bot_api.reply_message(event.reply_token, reply_msg)

        elif event.message.type == "image":
            # 圖片訊息處理（目前僅記錄）
            print(f"收到圖片訊息 from user: {event.source.user_id}")
            return "OK"
        else:
            # 其他訊息類型（語音、影片等）目前不處理
            continue

    return "OK"


async def call_agent_async(query: str, user_id: str) -> str:
    """
    非同步呼叫 Google ADK Agent 處理用戶查詢

    這是與 Google ADK Agent 互動的核心函數，負責：
    1. 管理用戶會話
    2. 將用戶查詢發送給 Agent
    3. 處理 Agent 的回應和錯誤
    4. 實現會話重試機制

    Args:
        query (str): 用戶的文字查詢
        user_id (str): LINE 用戶 ID

    Returns:
        str: Agent 的最終回應文字
    """
    print(f"\n>>> 用戶查詢: {query}")

    # 獲取或建立用戶會話
    session_id = await get_or_create_session(user_id)

    # 將用戶訊息轉換為 Google ADK 格式
    content = types.Content(
        role="user",  # 訊息角色：用戶
        parts=[types.Part(text=query)]  # 訊息內容
    )

    # 預設回應文字（當 Agent 沒有產生最終回應時使用）
    final_response_text = "Agent 沒有產生最終回應。"

    try:
        # 核心邏輯：執行 Agent 並處理事件流
        # run_async 會產生一系列事件，我們需要找到最終回應
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            # 除錯用：可以取消註解來查看所有事件
            # print(f"  [事件] 作者: {event.author}, 類型: {type(event).__name__}, 最終回應: {event.is_final_response()}, 內容: {event.content}")

            # 檢查是否為最終回應事件
            if event.is_final_response():
                # 處理正常回應
                if event.content and event.content.parts:
                    # 提取文字回應（假設在第一個部分）
                    final_response_text = event.content.parts[0].text

                    # 檢查是否包含任務 ID（表示剛剛啟動了影片處理任務）
                    if "任務ID:" in final_response_text:
                        # 嘗試從回應中提取任務 ID
                        import re
                        task_id_match = re.search(r'任務ID:\s*(\S+)', final_response_text)
                        if task_id_match:
                            task_id = task_id_match.group(1)
                            # 記錄活躍任務
                            if user_id not in user_active_tasks:
                                user_active_tasks[user_id] = []
                            if task_id not in user_active_tasks[user_id]:
                                user_active_tasks[user_id].append(task_id)
                                print(f"記錄活躍任務: 用戶 {user_id}, 任務 {task_id}")
                                
                                # 立即啟動背景監控，不查詢初始狀態（保持回應簡潔）
                                # 提取原始 URL（從用戶訊息中）
                                import re
                                url_match = re.search(r'https?://[^\s]+', query)
                                original_url = url_match.group(0) if url_match else ""
                                
                                # 啟動背景監控
                                start_task_monitoring(task_id, user_id, original_url)

                # 處理錯誤或升級情況
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent 升級處理: {event.error_message or '沒有具體訊息。'}"

                # 找到最終回應後停止處理
                break

    except ValueError as e:
        # 處理 ValueError，通常是會話相關錯誤
        print(f"處理請求時發生錯誤: {str(e)}")

        # 特殊處理：會話不存在錯誤
        if "Session not found" in str(e):
            print("會話遺失，嘗試重新建立...")

            # 移除無效會話
            active_sessions.pop(user_id, None)

            # 重新建立會話
            session_id = await get_or_create_session(user_id)

            # 重試執行 Agent
            try:
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            final_response_text = event.content.parts[0].text
                        elif event.actions and event.actions.escalate:
                            final_response_text = f"Agent 升級處理: {event.error_message or '沒有具體訊息。'}"
                        break

            except Exception as e2:
                # 重試也失敗
                final_response_text = f"很抱歉，處理您的請求時發生錯誤: {str(e2)}"
        else:
            # 其他 ValueError
            final_response_text = f"很抱歉，處理您的請求時發生錯誤: {str(e)}"

    # 輸出最終回應到控制台
    print(f"<<< Agent 回應: {final_response_text.strip()}")

    return final_response_text
