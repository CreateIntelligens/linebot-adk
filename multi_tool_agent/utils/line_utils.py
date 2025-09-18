# =============================================================================
# LINE Bot 工具函數
# 包含訊息推送、載入動畫等 LINE Bot 相關功能
# =============================================================================

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def push_video_to_user(user_id: str, video_data: bytes, text_content: str, video_info: dict = None):
    """
    推送影片給用戶

    Args:
        user_id (str): LINE 用戶 ID
        video_data (bytes): 影片檔案二進制數據
        text_content (str): 影片內容文字
        video_info (dict, optional): 影片資訊
    """
    temp_video_path = None
    temp_thumb_path = None

    try:
        # 動態導入避免循環依賴
        from linebot import AsyncLineBotApi
        from linebot.models import VideoSendMessage, TextSendMessage
        from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
        import aiohttp
        import uuid
        from pathlib import Path

        # 初始化 LINE Bot API
        async with aiohttp.ClientSession() as session:
            async_http_client = AiohttpAsyncHttpClient(session)
            line_bot_api = AsyncLineBotApi(
                channel_access_token=os.getenv("ChannelAccessToken"),
                async_http_client=async_http_client
            )

        if video_data and len(video_data) > 0:
            # 創建臨時檔案保存影片
            from .video_utils import create_temp_video_path, generate_thumbnail_from_video, cleanup_temp_files
            from .http_utils import upload_video_to_https_server, upload_image_to_https_server

            temp_video_path = create_temp_video_path()

            with open(temp_video_path, 'wb') as temp_file:
                temp_file.write(video_data)

            logger.info(f"影片已下載到本地: {temp_video_path}")

            # 產生並上傳預覽圖
            preview_https_url = None
            try:
                temp_thumb_path = generate_thumbnail_from_video(temp_video_path)
                if temp_thumb_path:
                    with open(temp_thumb_path, 'rb') as thumb_file:
                        thumb_data = thumb_file.read()

                    thumb_filename = Path(temp_thumb_path).name
                    preview_https_url = await upload_image_to_https_server(thumb_data, thumb_filename)
            except Exception as e:
                logger.error(f"❌ 產生或上傳預覽圖失敗: {e}")

            # 上傳影片
            https_url = await upload_video_to_https_server(video_data, video_info['filename'])

            if https_url:
                # 如果沒有預覽圖URL，就用影片URL作為備用
                final_preview_url = preview_https_url or https_url

                video_message = VideoSendMessage(
                    original_content_url=https_url,
                    preview_image_url=final_preview_url
                )
                await line_bot_api.push_message(user_id, video_message)
                logger.info(f"[PUSH] ✅ 影片已成功推送給用戶: {https_url}")
            else:
                logger.error("❌ 影片上傳到 HTTPS 伺服器失敗")
                raise Exception("Failed to upload video to HTTPS server")

        else:
            raise Exception("Video data is empty or invalid")

    except Exception as e:
        logger.error(f"❌ 推送影片時發生錯誤: {e}")
        # 不推送錯誤訊息，避免打擾用戶

    finally:
        # 清理臨時檔案
        cleanup_temp_files(temp_video_path, temp_thumb_path)


async def push_error_message_to_user(user_id: str, error_message: str):
    """
    推送錯誤訊息給用戶

    Args:
        user_id (str): LINE 用戶 ID
        error_message (str): 錯誤訊息內容
    """
    try:
        # 動態導入避免循環依賴
        from linebot import AsyncLineBotApi
        from linebot.models import TextSendMessage
        from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
        import aiohttp

        # 初始化 LINE Bot API
        async with aiohttp.ClientSession() as session:
            async_http_client = AiohttpAsyncHttpClient(session)
            line_bot_api = AsyncLineBotApi(
                channel_access_token=os.getenv("ChannelAccessToken"),
                async_http_client=async_http_client
            )

        message = TextSendMessage(text=f"❌ {error_message}")
        await line_bot_api.push_message(user_id, message)
        logger.info(f"[PUSH] ✅ 錯誤訊息已推送給用戶")

    except Exception as e:
        logger.error(f"推送錯誤訊息時發生錯誤: {e}")


