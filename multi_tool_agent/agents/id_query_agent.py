# =============================================================================
# ID 查詢 Agent - 通用任務狀態查詢
# =============================================================================

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

from ..utils.video_utils import process_video_task as _process_video_task

process_video_task = _process_video_task

class IDQueryAgent:
    """通用 ID 查詢 Agent - 自動檢測並查詢各種任務狀態"""

    def __init__(self):
        self.name = "ID Query Agent"
        self.description = "通用任務 ID 查詢代理，支援 ComfyUI、影片轉錄等各種任務類型"

    async def execute(self, task_id: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        執行 ID 查詢 - 並行查詢所有系統

        Args:
            task_id (str): 要查詢的任務 ID
            user_id (str): 用戶 ID

        Returns:
            Dict[str, Any]: 查詢結果
        """
        import asyncio

        try:
            logger.info(f"ID查詢代理開始並行查詢: {task_id}, 用戶: {user_id}")

            # 並行啟動所有查詢任務，設定 10 秒超時
            tasks = [
                asyncio.wait_for(self._check_comfyui_task(task_id), timeout=10),
                asyncio.wait_for(self._check_video_transcription_task(task_id), timeout=10),
                # 未來可以添加更多查詢任務
                # asyncio.wait_for(self._check_meme_task(task_id), timeout=10),
                # asyncio.wait_for(self._check_url_task(task_id), timeout=10),
            ]

            # 使用 asyncio.as_completed 來獲取第一個完成且有結果的查詢
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    if result is not None:
                        if isinstance(result, dict):
                            result.setdefault('has_video', False)
                        logger.info(f"ID查詢成功: {task_id}, 類型: {result.get('task_type', 'unknown')}")

                        # 如果任務已完成，嘗試下載影片
                        if result.get("task_status") == "completed":
                            task_type = result.get("task_type")
                            if task_type == "comfyui":
                                try:
                                    # 下載影片（reply 模式）
                                    from .comfyui_agent import ComfyUIAgent
                                    import os

                                    comfyui_agent = ComfyUIAgent()
                                    video_upload_dir = os.getenv("VIDEO_UPLOAD_DIR", "upload")
                                    video_result = await comfyui_agent.download_completed_video(task_id, save_dir=video_upload_dir)

                                    if video_result and video_result.get("status") == "success":
                                        result["video_filename"] = video_result.get("video_filename")
                                        result["video_info"] = video_result.get("video_info")
                                        result["has_video"] = True
                                        logger.info(f"任務 {task_id} 影片下載成功，準備回覆")
                                    else:
                                        message = (video_result or {}).get('message', '未知錯誤')
                                        logger.warning(f"任務 {task_id} 影片下載失敗: {message}")
                                except Exception as video_error:
                                    logger.error(f"下載影片時發生錯誤: {video_error}")

                        # 智能等待功能：如果任務正在處理中，等待5秒看是否完成
                        elif result.get("task_status") == "processing":
                            logger.info(f"任務 {task_id} 處理中，開始智能等待...")
                            task_type = result.get("task_type")

                            # 等待最多5秒，每秒檢查一次
                            for wait_count in range(5):
                                await asyncio.sleep(1)
                                logger.info(f"智能等待第 {wait_count + 1} 次檢查...")

                                # 根據任務類型重新檢查
                                if task_type == "comfyui":
                                    updated_result = await self._check_comfyui_task(task_id)
                                elif task_type == "video_transcription":
                                    updated_result = await self._check_video_transcription_task(task_id)
                                else:
                                    break  # 未知類型，停止等待

                                # 檢查是否已完成
                                if updated_result and updated_result.get("task_status") == "completed":
                                    logger.info(f"任務 {task_id} 在等待期間完成！")

                                    # 如果是 ComfyUI 任務，嘗試直接下載影片
                                    if task_type == "comfyui":
                                        try:
                                            # 下載影片（reply 模式）
                                            from .comfyui_agent import ComfyUIAgent
                                            import os

                                            comfyui_agent = ComfyUIAgent()
                                            video_upload_dir = os.getenv("VIDEO_UPLOAD_DIR", "upload")
                                            video_result = await comfyui_agent.download_completed_video(task_id, save_dir=video_upload_dir)

                                            if video_result and video_result.get("status") == "success":
                                                updated_result["video_filename"] = video_result.get("video_filename")
                                                updated_result["video_info"] = video_result.get("video_info")
                                                updated_result["has_video"] = True
                                                logger.info(f"任務 {task_id} 影片下載成功，準備回覆")
                                            else:
                                                message = (video_result or {}).get('message', '未知錯誤')
                                                logger.warning(f"任務 {task_id} 影片下載失敗: {message}")
                                        except Exception as video_error:
                                            logger.error(f"下載影片時發生錯誤: {video_error}")

                                    return updated_result
                                elif updated_result is None:
                                    # 任務消失了，停止等待
                                    logger.info(f"任務 {task_id} 在等待期間消失，停止等待")
                                    break

                            # 5秒後仍在處理中，返回處理中狀態
                            logger.info(f"任務 {task_id} 等待5秒後仍在處理中")

                        return result
                except asyncio.TimeoutError:
                    logger.debug(f"某個查詢任務超時: {task_id}")
                    continue
                except Exception as e:
                    logger.debug(f"某個查詢任務失敗: {e}")
                    continue

            # 所有查詢都沒有找到結果
            logger.info(f"ID查詢未找到: {task_id}")
            return {
                "status": "error",
                "error_message": f"❌ 找不到任務: {task_id}",
                "has_video": False
            }

        except Exception as e:
            logger.error(f"ID查詢代理執行時發生錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"查詢任務狀態時發生錯誤：{str(e)}",
                "has_video": False
            }

    async def _check_comfyui_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """檢查 ComfyUI 任務狀態"""
        try:
            from .comfyui_agent import ComfyUIAgent

            comfyui_agent = ComfyUIAgent()
            result = await comfyui_agent._check_comfyui_status(task_id)

            if result is not None:  # ComfyUI 系統認識這個 ID
                if result:  # 任務完成
                    return {
                        "status": "success",
                        "task_status": "completed",
                        "report": f"✅ ComfyUI 影片生成已完成",
                        "task_type": "comfyui",
                        "has_video": False
                    }
                else:  # 任務處理中
                    return {
                        "status": "success",
                        "task_status": "processing",
                        "report": f"🔄 ComfyUI 影片生成處理中...",
                        "task_type": "comfyui",
                        "has_video": False
                    }

            return None  # ComfyUI 不認識這個 ID

        except Exception as e:
            logger.debug(f"ComfyUI 任務查詢失敗: {e}")
            return None

    async def _check_video_transcription_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """檢查影片轉錄任務狀態"""
        try:
            from ..utils.video_utils import process_video_task

            result = await process_video_task(task_id)

            if result and result.get("status") == "success":
                original_report = result.get("report", "")
                formatted_report = f"✅ 影片轉錄摘要已完成\n\n{original_report}" if original_report else "✅ 影片轉錄摘要已完成"

                result["report"] = formatted_report
                result["task_type"] = "video_transcription"
                result.setdefault("has_video", False)
                return result

            return None  # 影片轉錄系統不認識這個 ID

        except Exception as e:
            logger.debug(f"影片轉錄任務查詢失敗: {e}")
            return None

    # 未來可以添加更多任務類型查詢方法
    # async def _check_meme_task(self, task_id: str) -> Optional[Dict[str, Any]]:
    #     """檢查梗圖生成任務狀態"""
    #     pass

    # async def _check_url_task(self, task_id: str) -> Optional[Dict[str, Any]]:
    #     """檢查短網址任務狀態"""
    #     pass
