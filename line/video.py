"""
LINE Bot 影片處理
處理影片的推送和回覆功能
"""

import logging
from line.client import get_line_bot_api

logger = logging.getLogger(__name__)


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

        # 使用 LINE Bot API 推送
        line_bot_api = get_line_bot_api()
        await line_bot_api.push_message(user_id, video_message)
        logger.info(f"🎬 [PUSH] 影片已成功推送給用戶: {user_id}, 檔案: {video_filename}")

    except Exception as e:
        logger.error(f"❌ 使用檔案名稱推送影片時發生錯誤: {e}")


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
        from linebot.models import VideoSendMessage

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

        # 使用 LINE Bot API 回覆
        line_bot_api = get_line_bot_api()
        await line_bot_api.reply_message(reply_token, video_message)
        logger.info(f"🎬 [REPLY] 影片已成功回覆給用戶: {user_id}, 檔案: {video_filename}")

    except Exception as e:
        logger.error(f"❌ 使用檔案名稱回覆影片時發生錯誤: {e}")