async def push_message_to_user(user_id: str, message: str):
    """
    主動推送訊息給用戶

    Args:
        user_id (str): LINE 用戶 ID
        message (str): 要推送的訊息內容
    """
    try:
        # 動態導入避免循環依賴
        from linebot import AsyncLineBotApi
        from linebot.models import TextSendMessage
        from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
        import aiohttp

        # 初始化 LINE Bot API
        async with aiohttp.ClientSession() as session:
            async_http_client = AiohttpAsyncHttpClient(session)
            line_bot_api = AsyncLineBotApi(
                channel_access_token=os.getenv("ChannelAccessToken"),
                async_http_client=async_http_client
            )

        push_msg = TextSendMessage(text=message)
        await line_bot_api.push_message(user_id, push_msg)
        logger.info(f"[PUSH] 推送訊息給用戶 {user_id}: {message[:50]}...")

    except Exception as e:
        logger.error(f"推送訊息失敗: {e}")


def display_loading_animation(line_user_id: str, loading_seconds: int = 5):
    """
    在回覆前顯示 LINE Bot 載入動畫

    Args:
        line_user_id (str): LINE 用戶 ID
        loading_seconds (int): 載入動畫持續秒數，預設 5 秒，最大 60 秒
    """
    import requests

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


async def create_reply_messages(agent_response: str):
    """
    根據 Agent 回應創建適當的 LINE 訊息物件

    如果回應包含圖片 URL，會同時回傳文字和圖片訊息。

    Args:
        agent_response (str): Agent 的回應文字

    Returns:
        list: LINE 訊息物件列表
    """
    import re

    messages = []

    # 檢查是否包含 meme URL
    url_pattern = r'https://i\.imgflip\.com/\w+\.jpg'
    meme_urls = re.findall(url_pattern, agent_response)

    if meme_urls:
        # 如果包含 meme URL，先回傳文字，再回傳圖片
        # 移除 URL 後的純文字回應
        text_response = re.sub(url_pattern, '', agent_response).strip()

        if text_response:
            from linebot.models import TextSendMessage
            messages.append(TextSendMessage(text=text_response))

        # 添加圖片訊息
        from linebot.models import ImageSendMessage
        for meme_url in meme_urls:
            messages.append(ImageSendMessage(
                original_content_url=meme_url,
                preview_image_url=meme_url
            ))
    else:
        # 一般文字回應
        from linebot.models import TextSendMessage
        messages.append(TextSendMessage(text=agent_response))

    return messages


async def reply_video_to_user(reply_token: str, user_id: str, video_data: bytes, text_content: str, video_info: dict = None):
    """
    回覆影片給用戶（用於主動查詢時的 reply）

    Args:
        reply_token (str): LINE reply token
        user_id (str): LINE 用戶 ID
        video_data (bytes): 影片檔案二進制數據
        text_content (str): 影片內容文字
        video_info (dict, optional): 影片資訊
    """
    temp_video_path = None
    temp_thumb_path = None

    try:
        # 動態導入避免循環依賴
        from linebot import AsyncLineBotApi
        from linebot.models import VideoSendMessage, TextSendMessage
        from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
        import aiohttp
        import uuid
        from pathlib import Path

        # 初始化 LINE Bot API
        async with aiohttp.ClientSession() as session:
            async_http_client = AiohttpAsyncHttpClient(session)
            line_bot_api = AsyncLineBotApi(
                channel_access_token=os.getenv("ChannelAccessToken"),
                async_http_client=async_http_client
            )

        if video_data and len(video_data) > 0:
            # 創建臨時檔案保存影片
            from .video_utils import create_temp_video_path, generate_thumbnail_from_video, cleanup_temp_files
            from .http_utils import upload_video_to_https_server, upload_image_to_https_server

            temp_video_path = create_temp_video_path()

            # 寫入影片檔案
            with open(temp_video_path, 'wb') as f:
                f.write(video_data)
            logger.info(f"影片已寫入臨時檔案: {temp_video_path}")

            # 生成縮圖
            temp_thumb_path = await generate_thumbnail_from_video(temp_video_path)
            preview_https_url = None

            if temp_thumb_path:
                # 上傳縮圖到 HTTPS 伺服器
                with open(temp_thumb_path, 'rb') as f:
                    thumb_data = f.read()
                thumb_filename = f"thumb_{uuid.uuid4().hex}.jpg"
                preview_https_url = await upload_image_to_https_server(thumb_data, thumb_filename)
                logger.info(f"縮圖已上傳: {preview_https_url}")

            # 上傳影片到 HTTPS 伺服器
            https_url = await upload_video_to_https_server(video_data, video_info['filename'])

            if https_url:
                logger.info(f"影片已上傳: {https_url}")

                # 使用預覽圖或影片 URL 作為預覽
                final_preview_url = preview_https_url if preview_https_url else https_url

                # 建立影片訊息
                video_message = VideoSendMessage(
                    original_content_url=https_url,
                    preview_image_url=final_preview_url
                )

                # 回覆影片訊息
                await line_bot_api.reply_message(reply_token, video_message)
                logger.info(f"🎬 [REPLY] 影片已成功回覆給用戶: {user_id}")
            else:
                raise Exception("Failed to upload video to HTTPS server")
        else:
            # 如果沒有影片數據，回覆文字訊息
            text_message = TextSendMessage(
                text=f"❌ 影片數據無效\n\n📝 查詢內容：{text_content}"
            )
            await line_bot_api.reply_message(reply_token, text_message)

    except Exception as e:
        logger.error(f"❌ 回覆影片時發生錯誤: {e}")
        try:
            # 發送備用訊息
            fallback_message = TextSendMessage(
                text=f"🎬 影片生成完成，但回覆時發生問題。\n\n📝 內容：{text_content[:50]}..."
            )
            await line_bot_api.reply_message(reply_token, fallback_message)
        except Exception as reply_error:
            logger.error(f"❌ 回覆備用訊息也失敗: {reply_error}")

    finally:
        # 清理臨時檔案
        cleanup_temp_files(temp_video_path, temp_thumb_path)


