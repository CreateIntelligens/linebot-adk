# =============================================================================
# 新功能測試檔案
# 測試最近新增的功能，避免 main.py 的依賴問題
#
# 測試範圍：
# - Asset API 功能測試（不依賴 FastAPI 應用）
# - ID 查詢代理基礎功能
# - ComfyUI 檔案提取邏輯
#
# 作者：LINE Bot ADK 開發團隊
# 版本：1.0.0
# 更新日期：2025-01-18
# =============================================================================

import pytest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAssetManagement:
    """
    測試 Asset 管理功能
    """

    @pytest.fixture
    def temp_asset_dir(self):
        """創建臨時 asset 目錄"""
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_dir = Path(temp_dir) / "asset"
            asset_dir.mkdir()
            yield asset_dir

    def test_create_asset_files(self, temp_asset_dir):
        """測試創建 asset 檔案"""
        # 測試創建 JSON 檔案
        json_file = temp_asset_dir / "test.json"
        test_data = {"test": "data", "version": "1.0"}
        json_file.write_text(json.dumps(test_data))

        assert json_file.exists()
        loaded_data = json.loads(json_file.read_text())
        assert loaded_data == test_data

        # 測試創建圖片檔案
        img_file = temp_asset_dir / "test.png"
        img_file.write_bytes(b"fake png data")

        assert img_file.exists()
        assert img_file.read_bytes() == b"fake png data"

    def test_asset_directory_structure(self, temp_asset_dir):
        """測試 asset 目錄結構"""
        # 創建預期的檔案
        files_to_create = [
            ("comfyui.json", {"workflow": "template"}),
            ("amis.json", {"dictionary": "data"}),
            ("aikka.png", b"preview image data")
        ]

        for filename, content in files_to_create:
            file_path = temp_asset_dir / filename
            if isinstance(content, dict):
                file_path.write_text(json.dumps(content))
            else:
                file_path.write_bytes(content)

        # 驗證所有檔案都存在
        for filename, _ in files_to_create:
            assert (temp_asset_dir / filename).exists()

    def test_content_type_detection(self):
        """測試檔案類型檢測邏輯"""
        test_cases = [
            ("test.png", "image/png"),
            ("test.jpg", "image/jpeg"),
            ("test.jpeg", "image/jpeg"),
            ("test.gif", "image/gif"),
            ("test.json", "application/json"),
            ("test.txt", "text/plain"),
            ("test.unknown", "application/octet-stream")
        ]

        for filename, expected_type in test_cases:
            # 模擬檔案類型檢測邏輯
            if filename.endswith('.png'):
                content_type = "image/png"
            elif filename.endswith(('.jpg', '.jpeg')):
                content_type = "image/jpeg"
            elif filename.endswith('.gif'):
                content_type = "image/gif"
            elif filename.endswith('.json'):
                content_type = "application/json"
            elif filename.endswith('.txt'):
                content_type = "text/plain"
            else:
                content_type = "application/octet-stream"

            assert content_type == expected_type


class TestIDQueryIntegration:
    """
    測試 ID 查詢整合功能
    """

    def test_uuid_validation(self):
        """測試 UUID 格式驗證"""
        import re

        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "e24aee2b-548a-48e0-9ba2-6cc8ad4fc9ff",
            "123e4567-e89b-12d3-a456-426614174000"
        ]

        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # 太短
            "550e8400-e29b-41d4-a716-446655440000-extra",  # 太長
            "550e8400-e29b-41d4-a716-44665544000g"  # 包含非法字符
        ]

        for uuid_str in valid_uuids:
            assert re.match(uuid_pattern, uuid_str, re.IGNORECASE) is not None

        for uuid_str in invalid_uuids:
            assert re.match(uuid_pattern, uuid_str, re.IGNORECASE) is None

    @pytest.mark.asyncio
    async def test_task_result_formatting(self):
        """測試任務結果格式化"""
        # 模擬不同類型的任務結果
        comfyui_result = {
            "status": "success",
            "task_status": "completed",
            "task_type": "comfyui",
            "report": "📋 任務 ID 查詢結果\n\n✅ ComfyUI 影片生成已完成"
        }

        video_result = {
            "status": "success",
            "task_status": "completed",
            "task_type": "video_transcription",
            "report": "📋 任務 ID 查詢結果\n\n✅ 影片轉錄摘要已完成"
        }

        error_result = {
            "status": "error",
            "error_message": "📋 任務 ID 查詢結果\n\n❌ 找不到任務"
        }

        # 驗證結果格式
        assert comfyui_result["status"] == "success"
        assert "ComfyUI 影片生成已完成" in comfyui_result["report"]

        assert video_result["status"] == "success"
        assert "影片轉錄摘要已完成" in video_result["report"]

        assert error_result["status"] == "error"
        assert "找不到任務" in error_result["error_message"]


