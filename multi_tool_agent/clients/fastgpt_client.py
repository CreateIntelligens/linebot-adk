"""
FastGPT API 客戶端

封裝 FastGPT 知識庫服務的 HTTP API 調用。
"""

import logging
import aiohttp
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class FastGPTClient:
    """
    FastGPT API 客戶端

    封裝 FastGPT 知識庫服務的 API 調用，支援對話管理和知識庫查詢。
    """

    def __init__(self, api_url: str, api_key: str):
        """
        初始化 FastGPT 客戶端

        Args:
            api_url: FastGPT API 端點 URL
            api_key: API 認證金鑰
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key

    async def chat(
        self,
        question: str,
        chat_id: Optional[str] = None,
        stream: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        發送聊天請求到 FastGPT 知識庫

        Args:
            question: 要查詢的問題
            chat_id: 對話 ID（用於會話管理，可選）
            stream: 是否使用串流模式（預設關閉）

        Returns:
            API 回應字典，失敗時返回 None
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "messages": [
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                "stream": stream
            }

            # 如果提供了 chat_id，加入請求中用於會話管理
            if chat_id:
                data["chatId"] = chat_id

            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"FastGPT API 返回錯誤: {response.status} - {error_text}")
                        return None

        except Exception as e:
            logger.error(f"調用 FastGPT API 時發生錯誤: {e}")
            return None

    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        從 FastGPT 回應中提取內容

        Args:
            response: FastGPT API 回應字典

        Returns:
            提取的文字內容，失敗時返回空字串
        """
        try:
            choices = response.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""
        except Exception as e:
            logger.error(f"提取 FastGPT 內容時發生錯誤: {e}")
            return ""
