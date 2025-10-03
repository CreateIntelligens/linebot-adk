# =============================================================================
# ComfyUI AI 影片生成代理
# 負責將 AI 回應轉換成影片，並非同步處理完成後推送到 LINE
# 提供完整的 ComfyUI 工作流程管理，包括模板載入、文字修改、工作提交、狀態監控等功能
# =============================================================================

import asyncio
import os
import json
import logging
from typing import Optional, Dict, Any

from ..clients.comfyui_client import ComfyUIClient

# 設定 logger
logger = logging.getLogger(__name__)

# ComfyUI 配置
COMFYUI_API_URL = os.getenv("COMFYUI_API_URL", "http://localhost:8188")


class ComfyUIAgent:
    """
    ComfyUI AI 影片生成 Agent

    負責將 AI 回應轉換成影片，並非同步處理完成後推送到 LINE。
    提供完整的 ComfyUI 工作流程管理，包括模板載入、文字修改、工作提交、狀態監控等功能。
    """

    def __init__(self, name: str = "comfyui", description: str = "使用ComfyUI生成AI影片，支援文字到影片的轉換"):
        self.name = name
        self.description = description
        self.client = ComfyUIClient(COMFYUI_API_URL)

    async def execute(self, ai_response: str, user_id: str) -> dict:
        """
        生成 AI 影片

        Args:
            ai_response (str): AI 生成的文字內容，用於影片腳本
            user_id (str): 請求影片生成的使用者 ID

        Returns:
            dict: 影片生成結果字典
                - status: "success" 或 "error"
                - report: 成功時的報告訊息
                - error_message: 錯誤時的錯誤訊息
                - data: 額外資料 (成功時)
        """
        try:
            # 檢查必要參數
            if not ai_response or not user_id:
                return {
                    "status": "error",
                    "error_message": "缺少必要參數：ai_response 或 user_id"
                }

            # 載入並修改模板
            template = self._load_comfyui_template()
            if not template:
                return {
                    "status": "error",
                    "error_message": "無法載入 ComfyUI 模板"
                }

            # 修改文字內容
            workflow = self._modify_comfyui_text(template, ai_response)

            # 提交工作
            prompt_id = await self._submit_comfyui_job(workflow)
            if prompt_id:
                logger.info(f"用戶 {user_id} 的影片生成工作已提交: {prompt_id}")
                return {
                    "status": "success",
                    "report": f"影片生成工作已提交，工作ID: {prompt_id}",
                    "data": {"prompt_id": prompt_id, "status": "submitted"}
                }
            else:
                return {
                    "status": "error",
                    "error_message": "Aikka 目前無法回覆，請稍後再試。"
                }

        except Exception as e:
            logger.error(f"生成 AI 影片時發生錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"影片生成服務發生錯誤: {str(e)}"
            }

    def _load_comfyui_template(self) -> Dict[str, Any]:
        """
        載入 ComfyUI 工作流程 JSON 模板
        """
        try:
            template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'asset/comfyui.json')
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
            video_data = await self.client.download_file(
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

    async def download_completed_video(self, task_id: str, save_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        下載已完成的 ComfyUI 影片

        Args:
            task_id (str): ComfyUI 任務 ID
            save_dir (str, optional): 儲存目錄路徑,如果提供則儲存到本地

        Returns:
            dict: 包含以下欄位:
                - status: "success" 或 "error"
                - video_data: 影片的二進位數據 (成功時)
                - video_filename: 影片檔案名稱 (成功時)
                - video_path: 本地儲存路徑 (如果有提供 save_dir)
                - video_info: 影片資訊字典 (成功時)
                - message: 錯誤訊息 (失敗時)
        """
        try:
            # 檢查工作狀態
            result = await self._check_comfyui_status(task_id)
            if not result:
                return {"status": "error", "message": "無法取得 ComfyUI 工作狀態"}

            # 提取影片資訊
            video_info = self._extract_video_info(result)
            if not video_info:
                return {"status": "error", "message": "無法取得影片檔案資訊"}

            logger.info(f"找到影片檔案: {video_info['filename']}")

            # 下載影片
            video_data = await self._download_comfyui_video(video_info)
            if not video_data or len(video_data) == 0:
                return {"status": "error", "message": "影片下載失敗或檔案為空"}

            logger.info(f"影片下載成功，大小: {len(video_data)} bytes")

            # 使用任務 ID 作為檔案名稱
            video_filename = f"{task_id}.mp4"
            response = {
                "status": "success",
                "video_data": video_data,
                "video_filename": video_filename,
                "video_info": video_info
            }

            # 如果提供了儲存目錄,儲存到本地
            if save_dir:
                from pathlib import Path
                save_path = Path(save_dir)
                save_path.mkdir(parents=True, exist_ok=True)

                video_file_path = save_path / video_filename

                # 檢查檔案是否已存在
                if video_file_path.exists():
                    logger.info(f"影片檔案已存在於本地: {video_file_path}")
                else:
                    with open(video_file_path, 'wb') as f:
                        f.write(video_data)
                    logger.info(f"影片已儲存到: {video_file_path}")

                response["video_path"] = str(video_file_path)

            return response

        except Exception as e:
            logger.error(f"下載 ComfyUI 影片時發生錯誤: {e}")
            return {"status": "error", "message": f"處理錯誤: {str(e)}"}

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
