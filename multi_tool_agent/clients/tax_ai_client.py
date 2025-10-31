"""
美國稅務 AI Client - 串接 Fact Graph + LLM API (IRS)
"""
import os
import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TaxAIClient:
    """美國稅務 AI 客戶端 (IRS - 個人所得稅)"""

    def __init__(self):
        self.api_base_url = os.getenv("TAX_AI_API_URL", "http://10.9.0.32:8897")
        self.chat_endpoint = f"{self.api_base_url}/api/chat"
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        與美國稅務 AI (IRS) 進行對話

        Args:
            message: 使用者訊息 (關於美國個人所得稅的問題)
            session_id: 會話 ID (可選,用於維持對話上下文)

        Returns:
            Dict 包含:
                - status: "success" 或 "error"
                - message: AI 回應訊息
                - fact_graph_data: Fact Graph 資料 (可選)
                - error_message: 錯誤訊息 (當 status="error" 時)

        Note:
            本 API 僅處理美國國稅局(IRS)的個人所得稅問題
        """
        try:
            payload = {
                "message": message,
                "session_id": session_id or "default"
            }

            logger.info(f"呼叫稅務 AI API: {self.chat_endpoint}")
            logger.debug(f"請求內容: {payload}")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.chat_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"稅務 AI 回應成功")
                        logger.debug(f"回應內容: {data}")

                        return {
                            "status": "success",
                            "message": data.get("message", ""),
                            "fact_graph_data": data.get("fact_graph_data")
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"稅務 AI API 回應錯誤 {response.status}: {error_text}")
                        return {
                            "status": "error",
                            "error_message": f"API 回應錯誤 {response.status}: {error_text}"
                        }

        except aiohttp.ClientError as e:
            logger.error(f"稅務 AI API 連線錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"連線錯誤: {str(e)}"
            }
        except Exception as e:
            logger.error(f"稅務 AI 發生未預期錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"未預期錯誤: {str(e)}"
            }
