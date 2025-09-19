# =============================================================================
# HTTP 請求工具函數
# 包含檔案上傳、API 調用等 HTTP 相關功能
# =============================================================================

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def upload_image_to_https_server(image_data: bytes, filename: str) -> Optional[str]:
    """
    上傳圖片到 HTTPS 伺服器

    Args:
        image_data (bytes): 圖片檔案二進制數據
        filename (str): 檔案名稱

    Returns:
        Optional[str]: 上傳成功返回 URL，失敗返回 None
    """
    try:
        import aiohttp

        upload_url = "https://adkline.147.5gao.ai/upload"
        logger.info(f"上傳圖片到: {upload_url}")

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file',
                          image_data,
                          filename=filename,
                          content_type='image/jpeg')

            async with session.post(upload_url, data=data) as upload_response:
                if upload_response.status == 200:
                    result = await upload_response.json()
                    upload_url = result.get('url', f"https://adkline.147.5gao.ai/files/{filename}")
                    logger.info(f"✅ 圖片上傳成功: {upload_url}")
                    return upload_url
                else:
                    error_text = await upload_response.text()
                    logger.error(f"❌ 圖片上傳失敗: {upload_response.status} - {error_text}")
                    return None

    except Exception as e:
        logger.error(f"❌ 上傳圖片時發生錯誤: {e}")
        return None


async def upload_video_to_https_server(video_data: bytes, filename: str) -> Optional[str]:
    """
    上傳影片到 HTTPS 伺服器

    Args:
        video_data (bytes): 影片檔案二進制數據
        filename (str): 檔案名稱

    Returns:
        Optional[str]: 上傳成功返回 URL，失敗返回 None
    """
    try:
        import aiohttp

        # 直接上傳檔案到 HTTPS 伺服器
        upload_url = "https://adkline.147.5gao.ai/upload"
        logger.info(f"上傳檔案到: {upload_url}")

        async with aiohttp.ClientSession() as session:
            # 準備檔案上傳
            data = aiohttp.FormData()
            data.add_field('file',
                          video_data,
                          filename=filename,
                          content_type='video/mp4')

            # 上傳檔案
            async with session.post(upload_url, data=data) as upload_response:
                if upload_response.status == 200:
                    result = await upload_response.json()
                    upload_url = result.get('url', f"https://adkline.147.5gao.ai/files/{filename}")
                    logger.info(f"✅ 檔案上傳成功: {upload_url}")
                    return upload_url
                else:
                    error_text = await upload_response.text()
                    logger.error(f"❌ 檔案上傳失敗: {upload_response.status} - {error_text}")
                    return None

    except Exception as e:
        logger.error(f"❌ 上傳影片時發生錯誤: {e}")
        return None


async def create_short_url(url: str, slug: Optional[str] = None) -> Dict[str, Any]:
    """
    使用 aiurl.tw 服務建立短網址

    Args:
        url (str): 要縮短的原始長網址
        slug (Optional[str]): 自訂的短網址 slug，可選參數

    Returns:
        Dict[str, Any]: 包含狀態和結果的字典
    """
    # aiurl.tw API 端點
    api_url = "https://aiurl.tw/api/link/create"

    # 檢查是否有 API token
    api_token = os.getenv('AIURL_API_TOKEN')
    if not api_token:
        return {
            "status": "error",
            "error_message": "建立短網址錯誤：未設定 AIURL_API_TOKEN 環境變數"
        }

    # 設定請求標頭
    headers = {
        # API 認證 token
        "authorization": f"Bearer {api_token}",
        "content-type": "application/json"   # 請求內容類型
    }

    # 處理預設值 - 如果用戶說隨意/隨便等，設為空字串讓系統自動生成
    if slug is None or slug.lower() in ["隨意", "隨便", "你決定", "自動", "random"]:
        slug = ""

    # 建構請求資料
    data = {"url": url}
    if slug:  # 如果提供了自訂 slug，加入請求資料中
        data["slug"] = slug

    try:
        import aiohttp

        # 使用 aiohttp 發送 POST 請求
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=data, headers=headers) as response:
                if response.status == 201:  # HTTP 201 Created 表示成功建立
                    result = await response.json()

                    # 從回應中提取連結資訊
                    link_info = result.get("link", {})
                    short_url = f"https://aiurl.tw/{link_info.get('slug', '')}"

                    return {
                        "status": "success",
                        "report": f"短網址已建立：{short_url}",
                        "short_url": short_url,
                        "original_url": url
                    }
                else:
                    # API 回應錯誤，讀取錯誤訊息
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error_message": f"建立短網址失敗：{response.status} - {error_text}"
                    }

    except Exception as e:
        # 捕獲所有異常，包括網路錯誤、JSON 解析錯誤等
        return {
            "status": "error",
            "error_message": f"建立短網址時發生錯誤：{str(e)}"
        }


async def process_video_request(url: str, summary_language: str = "zh", summary_words: int = None) -> Dict[str, Any]:
    """
    處理影片摘要請求

    Args:
        url (str): 影片 URL
        summary_language (str): 摘要語言，預設為 "zh"
        summary_words (int): 摘要字數限制，可選參數

    Returns:
        Dict[str, Any]: 處理結果
    """
    # AI 影片轉錄器 API 端點
    api_base_url = os.getenv("VIDEO_API_BASE_URL") or "http://10.9.0.32:8893"
    process_url = f"{api_base_url}/api/process-video"

    # 處理預設值
    if not summary_language:
        summary_language = "zh"

    # 建構請求資料
    data = {
        "url": url,
        "summary_language": summary_language
    }

    # 只有用戶明確指定字數時才加入參數
    if summary_words is not None:
        data["summary_words"] = summary_words

    try:
        import aiohttp

        # 使用 aiohttp 發送 POST 請求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                process_url,
                data=data,  # 使用 form data
                timeout=aiohttp.ClientTimeout(total=20)  # 設定 60 秒超時
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # 從回應中提取任務 ID
                    task_id = result.get("task_id", "unknown")

                    # 任務ID將在 main.py 中記錄到用戶活躍任務列表

                    return {
                        "status": "success",
                        "report": f"摘要擷取中... 任務ID: {task_id}",
                        "task_id": task_id
                    }
                else:
                    # API 回應錯誤
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error_message": f"影片處理請求失敗：{response.status} - {error_text}"
                    }

    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error_message": "影片處理請求超時，請稍後再試。"
        }
    except Exception as e:
        # 捕獲所有異常
        return {
            "status": "error",
            "error_message": f"處理影片時發生錯誤：{str(e)}"
        }
