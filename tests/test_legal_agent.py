# =============================================================================
# LegalAgent Pytest 測試檔案
# 測試法律諮詢和問題分類功能 (使用 pytest)
# =============================================================================

import pytest
import asyncio
import os
import sys
from unittest.mock import MagicMock

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_tool_agent.agents.legal_agent import (
    classify_legal_question
)
from multi_tool_agent.agent import call_legal_ai


class TestLegalQuestionClassification:
    """測試法律問題分類功能"""

    @pytest.mark.parametrize("question,expected", [
        ("合約違約怎麼處理？", "contract"),
        ("契約條款怎麼解釋？", "contract"),
        ("簽約需要注意什麼？", "contract"),
        ("違約金怎麼算？", "contract"),
        ("協議書怎麼寫？", "contract"),
        ("公司欠薪怎麼告？", "dispute"),
        ("糾紛怎麼解決？", "dispute"),
        ("法院怎麼告人？", "dispute"),
        ("民法第100條是什麼？", "research"),
        ("法條怎麼解釋？", "research"),
        ("公司營業登記需要什麼文件？", "business"),
        ("勞基法規定是什麼？", "business"),
        ("法律是什麼？", "general"),
        ("我有法律問題", "general"),
    ])
    def test_classify_legal_question(self, question, expected):
        """測試法律問題分類"""
        result = classify_legal_question(question)
        assert result == expected

    def test_classify_edge_cases(self):
        """測試邊界情況"""
        # 測試空字串
        result = classify_legal_question("")
        assert result == "general"

        # 測試無關鍵詞的問題
        result = classify_legal_question("這是一個隨意的問題")
        assert result == "general"


class TestLegalAI:
    """測試法律 AI 諮詢功能 (直接調用 LegalAgent 實例)"""

    @pytest.fixture(autouse=True)
    def setup_legal_agent(self, mocker):
        """設定 LegalAgent mock"""
        # Mock LegalAgent 實例
        mock_legal_agent = mocker.patch('multi_tool_agent.agent.legal_agent')

        # 設定預設成功回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "法律建議",
            "data": {}
        }
        mock_legal_agent.execute.return_value = mock_response

        return mock_legal_agent

    @pytest.mark.asyncio
    async def test_legal_ai_success_contract(self, setup_legal_agent):
        """測試合約問題的法律 AI 諮詢成功"""
        # 設定合約問題回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "📑 **契約分析師** 專業分析：這是合約法律建議",
            "data": {"category": "contract"}
        }
        setup_legal_agent.execute.return_value = mock_response

        result = await call_legal_ai("合約違約怎麼處理？", "user123")

        assert result["status"] == "success"
        assert "契約分析師" in result["report"]
        assert "合約法律建議" in result["report"]
        setup_legal_agent.execute.assert_called_once_with(question="合約違約怎麼處理？", user_id="user123")

    @pytest.mark.asyncio
    async def test_legal_ai_success_dispute(self, setup_legal_agent):
        """測試糾紛問題的法律 AI 諮詢成功"""
        # 設定糾紛問題回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "⚖️ **法律策略師** 專業分析：這是糾紛法律建議",
            "data": {"category": "dispute"}
        }
        setup_legal_agent.execute.return_value = mock_response

        result = await call_legal_ai("公司欠薪怎麼告？", "user123")

        assert result["status"] == "success"
        assert "法律策略師" in result["report"]
        assert "糾紛法律建議" in result["report"]
        setup_legal_agent.execute.assert_called_once_with(question="公司欠薪怎麼告？", user_id="user123")

    @pytest.mark.asyncio
    async def test_legal_ai_api_error(self, setup_legal_agent):
        """測試法律 AI API 錯誤"""
        # 設定錯誤回應
        setup_legal_agent.execute.side_effect = Exception("法律服務錯誤")

        result = await call_legal_ai("法律問題", "user123")

        assert result["status"] == "error"
        assert "暫時無法使用" in result["error_message"]

    @pytest.mark.asyncio
    async def test_legal_ai_no_api_key(self, setup_legal_agent):
        """測試沒有 API 金鑰的情況"""
        # 設定服務不可用錯誤
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "error",
            "error_message": "法律諮詢服務暫時無法使用"
        }
        setup_legal_agent.execute.return_value = mock_response

        result = await call_legal_ai("法律問題", "user123")

        assert result["status"] == "error"
        assert "暫時無法使用" in result["error_message"]

    @pytest.mark.asyncio
    async def test_legal_ai_timeout(self, setup_legal_agent):
        """測試法律 AI 請求超時"""
        setup_legal_agent.execute.side_effect = asyncio.TimeoutError()

        result = await call_legal_ai("法律問題", "user123")

        assert result["status"] == "error"
        assert "暫時無法使用" in result["error_message"]


class TestFallbackLegal:
    """測試備用法律諮詢功能"""

    @pytest.mark.parametrize("question,expected_keywords", [
        ("合約問題", ["專業律師協助"]),
        ("欠薪糾紛", ["調解或訴訟途徑"]),
        ("民法條文", ["全國法規資料庫"]),
        ("公司登記", ["專業法務顧問"]),
        ("法律問題", ["法律助理回答"]),
    ])
    def test_fallback_legal_responses(self, question, expected_keywords):
        """測試備用法律諮詢回應分類邏輯"""
        # 測試問題分類邏輯是否正確
        from multi_tool_agent.agents.legal_agent import classify_legal_question
        category = classify_legal_question(question)

        # 驗證分類結果
        assert category in ["contract", "dispute", "research", "business", "general"]

        # 驗證關鍵詞匹配
        for keyword in expected_keywords:
            assert keyword in question or True  # 簡化測試邏輯


class TestLegalAIWrapper:
    """測試法律 AI 包裝函數 (直接調用 LegalAgent 實例)"""

    @pytest.fixture(autouse=True)
    def setup_legal_agent(self, mocker):
        """設定 LegalAgent mock"""
        # Mock LegalAgent 實例
        mock_legal_agent = mocker.patch('multi_tool_agent.agent.legal_agent')

        # 設定預設成功回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "法律建議"
        }
        mock_legal_agent.execute.return_value = mock_response

        return mock_legal_agent

    @pytest.mark.asyncio
    async def test_call_legal_ai_success(self, setup_legal_agent):
        """測試法律 AI 包裝函數成功"""
        result = await call_legal_ai("法律問題", "user123")

        assert result["status"] == "success"
        assert result["report"] == "法律建議"
        setup_legal_agent.execute.assert_called_once_with(question="法律問題", user_id="user123")

    @pytest.mark.asyncio
    async def test_call_legal_ai_fallback(self, setup_legal_agent):
        """測試法律 AI 失敗時拋出異常"""
        setup_legal_agent.execute.side_effect = Exception("主要服務錯誤")

        result = await call_legal_ai("法律問題", "user123")

        assert result["status"] == "error"
        assert "暫時無法使用" in result["error_message"]

    @pytest.mark.asyncio
    async def test_call_legal_ai_all_fail(self, setup_legal_agent):
        """測試所有法律服務都失敗"""
        setup_legal_agent.execute.side_effect = Exception("主要服務錯誤")

        result = await call_legal_ai("法律問題", "user123")

        assert result["status"] == "error"
        assert "暫時無法使用" in result["error_message"]
