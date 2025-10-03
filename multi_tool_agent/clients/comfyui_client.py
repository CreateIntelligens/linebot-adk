"""
ComfyUI API 客戶端

封裝 ComfyUI 服務的所有 HTTP API 調用。
"""

import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """
    ComfyUI API 客戶端

    封裝 ComfyUI 服務的所有 API 調用，提供統一的介面。
    支援工作流程提交、狀態查詢、歷史記錄獲取和檔案下載等功能。
    """

    def __init__(self, base_url: str):
        """
        初始化 ComfyUI 客戶端

        Args:
            base_url: ComfyUI 服務的基礎 URL
        """
        self.base_url = base_url.rstrip('/')

    async def queue_prompt(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        提交工作流程到 ComfyUI 佇列

        Args:
            workflow: ComfyUI 工作流程配置字典

        Returns:
            包含工作 ID 的回應字典，失敗時返回 None
        """
        try:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    f"{self.base_url}/prompt",
                    json={"prompt": workflow, "client_id": "linebot_adk"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"提交 ComfyUI 工作時發生錯誤: {e}")
            return None

    async def get_queue_status(self) -> Optional[Dict[str, Any]]:
        """
        獲取 ComfyUI 工作佇列狀態

        Returns:
            佇列狀態資訊字典，失敗時返回 None
        """
        try:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(f"{self.base_url}/queue") as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"獲取 ComfyUI 佇列狀態時發生錯誤: {e}")
            return None

    async def get_history(self, prompt_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        獲取 ComfyUI 工作歷史記錄

        Args:
            prompt_id: 特定的工作 ID（可選）

        Returns:
            歷史記錄字典，失敗時返回 None
        """
        try:
            url = f"{self.base_url}/history"
            if prompt_id:
                url += f"/{prompt_id}"

            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"獲取 ComfyUI 歷史記錄時發生錯誤: {e}")
            return None

    async def download_file(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output"
    ) -> Optional[bytes]:
        """
        從 ComfyUI 下載生成的檔案（圖片或影片）

        Args:
            filename: 檔案名稱
            subfolder: 子資料夾路徑（預設為空）
            folder_type: 資料夾類型（預設為 "output"）

        Returns:
            檔案的二進位資料，失敗時返回 None
        """
        try:
            params = {
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type
            }
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(f"{self.base_url}/view", params=params) as response:
                    response.raise_for_status()
                    return await response.read()
        except Exception as e:
            logger.error(f"下載 ComfyUI 檔案時發生錯誤: {e}")
            return None
