import aiohttp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SearchAgent:
    """
    An agent that uses Google Programmable Search Engine to perform web searches.
    """

    def __init__(self):
        import os
        # Google Custom Search API配置 - 從環境變數讀取
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def execute(self, query: str, max_results: int) -> Dict[str, Any]:
        """
        Performs a web search using Google Programmable Search Engine.

        Args:
            query: The search query.
            max_results: The maximum number of results to return (max 10 for Google API).

        Returns:
            A dictionary containing the search results or an error.
        """
        if not self.api_key or not self.search_engine_id:
            return {
                "status": "error",
                "error_message": "Google搜尋服務未配置，請設定 GOOGLE_SEARCH_API_KEY 和 GOOGLE_SEARCH_ENGINE_ID 環境變數。"
            }

        try:
            logger.info(f"Performing Google search for: {query}")

            # Google Custom Search API最多只能返回10個結果
            num_results = min(max_results, 10)

            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': f'{query} (site:tw OR 台灣) 繁體中文',  # 強化台灣繁體中文搜尋
                'num': num_results,
                'hl': 'zh-TW',  # 設定語言為繁體中文
                'gl': 'TW',     # 限制搜尋地區為台灣
                'cr': 'countryTW'  # 限制國家/地區為台灣
            }

            # 使用明確的 connector 配置來確保連接正確關閉
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])

                        if not items:
                            return {
                                "status": "success",
                                "report": f"🔍 搜尋「{query}」沒有找到相關結果。"
                            }

                        # 格式化搜尋結果
                        report_parts = []
                        for i, item in enumerate(items):
                            title = item.get('title', '無標題')
                            link = item.get('link', '')
                            snippet = item.get('snippet', '無描述')

                            # 限制snippet長度避免太長
                            if len(snippet) > 150:
                                snippet = snippet[:150] + "..."

                            report_parts.append(f"{i+1}. **{title}**\n{snippet}\n🔗 {link}")

                        final_report = "\n\n".join(report_parts)

                        return {
                            "status": "success",
                            "report": f"🔍 搜尋「{query}」的結果：\n\n{final_report}"
                        }

                    elif response.status == 403:
                        return {
                            "status": "error",
                            "error_message": "Google搜尋API配額已用完或API金鑰無效。"
                        }

                    else:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "error_message": f"Google搜尋API請求失敗：{response.status} - {error_text}"
                        }

        except Exception as e:
            logger.error(f"Google search error: {e}")
            return {
                "status": "error",
                "error_message": f"搜尋時發生錯誤：{str(e)}"
            }
