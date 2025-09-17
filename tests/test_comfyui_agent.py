# =============================================================================
# ComfyUI Agent Pytest 測試檔案
# 測試 AI 影片生成和 ComfyUI 相關功能 (使用 pytest)
# =============================================================================

import pytest
import asyncio
import os
import sys
import json
import tempfile
from unittest.mock import AsyncMock

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_tool_agent.agents.comfyui_agent import ComfyUIClient
from multi_tool_agent.agent import generate_ai_video as generate_ai_video_wrapper


class TestComfyUIClient:
    """測試 ComfyUI 客戶端"""

    @pytest.fixture
    def client(self):
        """建立 ComfyUI 客戶端實例"""
        return ComfyUIClient("http://localhost:8188")

    @pytest.mark.asyncio
    async def test_queue_prompt_success(self, client, mocker):
        """測試成功提交工作流程"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"prompt_id": "test_123"})

        mock_session = mocker.patch('multi_tool_agent.comfyui_agent.aiohttp.ClientSession')
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        result = await client.queue_prompt({"test": "workflow"})

        assert result is not None
        assert result["prompt_id"] == "test_123"

    @pytest.mark.asyncio
    async def test_queue_prompt_error(self, client, mocker):
        """測試提交工作流程錯誤"""
        mock_session = mocker.patch('multi_tool_agent.comfyui_agent.aiohttp.ClientSession')
        mock_session.return_value.__aenter__.return_value.post.side_effect = Exception("網路錯誤")

        result = await client.queue_prompt({"test": "workflow"})

        assert result is None

    @pytest.mark.asyncio
    async def test_get_queue_status_success(self, client, mocker):
        """測試成功獲取佇列狀態"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"queue": []})

        mock_session = mocker.patch('multi_tool_agent.comfyui_agent.aiohttp.ClientSession')
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        result = await client.get_queue_status()

        assert result is not None
        assert "queue" in result

    @pytest.mark.asyncio
    async def test_get_history_success(self, client, mocker):
        """測試成功獲取歷史記錄"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"test_123": {"outputs": {}}})

        mock_session = mocker.patch('multi_tool_agent.comfyui_agent.aiohttp.ClientSession')
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        result = await client.get_history("test_123")

        assert result is not None
        assert "test_123" in result

    @pytest.mark.asyncio
    async def test_get_image_success(self, client, mocker):
        """測試成功下載圖片"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake_image_data")

        mock_session = mocker.patch('multi_tool_agent.comfyui_agent.aiohttp.ClientSession')
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        result = await client.get_image("test.jpg")

        assert result == b"fake_image_data"


# Removed test classes that reference functions that no longer exist


class TestAIVideoGeneration:
    """測試 AI 影片生成功能 (使用 MasterAgent)"""

    @pytest.fixture(autouse=True)
    def setup_master_agent(self, mocker):
        """設定 MasterAgent mock"""
        # Mock MasterAgent
        mock_master = mocker.patch('multi_tool_agent.agent.master')

        # 設定預設成功回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "影片生成成功",
            "data": {"prompt_id": "test_123"}
        }
        mock_master.execute.return_value = mock_response

        return mock_master

    @pytest.mark.asyncio
    async def test_generate_ai_video_success(self, setup_master_agent):
        """測試成功生成 AI 影片"""
        result = await generate_ai_video("測試文字內容", "user123")

        assert result["status"] == "success"
        assert "影片正在生成中" in result["report"]
        assert "測試文字內容" in result["report"]
        setup_master_agent.execute.assert_called_once_with("video", text_content="測試文字內容", user_id="user123")

    @pytest.mark.asyncio
    async def test_generate_ai_video_template_error(self, setup_master_agent):
        """測試載入模板錯誤"""
        # 設定模板錯誤回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "error",
            "error_message": "無法載入 ComfyUI 模板"
        }
        setup_master_agent.execute.return_value = mock_response

        result = await generate_ai_video("測試文字內容", "user123")

        assert result["status"] == "error"
        assert "無法載入 ComfyUI 模板" in result["error_message"]

    @pytest.mark.asyncio
    async def test_generate_ai_video_submit_error(self, setup_master_agent):
        """測試提交工作錯誤"""
        # 設定提交錯誤回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "service_unavailable",
            "error_message": "ComfyUI 服務目前無法連接"
        }
        setup_master_agent.execute.return_value = mock_response

        result = await generate_ai_video("測試文字內容", "user123")

        assert result["status"] == "service_unavailable"
        assert "ComfyUI 服務目前無法連接" in result["error_message"]


class TestAIVideoWrapper:
    """測試 AI 影片生成包裝函數"""

    @pytest.mark.asyncio
    async def test_generate_ai_video_wrapper_success(self, mocker):
        """測試 AI 影片生成包裝函數成功"""
        mock_generate = mocker.patch('multi_tool_agent.agent.generate_ai_video')
        mock_generate.return_value = {
            "status": "success",
            "report": "影片生成成功"
        }

        result = await generate_ai_video_wrapper("測試文字", "user123")

        assert result["status"] == "success"
        assert "影片正在生成中" in result["report"]

    @pytest.mark.asyncio
    async def test_generate_ai_video_wrapper_error(self, mocker):
        """測試 AI 影片生成包裝函數錯誤"""
        mock_generate = mocker.patch('multi_tool_agent.agent.generate_ai_video')
        mock_generate.return_value = {
            "status": "service_unavailable",
            "error_message": "服務不可用"
        }

        result = await generate_ai_video_wrapper("測試文字", "user123")

        assert result["status"] == "error"
        assert "服務不可用" in result["error_message"]
