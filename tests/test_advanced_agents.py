# =============================================================================
# Advanced Agents Pytest 測試檔案
# 測試知識庫、法律諮詢、Meme生成等高級功能
# =============================================================================

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from multi_tool_agent.agent import (
    query_knowledge_base,
    query_set_knowledge_base,
    call_legal_ai,
    generate_meme,
    generate_ai_video,
    get_task_status
)


class TestKnowledgeBase:
    """測試知識庫功能"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.knowledge_agent.KnowledgeAgent')
    async def test_query_hihi_knowledge_success(self, mock_agent_class):
        """測試hihi知識庫查詢成功"""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "status": "success",
            "report": "🎭 hihi導覽先生節目資訊：這是一個台語節目..."
        }
        mock_agent.execute.return_value = mock_result

        result = await query_knowledge_base("hihi導覽先生介紹")

        assert result["status"] == "success"
        assert "hihi導覽先生" in result["report"]
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.knowledge_agent.KnowledgeAgent')
    async def test_query_set_knowledge_success(self, mock_agent_class):
        """測試SET知識庫查詢成功"""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "status": "success",
            "report": "📺 SET三立電視節目資訊：綜藝大熱門是..."
        }
        mock_agent.execute.return_value = mock_result

        result = await query_set_knowledge_base("綜藝大熱門")

        assert result["status"] == "success"
        assert "SET" in result["report"]
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_knowledge_base_exception(self):
        """測試知識庫異常處理"""
        with patch('multi_tool_agent.agents.knowledge_agent.KnowledgeAgent') as mock_class:
            mock_class.side_effect = Exception("知識庫服務錯誤")

            result = await query_knowledge_base("測試問題")

            assert result["status"] == "error"
            assert "知識庫時發生錯誤" in result["error_message"]


class TestLegalAI:
    """測試法律諮詢功能"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.legal_agent.LegalAgent')
    async def test_legal_consultation_success(self, mock_agent_class):
        """測試法律諮詢成功"""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "status": "success",
            "report": "⚖️ 法律建議：根據民法相關規定..."
        }
        mock_agent.execute.return_value = mock_result

        result = await call_legal_ai("租屋契約糾紛")

        assert result["status"] == "success"
        assert "法律建議" in result["report"]
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_legal_consultation_exception(self):
        """測試法律諮詢異常處理"""
        with patch('multi_tool_agent.agents.legal_agent.LegalAgent') as mock_class:
            mock_class.side_effect = Exception("法律服務錯誤")

            result = await call_legal_ai("法律問題")

            assert result["status"] == "error"
            assert "法律諮詢時發生錯誤" in result["error_message"]


class TestMemeGeneration:
    """測試Meme生成功能"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.meme_agent.MemeAgent')
    async def test_generate_meme_success(self, mock_agent_class):
        """測試Meme生成成功"""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "status": "success",
            "report": "🎨 Meme 已生成：https://i.imgflip.com/test123.jpg"
        }
        mock_agent.execute.return_value = mock_result

        result = await generate_meme("當你寫code到半夜")

        assert result["status"] == "success"
        assert "Meme 已生成" in result["report"]
        assert "imgflip.com" in result["report"]
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_meme_exception(self):
        """測試Meme生成異常處理"""
        with patch('multi_tool_agent.agents.meme_agent.MemeAgent') as mock_class:
            mock_class.side_effect = Exception("圖片生成錯誤")

            result = await generate_meme("測試梗圖")

            assert result["status"] == "error"
            assert "生成時發生錯誤" in result["error_message"]


class TestAIVideoGeneration:
    """測試AI影片生成功能"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent')
    async def test_generate_ai_video_success(self, mock_agent_class):
        """測試AI影片生成成功"""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "status": "success",
            "report": "🎬 AI影片生成中...任務ID: video_12345"
        }
        mock_agent.execute.return_value = mock_result

        result = await generate_ai_video("生成一段關於科技的影片")

        assert result["status"] == "success"
        assert "AI影片生成" in result["report"]
        assert "任務ID" in result["report"]
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_ai_video_exception(self):
        """測試AI影片生成異常處理"""
        with patch('multi_tool_agent.agents.comfyui_agent.ComfyUIAgent') as mock_class:
            mock_class.side_effect = Exception("影片生成服務錯誤")

            result = await generate_ai_video("測試影片")

            assert result["status"] == "error"
            assert "生成時發生錯誤" in result["error_message"]


class TestTaskStatus:
    """測試任務狀態查詢功能"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.video_utils.process_video_task')
    async def test_get_task_status_success(self, mock_video_task):
        """測試任務狀態查詢成功"""
        mock_video_task.return_value = {
            "status": "success",
            "task_status": "completed",
            "report": "✅ 任務已完成：影片處理完成"
        }

        result = await get_task_status("task_12345")

        assert result["status"] == "success"
        assert result["task_status"] == "completed"
        assert "任務已完成" in result["report"]
        mock_video_task.assert_called_once_with("task_12345")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.video_utils.process_video_task')
    async def test_get_task_status_processing(self, mock_video_task):
        """測試任務狀態查詢進行中"""
        mock_video_task.return_value = {
            "status": "success",
            "task_status": "processing",
            "report": "⏳ 任務處理中...預估還需5分鐘"
        }

        result = await get_task_status("task_67890")

        assert result["status"] == "success"
        assert result["task_status"] == "processing"
        assert "處理中" in result["report"]

    @pytest.mark.asyncio
    async def test_get_task_status_exception(self):
        """測試任務狀態查詢異常處理"""
        with patch('multi_tool_agent.utils.video_utils.process_video_task') as mock_task:
            mock_task.side_effect = Exception("任務查詢服務錯誤")

            result = await get_task_status("invalid_task")

            assert result["status"] == "error"
            assert "狀態時發生錯誤" in result["error_message"]


@pytest.mark.parametrize("knowledge_type,function,expected_text", [
    ("hihi", query_knowledge_base, "hihi導覽先生"),
    ("set", query_set_knowledge_base, "SET三立電視"),
])
@pytest.mark.asyncio
async def test_knowledge_base_types(knowledge_type, function, expected_text):
    """參數化測試不同知識庫類型"""
    with patch('multi_tool_agent.agents.knowledge_agent.KnowledgeAgent') as mock_class:
        mock_agent = AsyncMock()
        mock_class.return_value = mock_agent

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "status": "success",
            "report": f"📚 {expected_text}相關資訊..."
        }
        mock_agent.execute.return_value = mock_result

        result = await function("測試問題")

        assert result["status"] == "success"
        assert expected_text in result["report"]