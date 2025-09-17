# =============================================================================
# Utils Pytest 測試檔案
# 測試工具函數（簡單API調用）
# =============================================================================

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from multi_tool_agent.agent import (
    get_amis_word_of_the_day,
    create_short_url,
    video_transcriber
)


class TestAmisUtils:
    """測試阿美族語工具函數"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.amis_utils.get_amis_word_of_the_day')
    async def test_get_amis_word_success(self, mock_amis_util):
        """測試阿美族語每日一字成功"""
        mock_amis_util.return_value = {
            "status": "success",
            "report": "📚 今日阿美族語一字：\n\n**中文**：你好\n**阿美語**：kapa\n**發音**：[kapa]\n**例句**：kapa kiso! (你好！)"
        }

        result = await get_amis_word_of_the_day()

        assert result["status"] == "success"
        assert "阿美語" in result["report"]
        assert "中文" in result["report"]
        mock_amis_util.assert_called_once()

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.amis_utils.get_amis_word_of_the_day')
    async def test_get_amis_word_error(self, mock_amis_util):
        """測試阿美族語查詢錯誤"""
        mock_amis_util.side_effect = Exception("詞典服務錯誤")

        result = await get_amis_word_of_the_day()

        assert result["status"] == "error"
        assert "詞典查詢時發生錯誤" in result["error_message"]


class TestUrlUtils:
    """測試短網址工具函數"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.http_utils.create_short_url')
    async def test_create_short_url_success(self, mock_url_util):
        """測試建立短網址成功"""
        mock_url_util.return_value = {
            "status": "success",
            "report": "✅ 短網址建立成功：\n🔗 https://aiurl.tw/test123\n📊 原始網址：https://example.com/very/long/url"
        }

        result = await create_short_url("https://example.com/very/long/url", "test123")

        assert result["status"] == "success"
        assert "短網址建立成功" in result["report"]
        assert "aiurl.tw" in result["report"]
        mock_url_util.assert_called_once_with(url="https://example.com/very/long/url", slug="test123")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.http_utils.create_short_url')
    async def test_create_short_url_empty_slug(self, mock_url_util):
        """測試建立短網址空slug"""
        mock_url_util.return_value = {
            "status": "success",
            "report": "✅ 短網址建立成功：\n🔗 https://aiurl.tw/abc123\n📊 原始網址：https://example.com"
        }

        result = await create_short_url("https://example.com", "")

        assert result["status"] == "success"
        mock_url_util.assert_called_once_with(url="https://example.com", slug="")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.http_utils.create_short_url')
    async def test_create_short_url_api_error(self, mock_url_util):
        """測試短網址API錯誤"""
        mock_url_util.return_value = {
            "status": "error",
            "error_message": "短網址服務暫時無法使用，請稍後再試。"
        }

        result = await create_short_url("https://example.com", "test")

        assert result["status"] == "error"
        assert "短網址服務" in result["error_message"]


class TestVideoUtils:
    """測試影片處理工具函數"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.http_utils.process_video_request')
    async def test_video_transcriber_success(self, mock_video_util):
        """測試影片轉錄成功"""
        mock_video_util.return_value = {
            "status": "success",
            "report": "🎬 影片轉錄任務已啟動\n📹 影片：https://example.com/video.mp4\n🆔 任務ID：task_123\n⏱️ 預計處理時間：5-10分鐘"
        }

        result = await video_transcriber("https://example.com/video.mp4", "zh")

        assert result["status"] == "success"
        assert "轉錄任務" in result["report"]
        assert "task_" in result["report"]
        mock_video_util.assert_called_once_with("https://example.com/video.mp4", "zh")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.http_utils.process_video_request')
    async def test_video_transcriber_invalid_url(self, mock_video_util):
        """測試影片轉錄無效URL"""
        mock_video_util.return_value = {
            "status": "error",
            "error_message": "無效的影片URL或影片無法存取"
        }

        result = await video_transcriber("invalid-url", "zh")

        assert result["status"] == "error"
        assert "無效" in result["error_message"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.http_utils.process_video_request')
    async def test_video_transcriber_exception(self, mock_video_util):
        """測試影片轉錄異常處理"""
        mock_video_util.side_effect = Exception("網路連接錯誤")

        result = await video_transcriber("https://example.com/video.mp4", "zh")

        assert result["status"] == "error"
        assert "轉錄處理時發生錯誤" in result["error_message"]


@pytest.mark.parametrize("original_url,custom_slug,expected_call", [
    ("https://example.com", "test", ("https://example.com", "test")),
    ("https://very-long-url.example.com/path/to/resource", "", ("https://very-long-url.example.com/path/to/resource", "")),
    ("http://simple.com", "custom123", ("http://simple.com", "custom123")),
])
@pytest.mark.asyncio
@patch('multi_tool_agent.utils.http_utils.create_short_url')
async def test_create_short_url_parameters(mock_url_util, original_url, custom_slug, expected_call):
    """參數化測試短網址建立"""
    mock_url_util.return_value = {
        "status": "success",
        "report": f"✅ 短網址建立成功：\n🔗 https://aiurl.tw/{custom_slug or 'abc123'}"
    }

    result = await create_short_url(original_url, custom_slug)

    assert result["status"] == "success"
    mock_url_util.assert_called_once_with(url=expected_call[0], slug=expected_call[1])


class TestUtilsIntegration:
    """測試Utils整合測試"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.http_utils.process_video_request')
    @patch('multi_tool_agent.utils.http_utils.create_short_url')
    @patch('multi_tool_agent.utils.amis_utils.get_amis_word_of_the_day')
    async def test_utils_workflow(self, mock_amis, mock_url, mock_video):
        """測試多個工具函數工作流程"""
        # 設定mock回應
        mock_amis.return_value = {
            "status": "success",
            "report": "📚 今日阿美族語一字：kapa (你好)"
        }

        mock_url.return_value = {
            "status": "success",
            "report": "✅ 短網址建立成功：https://aiurl.tw/test"
        }

        mock_video.return_value = {
            "status": "success",
            "report": "🎬 影片轉錄任務已啟動，任務ID：task_123"
        }

        # 執行工作流程
        amis_result = await get_amis_word_of_the_day()
        url_result = await create_short_url("https://example.com", "test")
        video_result = await video_transcriber("https://example.com/video.mp4", "zh")

        # 驗證結果
        assert amis_result["status"] == "success"
        assert url_result["status"] == "success"
        assert video_result["status"] == "success"

        # 驗證調用
        mock_amis.assert_called_once()
        mock_url.assert_called_once_with(url="https://example.com", slug="test")
        mock_video.assert_called_once_with("https://example.com/video.mp4", "zh")