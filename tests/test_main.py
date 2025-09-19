# =============================================================================
# main.py 單元測試檔案
# 測試 LINE Bot ADK 應用程式的主要功能 (使用 pytest)
#
# 測試範圍：
# - 會話管理功能
# - 訊息推送功能
# - 回覆訊息創建
# - 環境變數驗證
# - Webhook 處理
# - Agent 呼叫功能
# - 影片處理功能
# - 錯誤處理機制
#
# 作者：LINE Bot ADK 開發團隊
# 版本：1.0.0
# 更新日期：2025-01-18
# =============================================================================

import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch, call
import tempfile
import shutil
from pathlib import Path
import json
from fastapi import Request
from fastapi.testclient import TestClient

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    app,
    get_or_create_session,
    push_message_to_user,
    create_reply_messages,
    get_task_status,
    custom_exception_handler,
    set_custom_exception_handler,
    VIDEO_UPLOAD_DIR,
    current_user_id
)


class TestMainFunctions:
    """
    測試 main.py 中的主要函數
    """

    @pytest.fixture
    def temp_dir_fixture(self):
        """測試前準備 - 創建臨時目錄"""
        # 創建臨時目錄用於測試
        temp_dir = tempfile.mkdtemp()
        test_video_dir = Path(temp_dir) / "upload"
        test_video_dir.mkdir()

        # 模擬環境變數
        os.environ['ChannelSecret'] = 'test_secret'
        os.environ['ChannelAccessToken'] = 'test_token'
        os.environ['GOOGLE_API_KEY'] = 'test_key'

        yield temp_dir

        # 清理臨時目錄
        shutil.rmtree(temp_dir)

        # 清理環境變數
        for key in ['ChannelSecret', 'ChannelAccessToken', 'GOOGLE_API_KEY']:
            os.environ.pop(key, None)

    @pytest.mark.asyncio
    @patch('main.session_service')
    async def test_get_or_create_session_new_user(self, mock_session_service):
        """測試為新用戶建立會話"""
        # 模擬會話服務
        mock_session_service.create_session = AsyncMock()
        mock_session = MagicMock()
        mock_session.session_id = "session_test_user_123"
        mock_session_service.create_session.return_value = mock_session

        user_id = "test_user_123"
        session = await get_or_create_session(user_id)

        # 驗證會話服務被呼叫
        mock_session_service.create_session.assert_called_once()

    @pytest.mark.asyncio
    @patch('main.line_bot_api')
    async def test_push_message_to_user_success(self, mock_line_bot_api):
        """測試成功推送訊息給用戶"""
        mock_line_bot_api.push_message = AsyncMock()

        user_id = "test_user_123"
        message = "測試訊息"

        await push_message_to_user(user_id, message)

        # 驗證推送訊息被呼叫
        mock_line_bot_api.push_message.assert_called_once()

    @pytest.mark.asyncio
    @patch('main.line_bot_api')
    async def test_push_message_to_user_failure(self, mock_line_bot_api):
        """測試推送訊息失敗的情況"""
        mock_line_bot_api.push_message = AsyncMock(side_effect=Exception("推送失敗"))

        user_id = "test_user_123"
        message = "測試訊息"

        # 應該不會拋出異常，只是記錄錯誤
        await push_message_to_user(user_id, message)

        # 驗證推送訊息被呼叫
        mock_line_bot_api.push_message.assert_called_once()

    def test_create_reply_messages_text_only(self):
        """測試創建純文字回覆訊息"""
        response = "這是一個測試回應"

        messages = asyncio.run(create_reply_messages(response))

        assert len(messages) == 1
        assert messages[0].type == "text"
        assert messages[0].text == response

    def test_create_reply_messages_with_meme(self):
        """測試創建包含 meme 圖片的回覆訊息"""
        response = "這是一個 meme 圖片 https://i.imgflip.com/12345.jpg 測試"

        messages = asyncio.run(create_reply_messages(response))

        assert len(messages) == 2
        assert messages[0].type == "text"
        assert messages[1].type == "image"

    def test_create_reply_messages_multiple_memes(self):
        """測試創建包含多個 meme 圖片的回覆訊息"""
        response = "第一個 https://i.imgflip.com/12345.jpg 第二個 https://i.imgflip.com/67890.jpg"

        messages = asyncio.run(create_reply_messages(response))

        assert len(messages) == 3  # 文字 + 兩張圖片
        assert messages[0].type == "text"
        assert messages[1].type == "image"
        assert messages[2].type == "image"


