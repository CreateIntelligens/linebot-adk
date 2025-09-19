# =============================================================================
# ID 查詢代理單元測試檔案
# 測試通用任務狀態查詢功能 (使用 pytest)
#
# 測試範圍：
# - ComfyUI 任務狀態查詢
# - 影片轉錄任務狀態查詢
# - 並行查詢功能
# - 智能等待功能
# - 影片檔案處理
# - 錯誤處理機制
#
# 作者：LINE Bot ADK 開發團隊
# 版本：1.0.0
# 更新日期：2025-01-18
# =============================================================================

import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch, call

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_tool_agent.agents.id_query_agent import IDQueryAgent


class TestIDQueryAgent:
    """
    測試 ID 查詢代理的核心功能
    """

    @pytest.fixture
    def id_query_agent(self):
        """創建 ID 查詢代理實例"""
        return IDQueryAgent()

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent')
    async def test_check_comfyui_task_completed(self, mock_comfyui_agent_class, id_query_agent):
        """測試檢查已完成的 ComfyUI 任務"""
        # 模擬 ComfyUI Agent
        mock_agent = MagicMock()
        mock_agent._check_comfyui_status = AsyncMock(return_value={
            "outputs": {
                "6": {
                    "videos": [{
                        "filename": "test_video.mp4",
                        "subfolder": "",
                        "type": "output"
                    }]
                }
            }
        })
        mock_comfyui_agent_class.return_value = mock_agent

        result = await id_query_agent._check_comfyui_task("test_task_123")

        assert result["status"] == "success"
        assert result["task_status"] == "completed"
        assert result["task_type"] == "comfyui"
        assert "ComfyUI 影片生成已完成" in result["report"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent')
    async def test_check_comfyui_task_processing(self, mock_comfyui_agent_class, id_query_agent):
        """測試檢查處理中的 ComfyUI 任務"""
        # 模擬 ComfyUI Agent 返回空結果（處理中）
        mock_agent = MagicMock()
        mock_agent._check_comfyui_status = AsyncMock(return_value={})
        mock_comfyui_agent_class.return_value = mock_agent

        result = await id_query_agent._check_comfyui_task("test_task_123")

        assert result["status"] == "success"
        assert result["task_status"] == "processing"
        assert result["task_type"] == "comfyui"
        assert "處理中" in result["report"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent')
    async def test_check_comfyui_task_not_found(self, mock_comfyui_agent_class, id_query_agent):
        """測試檢查不存在的 ComfyUI 任務"""
        # 模擬 ComfyUI Agent 返回 None（任務不存在）
        mock_agent = MagicMock()
        mock_agent._check_comfyui_status = AsyncMock(return_value=None)
        mock_comfyui_agent_class.return_value = mock_agent

        result = await id_query_agent._check_comfyui_task("test_task_123")

        assert result is None

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.process_video_task')
    async def test_check_video_transcription_task_completed(self, mock_process_video_task, id_query_agent):
        """測試檢查已完成的影片轉錄任務"""
        mock_process_video_task.return_value = {
            "status": "success",
            "report": "影片轉錄已完成，內容：這是一個測試影片。",
            "task_status": "completed"
        }

        result = await id_query_agent._check_video_transcription_task("test_task_123")

        assert result["status"] == "success"
        assert result["task_type"] == "video_transcription"
        assert "影片轉錄摘要已完成" in result["report"]
        assert "這是一個測試影片" in result["report"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.process_video_task')
    async def test_check_video_transcription_task_not_found(self, mock_process_video_task, id_query_agent):
        """測試檢查不存在的影片轉錄任務"""
        mock_process_video_task.return_value = {
            "status": "error",
            "error_message": "找不到任務"
        }

        result = await id_query_agent._check_video_transcription_task("test_task_123")

        assert result is None

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_comfyui_task')
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_video_transcription_task')
    async def test_execute_parallel_query_comfyui_success(self, mock_check_video, mock_check_comfyui, id_query_agent):
        """測試並行查詢 - ComfyUI 任務成功"""
        # ComfyUI 任務存在並已完成
        mock_check_comfyui.return_value = {
            "status": "success",
            "task_status": "completed",
            "task_type": "comfyui",
            "report": "ComfyUI 任務已完成"
        }
        # 影片轉錄任務不存在
        mock_check_video.return_value = None

        result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "success"
        assert result["task_status"] == "completed"
        assert result["task_type"] == "comfyui"

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_comfyui_task')
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_video_transcription_task')
    async def test_execute_parallel_query_video_success(self, mock_check_video, mock_check_comfyui, id_query_agent):
        """測試並行查詢 - 影片轉錄任務成功"""
        # ComfyUI 任務不存在
        mock_check_comfyui.return_value = None
        # 影片轉錄任務存在並已完成
        mock_check_video.return_value = {
            "status": "success",
            "task_status": "completed",
            "task_type": "video_transcription",
            "report": "影片轉錄已完成"
        }

        result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "success"
        assert result["task_status"] == "completed"
        assert result["task_type"] == "video_transcription"

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_comfyui_task')
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_video_transcription_task')
    async def test_execute_parallel_query_not_found(self, mock_check_video, mock_check_comfyui, id_query_agent):
        """測試並行查詢 - 任務不存在"""
        # 所有任務都不存在
        mock_check_comfyui.return_value = None
        mock_check_video.return_value = None

        result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "error"
        assert "找不到任務" in result["error_message"]
        assert "test_task_123" in result["error_message"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_comfyui_task')
    async def test_execute_comfyui_with_video_download(self, mock_check_comfyui, id_query_agent):
        """測試 ComfyUI 任務完成時下載影片"""
        # ComfyUI 任務已完成
        mock_check_comfyui.return_value = {
            "status": "success",
            "task_status": "completed",
            "task_type": "comfyui",
            "report": "ComfyUI 任務已完成"
        }

        # 模擬影片下載功能
        mock_handle_completion = AsyncMock(return_value={
            "status": "success",
            "video_filename": "test_task_123.mp4",
            "video_info": {"duration": 30}
        })

        with patch('sys.modules', {'main': MagicMock(handle_comfyui_completion=mock_handle_completion)}):
            result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "success"
        assert result["has_video"] is True
        assert result["video_filename"] == "test_task_123.mp4"

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_comfyui_task')
    async def test_execute_smart_wait_processing_to_completed(self, mock_check_comfyui, id_query_agent):
        """測試智能等待功能 - 從處理中變為完成"""
        # 第一次查詢：處理中
        # 後續查詢：完成
        mock_check_comfyui.side_effect = [
            {
                "status": "success",
                "task_status": "processing",
                "task_type": "comfyui",
                "report": "ComfyUI 任務處理中"
            },
            {
                "status": "success",
                "task_status": "completed",
                "task_type": "comfyui",
                "report": "ComfyUI 任務已完成"
            }
        ]

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "success"
        assert result["task_status"] == "completed"
        # 驗證至少等待了一次
        mock_sleep.assert_called()

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_comfyui_task')
    async def test_execute_smart_wait_timeout(self, mock_check_comfyui, id_query_agent):
        """測試智能等待功能 - 超時仍在處理中"""
        # 一直返回處理中狀態
        mock_check_comfyui.return_value = {
            "status": "success",
            "task_status": "processing",
            "task_type": "comfyui",
            "report": "ComfyUI 任務處理中"
        }

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "success"
        assert result["task_status"] == "processing"
        # 驗證等待了多次（最多5次）
        assert mock_sleep.call_count <= 5

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, id_query_agent):
        """測試異常處理"""
        with patch('asyncio.as_completed', side_effect=Exception("測試異常")):
            result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "error"
        assert "查詢任務狀態時發生錯誤" in result["error_message"]


class TestIDQueryAgentIntegration:
    """
    測試 ID 查詢代理的整合功能
    """

    @pytest.fixture
    def id_query_agent(self):
        """創建 ID 查詢代理實例"""
        return IDQueryAgent()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, id_query_agent):
        """測試代理初始化"""
        assert id_query_agent.name == "ID Query Agent"
        assert "通用任務 ID 查詢代理" in id_query_agent.description

    @pytest.mark.asyncio
    @patch('asyncio.wait_for')
    async def test_timeout_handling(self, mock_wait_for, id_query_agent):
        """測試超時處理"""
        # 模擬查詢超時
        mock_wait_for.side_effect = [
            asyncio.TimeoutError(),  # ComfyUI 查詢超時
            asyncio.TimeoutError()   # 影片轉錄查詢超時
        ]

        result = await id_query_agent.execute("test_task_123", "test_user_123")

        assert result["status"] == "error"
        assert "找不到任務" in result["error_message"]

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_comfyui_task')
    @patch('multi_tool_agent.agents.id_query_agent.IDQueryAgent._check_video_transcription_task')
    async def test_first_success_wins(self, mock_check_video, mock_check_comfyui, id_query_agent):
        """測試第一個成功的查詢獲勝"""
        # 設定延遲，模擬不同的響應時間
        async def slow_comfyui_check(task_id):
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "task_status": "completed",
                "task_type": "comfyui",
                "report": "ComfyUI 任務已完成"
            }

        async def fast_video_check(task_id):
            return {
                "status": "success",
                "task_status": "completed",
                "task_type": "video_transcription",
                "report": "影片轉錄已完成"
            }

        mock_check_comfyui.side_effect = slow_comfyui_check
        mock_check_video.side_effect = fast_video_check

        result = await id_query_agent.execute("test_task_123", "test_user_123")

        # 應該是影片轉錄結果（更快）
        assert result["task_type"] == "video_transcription"


# 測試執行器
if __name__ == "__main__":
    pytest.main([__file__, "-v"])