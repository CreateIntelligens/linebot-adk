"""
LINE Bot 載入動畫
處理載入動畫的顯示
"""

import os
import json
import requests


def display_loading_animation(line_user_id: str, loading_seconds: int = 5):
    """
    在回覆前顯示 LINE Bot 載入動畫

    Args:
        line_user_id (str): LINE 用戶 ID
        loading_seconds (int): 載入動畫持續秒數，預設 5 秒，最大 60 秒
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
