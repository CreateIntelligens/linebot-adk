# =============================================================================
# 影片處理工具函數
# 包含影片監控、上傳、縮圖生成等功能
# =============================================================================

import os
import asyncio
import logging
import subprocess
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def monitor_and_push_video(prompt_id: str, user_id: str, text_content: str):
    """
    監控影片生成進度並在完成後推送給用戶

    這是一個背景任務，會持續監控 ComfyUI 的工作進度，
    當影片生成完成後，會自動推送給指定用戶。

    Args:
        prompt_id (str): ComfyUI 工作 ID
        user_id (str): 用戶 ID
        text_content (str): 影片內容文字
    """
    try:
        logger.info(f"開始監控影片生成: {prompt_id}")

        # 動態導入避免循環依賴
        from ..agents.comfyui_agent import ComfyUIAgent
        from .line_utils import push_video_to_user

        # 設定監控參數
        max_attempts = 120  # 最多檢查 120 次（2分鐘）
        check_interval = 1   # 每 1 秒檢查一次
        initial_delay = 5    # 初始等待 5 秒讓工作開始

        # 創建 ComfyUI agent 實例
        comfyui_agent = ComfyUIAgent()

        # 初始等待，讓 ComfyUI 有時間開始處理
        logger.info(f"等待 {initial_delay} 秒讓 ComfyUI 開始處理...")
        await asyncio.sleep(initial_delay)

        # 持續監控工作狀態
        for attempt in range(max_attempts):
            try:
                logger.info(f"檢查影片狀態（{attempt + 1}/{max_attempts}）: {prompt_id}")

                result = await comfyui_agent._check_comfyui_status(prompt_id)
                if result:
                    logger.info(f"工作狀態檢查成功: {prompt_id}")
                    video_info = comfyui_agent._extract_video_info(result)
                    if video_info:
                        logger.info(f"找到影片檔案資訊: {video_info['filename']}")

                        # 下載影片檔案
                        video_data = await comfyui_agent._download_comfyui_video(video_info)

                        if video_data and len(video_data) > 0:
                            logger.info(f"影片下載成功，大小: {len(video_data)} bytes")

                            # 影片下載成功，推送給用戶
                            await push_video_to_user(user_id, video_data, text_content, video_info)
                            logger.info(f"[PUSH] ✅ 影片已成功推送給用戶: {user_id}")
                            return  # 成功完成
                        else:
                            logger.info(f"影片下載失敗或檔案為空")
                    else:
                        logger.info(f"無法取得影片檔案資訊")
                else:
                    logger.info(f"工作狀態檢查返回 None")

                # 等待後再次檢查
                if attempt < max_attempts - 1:
                    logger.info(f"等待 {check_interval} 秒後再次檢查...")
                    await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"檢查影片狀態時發生錯誤（嘗試 {attempt + 1}/{max_attempts}）: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(check_interval)

        # 所有嘗試都失敗了，只記錄日誌，不推送錯誤訊息給用戶
        logger.error(f"❌ 影片監控失敗，已達最大嘗試次數: {prompt_id}")
        logger.error(f"工作 ID: {prompt_id}，用戶 ID: {user_id}")
        logger.error(f"影片內容: {text_content[:50]}...")

    except Exception as e:
        logger.error(f"監控影片生成時發生系統錯誤: {e}")
        # 移除錯誤訊息推送依賴


async def generate_thumbnail_from_video(video_path: str) -> Optional[str]:
    """
    使用 ffmpeg 從影片的第1秒擷取一張靜態預覽圖。

    Args:
        video_path (str): 影片檔案的路徑。

    Returns:
        Optional[str]: 成功時返回預覽圖的路徑，失敗時返回 None。
    """
    try:
        video_path_obj = Path(video_path)
        thumb_filename = f"{video_path_obj.stem}_thumb.jpg"
        thumb_path = video_path_obj.parent / thumb_filename

        # ffmpeg 指令：從第 1 秒 (-ss 1) 擷取 1 幀 (-vframes 1)
        command = [
            "ffmpeg",
            "-i", str(video_path),
            "-ss", "1",
            "-vframes", "1",
            str(thumb_path)
        ]

        logger.info(f"執行 ffmpeg 指令: {' '.join(command)}")

        # 使用 subprocess.run 執行同步指令
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"❌ ffmpeg 執行失敗，返回碼: {result.returncode}")
            logger.error(f"ffmpeg stderr: {result.stderr}")
            return None

        if thumb_path.exists():
            logger.info(f"✅ 預覽圖已成功產生: {thumb_path}")
            return str(thumb_path)
        else:
            logger.error("❌ ffmpeg 執行完畢但找不到預覽圖檔案")
            return None

    except FileNotFoundError:
        logger.error("❌ ffmpeg 指令未找到。請確認 ffmpeg 已安裝並在系統路徑中。")
        return None
    except Exception as e:
        logger.error(f"❌ 產生預覽圖時發生未預期錯誤: {e}")
        return None


