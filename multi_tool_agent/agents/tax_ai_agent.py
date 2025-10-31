"""
稅務 AI Agent - 處理美國個人所得稅相關問題 (IRS)
"""
import logging
from typing import Dict, Any, Optional
from ..clients.tax_ai_client import TaxAIClient

logger = logging.getLogger(__name__)


class TaxAIAgent:
    """美國稅務 AI 代理 (IRS - 個人所得稅諮詢)"""

    def __init__(self):
        self.client = TaxAIClient()

    async def execute(
        self,
        question: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        執行美國稅務諮詢 (IRS)

        Args:
            question: 美國個人所得稅相關問題
            user_id: 使用者 ID (用作 session_id 以維持對話上下文)

        Returns:
            Dict 包含:
                - status: "success" 或 "error"
                - report: 稅務 AI 回應 (當 status="success" 時)
                - error_message: 錯誤訊息 (當 status="error" 時)

        Note:
            本工具僅適用於美國國稅局(IRS)的個人所得稅諮詢
        """
        try:
            # 使用 user_id 作為 session_id,為每個使用者維持獨立的對話上下文
            session_id = user_id or "anonymous"

            logger.info(f"稅務 AI Agent 開始處理問題: {question} (session: {session_id})")

            # 呼叫 Tax AI Client
            result = await self.client.chat(
                message=question,
                session_id=session_id
            )

            if result["status"] == "success":
                # 格式化回應
                response_message = result["message"]
                fact_graph = result.get("fact_graph_data")

                # 如果有 fact_graph_data,可以在這裡做進一步處理
                # 目前先簡單回傳 AI 的訊息
                logger.info(f"稅務 AI 回應成功: {response_message}")

                return {
                    "status": "success",
                    "report": response_message
                }
            else:
                logger.error(f"稅務 AI 回應錯誤: {result.get('error_message')}")
                return {
                    "status": "error",
                    "error_message": result.get("error_message", "未知錯誤")
                }

        except Exception as e:
            logger.error(f"稅務 AI Agent 執行失敗: {e}")
            return {
                "status": "error",
                "error_message": f"稅務諮詢失敗: {str(e)}"
            }
