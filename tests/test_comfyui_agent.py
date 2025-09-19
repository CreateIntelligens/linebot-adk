# =============================================================================
# ComfyUI Agent 單元測試檔案
# 測試 AI 影片生成功能 (使用 pytest)
#
# 測試範圍：
# - ComfyUI 客戶端 API 呼叫
# - 工作流程模板載入
# - 文字內容修改
# - 工作提交和監控
# - 影片資訊提取
# - 影片檔案下載
# - 錯誤處理機制
#
# 作者：LINE Bot ADK 開發團隊
# 版本：1.0.0
# 更新日期：2025-01-18
# =============================================================================

import pytest
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import aiohttp

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_tool_agent.agents.comfyui_agent import ComfyUIClient, ComfyUIAgent


class TestComfyUIClient:
    """
    測試 ComfyUI 客戶端基礎功能
    """

    @pytest.fixture
    def client(self):
        """創建 ComfyUI 客戶端實例"""
        return ComfyUIClient("http://localhost:8188")

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_queue_prompt_success(self, mock_session_class, client):
        """測試成功提交工作流程"""
        # 模擬 aiohttp 回應
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"prompt_id": "test_prompt_123"})
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        workflow = {"test": "workflow"}
        result = await client.queue_prompt(workflow)

        assert result == {"prompt_id": "test_prompt_123"}
        mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_queue_prompt_error(self, mock_session_class, client):
        """測試提交工作流程失敗"""
        # 模擬網路錯誤
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post.side_effect = aiohttp.ClientError("Network error")
        mock_session_class.return_value = mock_session

        workflow = {"test": "workflow"}
        result = await client.queue_prompt(workflow)

        assert result is None

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_get_queue_status_success(self, mock_session_class, client):
        """測試成功獲取佇列狀態"""
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "queue_running": [],
            "queue_pending": []
        })
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        result = await client.get_queue_status()

        assert "queue_running" in result
        assert "queue_pending" in result

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_get_history_with_prompt_id(self, mock_session_class, client):
        """測試獲取特定任務的歷史記錄"""
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "test_prompt_123": {
                "outputs": {
                    "6": {
                        "videos": [{
                            "filename": "test_video.mp4",
                            "subfolder": "",
                            "type": "output"
                        }]
                    }
                }
            }
        })
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        result = await client.get_history("test_prompt_123")

        assert "test_prompt_123" in result
        mock_session.get.assert_called_once_with("http://localhost:8188/history/test_prompt_123")

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_get_image_success(self, mock_session_class, client):
        """測試成功下載影片檔案"""
        mock_response = MagicMock()
        mock_response.read = AsyncMock(return_value=b"fake video data")
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        result = await client.get_image("test_video.mp4", "", "output")

        assert result == b"fake video data"


