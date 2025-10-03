"""
知識庫 Agent
處理 hihi 導覽先生知識庫和 SET 三立電視知識庫查詢功能
"""

import os
import logging
from typing import Dict, Any

from ..clients.fastgpt_client import FastGPTClient

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """
    知識庫 Agent
    提供 hihi 導覽先生和 SET 三立電視知識庫查詢功能
    """

    def __init__(self, name="knowledge", description="提供 hihi 導覽先生和 SET 三立電視知識庫查詢功能"):
        self.name = name
        self.description = description

    async def execute(self, **kwargs) -> dict:
        """
        執行知識庫查詢

        Args:
            knowledge_type: 知識庫類型 ('hihi' 或 'set')
            question: 要查詢的問題
            user_id: 用戶ID

        Returns:
            dict: 查詢結果字典
                - status: "success", "error", 或 "not_relevant"
                - report: 成功時的報告訊息
                - error_message: 錯誤時的錯誤訊息
        """
        try:
            # 檢查必要參數
            required_params = ['knowledge_type', 'question', 'user_id']
            for param in required_params:
                if param not in kwargs:
                    return {
                        "status": "error",
                        "error_message": f"缺少必要參數: {param}"
                    }

            knowledge_type = kwargs['knowledge_type']
            question = kwargs['question']
            user_id = kwargs['user_id']

            if knowledge_type == 'hihi':
                return await self.query_hihi(question, user_id)
            elif knowledge_type == 'set':
                return await self.query_set(question, user_id)
            else:
                return {
                    "status": "error",
                    "error_message": f"不支援的知識庫類型: {knowledge_type}"
                }

        except Exception as e:
            logger.error(f"查詢知識庫時發生錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"查詢知識庫時發生未預期的錯誤: {str(e)}"
            }

    async def query_hihi(self, question: str, user_id: str) -> dict:
        """
        查詢公視 hihi 導覽先生知識庫

        Args:
            question: 要查詢的問題
            user_id: 用戶 ID

        Returns:
            dict: 查詢結果
        """
        # 從全局變數獲取真實用戶 ID
        from ..agent import current_user_id
        real_user_id = current_user_id or user_id
        logger.info(f"hihi 知識庫查詢: {question}, 用戶: {real_user_id}")

        # 配置
        api_url = os.getenv("FASTGPT_API_URL", "http://llm.5gao.ai:1987/api/v1")
        api_key = os.getenv("FASTGPT_HIHI_API_KEY", "")

        if not api_key:
            return {
                "status": "error",
                "error_message": "抱歉，hihi 知識庫服務暫時無法使用。"
            }

        try:
            # 使用 FastGPT Client
            client = FastGPTClient(api_url, api_key)
            response = await client.chat(question, chat_id=real_user_id)

            if not response:
                return {
                    "status": "error",
                    "error_message": "知識庫服務無回應"
                }

            # 提取內容
            content = client.extract_content(response)
            if not content:
                return {
                    "status": "not_relevant",
                    "error_message": "知識庫沒有回應"
                }

            # 檢查是否為無效回答
            no_answer_keywords = ["不知道", "無法回答", "沒有相關", "找不到", "不清楚", "無相關資訊"]
            if any(keyword in content for keyword in no_answer_keywords):
                return {
                    "status": "not_relevant",
                    "error_message": "知識庫中沒有找到相關資訊"
                }

            return {
                "status": "success",
                "report": content
            }

        except Exception as e:
            logger.error(f"hihi 知識庫查詢失敗: {e}")
            return {
                "status": "error",
                "error_message": "抱歉，hihi 知識庫服務目前遇到問題。"
            }

    async def query_set(self, question: str, user_id: str) -> dict:
        """
        查詢 SET 三立電視知識庫

        Args:
            question: 要查詢的問題
            user_id: 用戶 ID

        Returns:
            dict: 查詢結果
        """
        # 從全局變數獲取真實用戶 ID
        from ..agent import current_user_id
        real_user_id = current_user_id or user_id
        logger.info(f"SET 知識庫查詢: {question}, 用戶: {real_user_id}")

        # 配置
        api_url = os.getenv("FASTGPT_API_URL", "http://llm.5gao.ai:1987/api/v1")
        api_key = os.getenv("FASTGPT_SET_API_KEY", "")

        if not api_key:
            return {
                "status": "error",
                "error_message": "抱歉，SET 知識庫服務暫時無法使用。"
            }

        try:
            # 使用 FastGPT Client（加上 set_ 前綴區分對話）
            client = FastGPTClient(api_url, api_key)
            response = await client.chat(question, chat_id=f"set_{real_user_id}")

            if not response:
                return {
                    "status": "error",
                    "error_message": "知識庫服務無回應"
                }

            # 提取內容
            content = client.extract_content(response)
            if not content:
                return {
                    "status": "not_relevant",
                    "error_message": "知識庫沒有回應"
                }

            # 檢查是否為無效回答
            no_answer_keywords = ["不知道", "無法回答", "沒有相關", "找不到", "不清楚", "無相關資訊"]
            if any(keyword in content for keyword in no_answer_keywords):
                return {
                    "status": "not_relevant",
                    "error_message": "知識庫中沒有找到相關資訊"
                }

            return {
                "status": "success",
                "report": content
            }

        except Exception as e:
            logger.error(f"SET 知識庫查詢失敗: {e}")
            return {
                "status": "error",
                "error_message": "抱歉，SET 知識庫服務目前遇到問題。"
            }
