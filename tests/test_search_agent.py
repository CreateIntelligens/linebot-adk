# =============================================================================
# Search Agent Pytest 測試檔案
# 測試Google搜尋功能
# =============================================================================

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from multi_tool_agent.agent import search_web


class TestSearchAgent:
    """測試Google搜尋功能"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.search_agent.SearchAgent')
    async def test_search_web_success(self, mock_search_agent_class):
        """測試搜尋功能成功"""
        # 設定mock
        mock_agent = AsyncMock()
        mock_search_agent_class.return_value = mock_agent

        mock_agent.execute.return_value = {
            "status": "success",
            "report": "🔍 搜尋「台灣美食」的結果：\n\n1. **台灣美食介紹**\n台灣擁有豐富的美食文化...\n🔗 https://example.com"
        }

        result = await search_web("台灣美食")

        assert result["status"] == "success"
        assert "台灣美食" in result["report"]
        mock_agent.execute.assert_called_once_with(query="台灣美食", max_results=5)

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.search_agent.SearchAgent')
    async def test_search_web_no_results(self, mock_search_agent_class):
        """測試搜尋無結果"""
        mock_agent = AsyncMock()
        mock_search_agent_class.return_value = mock_agent

        mock_agent.execute.return_value = {
            "status": "success",
            "report": "🔍 搜尋「inexistent_query_12345」沒有找到相關結果。"
        }

        result = await search_web("inexistent_query_12345")

        assert result["status"] == "success"
        assert "沒有找到相關結果" in result["report"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.search_agent.SearchAgent')
    async def test_search_web_api_error(self, mock_search_agent_class):
        """測試搜尋API錯誤"""
        mock_agent = AsyncMock()
        mock_search_agent_class.return_value = mock_agent

        mock_agent.execute.return_value = {
            "status": "error",
            "error_message": "Google搜尋API配額已用完或API金鑰無效。"
        }

        result = await search_web("test query")

        assert result["status"] == "error"
        assert "API" in result["error_message"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.search_agent.SearchAgent')
    async def test_search_web_exception(self, mock_search_agent_class):
        """測試搜尋異常處理"""
        mock_search_agent_class.side_effect = Exception("測試異常")

        result = await search_web("test query")

        assert result["status"] == "error"
        assert "搜尋時發生錯誤" in result["error_message"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.search_agent.SearchAgent')
    async def test_search_web_config_missing(self, mock_search_agent_class):
        """測試搜尋配置缺失"""
        mock_agent = AsyncMock()
        mock_search_agent_class.return_value = mock_agent

        mock_agent.execute.return_value = {
            "status": "error",
            "error_message": "Google搜尋服務未配置，請設定 GOOGLE_SEARCH_API_KEY 和 GOOGLE_SEARCH_ENGINE_ID 環境變數。"
        }

        result = await search_web("test query")

        assert result["status"] == "error"
        assert "環境變數" in result["error_message"]


@pytest.mark.parametrize("query,expected_in_report", [
    ("台灣景點", "台灣景點"),
    ("美食推薦", "美食推薦"),
    ("Python教學", "Python教學"),
    ("今日新聞", "今日新聞"),
])
@pytest.mark.asyncio
@patch('multi_tool_agent.agents.search_agent.SearchAgent')
async def test_search_web_various_queries(mock_search_agent_class, query, expected_in_report):
    """參數化測試不同搜尋查詢"""
    mock_agent = AsyncMock()
    mock_search_agent_class.return_value = mock_agent

    mock_agent.execute.return_value = {
        "status": "success",
        "report": f"🔍 搜尋「{query}」的結果：\n\n1. **相關結果**\n內容描述...\n🔗 https://example.com"
    }

    result = await search_web(query)

    assert result["status"] == "success"
    assert expected_in_report in result["report"]
    mock_agent.execute.assert_called_once_with(query=query, max_results=5)


# 整合測試移除，因為依賴環境配置複雜