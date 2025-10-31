"""
ID 查詢 Client - 串接 Social Analyzer OSINT API
GitHub: https://github.com/qeeqbox/social-analyzer
"""
import os
import logging
import aiohttp
from typing import Optional, Dict, Any
import uuid

logger = logging.getLogger(__name__)


class IDQueryClient:
    """ID/字串查詢客戶端 (OSINT 分析工具)"""

    def __init__(self):
        self.api_base_url = os.getenv("ID_QUERY_API_URL", "http://10.9.0.32:8901")
        self.analyze_endpoint = f"{self.api_base_url}/analyze_string"
        self.timeout = aiohttp.ClientTimeout(total=60)  # OSINT 查詢可能需要較長時間

        # 預設選項 - 啟用所有分析功能
        self.default_options = ",".join([
            "WordInfo",
            "MostCommon",
            "FindOrigins",
            "LookUps",
            "CustomSearch",
            "FindUserProfilesFast",
            "GetUserProfilesFast",
            "ExtractMetadata",
            "ExtractPatterns",
            "NetworkGraph",
            "FindNumbers",
            "CategoriesStats",
            "MetadataStats",
            "FindAges",
            "FindSymbols",
            "SplitWordsByAlphabet",
            "SplitWordsByUpperCase"
        ])

    async def analyze(
        self,
        query_string: str,
        options: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析字串/ID/使用者名稱

        Args:
            query_string: 要分析的字串 (使用者名稱、ID 等)
            options: 分析選項 (預設使用全部功能)

        Returns:
            Dict 包含:
                - status: "success" 或 "error"
                - username: 查詢的字串
                - social_media: 社交媒體個人資料列表
                - word_info: 字詞資訊
                - composition: 字串組成分析
                - search_results: 相關搜尋結果
                - error_message: 錯誤訊息 (當 status="error" 時)
        """
        try:
            payload = {
                "string": query_string,
                "option": options or self.default_options,
                "group": False,
                "uuid": str(uuid.uuid4())[:11]  # 生成短 UUID
            }

            logger.info(f"呼叫 ID 查詢 API: {self.analyze_endpoint}")
            logger.debug(f"查詢字串: {query_string}")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.analyze_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"ID 查詢成功")

                        # 解析並整理回應資料
                        result = self._parse_response(data)
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"ID 查詢 API 錯誤 {response.status}: {error_text}")
                        return {
                            "status": "error",
                            "error_message": f"API 錯誤 {response.status}: {error_text}"
                        }

        except aiohttp.ClientError as e:
            logger.error(f"ID 查詢 API 連線錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"連線錯誤: {str(e)}"
            }
        except Exception as e:
            logger.error(f"ID 查詢發生未預期錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"未預期錯誤: {str(e)}"
            }

    def _parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 API 回應,提取重要資訊"""
        try:
            username = data.get("username", "")

            # 社交媒體個人資料
            social_media = []
            user_info = data.get("user_info_normal", {}).get("data", [])
            for profile in user_info:
                if profile.get("found", 0) > 0:  # 只保留找到的資料
                    # 過濾假陽性：檢查是否為錯誤頁面
                    title = profile.get("title", "")
                    text = profile.get("text", "")

                    # 跳過明顯的錯誤頁面
                    error_indicators = [
                        "Error", "error",
                        "SORRY", "Sorry",
                        "SOMETHING WENT WRONG",
                        "Page Not Found",
                        "not found",
                        "doesn't exist",
                        "unavailable"
                    ]

                    is_error = any(indicator in title for indicator in error_indicators)
                    is_error = is_error or any(indicator in text for indicator in error_indicators)

                    # 如果不是錯誤頁面才加入
                    if not is_error:
                        social_media.append({
                            "platform": self._extract_platform_name(profile.get("link", "")),
                            "link": profile.get("link", ""),
                            "status": profile.get("status", ""),
                            "confidence": profile.get("rate", ""),
                            "title": title
                        })

            # 字詞資訊
            word_info = []
            for word_data in data.get("words_info", []):
                word = word_data.get("word", "")
                text = word_data.get("text", "")
                if text and text != "unknown":
                    word_info.append({
                        "word": word,
                        "description": text[:200]  # 限制長度
                    })

            # 字串組成分析
            table = data.get("table", {})
            composition = {
                "numbers": table.get("number", []),
                "unknown": table.get("unknown", []),
                "maybe": table.get("maybe", [])
            }

            # 搜尋結果 (取前 5 筆)
            search_results = []
            for result in data.get("custom_search", [])[:5]:
                search_results.append({
                    "title": result.get("link", ""),
                    "snippet": result.get("snippet", "")[:150]  # 限制長度
                })

            return {
                "status": "success",
                "username": username,
                "social_media": social_media,
                "word_info": word_info,
                "composition": composition,
                "search_results": search_results
            }

        except Exception as e:
            logger.error(f"解析回應時發生錯誤: {e}")
            return {
                "status": "error",
                "error_message": f"解析回應失敗: {str(e)}"
            }

    def _extract_platform_name(self, url: str) -> str:
        """從 URL 提取平台名稱"""
        platform_map = {
            "facebook.com": "Facebook",
            "twitter.com": "Twitter / X",
            "reddit.com": "Reddit",
            "instagram.com": "Instagram",
            "pinterest.com": "Pinterest",
            "telegram": "Telegram",
            "tiktok.com": "TikTok",
            "youtube.com": "YouTube",
            "tumblr.com": "Tumblr",
            "linkedin.com": "LinkedIn"
        }

        for key, value in platform_map.items():
            if key in url:
                return value

        return "Unknown"
