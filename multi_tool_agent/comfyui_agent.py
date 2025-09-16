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

# 建立全域 ComfyUI 客戶端
comfyui_client = ComfyUIClient(COMFYUI_API_URL)

# 載入 ComfyUI 工作流程模板
def load_comfyui_template() -> Dict[str, Any]:
    """
    載入 ComfyUI 工作流程 JSON 模板

    從專案根目錄的 comfyui.json 檔案中讀取預定義的工作流程模板，
    用於 AI 影片生成的基礎配置。

    Returns:
        Dict[str, Any]: ComfyUI 工作流程配置字典，載入失敗時返回空字典

    Raises:
        FileNotFoundError: 當 comfyui.json 檔案不存在時
        json.JSONDecodeError: 當 JSON 格式錯誤時
    """
    try:
        template_path = os.path.join(os.path.dirname(__file__), '..', 'comfyui.json')
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

def modify_comfyui_text(template: Dict[str, Any], ai_response: str) -> Dict[str, Any]:
    """
    修改 ComfyUI 模板中的文字內容（節點 12）

    在 ComfyUI 工作流程模板的文字生成節點（通常是節點 12）中插入 AI 回應文字，
    這樣 ComfyUI 就能根據提供的文字內容生成對應的影片。

    Args:
        template (Dict[str, Any]): ComfyUI 工作流程模板字典
        ai_response (str): 要插入模板的 AI 回應文字

    Returns:
        Dict[str, Any]: 修改後的工作流程模板，包含更新的文字內容

    Note:
        此函數會直接修改傳入的 template 字典，並返回同一個物件的參考。
        如果模板中沒有找到節點 12 或其 inputs，會記錄警告但不拋出異常。
    """
    if "12" in template and "inputs" in template["12"]:
        template["12"]["inputs"]["text"] = ai_response
        logger.info(f"已更新 ComfyUI 文字: {ai_response[:50]}...")
    else:
        logger.warning("ComfyUI 模板中找不到節點 12 或其 inputs")

    return template

async def submit_comfyui_job(workflow: Dict[str, Any]) -> Optional[str]:
    """
    提交 ComfyUI 工作到佇列

    將配置好的工作流程發送到 ComfyUI 服務進行處理，並獲取工作 ID 用於後續追蹤。

    Args:
        workflow (Dict[str, Any]): 配置完成的工作流程字典，包含所有必要的節點和參數

    Returns:
        Optional[str]: 工作 ID 字串，提交失敗時返回 None

    Raises:
        aiohttp.ClientError: 網路連線錯誤
        asyncio.TimeoutError: 請求超時
        json.JSONDecodeError: 回應解析錯誤

    Note:
        工作 ID 可能以不同的鍵名返回（prompt_id、job_id 或 id），此函數會依序嘗試獲取。
    """
    try:
        result = await comfyui_client.queue_prompt(workflow)
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

async def check_comfyui_status(prompt_id: str) -> Optional[Dict[str, Any]]:
    """
    檢查 ComfyUI 工作狀態

    根據工作 ID 查詢 ComfyUI 中對應工作的當前狀態和結果。
    如果工作已完成，會返回完整的結果資料；如果還在處理中，則返回 None。

    Args:
        prompt_id (str): 要檢查的工作 ID

    Returns:
        Optional[Dict[str, Any]]: 工作結果字典（當工作完成時），還在處理中時返回 None

    Raises:
        aiohttp.ClientError: 網路連線錯誤
        asyncio.TimeoutError: 請求超時

    Note:
        此函數只檢查指定 ID 的工作狀態，不會等待工作完成。
        工作完成後的結果包含在 "outputs" 鍵中。
    """
    try:
        result = await comfyui_client.get_history(prompt_id)
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

