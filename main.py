# =============================================================================
# main.py - LINE Bot ADK 主應用程式檔案
# 使用 Google ADK (Agent Development Kit) 和 Google Gemini 模型的主應用程式
# 提供天氣查詢、時間查詢、短網址生成、公視hihi導覽先生資訊查詢、SET三立電視資訊查詢、
# 影片處理、法律諮詢、Meme生成和AI影片生成功能
#
# 主要組件：
# - FastAPI Web 應用程式框架
# - LINE Bot SDK 訊息處理
# - Google ADK Agent 系統
# - 多種工具函數整合
# - 影片檔案上傳與管理
# - 非同步任務監控系統
#
# 作者：LINE Bot ADK 開發團隊
# 版本：1.0.0
# 更新日期：2025-01-18
# =============================================================================

from fastapi import Request, FastAPI, HTTPException
import shutil
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.agents import Agent
from multi_tool_agent.agent import (
    get_weather,           # 天氣查詢功能
    get_weather_forecast,  # 天氣預報功能
    get_current_time,      # 時間查詢功能
    create_short_url,      # 短網址生成功能
    query_knowledge_base,  # hihi導覽先生知識庫查詢功能
    query_set_knowledge_base,  # SET三立電視知識庫查詢功能
    video_transcriber,     # 影片轉錄功能
    call_legal_ai,         # 法律諮詢功能
    generate_meme,         # Meme 生成功能
    generate_ai_video,     # AI 影片生成功能
    before_reply_display_loading_animation,  # 載入動畫功能
    get_amis_word_of_the_day,  # 阿美族語每日一字
    search_web,  # 網路搜尋
)


# 全域變數：當前用戶 ID（由 main.py 設定）
current_user_id = None

# =============================================================================
# ID 查詢工具函數
# =============================================================================

def get_task_status(task_id: str) -> dict:
    """
    通用任務狀態查詢功能 - 調用 ID 查詢 Agent。

    處理用戶提供的任務 ID，查詢對應的任務狀態和結果。
    支援異步執行和事件循環處理，自動設定影片數據供回覆使用。

    Args:
        task_id (str): 要查詢的任務 ID，格式通常為 UUID

    Returns:
        dict: 查詢結果，包含以下欄位：
            - status (str): 查詢狀態 ("success" 或 "error")
            - task_status (str, optional): 任務狀態 ("processing", "completed", "failed")
            - error_message (str, optional): 錯誤訊息（當 status 為 "error" 時）
            - has_video (bool, optional): 是否包含影片數據
            - video_filename (str, optional): 影片檔案名稱
            - video_info (dict, optional): 影片相關資訊

    Raises:
        Exception: 當 ID 查詢 Agent 調用失敗時拋出

    Example:
        >>> result = get_task_status("550e8400-e29b-41d4-a716-446655440000")
        >>> print(result["status"])
        success
    """
    print(f"🔍 get_task_status 被調用，參數: {task_id}")

    try:
        import asyncio
        from multi_tool_agent.agents.id_query_agent import IDQueryAgent

        # 從全域變數獲取用戶 ID
        user_id = current_user_id or "anonymous"
        print(f"🔍 使用用戶 ID: {user_id}")

        # 使用 asyncio.run() 來處理異步調用
        async def run_query():
            agent = IDQueryAgent()
            result = await agent.execute(task_id=task_id, user_id=user_id)
            print(f"🔍 IDQueryAgent 返回結果: {result}")
            return result

        # 檢查是否已經在事件循環中
        try:
            loop = asyncio.get_running_loop()
            print("🔍 已經在事件循環中，使用新任務")
            # 如果已經在循環中，創建任務
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_query())
                result = future.result()
        except RuntimeError:
            print("🔍 不在事件循環中，直接運行")
            # 不在循環中，直接運行
            result = asyncio.run(run_query())

        # 如果結果包含影片數據，設定到 main 模組供回覆使用
        if result and result.get("has_video"):
            try:
                import sys
                main_module = sys.modules.get('main')
                if main_module and hasattr(main_module, 'call_agent_async'):
                    main_module.call_agent_async._last_query_result = result
                    print(f"影片數據已設定供回覆使用: {task_id}")
            except Exception as set_error:
                print(f"設定影片數據時發生錯誤: {set_error}")

        print(f"🔍 get_task_status 返回: {result}")
        return result
    except Exception as e:
        print(f"❌ 調用 ID 查詢 Agent 時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error_message": f"查詢任務狀態時發生錯誤：{str(e)}"}
from linebot import AsyncLineBotApi, WebhookParser
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, ImageSendMessage
import os
import sys
import asyncio
import warnings
from contextlib import asynccontextmanager

import aiohttp

# 過濾 Google ADK 內部的 aiohttp unclosed session 警告
# 這是 Google ADK 的已知問題，我們無法修復
warnings.filterwarnings(
    "ignore", message=".*Unclosed client session.*", category=ResourceWarning)
warnings.filterwarnings(
    "ignore", message=".*Unclosed connector.*", category=ResourceWarning)

# 也過濾所有 aiohttp 相關的 ResourceWarning
warnings.filterwarnings("ignore", category=ResourceWarning, module="aiohttp.*")

# 設定自定義 exception handler 來過濾 aiohttp 的 unclosed session 訊息


