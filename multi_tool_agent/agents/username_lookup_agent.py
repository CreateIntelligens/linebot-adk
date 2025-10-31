"""
使用者名稱查詢 Agent - OSINT 字串分析
"""
import logging
from typing import Dict, Any, Optional
from ..clients.id_query_client import IDQueryClient

logger = logging.getLogger(__name__)


class UsernameLookupAgent:
    """使用者名稱/ID 查詢代理 (OSINT 分析工具)"""

    def __init__(self):
        self.client = IDQueryClient()

    async def execute(
        self,
        username: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        執行使用者名稱/ID 查詢

        Args:
            username: 要查詢的使用者名稱或 ID
            user_id: 使用者 ID (用於記錄)

        Returns:
            Dict 包含:
                - status: "success" 或 "error"
                - report: 格式化的查詢結果
                - error_message: 錯誤訊息 (當 status="error" 時)
        """
        try:
            logger.info(f"使用者名稱查詢 Agent 開始查詢: {username}")

            # 呼叫 ID Query Client
            result = await self.client.analyze(username)

            if result["status"] == "success":
                # 格式化回應
                report = self._format_report(result)

                logger.info(f"使用者名稱查詢成功: {username}")

                return {
                    "status": "success",
                    "report": report
                }
            else:
                logger.error(f"使用者名稱查詢錯誤: {result.get('error_message')}")
                return {
                    "status": "error",
                    "error_message": result.get("error_message", "未知錯誤")
                }

        except Exception as e:
            logger.error(f"使用者名稱查詢 Agent 執行失敗: {e}")
            return {
                "status": "error",
                "error_message": f"查詢失敗: {str(e)}"
            }

    def _format_report(self, result: Dict[str, Any]) -> str:
        """格式化查詢結果為易讀的文字，包含 snippets 讓 ADK Agent 自己總結"""
        username = result.get("username", "")
        social_media = result.get("social_media", [])
        search_results = result.get("search_results", [])

        # 建立報告
        report_lines = [f"查詢 {username} 的 OSINT 結果:\n"]

        # 收集所有資訊片段
        snippets = []
        links = []

        # 只保留確定找到的社交媒體 (good status)
        confirmed = [p for p in social_media if p.get("status") == "good"]

        # 加入確定找到的社交媒體
        for profile in confirmed[:3]:
            platform = profile.get("platform", "Unknown")
            link = profile.get("link", "")
            links.append(f"{platform}: {link}")

        # 收集搜尋結果的 snippets 和連結
        for result_item in search_results[:5]:
            link = result_item.get("title", "")
            snippet = result_item.get("snippet", "")

            if link and not any(link in str(p.get("link", "")) for p in confirmed):
                links.append(link)
                if snippet and len(snippet) > 20:
                    snippets.append(snippet)

        # 組合報告
        if snippets:
            report_lines.append("【相關資訊摘要】")
            for snippet in snippets[:5]:  # 最多5個摘要
                # 清理摘要，移除過長內容
                clean_snippet = snippet.replace('\n', ' ').strip()
                if len(clean_snippet) > 200:
                    clean_snippet = clean_snippet[:200] + "..."
                report_lines.append(f"- {clean_snippet}")
            report_lines.append("")

        if links:
            report_lines.append("【參考連結】")
            for idx, link in enumerate(links[:5], 1):  # 最多5個連結
                report_lines.append(f"{idx}. {link}")

        # 如果完全沒有結果
        if not links and not snippets:
            report_lines.append("未找到任何相關資訊")

        # 給 Agent 的提示
        report_lines.append("\n[請根據以上資訊摘要，用繁體中文簡短描述這個使用者，然後列出參考連結]")

        return "\n".join(report_lines)
