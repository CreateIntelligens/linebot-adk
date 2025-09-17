# =============================================================================
# ComfyUI AI 影片生成代理
# 負責將 AI 回應轉換成影片，並非同步處理完成後推送到 LINE
# 提供完整的 ComfyUI 工作流程管理，包括模板載入、文字修改、工作提交、狀態監控等功能
# =============================================================================

import os
import json
import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from ..base.agent_base import BaseAgent
from ..base.registry import register_agent

# 設定 logger
logger = logging.getLogger(__name__)

# ComfyUI 配置
COMFYUI_API_URL = os.getenv("COMFYUI_API_URL", "http://localhost:8188")

# 標準 ComfyUI API 端點
class ComfyUIClient:
    """
    ComfyUI API 客戶端

    封裝 ComfyUI 服務的所有 API 調用，提供統一的介面來與 ComfyUI 服務互動。
    支援工作流程提交、狀態查詢、歷史記錄獲取和檔案下載等功能。

    Attributes:
        base_url (str): ComfyUI 服務的基礎 URL
    """

    def __init__(self, base_url: str):
        """
        初始化 ComfyUI 客戶端

        Args:
            base_url (str): ComfyUI 服務的基礎 URL
        """
        self.base_url = base_url.rstrip('/')

    async def queue_prompt(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        提交工作流程到 ComfyUI 佇列

        將指定的工作流程發送到 ComfyUI 服務進行處理，並返回工作 ID 等資訊。

        Args:
            workflow (Dict[str, Any]): ComfyUI 工作流程配置字典

        Returns:
            Optional[Dict[str, Any]]: 包含工作 ID 的回應字典，失敗時返回 None

        Raises:
            aiohttp.ClientError: 網路請求相關錯誤
            asyncio.TimeoutError: 請求超時
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/prompt",
                    json={"prompt": workflow, "client_id": "linebot_adk"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error queuing prompt: {e}")
            return None

    async def get_queue_status(self) -> Optional[Dict[str, Any]]:
        """
        獲取 ComfyUI 工作佇列狀態

        查詢 ComfyUI 服務當前的工作佇列狀態，包括正在處理和排隊中的工作。

        Returns:
            Optional[Dict[str, Any]]: 佇列狀態資訊字典，失敗時返回 None

        Raises:
            aiohttp.ClientError: 網路請求相關錯誤
            asyncio.TimeoutError: 請求超時
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/queue") as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return None

    async def get_history(self, prompt_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        獲取 ComfyUI 工作歷史記錄

        查詢已完成的工作歷史記錄，如果指定了 prompt_id 則只返回該工作的記錄。

        Args:
            prompt_id (Optional[str]): 特定的工作 ID，可選參數

        Returns:
            Optional[Dict[str, Any]]: 歷史記錄字典，失敗時返回 None

        Raises:
            aiohttp.ClientError: 網路請求相關錯誤
            asyncio.TimeoutError: 請求超時
        """
        try:
            url = f"{self.base_url}/history"
            if prompt_id:
                url += f"/{prompt_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return None

    async def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        """
        從 ComfyUI 下載生成的圖片或影片檔案

        根據檔案名稱、子資料夾和類型從 ComfyUI 服務下載產生的媒體檔案。

        Args:
            filename (str): 檔案名稱
            subfolder (str): 子資料夾路徑，預設為空字串
            folder_type (str): 資料夾類型，預設為 "output"

        Returns:
            Optional[bytes]: 檔案的二進位資料，失敗時返回 None

        Raises:
            aiohttp.ClientError: 網路請求相關錯誤
            asyncio.TimeoutError: 請求超時
        """
        try:
            params = {
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/view", params=params) as response:
                    response.raise_for_status()
                    return await response.read()
        except Exception as e:
            logger.error(f"Error getting image: {e}")
            return None


@register_agent(name="comfyui", description="使用ComfyUI生成AI影片，支援文字到影片的轉換")
class ComfyUIAgent(BaseAgent):
    """
    ComfyUI AI 影片生成 Agent

    負責將 AI 回應轉換成影片，並非同步處理完成後推送到 LINE。
    提供完整的 ComfyUI 工作流程管理，包括模板載入、文字修改、工作提交、狀態監控等功能。
    """

    def __init__(self, name: str = "comfyui", description: str = "使用ComfyUI生成AI影片，支援文字到影片的轉換"):
        super().__init__(name, description)
        self.client = ComfyUIClient(COMFYUI_API_URL)

    async def execute(self, ai_response: str, user_id: str):
        """
        生成 AI 影片

        Args:
            ai_response (str): AI 生成的文字內容，用於影片腳本
            user_id (str): 請求影片生成的使用者 ID

        Returns:
            AgentResponse: 影片生成結果
        """
        try:
            # 檢查必要參數
            self.validate_params(['ai_response', 'user_id'], ai_response=ai_response, user_id=user_id)

            # 載入並修改模板
            template = self._load_comfyui_template()
            if not template:
                return self._create_error_response("無法載入 ComfyUI 模板")

            # 修改文字內容
            workflow = self._modify_comfyui_text(template, ai_response)

            # 提交工作
            prompt_id = await self._submit_comfyui_job(workflow)
            if prompt_id:
                logger.info(f"用戶 {user_id} 的影片生成工作已提交: {prompt_id}")
                return self._create_success_response(
                    f"影片生成工作已提交，工作ID: {prompt_id}",
                    {"prompt_id": prompt_id, "status": "submitted"}
                )
            else:
                return self._create_error_response("ComfyUI 服務目前無法連接，請稍後再試。")

        except Exception as e:
            logger.error(f"生成 AI 影片時發生錯誤: {e}")
            return self._create_error_response(f"影片生成服務發生錯誤: {str(e)}")

    def _load_comfyui_template(self) -> Dict[str, Any]:
        """
        載入 ComfyUI 工作流程 JSON 模板
        """
        try:
            template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'comfyui.json')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # 替換環境變數
            template_content = template_content.replace(
                "${COMFYUI_TTS_API_URL}",
                os.getenv("COMFYUI_TTS_API_URL", "http://57.182.124.55:8001/tts_url")
            )

            return json.loads(template_content)
        except Exception as e:
            logger.error(f"載入 ComfyUI 模板失敗: {e}")
            return {}

    def _modify_comfyui_text(self, template: Dict[str, Any], ai_response: str) -> Dict[str, Any]:
        """
        修改 ComfyUI 模板中的文字內容（節點 12）
        """
        if "12" in template and "inputs" in template["12"]:
            template["12"]["inputs"]["text"] = ai_response
            logger.info(f"已更新 ComfyUI 文字: {ai_response[:50]}...")
        else:
            logger.warning("ComfyUI 模板中找不到節點 12 或其 inputs")

        return template

    async def _submit_comfyui_job(self, workflow: Dict[str, Any]) -> Optional[str]:
        """
        提交 ComfyUI 工作到佇列
        """
        try:
            result = await self.client.queue_prompt(workflow)
            if result:
                prompt_id = result.get("prompt_id") or result.get("job_id") or result.get("id")
                if prompt_id:
                    logger.info(f"ComfyUI 工作已提交，ID: {prompt_id}")
                    return prompt_id
                else:
                    logger.warning(f"提交成功但無法獲取工作 ID: {result}")
                    return None
            else:
                logger.error("無法連接到 ComfyUI 服務")
                return None

        except Exception as e:
            logger.error(f"提交 ComfyUI 工作時發生錯誤: {e}")
            return None

    async def _check_comfyui_status(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        檢查 ComfyUI 工作狀態
        """
        try:
            result = await self.client.get_history(prompt_id)
            if result:
                # 標準 ComfyUI 格式
                if prompt_id in result:
                    job_result = result[prompt_id]
                    if "outputs" in job_result:
                        logger.info(f"ComfyUI 工作 {prompt_id} 已完成")
                        return job_result

                logger.warning(f"無法檢查工作 {prompt_id} 的狀態")
                return None

        except Exception as e:
            logger.error(f"檢查 ComfyUI 狀態時發生錯誤: {e}")
            return None

    def _extract_video_info(self, job_result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        從 ComfyUI 工作結果中提取影片檔案資訊
        """
        try:
            # 查找影片輸出（通常在節點 6）
            outputs = job_result.get("outputs", {})

            for node_output in outputs.values():
                # 尋找影片檔案
                if "gifs" in node_output or "videos" in node_output:
                    videos = node_output.get("gifs", []) or node_output.get("videos", [])

                    if videos:
                        video_info = videos[0]  # 取第一個影片
                        return {
                            "filename": video_info.get("filename", ""),
                            "subfolder": video_info.get("subfolder", ""),
                            "type": video_info.get("type", "output")
                        }

            logger.warning("ComfyUI 結果中找不到影片檔案")
            return None

        except Exception as e:
            logger.error(f"提取影片資訊時發生錯誤: {e}")
            return None

    async def _download_comfyui_video(self, video_info: Dict[str, str]) -> Optional[bytes]:
        """
        從 ComfyUI 服務下載生成的影片檔案
        """
        try:
            video_data = await self.client.get_image(
                filename=video_info["filename"],
                subfolder=video_info["subfolder"],
                folder_type=video_info["type"]
            )

            if video_data:
                logger.info(f"成功下載影片: {video_info['filename']}")
                return video_data
            else:
                logger.error(f"下載影片失敗: {video_info['filename']}")
                return None

        except Exception as e:
            logger.error(f"下載影片時發生錯誤: {e}")
            return None

    async def monitor_job(self, prompt_id: str, user_id: str, max_wait_time: int = 300) -> Optional[bytes]:
        """
        監控 ComfyUI 工作進度並在完成後下載影片
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            # 檢查是否超時
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time > max_wait_time:
                logger.warning(f"ComfyUI 工作 {prompt_id} 超時")
                return None

            # 檢查工作狀態
            result = await self._check_comfyui_status(prompt_id)
            if result:
                # 工作已完成，開始提取和下載影片
                video_info = self._extract_video_info(result)
                if video_info:
                    # 成功提取影片資訊，嘗試下載
                    video_data = await self._download_comfyui_video(video_info)
                    if video_data:
                        logger.info(f"用戶 {user_id} 的影片生成完成")
                        return video_data
                    else:
                        logger.error(f"下載用戶 {user_id} 的影片失敗")
                        return None
                else:
                    logger.error(f"用戶 {user_id} 的工作完成但無法找到影片")
                    return None

            # 等待 5 秒後再次檢查
            await asyncio.sleep(5)

    def _create_success_response(self, report: str, data: Optional[dict] = None):
        """創建成功回應"""
        from ..base.types import AgentResponse
        return AgentResponse.success(report, data or {})

    def _create_error_response(self, error_message: str):
        """創建錯誤回應"""
        from ..base.types import AgentResponse
        return AgentResponse.error(error_message)
