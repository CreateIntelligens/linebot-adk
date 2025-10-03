"""
LINE Bot 客戶端
管理 LINE Bot API 的初始化和基本操作
"""

import os
import aiohttp
from linebot import AsyncLineBotApi, WebhookParser
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient

# 全域變數
session = None
async_http_client = None
line_bot_api = None
parser = None


async def init_line_bot():
    """
    初始化 LINE Bot 相關組件

    建立必要的 LINE Bot SDK 組件，包括 HTTP 客戶端、API 實例和 Webhook 解析器。
    此函數使用全域變數來儲存初始化後的組件實例，避免重複初始化。
    """
    global session, async_http_client, line_bot_api, parser

    if session is None:
        channel_access_token = os.getenv("ChannelAccessToken", "")
        channel_secret = os.getenv("ChannelSecret", "")

        session = aiohttp.ClientSession()
        async_http_client = AiohttpAsyncHttpClient(session)
        line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)
        parser = WebhookParser(channel_secret)


def get_line_bot_api():
    """
    獲取 LINE Bot API 實例

    Returns:
        AsyncLineBotApi: LINE Bot API 實例
    """
    return line_bot_api


def get_parser():
    """
    獲取 Webhook 解析器

    Returns:
        WebhookParser: Webhook 解析器實例
    """
    return parser


async def close_line_bot():
    """
    關閉 LINE Bot 相關資源
    """
    global session, async_http_client, line_bot_api, parser

    if session:
        await session.close()
        session = None
        async_http_client = None
        line_bot_api = None
        parser = None