class TestComfyUIAgent:
    """
    測試 ComfyUI Agent 主要功能
    """

    @pytest.fixture
    def agent(self):
        """創建 ComfyUI Agent 實例"""
        return ComfyUIAgent()

    def test_agent_initialization(self, agent):
        """測試代理初始化"""
        assert agent.name == "comfyui"
        assert "ComfyUI生成AI影片" in agent.description
        assert agent.client is not None

    @patch('os.path.join')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "template", "12": {"inputs": {"text": "original"}}}')
    def test_load_comfyui_template_success(self, mock_file, mock_join, agent):
        """測試成功載入 ComfyUI 模板"""
        mock_join.return_value = "/fake/path/comfyui.json"

        with patch.dict(os.environ, {'COMFYUI_TTS_API_URL': 'http://test:8001/tts_url'}):
            template = agent._load_comfyui_template()

        assert template["test"] == "template"
        assert "12" in template

    @patch('os.path.join')
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_load_comfyui_template_file_not_found(self, mock_file, mock_join, agent):
        """測試模板檔案不存在"""
        mock_join.return_value = "/fake/path/comfyui.json"

        template = agent._load_comfyui_template()

        assert template == {}

    def test_modify_comfyui_text_success(self, agent):
        """測試成功修改文字內容"""
        template = {
            "12": {
                "inputs": {
                    "text": "原始文字"
                }
            }
        }
        new_text = "新的文字內容"

        result = agent._modify_comfyui_text(template, new_text)

        assert result["12"]["inputs"]["text"] == new_text

    def test_modify_comfyui_text_missing_node(self, agent):
        """測試修改不存在的節點"""
        template = {"other_node": {"inputs": {}}}
        new_text = "新的文字內容"

        result = agent._modify_comfyui_text(template, new_text)

        # 模板應該保持不變
        assert result == template

    def test_extract_video_info_success(self, agent):
        """測試成功提取影片資訊"""
        job_result = {
            "outputs": {
                "6": {
                    "videos": [{
                        "filename": "test_video.mp4",
                        "subfolder": "videos",
                        "type": "output"
                    }]
                }
            }
        }

        video_info = agent._extract_video_info(job_result)

        assert video_info["filename"] == "test_video.mp4"
        assert video_info["subfolder"] == "videos"
        assert video_info["type"] == "output"

    def test_extract_video_info_gifs_format(self, agent):
        """測試提取 GIF 格式的影片資訊"""
        job_result = {
            "outputs": {
                "6": {
                    "gifs": [{
                        "filename": "test_animation.gif",
                        "subfolder": "",
                        "type": "output"
                    }]
                }
            }
        }

        video_info = agent._extract_video_info(job_result)

        assert video_info["filename"] == "test_animation.gif"

    def test_extract_video_info_no_video(self, agent):
        """測試沒有影片輸出的情況"""
        job_result = {
            "outputs": {
                "13": {
                    "audio": [{
                        "filename": "test_audio.wav",
                        "subfolder": "",
                        "type": "temp"
                    }]
                }
            }
        }

        video_info = agent._extract_video_info(job_result)

        assert video_info is None

    def test_extract_video_info_empty_outputs(self, agent):
        """測試空輸出的情況"""
        job_result = {"outputs": {}}

        video_info = agent._extract_video_info(job_result)

        assert video_info is None

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._load_comfyui_template')
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._submit_comfyui_job')
    async def test_execute_success(self, mock_submit_job, mock_load_template, agent):
        """測試成功執行影片生成"""
        mock_load_template.return_value = {"test": "template"}
        mock_submit_job.return_value = "test_prompt_123"

        result = await agent.execute("測試文字內容", "test_user_123")

        assert result["status"] == "success"
        assert "test_prompt_123" in result["report"]
        assert result["data"]["prompt_id"] == "test_prompt_123"

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._load_comfyui_template')
    async def test_execute_missing_template(self, mock_load_template, agent):
        """測試模板載入失敗"""
        mock_load_template.return_value = {}

        result = await agent.execute("測試文字內容", "test_user_123")

        assert result["status"] == "error"
        assert "無法載入 ComfyUI 模板" in result["error_message"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._load_comfyui_template')
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._submit_comfyui_job')
    async def test_execute_submit_failure(self, mock_submit_job, mock_load_template, agent):
        """測試工作提交失敗"""
        mock_load_template.return_value = {"test": "template"}
        mock_submit_job.return_value = None

        result = await agent.execute("測試文字內容", "test_user_123")

        assert result["status"] == "error"
        assert "Aikka 目前無法回覆" in result["error_message"]

    @pytest.mark.asyncio
    async def test_execute_missing_parameters(self, agent):
        """測試缺少必要參數"""
        result = await agent.execute("", "test_user_123")

        assert result["status"] == "error"
        assert "缺少必要參數" in result["error_message"]

    @pytest.mark.asyncio
    async def test_submit_comfyui_job_success(self, agent):
        """測試成功提交 ComfyUI 工作"""
        agent.client.queue_prompt = AsyncMock(return_value={"prompt_id": "test_prompt_123"})

        workflow = {"test": "workflow"}
        result = await agent._submit_comfyui_job(workflow)

        assert result == "test_prompt_123"

    @pytest.mark.asyncio
    async def test_submit_comfyui_job_alternative_id_format(self, agent):
        """測試不同格式的工作 ID 回應"""
        agent.client.queue_prompt = AsyncMock(return_value={"job_id": "test_job_456"})

        workflow = {"test": "workflow"}
        result = await agent._submit_comfyui_job(workflow)

        assert result == "test_job_456"

    @pytest.mark.asyncio
    async def test_submit_comfyui_job_no_id(self, agent):
        """測試沒有工作 ID 的回應"""
        agent.client.queue_prompt = AsyncMock(return_value={"other_field": "value"})

        workflow = {"test": "workflow"}
        result = await agent._submit_comfyui_job(workflow)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_comfyui_status_completed(self, agent):
        """測試檢查已完成的任務狀態"""
        agent.client.get_history = AsyncMock(return_value={
            "test_prompt_123": {
                "outputs": {
                    "6": {
                        "videos": [{"filename": "test.mp4"}]
                    }
                }
            }
        })

        result = await agent._check_comfyui_status("test_prompt_123")

        assert result is not None
        assert "outputs" in result

    @pytest.mark.asyncio
    async def test_check_comfyui_status_not_found(self, agent):
        """測試檢查不存在的任務狀態"""
        agent.client.get_history = AsyncMock(return_value=None)

        result = await agent._check_comfyui_status("test_prompt_123")

        assert result is None

    @pytest.mark.asyncio
    async def test_download_comfyui_video_success(self, agent):
        """測試成功下載影片檔案"""
        agent.client.get_image = AsyncMock(return_value=b"fake video content")

        video_info = {
            "filename": "test_video.mp4",
            "subfolder": "",
            "type": "output"
        }

        result = await agent._download_comfyui_video(video_info)

        assert result == b"fake video content"
        agent.client.get_image.assert_called_once_with(
            filename="test_video.mp4",
            subfolder="",
            folder_type="output"
        )

    @pytest.mark.asyncio
    async def test_download_comfyui_video_failure(self, agent):
        """測試下載影片檔案失敗"""
        agent.client.get_image = AsyncMock(return_value=None)

        video_info = {
            "filename": "test_video.mp4",
            "subfolder": "",
            "type": "output"
        }

        result = await agent._download_comfyui_video(video_info)

        assert result is None


class TestComfyUIAgentIntegration:
    """
    測試 ComfyUI Agent 整合功能
    """

    @pytest.fixture
    def agent(self):
        """創建 ComfyUI Agent 實例"""
        return ComfyUIAgent()

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._check_comfyui_status')
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._extract_video_info')
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._download_comfyui_video')
    @patch('asyncio.sleep')
    async def test_monitor_job_success(self, mock_sleep, mock_download, mock_extract, mock_check_status, agent):
        """測試成功監控工作完成"""
        # 第一次檢查返回 None，第二次返回結果
        mock_check_status.side_effect = [None, {"outputs": {"6": {}}}]
        mock_extract.return_value = {
            "filename": "test_video.mp4",
            "subfolder": "",
            "type": "output"
        }
        mock_download.return_value = b"video content"

        result = await agent.monitor_job("test_prompt_123", "test_user_123", max_wait_time=10)

        assert result == b"video content"
        # 應該至少睡眠一次
        mock_sleep.assert_called()

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent._check_comfyui_status')
    @patch('asyncio.sleep')
    async def test_monitor_job_timeout(self, mock_sleep, mock_check_status, agent):
        """測試監控工作超時"""
        mock_check_status.return_value = None  # 一直返回 None

        # 模擬時間流逝
        import asyncio
        original_time = asyncio.get_event_loop().time
        mock_time_values = [0, 5, 10, 15]  # 模擬時間超過 max_wait_time
        mock_time_iter = iter(mock_time_values)

        with patch.object(asyncio.get_event_loop(), 'time', side_effect=lambda: next(mock_time_iter)):
            result = await agent.monitor_job("test_prompt_123", "test_user_123", max_wait_time=10)

        assert result is None


# 測試執行器
if __name__ == "__main__":
    pytest.main([__file__, "-v"])