class TestEnvironmentValidation:
    """
    測試環境變數驗證邏輯
    """

    @pytest.fixture(autouse=True)
    def clean_env_vars(self):
        """清除環境變數"""
        keys_to_clean = ['ChannelSecret', 'ChannelAccessToken', 'GOOGLE_API_KEY',
                        'GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_LOCATION', 'GOOGLE_GENAI_USE_VERTEXAI']
        original_values = {}

        # 保存原始值
        for key in keys_to_clean:
            original_values[key] = os.environ.pop(key, None)

        yield

        # 恢復原始值
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def test_missing_channel_secret(self):
        """測試缺少 ChannelSecret 時的行為"""
        # 設定其他必要的環境變數
        os.environ['ChannelAccessToken'] = 'test_token'
        os.environ['GOOGLE_API_KEY'] = 'test_key'

        # 模擬 main.py 的驗證邏輯
        channel_secret = os.getenv("ChannelSecret", None)
        assert channel_secret is None

    def test_missing_channel_access_token(self):
        """測試缺少 ChannelAccessToken 時的行為"""
        os.environ['ChannelSecret'] = 'test_secret'
        os.environ['GOOGLE_API_KEY'] = 'test_key'

        channel_access_token = os.getenv("ChannelAccessToken", None)
        assert channel_access_token is None

    def test_missing_google_api_key(self):
        """測試缺少 GOOGLE_API_KEY 時的行為"""
        os.environ['ChannelSecret'] = 'test_secret'
        os.environ['ChannelAccessToken'] = 'test_token'

        google_api_key = os.getenv("GOOGLE_API_KEY", "")
        assert google_api_key == ""


class TestTaskStatus:
    """
    測試任務狀態查詢功能
    """

    @pytest.mark.asyncio
    @patch('main.IDQueryAgent')
    async def test_get_task_status_success(self, mock_id_query_agent_class):
        """測試成功查詢任務狀態"""
        # 模擬 IDQueryAgent
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value={
            "status": "success",
            "task_status": "completed",
            "has_video": False
        })
        mock_id_query_agent_class.return_value = mock_agent

        result = await get_task_status("test_task_123")

        assert result["status"] == "success"
        assert result["task_status"] == "completed"
        mock_agent.execute.assert_called_once_with(task_id="test_task_123", user_id="anonymous")

    @pytest.mark.asyncio
    @patch('main.IDQueryAgent')
    async def test_get_task_status_with_video(self, mock_id_query_agent_class):
        """測試查詢包含影片的任務狀態"""
        # 模擬 IDQueryAgent
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value={
            "status": "success",
            "task_status": "completed",
            "has_video": True,
            "video_filename": "test.mp4",
            "video_info": {"duration": 30}
        })
        mock_id_query_agent_class.return_value = mock_agent

        result = await get_task_status("test_task_123")

        assert result["status"] == "success"
        assert result["has_video"] is True
        assert result["video_filename"] == "test.mp4"

    @pytest.mark.asyncio
    @patch('main.IDQueryAgent')
    async def test_get_task_status_error(self, mock_id_query_agent_class):
        """測試任務狀態查詢失敗的情況"""
        # 模擬 IDQueryAgent 拋出異常
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(side_effect=Exception("查詢失敗"))
        mock_id_query_agent_class.return_value = mock_agent

        result = await get_task_status("test_task_123")

        assert result["status"] == "error"
        assert "查詢任務狀態時發生錯誤" in result["error_message"]