async def reply_video_with_filename(reply_token: str, user_id: str, video_filename: str, text_content: str, video_info: dict = None):
    """
    使用本地檔案名稱回覆影片給用戶（用於已儲存到 upload 目錄的影片）

    Args:
        reply_token (str): LINE reply token
        user_id (str): LINE 用戶 ID
        video_filename (str): 影片檔案名稱（位於 upload 目錄）
        text_content (str): 影片內容文字
        video_info (dict, optional): 影片資訊
    """
    try:
        # 動態導入避免循環依賴
        from linebot.models import VideoSendMessage, TextSendMessage

        # 建構影片 URL（使用本地 /files/{filename} 端點）
        video_url = f"https://adkline.147.5gao.ai/files/{video_filename}"
        preview_url = "https://adkline.147.5gao.ai/asset/aikka.png"  # 使用固定預覽圖

        logger.info(f"使用本地影片檔案回覆: {video_filename}")
        logger.info(f"影片 URL: {video_url}")

        # 建立影片訊息
        video_message = VideoSendMessage(
            original_content_url=video_url,
            preview_image_url=preview_url
        )

        # 使用全域 LINE Bot API 實例（由 main.py 初始化）
        # 動態獲取全域實例
        import sys
        main_module = sys.modules.get('main')
        if main_module and hasattr(main_module, 'line_bot_api'):
            line_bot_api = main_module.line_bot_api
            # 回覆影片訊息
            await line_bot_api.reply_message(reply_token, video_message)
            logger.info(f"🎬 [REPLY] 影片已成功回覆給用戶: {user_id}, 檔案: {video_filename}")
        else:
            raise Exception("LINE Bot API instance not found")

    except Exception as e:
        logger.error(f"❌ 使用檔案名稱回覆影片時發生錯誤: {e}")
        # 不發送錯誤訊息，避免打擾用戶


async def push_video_with_filename(user_id: str, video_filename: str, text_content: str, video_info: dict = None):
    """
    使用本地檔案名稱推送影片給用戶（用於已儲存到 upload 目錄的影片）

    Args:
        user_id (str): LINE 用戶 ID
        video_filename (str): 影片檔案名稱（位於 upload 目錄）
        text_content (str): 影片內容文字
        video_info (dict, optional): 影片資訊
    """
    try:
        # 動態導入避免循環依賴
        from linebot.models import VideoSendMessage

        # 建構影片 URL（使用本地 /files/{filename} 端點）
        video_url = f"https://adkline.147.5gao.ai/files/{video_filename}"
        preview_url = "https://adkline.147.5gao.ai/asset/aikka.png"  # 使用固定預覽圖

        logger.info(f"使用本地影片檔案推送: {video_filename}")
        logger.info(f"影片 URL: {video_url}")

        # 建立影片訊息
        video_message = VideoSendMessage(
            original_content_url=video_url,
            preview_image_url=preview_url
        )

        # 使用全域 LINE Bot API 實例（由 main.py 初始化）
        import sys
        main_module = sys.modules.get('main')
        if main_module and hasattr(main_module, 'line_bot_api'):
            line_bot_api = main_module.line_bot_api
            # 推送影片訊息
            await line_bot_api.push_message(user_id, video_message)
            logger.info(f"🎬 [PUSH] 影片已成功推送給用戶: {user_id}, 檔案: {video_filename}")
        else:
            raise Exception("LINE Bot API instance not found")

    except Exception as e:
        logger.error(f"❌ 使用檔案名稱推送影片時發生錯誤: {e}")
        # 不發送錯誤訊息，避免打擾用戶
