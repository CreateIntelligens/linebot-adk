# =============================================================================
# MemeAgent Pytest 測試檔案
# 測試 Meme 生成和相關功能 (使用 pytest)
# =============================================================================

import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_tool_agent.agents.meme_agent import MemeAgent
from multi_tool_agent.agent import generate_meme as generate_meme_wrapper


# Removed test classes that reference functions that no longer exist


class TestMemeGeneration:
    """測試完整的 Meme 生成流程 (使用 MasterAgent)"""

    @pytest.fixture(autouse=True)
    def setup_master_agent(self, mocker):
        """設定 MasterAgent mock"""
        # Mock MasterAgent
        mock_master = mocker.patch('multi_tool_agent.agent.master')

        # 設定預設成功回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "🎭 Meme 已生成！主題：測試想法",
            "data": {"meme_url": "https://i.imgflip.com/test.jpg"}
        }
        mock_master.execute.return_value = mock_response

        return mock_master

    @pytest.mark.asyncio
    async def test_generate_meme_success(self, setup_master_agent):
        """測試成功生成完整 meme"""
        result = await generate_meme("測試 meme 想法", "user123")

        assert result["status"] == "success"
        assert "🎭 Meme 已生成" in result["report"]
        assert "測試想法" in result["report"]
        setup_master_agent.execute.assert_called_once_with("meme", meme_idea="測試 meme 想法", user_id="user123")

    @pytest.mark.asyncio
    async def test_generate_meme_text_generation_fail(self, setup_master_agent):
        """測試 meme 文字生成失敗"""
        # 設定失敗回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "error",
            "error_message": "無法生成合適的 meme 文字"
        }
        setup_master_agent.execute.return_value = mock_response

        result = await generate_meme("測試想法", "user123")

        assert result["status"] == "error"
        assert "無法生成合適的 meme 文字" in result["error_message"]

    @pytest.mark.asyncio
    async def test_generate_meme_no_api_key(self, setup_master_agent):
        """測試沒有 Google API 金鑰"""
        # 設定服務不可用錯誤
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "error",
            "error_message": "Meme 生成服務暫時無法使用"
        }
        setup_master_agent.execute.return_value = mock_response

        result = await generate_meme("測試想法", "user123")

        assert result["status"] == "error"
        assert "暫時無法使用" in result["error_message"]

    @pytest.mark.asyncio
    async def test_generate_meme_imgflip_fail(self, setup_master_agent):
        """測試 ImgFlip 生成失敗"""
        # 設定生成失敗回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "error",
            "error_message": "Meme 生成失敗"
        }
        setup_master_agent.execute.return_value = mock_response

        result = await generate_meme("測試想法", "user123")

        assert result["status"] == "error"
        assert "Meme 生成失敗" in result["error_message"]


# Removed TestFallbackMemeGenerator class - function doesn't exist as standalone


class TestMemeWrapper:
    """測試 Meme 生成包裝函數"""

    @pytest.mark.asyncio
    async def test_generate_meme_wrapper_success(self, mocker):
        """測試 meme 生成包裝函數成功"""
        mock_generate_meme = mocker.patch('multi_tool_agent.agent.generate_meme')
        mock_generate_meme.return_value = {
            "status": "success",
            "meme_url": "https://i.imgflip.com/test.jpg",
            "report": "Meme 生成成功"
        }

        result = await generate_meme_wrapper("測試想法", "user123")

        assert result["status"] == "success"
        assert result["meme_url"] == "https://i.imgflip.com/test.jpg"

    @pytest.mark.asyncio
    async def test_generate_meme_wrapper_fallback(self, mocker):
        """測試 meme 生成失敗時使用備用服務"""
        mock_generate_meme = mocker.patch('multi_tool_agent.agent.generate_meme')
        mock_fallback = mocker.patch('multi_tool_agent.agent.fallback_meme_generator')

        mock_generate_meme.side_effect = Exception("主要服務錯誤")
        mock_fallback.return_value = {
            "status": "success",
            "report": "備用建議"
        }

        result = await generate_meme_wrapper("測試想法", "user123")

        assert result["status"] == "success"
        assert result["report"] == "備用建議"
        mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_meme_wrapper_all_fail(self, mocker):
        """測試所有 meme 服務都失敗"""
        mock_generate_meme = mocker.patch('multi_tool_agent.agent.generate_meme')
        mock_fallback = mocker.patch('multi_tool_agent.agent.fallback_meme_generator')

        mock_generate_meme.side_effect = Exception("主要服務錯誤")
        mock_fallback.side_effect = Exception("備用服務錯誤")

        result = await generate_meme_wrapper("測試想法", "user123")

        assert result["status"] == "error"
        assert "暫時無法使用" in result["error_message"]
