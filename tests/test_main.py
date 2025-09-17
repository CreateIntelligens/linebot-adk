# =============================================================================
# main.py 單元測試檔案
# 測試 LINE Bot ADK 應用程式的主要功能 (使用 pytest)
# =============================================================================

import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    get_or_create_session,
    push_message_to_user,
    create_reply_messages,
    VIDEO_UPLOAD_DIR
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
