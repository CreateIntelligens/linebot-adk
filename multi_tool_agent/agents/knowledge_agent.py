"""
知識庫 Agent
處理 hihi 導覽先生知識庫和 SET 三立電視知識庫查詢功能
"""

import os
import asyncio
import aiohttp
from typing import Optional


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
            return {
                "status": "error",
                "error_message": f"查詢知識庫時發生未預期的錯誤: {str(e)}"
            }

    async def query_hihi(self, question: str, user_id: str) -> dict:
        """
        查詢公視hihi導覽先生知識庫

        使用 FastGPT API 查詢公視台語節目「hihi導覽先生」相關內容，支援上下文對話管理。
        可回答節目介紹、角色資訊、內容摘要等相關問題。

        Args:
            question (str): 要查詢的問題或內容
            user_id (str): 必須傳入用戶的真實 ID，用於維持每個用戶的獨立對話上下文

        Returns:
            dict: 包含查詢結果的字典
                - status: "success", "error", 或 "not_relevant"
                - report: 成功時的報告訊息
                - error_message: 錯誤時的錯誤訊息

        Example:
            >>> agent = KnowledgeAgent()
            >>> result = await agent.query_hihi("hihi先生是誰？", user_id)
            >>> print(result.report)
            🧠 知識庫回答：hihi先生是公視台語節目的主角...
        """
        # 從全局變數或參數獲取真實用戶 ID
        from ..agent import current_user_id
        real_user_id = current_user_id or user_id
        print(f"hihi導覽先生知識庫查詢: {question}, 用戶ID: {real_user_id} (ADK傳入: {user_id})")

        # FastGPT API 配置 - 從環境變數讀取
        api_url = os.getenv(
            "FASTGPT_API_URL") or "http://llm.5gao.ai:1987/api/v1/chat/completions"
        api_key = os.getenv("FASTGPT_HIHI_API_KEY") or ""

        # 檢查必要的配置
        if not api_key:
            return {
                "status": "error",
                "error_message": "抱歉，目前知識庫服務暫時無法使用，請稍後再試。如果是關於 hihi 先生的問題，建議直接觀看公視節目獲取最新資訊。"
            }

        # 設定請求標頭
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 建構請求資料，包含 chatId 用於會話管理
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "stream": False,  # 不使用串流模式
            "chatId": real_user_id  # 使用真實用戶ID作為對話識別
        }

        try:
            # 使用 aiohttp 發送 POST 請求
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.post(
                    api_url,
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 從回應中提取答案內容
                        choices = result.get("choices", [])
                        if choices:
                            content = choices[0].get(
                                "message", {}).get("content", "")

                            # 檢查回答是否包含「不知道」、「無法回答」等關鍵詞
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
                        else:
                            return {
                                "status": "not_relevant",
                                "error_message": "知識庫沒有回應"
                            }
                    else:
                        # API 回應錯誤
                        if response.status == 401:
                            return {
                                "status": "error",
                                "error_message": "抱歉，知識庫服務認證失效，請稍後再試。建議直接觀看公視 hihi 先生節目獲取最新資訊。"
                            }
                        elif response.status == 403:
                            return {
                                "status": "error",
                                "error_message": "抱歉，知識庫服務暫時無法存取，請稍後再試。"
                            }
                        else:
                            return {
                                "status": "error",
                                "error_message": "抱歉，知識庫服務暫時忙碌中，請稍後再試。如果急需資訊，建議直接觀看公視節目。"
                            }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error_message": "抱歉，知識庫查詢超時了，請稍後再試。如果急需 hihi 先生相關資訊，建議直接觀看公視節目。"
            }
        except Exception as e:
            # 捕獲所有其他異常，避免暴露技術細節
            return {
                "status": "error",
                "error_message": "抱歉，知識庫服務目前遇到一些問題，請稍後再試。如果是關於 hihi 先生的問題，建議直接觀看公視節目獲取最新資訊。"
            }

    async def query_set(self, question: str, user_id: str) -> dict:
        """
        查詢SET三立電視知識庫

        使用 FastGPT API 查詢三立電視相關內容，支援上下文對話管理。
        可回答三立電視台節目介紹、藝人資訊、節目內容等相關問題。

        Args:
            question (str): 要查詢的問題或內容
            user_id (str): 必須傳入用戶的真實 ID，用於維持每個用戶的獨立對話上下文

        Returns:
            dict: 包含查詢結果的字典
                - status: "success", "error", 或 "not_relevant"
                - report: 成功時的報告訊息
                - error_message: 錯誤時的錯誤訊息

        Example:
            >>> agent = KnowledgeAgent()
            >>> result = await agent.query_set("三立有什麼節目？", user_id)
            >>> print(result["report"])
            📺 SET三立電視回答：三立電視台有多個頻道，包含戲劇、綜藝、新聞等節目...
        """
        # 從全局變數或參數獲取真實用戶 ID
        from ..agent import current_user_id
        real_user_id = current_user_id or user_id
        print(f"SET三立知識庫查詢: {question}, 用戶ID: {real_user_id} (ADK傳入: {user_id})")

        # FastGPT API 配置 - 從環境變數讀取
        api_url = os.getenv(
            "FASTGPT_API_URL") or "http://llm.5gao.ai:1987/api/v1/chat/completions"
        api_key = os.getenv("FASTGPT_SET_API_KEY") or ""

        # 檢查必要的配置
        if not api_key:
            return {
                "status": "error",
                "error_message": "抱歉，目前SET三立電視知識庫服務暫時無法使用，請稍後再試。如果是關於三立節目的問題，建議直接查看三立電視官網獲取最新資訊。"
            }

        # 設定請求標頭
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 建構請求資料，包含 chatId 用於會話管理
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "stream": False,  # 不使用串流模式
            "chatId": f"set_{real_user_id}"  # 使用真實用戶ID和 set_ 前綴區分對話
        }

        try:
            # 使用 aiohttp 發送 POST 請求
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.post(
                    api_url,
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 從回應中提取答案內容
                        choices = result.get("choices", [])
                        if choices:
                            content = choices[0].get(
                                "message", {}).get("content", "")

                            # 檢查回答是否包含「不知道」、「無法回答」等關鍵詞
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
                        else:
                            return {
                                "status": "not_relevant",
                                "error_message": "知識庫沒有回應"
                            }
                    else:
                        # API 回應錯誤
                        if response.status == 401:
                            return {
                                "status": "error",
                                "error_message": "抱歉，SET三立電視知識庫服務認證失效，請稍後再試。建議直接查看三立電視官網獲取最新資訊。"
                            }
                        elif response.status == 403:
                            return {
                                "status": "error",
                                "error_message": "抱歉，SET三立電視知識庫服務暫時無法存取，請稍後再試。"
                            }
                        else:
                            return {
                                "status": "error",
                                "error_message": "抱歉，SET三立電視知識庫服務暫時忙碌中，請稍後再試。如果急需資訊，建議直接查看三立電視官網。"
                            }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error_message": "抱歉，SET三立電視知識庫查詢超時了，請稍後再試。如果急需節目資訊，建議直接查看三立電視官網。"
            }
        except Exception as e:
            # 捕獲所有其他異常，避免暴露技術細節
            return {
                "status": "error",
                "error_message": "抱歉，SET三立電視知識庫服務目前遇到一些問題，請稍後再試。如果是關於三立節目的問題，建議直接查看三立電視官網獲取最新資訊。"
            }