def create_temp_video_path() -> str:
    """
    創建臨時影片檔案路徑

    Returns:
        str: 臨時影片檔案的完整路徑
    """
    video_dir = Path("/app/upload")
    video_dir.mkdir(exist_ok=True)
    temp_filename = f"temp_{uuid.uuid4().hex}.mp4"
    return str(video_dir / temp_filename)


def cleanup_temp_files(*file_paths: str):
    """
    清理臨時檔案

    Args:
        *file_paths: 要清理的檔案路徑
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.info(f"已清理臨時檔案: {file_path}")
            except Exception as e:
                logger.error(f"清理臨時檔案失敗: {file_path}, 錯誤: {e}")



async def get_video_task_result(task_id: str) -> Optional[str]:
    """
    獲取影片轉錄任務的完整結果內容

    Args:
        task_id (str): 任務 ID

    Returns:
        Optional[str]: 完整的轉錄結果內容，失敗時返回 None
    """
    # AI 影片轉錄器 API 端點
    api_base_url = os.getenv("VIDEO_API_BASE_URL") or "http://10.9.0.32:8893"
    result_url = f"{api_base_url}/api/task-result/{task_id}"

    try:
        import aiohttp

        # 使用 aiohttp 發送 GET 請求
        async with aiohttp.ClientSession() as session:
            async with session.get(
                result_url,
                timeout=aiohttp.ClientTimeout(total=30)  # 設定 30 秒超時
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # 提取結果內容（根據實際 API 回應格式調整）
                    content = result.get("result", "") or result.get("summary", "") or result.get("content", "")
                    if content:
                        logger.info(f"成功獲取影片轉錄任務結果: {task_id}")
                        return content
                    else:
                        logger.warning(f"影片轉錄任務結果為空: {task_id}")
                        return None
                else:
                    logger.error(f"獲取影片轉錄任務結果失敗: {task_id}, 狀態碼: {response.status}")
                    return None

    except asyncio.TimeoutError:
        logger.error(f"獲取影片轉錄任務結果超時: {task_id}")
        return None
    except Exception as e:
        logger.error(f"獲取影片轉錄任務結果時發生錯誤: {task_id}, 錯誤: {e}")
        return None


async def process_video_task(task_id: str) -> Dict[str, Any]:
    """
    處理影片任務狀態查詢

    Args:
        task_id (str): 任務 ID

    Returns:
        Dict[str, Any]: 任務狀態資訊
    """
    # AI 影片轉錄器 API 端點
    api_base_url = os.getenv("VIDEO_API_BASE_URL") or "http://10.9.0.32:8893"
    status_url = f"{api_base_url}/api/task-status/{task_id}"

    try:
        import aiohttp

        # 使用 aiohttp 發送 GET 請求
        async with aiohttp.ClientSession() as session:
            async with session.get(
                status_url,
                timeout=aiohttp.ClientTimeout(total=30)  # 設定 30 秒超時
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # 提取任務狀態資訊
                    task_status = result.get("status", "unknown")
                    progress = result.get("progress", 0)
                    message = result.get("message", "")
                    summary = result.get("summary", "")

                    # 格式化狀態報告
                    if task_status == "completed":
                        # 如果有摘要內容，顯示摘要；否則顯示訊息
                        content = summary if summary else message
                        report = content if content else "任務已完成"
                    elif task_status == "processing":
                        report = f"🔄 處理中... 進度: {progress}%\n{message}"
                    elif task_status == "failed":
                        report = f"❌ 任務失敗\n{message}"
                    else:
                        report = f"📋 任務狀態: {task_status}\n{message}"

                    return {
                        "status": "success",
                        "report": report,
                        "task_status": task_status
                    }
                else:
                    # API 回應錯誤
                    if response.status == 404:
                        return {
                            "status": "error",
                            "error_message": f"找不到任務 ID: {task_id}"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "error_message": f"查詢任務狀態失敗：{response.status} - {error_text}"
                        }

    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error_message": "查詢任務狀態超時，請稍後再試。"
        }
    except Exception as e:
        # 捕獲所有異常
        return {
            "status": "error",
            "error_message": f"查詢任務狀態時發生錯誤：{str(e)}"
        }