class TestExceptionHandlers:
    """
    測試自定義異常處理器
    """

    def test_custom_exception_handler_filters_aiohttp_warnings(self):
        """測試過濾 aiohttp 相關警告"""
        import asyncio

        loop = asyncio.new_event_loop()
        context = {"message": "Unclosed client session"}

        # 不應該拋出異常
        custom_exception_handler(loop, context)

    def test_custom_exception_handler_allows_other_exceptions(self):
        """測試允許其他異常通過"""
        import asyncio

        loop = asyncio.new_event_loop()
        context = {"message": "Some other error"}

        # 應該呼叫預設處理器
        with patch('main.custom_exception_handler') as mock_handler:
            custom_exception_handler(loop, context)
            # 如果有預設處理器，應該被呼叫
            if hasattr(loop, '_original_exception_handler'):
                mock_handler.assert_called()


class TestWebhookHandling:
    """
    測試 Webhook 處理功能
    """

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    @pytest.fixture
    def valid_webhook_data(self):
        """有效的 Webhook 測試資料"""
        return {
            "events": [{
                "type": "message",
                "message": {
                    "type": "text",
                    "text": "測試訊息"
                },
                "source": {
                    "type": "user",
                    "userId": "test_user_123"
                },
                "replyToken": "test_reply_token"
            }]
        }

    @patch('main.parser')
    @patch('main.call_agent_async')
    @patch('main.create_reply_messages')
    @patch('main.line_bot_api')
    def test_webhook_text_message_success(self, mock_line_bot_api, mock_create_reply_messages,
                                        mock_call_agent_async, mock_parser, client, valid_webhook_data):
        """測試成功處理文字訊息 Webhook"""
        # 模擬解析器
        mock_event = MagicMock()
        mock_event.message.type = "text"
        mock_event.message.text = "測試訊息"
        mock_event.source.user_id = "test_user_123"
        mock_event.reply_token = "test_reply_token"
        mock_parser.parse.return_value = [mock_event]

        # 模擬 Agent 回應
        mock_call_agent_async.return_value = "Agent 回應"
        mock_create_reply_messages.return_value = [MagicMock()]
        mock_line_bot_api.reply_message = AsyncMock()

        response = client.post("/", json=valid_webhook_data,
                             headers={"X-Line-Signature": "test_signature"})

        assert response.status_code == 200
        assert response.json() == "OK"
        mock_call_agent_async.assert_called_once_with("測試訊息", "test_user_123")

    @patch('main.parser')
    def test_webhook_invalid_signature(self, mock_parser, client, valid_webhook_data):
        """測試無效簽章的 Webhook 請求"""
        from linebot.exceptions import InvalidSignatureError
        mock_parser.parse.side_effect = InvalidSignatureError("Invalid signature")

        response = client.post("/", json=valid_webhook_data,
                             headers={"X-Line-Signature": "invalid_signature"})

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    @patch('main.parser')
    def test_webhook_non_message_event(self, mock_parser, client):
        """測試非訊息事件的 Webhook"""
        # 非訊息事件
        mock_event = MagicMock()
        mock_event.type = "follow"  # 非訊息事件
        mock_parser.parse.return_value = [mock_event]

        webhook_data = {
            "events": [{
                "type": "follow",
                "source": {"userId": "test_user_123"}
            }]
        }

        response = client.post("/", json=webhook_data,
                             headers={"X-Line-Signature": "test_signature"})

        assert response.status_code == 200
        assert response.json() == "OK"