def custom_exception_handler(loop, context):
    """
    自定義異常處理器，過濾 Google ADK 相關的 aiohttp 警告訊息。

    Google ADK 內部會產生一些無害的 aiohttp unclosed session 警告，
    此處理器會過濾這些訊息以避免干擾正常日誌輸出。

    Args:
        loop (AbstractEventLoop): asyncio 事件循環
        context (dict): 異常上下文資訊

    Note:
        只過濾特定的 aiohttp 相關警告，其他異常仍會正常處理
    """
    message = context.get('message', '')
    if 'Unclosed client session' in message or 'Unclosed connector' in message:
        # 忽略 Google ADK 內部的無害警告
        return

    # 對於其他異常，使用預設處理器
    default_handler = getattr(loop, '_original_exception_handler', None)
    if default_handler:
        default_handler(loop, context)
    else:
        # 如果沒有原始處理器，就印出來
        print(f"Exception in event loop: {context}")


def set_custom_exception_handler():
    """
    設定自定義異常處理器以過濾 Google ADK 警告。

    在應用程式啟動時呼叫此函數來安裝自定義的異常處理器，
    用於過濾 Google ADK 內部產生的無害 aiohttp 警告訊息。

    Note:
        此函數應該在應用程式生命週期開始時呼叫
    """
    loop = asyncio.get_event_loop()
    if not hasattr(loop, '_original_exception_handler'):
        loop._original_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(custom_exception_handler)


# LINE Bot SDK 相關匯入

# 自訂工具函數匯入

# Google ADK 相關匯入

# =============================================================================
# 環境變數配置和驗證
# =============================================================================
# Google ADK 配置 - 決定使用哪種 Google AI 服務
# 預設使用免費的 Google AI API
USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI") or "FALSE"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""  # Google AI Studio API 金鑰

# LINE Bot 基本配置 - 從環境變數獲取
# LINE Channel Secret，用於驗證 Webhook
channel_secret = os.getenv("ChannelSecret", None)
# LINE Channel Access Token，用於發送訊息
channel_access_token = os.getenv("ChannelAccessToken", None)

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

# 初始化 HTTP 客戶端和 LINE Bot API
# 延遲初始化以避免測試時的 event loop 問題
session = None
async_http_client = None
line_bot_api = None
parser = None


