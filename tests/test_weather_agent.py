# =============================================================================
# Weather Utils Pytest 測試檔案
# 測試天氣查詢和預報功能 (使用 utils 實作)
# =============================================================================

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from multi_tool_agent.agent import get_weather, get_weather_forecast, get_current_time



class TestWeatherUtils:
    """測試天氣查詢 utils 實作"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.weather_utils.get_weather')
    async def test_get_weather_success(self, mock_get_weather):
        """測試天氣查詢成功"""
        mock_get_weather.return_value = {
            "status": "success",
            "report": "🌤️ 台北: 🌦 +19°C"
        }

        result = await get_weather("台北")

        assert result["status"] == "success"
        assert "report" in result
        mock_get_weather.assert_called_once_with("台北")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.weather_utils.get_weather')
    async def test_get_weather_error(self, mock_get_weather):
        """測試天氣查詢錯誤處理"""
        mock_get_weather.side_effect = Exception("天氣服務錯誤")

        result = await get_weather("不存在的城市")

        assert result["status"] == "error"
        assert "error_message" in result

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.weather_utils.get_weather_forecast')
    async def test_get_weather_forecast_success(self, mock_get_weather_forecast):
        """測試天氣預報成功"""
        mock_get_weather_forecast.return_value = {
            "status": "success",
            "report": "🔮 未來2天天氣預報：東京: ⛅ +15°C +3 km/h"
        }

        result = await get_weather_forecast("東京", "2")

        assert result["status"] == "success"
        assert "report" in result
        mock_get_weather_forecast.assert_called_once_with("東京", "2")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.weather_utils.get_weather_forecast')
    async def test_get_weather_forecast_default_days(self, mock_get_weather_forecast):
        """測試天氣預報使用預設天數"""
        mock_get_weather_forecast.return_value = {
            "status": "success",
            "report": "🔮 未來3天天氣預報：東京: ⛅ +15°C +3 km/h"
        }

        result = await get_weather_forecast("東京", "")

        assert result["status"] == "success"
        assert "report" in result
        mock_get_weather_forecast.assert_called_once_with("東京", "")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.time_utils.get_current_time')
    async def test_get_current_time_success(self, mock_get_current_time):
        """測試獲取當前時間成功"""
        mock_get_current_time.return_value = {
            "status": "success",
            "report": "🕑 台北 目前時間：2025-01-15 14:30:25 +0800"
        }

        result = await get_current_time("台北")

        assert result["status"] == "success"
        assert "台北" in result["report"]
        mock_get_current_time.assert_called_once_with("台北")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.time_utils.get_current_time')
    async def test_get_current_time_default_city(self, mock_get_current_time):
        """測試獲取當前時間使用預設城市"""
        mock_get_current_time.return_value = {
            "status": "success",
            "report": "台北 目前時間：2025-01-15 14:30:25 +08"
        }

        result = await get_current_time("")  # 空字串應該使用預設值

        assert result["status"] == "success"
        mock_get_current_time.assert_called_once_with("")

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.time_utils.get_current_time')
    async def test_get_current_time_error(self, mock_get_current_time):
        """測試獲取當前時間錯誤"""
        mock_get_current_time.side_effect = Exception("時間服務錯誤")

        result = await get_current_time("東京")

        assert result["status"] == "error"
        assert "發生錯誤" in result["error_message"]


# 參數化測試已經在上面的forecast測試中涵蓋，這裡不需要重複


@pytest.mark.parametrize("days,expected_days_param", [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("", ""),  # 空字串
])
@pytest.mark.asyncio
@patch('multi_tool_agent.utils.weather_utils.get_weather_forecast')
async def test_get_weather_forecast_days(mock_forecast_util, days, expected_days_param):
    """參數化測試不同預報天數"""
    mock_forecast_util.return_value = {
        "status": "success",
        "report": f"🔮 未來{days or '3'}天天氣預報：東京: ⛅ +15°C +3 km/h"
    }

    result = await get_weather_forecast("東京", days)

    assert result["status"] == "success"
    mock_forecast_util.assert_called_once_with("東京", expected_days_param)


class TestWeatherIntegration:
    """測試天氣功能整合測試"""

    @pytest.mark.asyncio
    @patch('multi_tool_agent.utils.weather_utils.get_weather_forecast')
    @patch('multi_tool_agent.utils.weather_utils.get_weather')
    async def test_weather_workflow(self, mock_weather_util, mock_forecast_util):
        """測試完整的天氣查詢工作流程"""
        # 設定mock回應
        mock_weather_util.return_value = {
            "status": "success",
            "report": "🌤️ 台北: 🌦 +19°C"
        }

        mock_forecast_util.return_value = {
            "status": "success",
            "report": "🔮 未來2天天氣預報：台北: ⛅ +15°C +3 km/h"
        }

        # 執行工作流程
        current_result = await get_weather("台北")
        forecast_result = await get_weather_forecast("台北", "2")

        assert current_result["status"] == "success"
        assert forecast_result["status"] == "success"

        # 驗證呼叫次數和參數
        mock_weather_util.assert_called_once_with("台北")
        mock_forecast_util.assert_called_once_with("台北", "2")