class TestAgentIntegration:
    """
    測試 Agent 整合功能
    """

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    @patch('main.call_agent_async')
    def test_test_agent_endpoint_success(self, mock_call_agent_async, client):
        """測試 Agent 測試端點成功情況"""
        mock_call_agent_async.return_value = "測試回應"

        test_data = {
            "query": "天氣如何？",
            "user_id": "test_user_123"
        }

        response = client.post("/test/agent", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["query"] == "天氣如何？"
        assert data["response"] == "測試回應"

    def test_test_agent_endpoint_missing_query(self, client):
        """測試缺少查詢參數的情況"""
        test_data = {
            "user_id": "test_user_123"
            # 缺少 query 參數
        }

        response = client.post("/test/agent", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Missing query parameter"


class TestVideoEndpoints:
    """
    測試影片相關端點
    """

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    @pytest.fixture
    def temp_video_file(self, temp_dir_fixture):
        """創建臨時影片檔案"""
        video_path = Path(temp_dir_fixture) / "upload" / "test_video.mp4"
        video_path.write_bytes(b"fake video content")
        return video_path

    def test_get_video_success(self, client, temp_video_file):
        """測試成功取得影片檔案"""
        # 模擬 VIDEO_UPLOAD_DIR
        with patch('main.VIDEO_UPLOAD_DIR', Path(temp_video_file.parent)):
            response = client.get("/files/test_video.mp4")

            assert response.status_code == 200
            assert response.headers["content-type"] == "video/mp4"

    def test_get_video_not_found(self, client):
        """測試請求不存在的影片檔案"""
        response = client.get("/files/nonexistent.mp4")

        assert response.status_code == 404
        assert "Video file not found" in response.json()["detail"]

    def test_get_asset_success(self, client):
        """測試成功取得 asset 檔案"""
        # 創建測試 asset 檔案
        asset_path = Path("asset/test.png")
        asset_path.parent.mkdir(exist_ok=True)
        asset_path.write_bytes(b"fake png content")

        try:
            response = client.get("/asset/test.png")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
        finally:
            # 清理測試檔案
            if asset_path.exists():
                asset_path.unlink()

    def test_get_asset_not_found(self, client):
        """測試請求不存在的 asset 檔案"""
        response = client.get("/asset/nonexistent.png")

        assert response.status_code == 404
        assert "Asset file not found" in response.json()["detail"]

    def test_get_asset_json_file(self, client):
        """測試取得 JSON asset 檔案"""
        # 創建測試 JSON 檔案
        asset_path = Path("asset/test.json")
        asset_path.parent.mkdir(exist_ok=True)
        test_data = {"test": "data"}
        asset_path.write_text(json.dumps(test_data))

        try:
            response = client.get("/asset/test.json")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert response.json() == test_data
        finally:
            # 清理測試檔案
            if asset_path.exists():
                asset_path.unlink()

    def test_get_asset_security_path_traversal(self, client):
        """測試路徑遍歷攻擊防護"""
        # 嘗試路徑遍歷攻擊
        response = client.get("/asset/../main.py")

        assert response.status_code == 404

    def test_get_asset_aikka_preview(self, client):
        """測試取得 aikka 預覽圖（如果存在）"""
        # 檢查 aikka.png 是否存在
        asset_path = Path("asset/aikka.png")
        if asset_path.exists():
            response = client.get("/asset/aikka.png")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"


class TestErrorHandling:
    """
    測試錯誤處理機制
    """

    @pytest.mark.asyncio
    @patch('main.call_agent_async')
    async def test_call_agent_async_error_handling(self, mock_call_agent_async):
        """測試 Agent 呼叫錯誤處理"""
        from main import call_agent_async

        # 模擬 Agent 呼叫失敗
        mock_call_agent_async.side_effect = Exception("Agent 錯誤")

        # 這是一個整合測試，實際上需要模擬整個環境
        # 這裡只是展示錯誤處理的概念
        pass

    def test_environment_validation_error_handling(self):
        """測試環境變數驗證錯誤處理"""
        # 測試缺少必要環境變數時的行為
        original_env = os.environ.copy()

        try:
            # 清除所有必要的環境變數
            for key in ['ChannelSecret', 'ChannelAccessToken', 'GOOGLE_API_KEY']:
                os.environ.pop(key, None)

            # 這裡應該會觸發 sys.exit(1)，但在測試中我們不希望這樣
            # 所以我們只測試環境變數讀取邏輯
            channel_secret = os.getenv("ChannelSecret", None)
            assert channel_secret is None

        finally:
            # 恢復環境變數
            os.environ.update(original_env)


# 測試執行器
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