async def init_line_bot():
    """
    初始化 LINE Bot 相關組件。

    建立必要的 LINE Bot SDK 組件，包括 HTTP 客戶端、API 實例和 Webhook 解析器。
    此函數使用全域變數來儲存初始化後的組件實例，避免重複初始化。

    Note:
        此函數需要在應用程式啟動時呼叫，且依賴於全域的環境變數配置
    """
    global session, async_http_client, line_bot_api, parser
    if session is None:
        session = aiohttp.ClientSession()  # aiohttp 異步 HTTP 客戶端
        async_http_client = AiohttpAsyncHttpClient(
            session)  # LINE Bot 非同步 HTTP 客戶端
        line_bot_api = AsyncLineBotApi(
            channel_access_token, async_http_client)  # LINE Bot API 實例
        parser = WebhookParser(channel_secret)  # Webhook 請求解析器，用於驗證請求真實性


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理器。

    使用 FastAPI 的 lifespan 事件處理器來管理應用程式的啟動和關閉流程。
    在啟動時初始化必要的組件，在關閉時清理資源。

    Args:
        app (FastAPI): FastAPI 應用程式實例

    Yields:
        None: 應用程式運行期間

    Note:
        此函數會在應用程式啟動時自動呼叫，負責初始化 LINE Bot 和異常處理器
    """
    # Startup: 初始化組件
    set_custom_exception_handler()  # 設定自定義異常處理器
    await init_line_bot()  # 初始化 LINE Bot 組件
    yield
    # Shutdown: 清理資源
    global session
    if session:
        await session.close()
        print("aiohttp session closed properly")

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="LINE Bot ADK",  # API 文件標題
    description="使用 Google ADK 的多功能 LINE Bot",  # API 文件描述
    version="1.0.0",  # 版本號
    lifespan=lifespan  # 使用 lifespan 事件處理器
)

# =============================================================================
# Google ADK Agent 系統初始化
# =============================================================================

# 建立主要的 Agent 實例，使用 multi_tool_agent 作為核心
root_agent = Agent(
    name="multi_tool_agent",  # Agent 唯一識別名稱
    model="gemini-2.0-flash-exp",  # 使用 Google Gemini 2.0 Flash 模型
    description="多功能助手，提供天氣查詢、時間查詢、短網址生成、公視hihi導覽先生資訊查詢、SET三立電視資訊查詢、影片處理、專業法律諮詢和 Meme 生成功能",  # Agent 功能描述
    instruction=(
        "你是一個多功能助手，專門處理使用者的各種請求。\n\n"
        "【核心原則：主動執行，絕不反問】\n"
        "- 使用者提出需求時，直接完成，不要要求確認。\n"
        "- 請求模糊時，立即選擇最佳合理預設值，自動補全參數。\n"
        "- 就算猜錯也沒關係，錯了使用者會糾正。\n"
        "- 不要解釋流程或工具使用方式，只輸出結果。\n"
        "- 多步驟請求時（如「先A然後B」），要展示每個步驟的結果。\n"
        "- 遇到「隨便」「你決定」等詞時，根據上下文判斷用戶真正需要的功能，主動執行最合理的選項。\n"
        "- 【重要】禁止問「需要嗎？」「要不要？」「可以嗎？」等確認問題，直接執行。\n"
        "- 【重要】看到「幫我用影片回覆」就直接生成影片，不要問任何問題。\n\n"
        "【任務分類邏輯】\n"
        "1. 梗圖 (meme)：\n"
        "   - 提到「meme」「梗圖」「迷因」「搞笑圖片」→ 用 Meme 生成工具。\n"
        "   - 如果要「參考」「範例」「推薦」→ 先用 search_web 找流行梗，再隨機選一個生成。\n"
        "   - 梗圖相關的「隨便」「你決定」→ 直接用去搜尋笑話或梗，並自行決定。\n"
        "   - 如果指定主題但沒文字 → 自動補流行主題相關梗文。\n\n"
        "2. 阿美族語：\n"
        "   - 提到「每日一字詞」「阿美族語」→ 用 get_amis_word_of_the_day。\n\n"
        "3. 法律：\n"
        "   - 提到「法律」「合約」「法院」「條文」→ 用法律諮詢工具。\n\n"
        "4. 天氣：\n"
        "   - 提到「天氣」「氣溫」「晴天」「下雨」→ 用天氣工具。\n"
        "   - 沒指定地點 → 預設「台北」。\n\n"
        "5. 時間：\n"
        "   - 提到「時間」「幾點」「今天幾號」「星期幾」→ 用時間工具。\n"
        "   - 沒指定地點 → 預設「台北」。\n\n"
        "6. 網址：\n"
        "   - 提到「網址」「短網址」或出現 http/https → 用短網址工具。\n"
        "   - 沒有 slug → 傳空字串。\n"
        "   - 「長網址」→ 生成格式：l + 大量0o混合 + ng（預設約300字元，可依用戶需求調整）。\n\n"
        "7. 影片轉錄：\n"
        "   - 提到「影片」「轉錄」「摘要」→ 用 video_transcriber(language=\"zh\")。\n\n"
        "8. AI 影片生成：\n"
        "   - 【僅限明確要求】用戶明確說「用影片」「影片回覆」「生成影片」「AI代言人」→ 用 generate_ai_video。\n"
        "   - 【重要】不要因為提到某個話題就自動用影片，必須用戶明確要求才使用。\n"
        "   - 缺少要講的文字時 → 根據當下要回答的問題自動生成合理內容讓AI代言人說出。\n\n"
        "9. 影視娛樂：\n"
        "   - 提到「節目」「電視」「藝人」「綜藝」「戲劇」→ 用 query_set_knowledge_base。\n\n"
        "10. hihi 導覽先生：\n"
        "   - 提到「hihi」「導覽先生」「公視」→ 用 query_knowledge_base。\n\n"
        "11. 任務 ID 查詢：\n"
        "   - 用戶提供一個 UUID 格式的 ID（如 xxx-xxx-xxx-xxx）→ 用 get_task_status。\n"
        "   - 關鍵詞：「查詢」「狀態」「進度」「完成了嗎」「怎麼樣了」「幫我查」「查一下」配合 ID。\n"
        "   - 單獨發送 UUID 格式字串也視為任務查詢。\n\n"
        "12. 搜尋：\n"
        "   - 以上皆不適用 → 用 search_web。\n\n"
        "13. 其他問題：\n"
        "   - 直接用 AI 回答。\n\n"
        "【額外規則】\n"
        "- 如果工具返回 status='not_relevant' 或回答不完整 → 立即用 search_web 補充。\n"
        "- 工具 status='error' → 先試 search_web，再失敗才回報。\n"
        "- 影片回覆請求：必須執行完整流程：查詢資訊 → 直接用 generate_ai_video 生成影片，不要詢問用戶。\n"
        "- 只能用繁體中文或英文回應，禁止簡體中文或其他語言。\n"
        "- 保持簡短直接，避免多餘廢話。\n\n"
        "知識庫說明：\n"
        "- hihi導覽先生：公視台語節目，包含節目介紹、角色資訊、內容摘要等\n"
        "- SET三立電視：三立電視台節目、藝人、戲劇等相關資訊\n\n"
        "系統提醒：呼叫工具函數時，自動使用當前用戶的真實 ID。\n\n"
        "回應語言規則（重要！）：\n"
        "- 【必須】用繁體中文回應，這是台灣用戶\n"
        "- 【只能】使用繁體中文或英文\n"
        "- 【確認】你的回應必須是台灣人能理解的繁體中文\n"
        "- 保持簡潔直接的回應風格"
    ),
    # 註冊可用的工具函數
    tools=[
        get_weather,
        get_weather_forecast,
        get_current_time,
        create_short_url,
        query_knowledge_base,
        query_set_knowledge_base,
        video_transcriber,
        call_legal_ai,
        generate_meme,
        generate_ai_video,
        get_amis_word_of_the_day,
        search_web,
        get_task_status,
    ],
)

print(f"Agent '{root_agent.name}' 初始化完成。")

# =============================================================================
# 會話管理系統
# =============================================================================

# 全域會話追蹤字典 - 記錄活躍用戶的會話 ID
# 鍵: user_id, 值: session_id
active_sessions = {}

# 全域任務追蹤字典 - 記錄用戶的活躍影片處理任務
# 鍵: user_id, 值: 任務 ID 列表
user_active_tasks = {}

# 任務監控狀態 - 記錄正在監控的任務
# 鍵: task_id, 值: {"user_id": str, "last_status": str, "original_url": str}
monitoring_tasks = {}


# 建立會話服務（用於管理用戶對話狀態）
session_service = InMemorySessionService()


async def get_or_create_session(user_id: str) -> Session:
    """
    獲取或建立用戶會話 (舊版方法，保留備用)。

    管理用戶會話的建立和快取，避免重複建立相同的會話。
    此方法主要用於兼容舊版 Google ADK 的會話管理方式。

    注意：新版 Google ADK Runner 會自動處理會話管理，
    只需要提供 session_id 字串即可，不需要手動創建 Session 物件。
    此函數保留作為兼容性考量。

    Args:
        user_id (str): LINE 用戶 ID，用於識別用戶會話

    Returns:
        Session: Google ADK 會話物件，包含會話狀態和上下文

    Note:
        會話物件會被快取在全域 active_sessions 字典中以提高效能
    """
    if user_id not in active_sessions:
        # 建立新會話
        session_id = f"session_{user_id}"
        session = await session_service.create_session(
            app_name="linebot_adk_app",
            user_id=user_id,
            session_id=session_id
        )
        active_sessions[user_id] = session
        print(
            f"建立新會話: App='linebot_adk_app', User='{user_id}', Session='{session_id}'")
    else:
        # 使用現有會話
        session = active_sessions[user_id]
        print(f"使用現有會話: User='{user_id}', Session='{session.id}'")

    return session


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
        api = line_bot_api
        await api.push_message(user_id, push_msg)
        print(f"[PUSH] 推送訊息給用戶 {user_id}: {message[:50]}...")
    except Exception as e:
        print(f"推送訊息失敗: {e}")


async def handle_comfyui_completion(task_id: str, user_id: str, use_push: bool = True):
    """
    處理 ComfyUI 任務完成後的影片下載和推送

    Args:
        task_id (str): ComfyUI 任務 ID
        user_id (str): 用戶 ID
        use_push (bool): True=用push推送，False=返回影片數據供reply使用
    """
    try:
        print(f"🎬 開始處理 ComfyUI 完成任務: {task_id}, 模式: {'push' if use_push else 'reply'}")

        # 統一的下載邏輯（push 和 reply 都一樣）
        from multi_tool_agent.agents.comfyui_agent import ComfyUIAgent

        # 使用 ComfyUI Agent 來處理
        comfyui_agent = ComfyUIAgent()
        result = await comfyui_agent._check_comfyui_status(task_id)
        if result:
            video_info = comfyui_agent._extract_video_info(result)
            if video_info:
                print(f"🎬 找到影片檔案: {video_info['filename']}")
                video_data = await comfyui_agent._download_comfyui_video(video_info)

                if video_data and len(video_data) > 0:
                    print(f"🎬 影片下載成功，大小: {len(video_data)} bytes")

                    # 使用任務 ID 作為檔案名稱，保持 .mp4 副檔名
                    video_filename = f"{task_id}.mp4"
                    video_file_path = VIDEO_UPLOAD_DIR / video_filename

                    # 檢查檔案是否已存在（避免重複下載）
                    if video_file_path.exists():
                        print(f"🎬 影片檔案已存在於本地: {video_file_path}")
                    else:
                        with open(video_file_path, 'wb') as f:
                            f.write(video_data)
                        print(f"🎬 影片已儲存到 upload 目錄: {video_file_path}")

                    # 根據模式決定如何處理
                    if use_push:
                        # push 模式：推送影片給用戶
                        from multi_tool_agent.utils.line_utils import push_video_with_filename
                        await push_video_with_filename(user_id, video_filename, "AI 影片生成完成", video_info)
                        return {"status": "success", "message": "影片已推送"}
                    else:
                        # reply 模式：返回檔案資訊供 reply 使用
                        return {"status": "success", "video_filename": video_filename, "video_info": video_info}
                else:
                    print(f"❌ 影片下載失敗或檔案為空")
                    return {"status": "error", "message": "影片下載失敗"}
            else:
                print(f"❌ 無法取得影片檔案資訊")
                return {"status": "error", "message": "無法取得影片檔案資訊"}
        else:
            print(f"❌ 無法取得 ComfyUI 工作狀態")
            return {"status": "error", "message": "無法取得工作狀態"}

    except Exception as e:
        print(f"❌ 處理 ComfyUI 完成任務時發生錯誤: {e}")
        # 移除錯誤訊息推送依賴
        if not use_push:
            return {"status": "error", "message": f"處理錯誤: {str(e)}"}


async def monitor_task_status(task_id: str, user_id: str):
    """
    監控單一任務狀態，完成時主動推送

    Args:
        task_id (str): 任務 ID
        user_id (str): 用戶 ID
    """
    max_checks = 120  # 最多檢查 120 次 (120 * 1秒 = 2分鐘)
    check_count = 0

    print(f"開始監控任務 {task_id}")

    # 初始等待 5 秒
    await asyncio.sleep(5)

    while check_count < max_checks:
        try:
            await asyncio.sleep(1)  # 每 1 秒檢查一次
            check_count += 1

            print(f"🔄 [POLLING] 任務 {task_id} 第 {check_count}/{max_checks} 次輪詢檢查...")

            # 使用 ID查詢 agent 的完整邏輯（和手動查詢一樣）
            from multi_tool_agent.agents.id_query_agent import IDQueryAgent
            id_query_agent = IDQueryAgent()

            # 並行查詢所有任務類型（ComfyUI 和影片轉錄）
            # 嘗試查詢各種任務類型
            comfyui_result = await id_query_agent._check_comfyui_task(task_id)
            video_result = await id_query_agent._check_video_transcription_task(task_id)

            if comfyui_result:  # 找到 ComfyUI 任務
                status_result = comfyui_result
            elif video_result:  # 找到影片轉錄任務
                status_result = video_result
            else:
                # 任務還沒出現或已失敗，停止監控
                print(f"📋 [POLLING] 任務 {task_id} 未找到，停止監控")
                break

            task_status = status_result.get("task_status", "unknown")
            task_type = status_result.get("task_type", "unknown")

            print(f"📊 [POLLING] 任務 {task_id} 狀態: {task_status}, 類型: {task_type}")

            # 檢查任務是否完成
            if task_status == "completed":
                # 根據任務類型處理完成邏輯
                if task_type == "comfyui":
                    # ComfyUI 影片生成完成 - 下載並推送影片（背景監控用 push）
                    print(f"🎬 ComfyUI 影片生成完成: {task_id}")
                    await handle_comfyui_completion(task_id, user_id, use_push=True)
                else:
                    # 影片轉錄摘要完成 - 推送文字摘要
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
                # 任務失敗，清理記錄但不推送（避免打擾用戶）
                if user_id in user_active_tasks and task_id in user_active_tasks[user_id]:
                    user_active_tasks[user_id].remove(task_id)
                if task_id in monitoring_tasks:
                    del monitoring_tasks[task_id]

                print(f"任務 {task_id} 失敗，已清理記錄")
                break

            # 更新監控狀態
            if task_id in monitoring_tasks:
                monitoring_tasks[task_id]["last_status"] = task_status

        except Exception as e:
            print(f"監控任務 {task_id} 時發生錯誤: {e}")
            # 監控出錯，清理並停止
            if user_id in user_active_tasks and task_id in user_active_tasks[user_id]:
                user_active_tasks[user_id].remove(task_id)
            if task_id in monitoring_tasks:
                del monitoring_tasks[task_id]
            print(f"任務 {task_id} 監控因錯誤停止")
            break

    # 監控超時清理
    if task_id in monitoring_tasks:
        del monitoring_tasks[task_id]
    print(f"任務 {task_id} 監控結束")


async def monitor_task_completion(task_id: str, user_id: str, original_url: str = ""):
    """
    監控任務完成狀態，完成時自動推送結果給用戶

    Args:
        task_id (str): 任務 ID
        user_id (str): 用戶 ID
        original_url (str): 原始影片 URL
    """
    max_checks = 120  # 最多檢查 120 次 (120 * 1秒 = 2分鐘)
    check_count = 0

    print(f"開始監控任務 {task_id}")

    # 初始等待 5 秒
    await asyncio.sleep(5)

    while check_count < max_checks:
        try:
            await asyncio.sleep(1)  # 每 1 秒檢查一次
            check_count += 1

            print(f"🔄 [POLLING] 任務 {task_id} 第 {check_count}/{max_checks} 次輪詢檢查...")

            # 使用 ID查詢 agent 的完整邏輯
            from multi_tool_agent.agents.id_query_agent import IDQueryAgent
            id_query_agent = IDQueryAgent()

            # 查詢各種任務類型
            comfyui_result = await id_query_agent._check_comfyui_task(task_id)
            video_result = await id_query_agent._check_video_transcription_task(task_id)

            if comfyui_result:  # 找到 ComfyUI 任務
                status_result = comfyui_result
            elif video_result:  # 找到影片轉錄任務
                status_result = video_result
            else:
                # 任務還沒出現，繼續等待
                continue

            task_status = status_result.get("task_status", "unknown")
            task_type = status_result.get("task_type", "unknown")

            print(f"📊 [POLLING] 任務 {task_id} 狀態: {task_status}, 類型: {task_type}")

            # 檢查任務是否完成
            if task_status == "completed":
                print(f"🎉 任務 {task_id} 已完成，推送結果給用戶")

                # 根據任務類型推送結果
                if task_type == "comfyui":
                    # ComfyUI 影片生成完成 - 推送影片
                    await handle_comfyui_completion(task_id, user_id, use_push=True)
                elif task_type == "video_transcription":
                    # 影片轉錄完成 - 推送摘要
                    report = status_result.get("report", "影片轉錄已完成")
                    await push_message_to_user(user_id, report)

                # 清理監控狀態
                if task_id in monitoring_tasks:
                    del monitoring_tasks[task_id]
                print(f"任務 {task_id} 監控結束")
                return

        except Exception as e:
            print(f"監控任務 {task_id} 時發生錯誤: {e}")
            await asyncio.sleep(1)

    # 超時未完成
    print(f"⏰ 任務 {task_id} 監控超時，停止監控")
    if task_id in monitoring_tasks:
        del monitoring_tasks[task_id]


def start_task_monitoring(task_id: str, user_id: str, original_url: str = ""):
    """
    記錄任務資訊，不執行監控（各工具有自己的查詢邏輯）

    Args:
        task_id (str): 任務 ID
        user_id (str): 用戶 ID
        original_url (str): 原始影片 URL
    """
    # 只記錄任務資訊
    monitoring_tasks[task_id] = {
        "user_id": user_id,
        "last_status": "processing",
        "original_url": original_url
    }
    print(f"記錄任務 {task_id} 資訊")

    # 啟動背景監控，任務完成時自動推送
    asyncio.create_task(monitor_task_completion(task_id, user_id, original_url))
    print(f"啟動任務 {task_id} 背景監控")


# =============================================================================
# 影片檔案服務端點 - 支援 LINE Bot 影片推送功能
# =============================================================================


# 影片檔案儲存目錄（使用 /tmp 確保權限正常）
VIDEO_UPLOAD_DIR = Path("/app/upload")
VIDEO_UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    接收影片檔案上傳

    用於接收從 ComfyUI 下載的影片檔案，儲存後提供 HTTPS 存取 URL。
    這是 LINE Bot 影片推送功能的重要組件。

    Returns:
        {"url": "https://adkline.147.5gao.ai/files/{filename}"}
    """
    try:
        # 儲存檔案到本地
        file_path = VIDEO_UPLOAD_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 返回可存取的 HTTPS URL
        file_url = f"https://adkline.147.5gao.ai/files/{file.filename}"

        print(f"✅ 影片檔案上傳成功: {file.filename}")
        print(f"💾 儲存路徑: {file_path}")
        print(f"🌐 存取 URL: {file_url}")

        return {"url": file_url}

    except Exception as e:
        print(f"❌ 影片檔案上傳失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{filename}")