def extract_video_info(job_result: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    從 ComfyUI 工作結果中提取影片檔案資訊

    解析 ComfyUI 完成的工作結果，尋找生成的影片檔案資訊。
    通常影片會在工作流程的輸出節點中，以 "gifs" 或 "videos" 鍵值儲存。

    Args:
        job_result (Dict[str, Any]): ComfyUI 工作完成後的結果字典

    Returns:
        Optional[Dict[str, str]]: 影片檔案資訊字典，包含以下鍵：
            - filename: 檔案名稱
            - subfolder: 子資料夾路徑
            - type: 資料夾類型
            如果找不到影片資訊則返回 None

    Note:
        此函數只返回第一個找到的影片檔案資訊。
        ComfyUI 的輸出格式可能因工作流程不同而有所差異。
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

async def download_comfyui_video(video_info: Dict[str, str]) -> Optional[bytes]:
    """
    從 ComfyUI 服務下載生成的影片檔案

    根據影片檔案資訊從 ComfyUI 服務的下載端點獲取實際的影片檔案資料。

    Args:
        video_info (Dict[str, str]): 影片檔案資訊字典，包含 filename、subfolder 和 type

    Returns:
        Optional[bytes]: 影片檔案的二進位資料，失敗時返回 None

    Raises:
        aiohttp.ClientError: 網路連線錯誤
        asyncio.TimeoutError: 下載超時

    Note:
        此函數會從 ComfyUI 的 /view 端點下載檔案，
        需要確保 ComfyUI 服務正在運行且檔案存在。
    """
    try:
        video_data = await comfyui_client.get_image(
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

async def generate_ai_video(ai_response: str, user_id: str) -> Dict[str, Any]:
    """
    使用 ComfyUI 生成 AI 影片的主要函數

    這是 AI 影片生成功能的入口函數，負責協調整個影片生成流程：
    1. 載入 ComfyUI 工作流程模板
    2. 將 AI 回應文字插入模板
    3. 提交工作到 ComfyUI 服務
    4. 返回工作狀態和 ID

    Args:
        ai_response (str): AI 生成的文字內容，用於影片腳本
        user_id (str): 請求影片生成的使用者 ID

    Returns:
        Dict[str, Any]: 包含以下鍵的結果字典：
            - status: "submitted"（成功提交）或 "service_unavailable"（服務不可用）或 "error"（其他錯誤）
            - prompt_id: 工作 ID（僅在 status 為 "submitted" 時存在）
            - error_message: 錯誤訊息（僅在 status 為 "error" 或 "service_unavailable" 時存在）

    Note:
        此函數只負責提交工作，不負責監控和下載。
        實際的影片生成是非同步進行的，完成後會通過其他機制通知用戶。
    """
    try:
        # 載入並修改模板
        template = load_comfyui_template()
        if not template:
            return {
                "status": "error",
                "error_message": "無法載入 ComfyUI 模板"
            }

        # 修改文字內容
        workflow = modify_comfyui_text(template, ai_response)

        # 提交工作
        prompt_id = await submit_comfyui_job(workflow)
        if prompt_id:
            logger.info(f"用戶 {user_id} 的影片生成工作已提交: {prompt_id}")
            return {
                "status": "submitted",
                "prompt_id": prompt_id
            }
        else:
            return {
                "status": "service_unavailable",
                "error_message": "ComfyUI 服務目前無法連接，請稍後再試。"
            }

    except Exception as e:
        logger.error(f"生成 AI 影片時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"影片生成服務發生錯誤: {str(e)}"
        }

async def monitor_comfyui_job(prompt_id: str, user_id: str, max_wait_time: int = 300) -> Optional[bytes]:
    """
    監控 ComfyUI 工作進度並在完成後下載影片

    持續監控指定 ComfyUI 工作的狀態，當工作完成時自動下載生成的影片檔案。
    此函數會定期檢查工作狀態，直到工作完成或超時。

    Args:
        prompt_id (str): 要監控的 ComfyUI 工作 ID
        user_id (str): 請求影片生成的使用者 ID，用於記錄日誌
        max_wait_time (int): 最大等待時間（秒），預設 300 秒（5 分鐘）

    Returns:
        Optional[bytes]: 影片檔案的二進位資料，失敗或超時時返回 None

    Note:
        此函數會阻塞執行，直到工作完成或超時。
        檢查間隔為 5 秒，以平衡響應速度和伺服器負載。
        如果工作完成但找不到影片檔案，也會返回 None。
    """
    start_time = asyncio.get_event_loop().time()

    while True:
        # 檢查是否超時
        elapsed_time = asyncio.get_event_loop().time() - start_time
        if elapsed_time > max_wait_time:
            logger.warning(f"ComfyUI 工作 {prompt_id} 超時")
            return None

        # 檢查工作狀態
        result = await check_comfyui_status(prompt_id)
        if result:
            # 工作已完成，開始提取和下載影片
            video_info = extract_video_info(result)
            if video_info:
                # 成功提取影片資訊，嘗試下載
                video_data = await download_comfyui_video(video_info)
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
