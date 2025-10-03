"""
LINE 訊息處理
處理訊息的推送、回覆和建立
"""

import re
import logging
from linebot.models import TextSendMessage, ImageSendMessage
from .client import get_line_bot_api

logger = logging.getLogger(__name__)


async def push_message_to_user(user_id: str, message: str):
    """
    主動推送訊息給用戶

    Args:
        user_id (str): LINE 用戶 ID
        message (str): 要推送的訊息內容
    """
    try:
        push_msg = TextSendMessage(text=message)
        api = get_line_bot_api()
        await api.push_message(user_id, push_msg)
        logger.info(f"[PUSH] 推送訊息給用戶 {user_id}: {message[:50]}...")
    except Exception as e:
        logger.error(f"推送訊息失敗: {e}")


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