async def get_video(filename: str):
    """
    提供影片檔案下載 (GET 方法)

    這是 LINE 播放影片時會調用的端點，必須支援 GET 方法並返回正確的 Content-Type。
    LINE Bot 的 VideoSendMessage 會使用這個端點來播放影片。

    Args:
        filename: 影片檔案名稱

    Returns:
        FileResponse: 影片檔案回應，設定正確的 Content-Type
    """
    try:
        file_path = VIDEO_UPLOAD_DIR / filename

        if not file_path.exists():
            print(f"❌ 請求的影片檔案不存在: {filename}")
            raise HTTPException(status_code=404, detail="Video file not found")

        print(f"📱 LINE 正在存取影片: {filename}")

        # 返回檔案，設置正確的 Content-Type 和 CORS 標頭
        return FileResponse(
            file_path,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=3600"  # 快取 1 小時
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 影片檔案存取失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/asset/{filename}")
async def get_asset(filename: str):
    """
    提供 asset 檔案下載 (預覽圖、JSON 模板等)

    用於提供預覽圖片和其他靜態資源檔案的存取。

    Args:
        filename: 檔案名稱

    Returns:
        FileResponse: 檔案回應，設定正確的 Content-Type
    """
    try:
        asset_dir = Path("/app/asset")
        file_path = asset_dir / filename

        if not file_path.exists():
            print(f"❌ 請求的 asset 檔案不存在: {filename}")
            raise HTTPException(status_code=404, detail="Asset file not found")

        print(f"📂 存取 asset 檔案: {filename}")

        # 根據檔案副檔名設定 Content-Type
        if filename.endswith('.png'):
            media_type = "image/png"
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            media_type = "image/jpeg"
        elif filename.endswith('.json'):
            media_type = "application/json"
        else:
            media_type = "application/octet-stream"

        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=3600"  # 1小時快取
            }
        )

    except Exception as e:
        print(f"❌ Asset 檔案存取失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# LINE Bot Webhook 處理
# =============================================================================


@app.post("/")
async def handle_callback(request: Request) -> str:
    """
    LINE Bot Webhook 回呼處理函數 - 主要訊息處理入口點。

    處理來自 LINE 平台的 Webhook 請求，負責驗證請求真實性、解析訊息事件，
    並將用戶查詢轉發給 Google ADK Agent 進行處理。這是整個 LINE Bot 的核心處理邏輯。

    處理流程：
    1. 驗證 LINE 請求簽章
    2. 解析 Webhook 事件
    3. 處理文字訊息（主要功能）
    4. 處理圖片訊息（目前僅記錄）
    5. 呼叫 Agent 處理用戶查詢
    6. 根據回應類型發送適當的訊息

    Args:
        request (Request): FastAPI 請求物件，包含 LINE 發送的 Webhook 資料
            - headers: 包含 X-Line-Signature 簽章
            - body: JSON 格式的 Webhook 事件資料

    Returns:
        str: 處理結果，成功時返回 "OK" 字串

    Raises:
        HTTPException: 當請求驗證失敗時拋出 400 錯誤，包含詳細錯誤訊息

    Example:
        當用戶發送 "天氣如何？" 時，此函數會：
        1. 驗證請求真實性
        2. 提取用戶 ID 和訊息內容
        3. 顯示載入動畫
        4. 呼叫 Agent 處理天氣查詢
        5. 回覆天氣資訊給用戶
    """
    # 從請求標頭獲取 LINE 簽章，用於驗證請求真實性
    signature = request.headers["X-Line-Signature"]

    # 獲取請求主體並轉換為字串
    body = await request.body()
    body = body.decode()

    try:
        # 使用 WebhookParser 解析和驗證請求
        # 如果簽章無效會拋出 InvalidSignatureError
        # parser 已經在 lifespan 中初始化
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

            # 立即顯示載入動畫，讓用戶知道 Bot 正在處理
            try:
                before_reply_display_loading_animation(
                    user_id, loading_seconds=60)
            except Exception as e:
                print(f"載入動畫顯示失敗: {e}")

            # ToolContext 會自動管理用戶上下文，不需要手動設定

            # 設定全域用戶 ID 供工具函數使用
            import multi_tool_agent.agent as agent_module
            agent_module.current_user_id = user_id

            # 呼叫 Agent 處理用戶查詢
            response = await call_agent_async(msg, user_id)

            # 檢查是否為 ID 查詢且有影片檔案需要回覆
            video_filename = None
            video_info = None
            if hasattr(call_agent_async, '_last_query_result'):
                last_result = call_agent_async._last_query_result
                if last_result and last_result.get("has_video"):
                    video_filename = last_result.get("video_filename")
                    video_info = last_result.get("video_info")
                    delattr(call_agent_async, '_last_query_result')  # 清理

            if video_filename and video_info:
                # 回覆影片（使用本地檔案）
                print(f"🎬 回覆影片給用戶: {user_id}, 檔案: {video_filename}")
                from multi_tool_agent.utils.line_utils import reply_video_with_filename
                await reply_video_with_filename(event.reply_token, user_id, video_filename, response, video_info)
            else:
                # 一般文字/圖片回應
                reply_messages = await create_reply_messages(response)
                api = line_bot_api
                await api.reply_message(event.reply_token, reply_messages)

        elif event.message.type == "image":
            # 圖片訊息處理（目前僅記錄）
            print(f"收到圖片訊息 from user: {event.source.user_id}")
            return "OK"
        else:
            # 其他訊息類型（語音、影片等）目前不處理
            continue

    return "OK"


# 建立 Runner（用於執行 Agent）
runner = Runner(
    app_name="linebot_adk_app",
    agent=root_agent,
    session_service=session_service
)

print(f"Runner 初始化完成")


async def call_agent_async(query: str, user_id: str) -> str:
    """
    非同步呼叫 Agent 處理用戶查詢 (修正版)

    使用正確的 Google ADK Runner 方式：
    1. 使用全域 runner 實例，避免重複創建
    2. 使用新版 run() 方法 API
    3. 簡化會話管理

    Args:
        query (str): 用戶的文字查詢
        user_id (str): LINE 用戶 ID

    Returns:
        str: Agent 的最終回應文字
    """
    print(f"\n>>> 用戶查詢: {query}")

    # 預設回應文字（當處理失敗時使用）
    final_response_text = "很抱歉，處理您的請求時發生錯誤，請稍後再試。"

    try:
        # 獲取或建立用戶會話
        session = await get_or_create_session(user_id)
        session_id = session.id

        # 將用戶訊息轉換為 Google ADK 格式
        from google.genai import types
        content = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        # 使用 Runner 執行 Agent
        final_response_text = "Agent 沒有產生最終回應。"
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            # 詳細日誌記錄 - 工具調用和回應
            try:
                # 檢查是否為工具調用事件
                if hasattr(event, 'content') and event.content:
                    event_content = event.content

                    # 檢查是否包含工具調用
                    if hasattr(event_content, 'parts') and event_content.parts:
                        for part in event_content.parts:
                            # 工具調用日誌
                            if hasattr(part, 'function_call'):
                                func_call = part.function_call
                                print(f"🔧 [TOOL_CALL] 調用工具: {func_call.name}")
                                if hasattr(func_call, 'args') and func_call.args:
                                    print(f"📥 [TOOL_ARGS] 參數: {dict(func_call.args)}")
                                else:
                                    print(f"📥 [TOOL_ARGS] 無參數")

                            # 工具回應日誌
                            if hasattr(part, 'function_response') and part.function_response is not None:
                                func_response = part.function_response
                                # 嘗試獲取工具名稱，如果失敗則跳過記錄
                                try:
                                    # 確保 func_response 不是 None 並且有 name 屬性
                                    if func_response is not None:
                                        tool_name = getattr(func_response, 'name', None)
                                        if tool_name:
                                            print(f"🔨 [TOOL_RESPONSE] 工具 {tool_name} 回應:")
                                            if hasattr(func_response, 'response') and func_response.response:
                                                response_content = func_response.response
                                                if isinstance(response_content, dict) and response_content:
                                                    # 只記錄重要的工具結果
                                                    if 'status' in response_content or 'report' in response_content:
                                                        import json
                                                        print(f"📤 [TOOL_RESULT] {json.dumps(response_content, ensure_ascii=False)}")
                                                elif isinstance(response_content, str) and response_content.strip():
                                                    print(f"📤 [TOOL_RESULT] {response_content}")
                                except Exception:
                                    # 靜默跳過工具回應記錄錯誤
                                    pass

                            # Agent 思考過程日誌
                            if hasattr(part, 'text') and part.text:
                                text_content = part.text.strip()
                                if text_content and not text_content.startswith('🔧') and not text_content.startswith('📥'):
                                    print(f"🤖 [AGENT_THINKING] {text_content}")

                # 收集最終回應
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    if hasattr(event, 'content') and event.content:
                        # 處理 Content 對象或字串
                        content = event.content
                        if hasattr(content, 'parts') and content.parts:
                            # 提取 parts 中的文字
                            final_response_text = ""
                            for part in content.parts:
                                if hasattr(part, 'text'):
                                    final_response_text += part.text
                        elif hasattr(content, 'text'):
                            final_response_text = content.text
                        elif isinstance(content, str):
                            final_response_text = content
                        else:
                            final_response_text = str(content)

            except Exception as log_error:
                # 日誌記錄失敗不應該影響主流程
                print(f"⚠️ [LOG_ERROR] 事件日誌記錄失敗: {log_error}")

                # 繼續處理最終回應
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    if hasattr(event, 'content') and event.content:
                        content = event.content
                        if hasattr(content, 'parts') and content.parts:
                            final_response_text = ""
                            for part in content.parts:
                                if hasattr(part, 'text'):
                                    final_response_text += part.text
                        elif hasattr(content, 'text'):
                            final_response_text = content.text
                        elif isinstance(content, str):
                            final_response_text = content
                        else:
                            final_response_text = str(content)

        # 任務監控已在工具函數中直接啟動，不需要再解析回應文字

        # 確保有回應內容
        if not final_response_text.strip():
            final_response_text = "很抱歉，系統沒有產生回應，請稍後再試。"

    except Exception as e:
        # 處理所有異常
        error_msg = f"處理請求時發生系統錯誤: {str(e)}"
        print(f"❌ {error_msg}")
        final_response_text = "很抱歉，系統目前遇到一些問題，請稍後再試。"

        # 特殊處理 Google Gemini API 錯誤
        if "500 INTERNAL" in str(e) or "ServerError" in str(e):
            final_response_text = "很抱歉，AI 服務暫時無法使用，請稍後再試。"
            print("Google Gemini API 服務錯誤")
        elif "session" in str(e).lower():
            final_response_text = "很抱歉，會話處理時發生錯誤，請重新開始對話。"
            print("會話管理錯誤")

    # 輸出最終回應到控制台
    print(f"[REPLY] <<< Agent 回應: {final_response_text.strip()}")

    return final_response_text


async def create_reply_messages(agent_response: str):
    """
    根據 Agent 回應創建適當的 LINE 訊息物件

    如果回應包含圖片 URL，會同時回傳文字和圖片訊息。

    Args:
        agent_response (str): Agent 的回應文字

    Returns:
        list: LINE 訊息物件列表
    """
    messages = []

    # 檢查是否包含 meme URL
    import re
    url_pattern = r'https://i\.imgflip\.com/\w+\.jpg'
    meme_urls = re.findall(url_pattern, agent_response)

    if meme_urls:
        # 如果包含 meme URL，先回傳文字，再回傳圖片
        # 移除 URL 後的純文字回應
        text_response = re.sub(url_pattern, '', agent_response).strip()

        if text_response:
            messages.append(TextSendMessage(text=text_response))

        # 添加圖片訊息
        for meme_url in meme_urls:
            messages.append(ImageSendMessage(
                original_content_url=meme_url,
                preview_image_url=meme_url
            ))
    else:
        # 一般文字回應
        messages.append(TextSendMessage(text=agent_response))

    return messages


# =============================================================================
# 測試端點 - 用於直接測試 Agent 功能
# =============================================================================

@app.post("/test/agent")
async def test_agent(request: Request):
    """
    測試端點 - 直接測試 Agent 功能。

    提供 HTTP API 端點用於直接測試 Google ADK Agent 的功能，
    不需要通過 LINE Bot 介面即可驗證 Agent 的回應。
    主要用於開發和測試階段的 Agent 功能驗證。

    Args:
        request (Request): FastAPI 請求物件，應包含 JSON 格式的測試資料

    Returns:
        dict: 測試結果，包含以下欄位：
            - status (str): 測試狀態 ("success" 或 "error")
            - query (str): 原始查詢內容
            - response (str): Agent 的回應內容
            - error (str, optional): 錯誤訊息（當 status 為 "error" 時）

    Raises:
        HTTPException: 當請求格式錯誤時間接拋出

    Example:
        POST /test/agent
        Content-Type: application/json

        {
            "query": "天氣如何？",
            "user_id": "test_user_123"
        }

        Response:
        {
            "status": "success",
            "query": "天氣如何？",
            "response": "台北市今天天氣晴朗，氣溫約 25°C。"
        }
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        user_id = data.get("user_id", "test_user")

        if not query:
            return {"error": "Missing query parameter"}

        # 呼叫 Agent 處理查詢
        response = await call_agent_async(query, user_id)

        return {
            "status": "success",
            "query": query,
            "response": response
        }

    except Exception as e:
        return {"error": str(e)}