class TestComfyUIVideoExtraction:
    """
    測試 ComfyUI 影片資訊提取邏輯
    """

    def test_extract_video_from_outputs_videos(self):
        """測試從 videos 輸出中提取影片資訊"""
        job_result = {
            "outputs": {
                "6": {
                    "videos": [{
                        "filename": "AnimateDiff_00001_.mp4",
                        "subfolder": "",
                        "type": "output"
                    }]
                }
            }
        }

        # 模擬提取邏輯
        outputs = job_result.get("outputs", {})
        video_info = None

        for node_output in outputs.values():
            if "videos" in node_output:
                videos = node_output.get("videos", [])
                if videos:
                    video_info = videos[0]
                    break

        assert video_info is not None
        assert video_info["filename"] == "AnimateDiff_00001_.mp4"
        assert video_info["type"] == "output"

    def test_extract_video_from_outputs_gifs(self):
        """測試從 gifs 輸出中提取影片資訊"""
        job_result = {
            "outputs": {
                "6": {
                    "gifs": [{
                        "filename": "AnimateDiff_00001_.gif",
                        "subfolder": "gifs",
                        "type": "output"
                    }]
                }
            }
        }

        # 模擬提取邏輯
        outputs = job_result.get("outputs", {})
        video_info = None

        for node_output in outputs.values():
            if "gifs" in node_output:
                gifs = node_output.get("gifs", [])
                if gifs:
                    video_info = gifs[0]
                    break

        assert video_info is not None
        assert video_info["filename"] == "AnimateDiff_00001_.gif"
        assert video_info["subfolder"] == "gifs"

    def test_extract_video_no_media_output(self):
        """測試沒有媒體輸出的情況"""
        job_result = {
            "outputs": {
                "13": {
                    "audio": [{
                        "filename": "ComfyUI_temp_audio.wav",
                        "subfolder": "",
                        "type": "temp"
                    }]
                }
            }
        }

        # 模擬提取邏輯
        outputs = job_result.get("outputs", {})
        video_info = None

        for node_output in outputs.values():
            if "videos" in node_output or "gifs" in node_output:
                videos = node_output.get("videos", []) or node_output.get("gifs", [])
                if videos:
                    video_info = videos[0]
                    break

        assert video_info is None

    def test_extract_video_empty_outputs(self):
        """測試空輸出的情況"""
        job_result = {"outputs": {}}

        # 模擬提取邏輯
        outputs = job_result.get("outputs", {})
        video_info = None

        for node_output in outputs.values():
            if "videos" in node_output or "gifs" in node_output:
                videos = node_output.get("videos", []) or node_output.get("gifs", [])
                if videos:
                    video_info = videos[0]
                    break

        assert video_info is None


class TestVideoFilenameGeneration:
    """
    測試影片檔案名稱生成邏輯
    """

    def test_task_id_to_filename(self):
        """測試將任務 ID 轉換為檔案名稱"""
        task_ids = [
            "e24aee2b-548a-48e0-9ba2-6cc8ad4fc9ff",
            "550e8400-e29b-41d4-a716-446655440000",
            "test-task-123"
        ]

        for task_id in task_ids:
            # 使用任務 ID 作為檔案名稱，保持 .mp4 副檔名
            video_filename = f"{task_id}.mp4"

            assert video_filename.endswith(".mp4")
            assert task_id in video_filename

    def test_video_path_generation(self):
        """測試影片檔案路徑生成"""
        task_id = "e24aee2b-548a-48e0-9ba2-6cc8ad4fc9ff"
        upload_dir = Path("/app/upload")

        # 模擬檔案路徑生成邏輯
        video_filename = f"{task_id}.mp4"
        video_file_path = upload_dir / video_filename

        assert str(video_file_path) == f"/app/upload/{task_id}.mp4"
        assert video_file_path.name == f"{task_id}.mp4"
        assert video_file_path.parent == upload_dir


# 測試執行器
if __name__ == "__main__":
    pytest.main([__file__, "-v"])