# =============================================================================
# Weather Agent Pytest 測試檔案
# 測試天氣查詢和預報功能 (直接調用 Agent 實例)
# =============================================================================

import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_tool_agent.agent import get_weather, get_weather_forecast, get_current_time
from multi_tool_agent.base.types import AgentResponse


class TestWeatherAgentDirect:
    """測試天氣查詢直接調用 Agent 實例"""

    @pytest.fixture(autouse=True)
    def setup_weather_agent(self, mocker):
        """設定 WeatherAgent mock"""
        # Mock WeatherAgent 實例
        mock_weather_agent = mocker.patch('multi_tool_agent.agent.weather_agent')

        # 設定預設成功回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "🌤️ 台北: 🌦 +19°C",
            "data": {"city": "台北"}
        }
        mock_weather_agent.get_weather.return_value = mock_response
        mock_weather_agent.get_weather_forecast.return_value = mock_response

        return mock_weather_agent

    @pytest.fixture(autouse=True)
    def setup_time_agent(self, mocker):
        """設定 TimeAgent mock"""
        # Mock TimeAgent 實例
        mock_time_agent = mocker.patch('multi_tool_agent.agent.time_agent')

        # 設定預設成功回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "台北 目前時間：2025-01-15 14:30:25 +08",
            "data": {"city": "台北"}
        }
        mock_time_agent.get_current_time.return_value = mock_response

        return mock_time_agent

    @pytest.mark.asyncio
    async def test_get_weather_direct_success(self, setup_weather_agent):
        """測試天氣查詢直接調用成功"""
        result = await get_weather("台北")

        assert result["status"] == "success"
        assert result["report"] == "🌤️ 台北: 🌦 +19°C"
        setup_weather_agent.get_weather.assert_called_once_with(city="台北")

    @pytest.mark.asyncio
    async def test_get_weather_direct_error(self, setup_weather_agent):
        """測試天氣查詢直接調用錯誤處理"""
        # 設定錯誤回應
        setup_weather_agent.get_weather.side_effect = Exception("測試錯誤")

        result = await get_weather("台北")

        assert result["status"] == "error"
        assert "發生錯誤" in result["error_message"]

    @pytest.mark.asyncio
    async def test_get_weather_forecast_direct_success(self, setup_weather_agent):
        """測試天氣預報直接調用成功"""
        # 設定預報成功回應
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "🔮 未來2天天氣預報：東京: ⛅ +15°C +3 km/h",
            "data": {"city": "東京", "days": "2"}
        }
        setup_weather_agent.get_weather_forecast.return_value = mock_response

        result = await get_weather_forecast("東京", "2")

        assert result["status"] == "success"
        assert "未來2天" in result["report"]
        setup_weather_agent.get_weather_forecast.assert_called_once_with(city="東京", days="2")

    @pytest.mark.asyncio
    async def test_get_weather_forecast_default_days(self, setup_weather_agent):
        """測試天氣預報使用預設天數"""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "status": "success",
            "report": "🔮 未來3天天氣預報：東京: ⛅ +15°C +3 km/h",
            "data": {"city": "東京", "days": "3"}
        }
        setup_weather_agent.get_weather_forecast.return_value = mock_response

        result = await get_weather_forecast("東京", "")

        assert result["status"] == "success"
        setup_weather_agent.get_weather_forecast.assert_called_once_with(city="東京", days="")

    @pytest.mark.asyncio
    async def test_get_current_time_direct_success(self, setup_time_agent):
        """測試獲取當前時間直接調用成功"""
        result = await get_current_time("台北")

        assert result["status"] == "success"
        assert "台北" in result["report"]
        setup_time_agent.get_current_time.assert_called_once_with(city="台北")

    @pytest.mark.asyncio
    async def test_get_current_time_default_city(self, setup_time_agent):
        """測試獲取當前時間使用預設城市"""
        result = await get_current_time("")  # 空字串應該使用預設值

        assert result["status"] == "success"
        setup_time_agent.get_current_time.assert_called_once_with(city="")

    @pytest.mark.asyncio
    async def test_get_current_time_direct_error(self, setup_time_agent):
        """測試獲取當前時間直接調用錯誤"""
        setup_time_agent.get_current_time.side_effect = Exception("時間服務錯誤")

        result = await get_current_time("東京")

        assert result["status"] == "error"
        assert "發生錯誤" in result["error_message"]


# 參數化測試 - 測試不同城市的預設行為
@pytest.mark.parametrize("city,expected_city_param", [
    ("台北", "台北"),
    ("東京", "東京"),
    ("New York", "New York"),
    ("", ""),  # 空字串
])
@pytest.mark.asyncio
async def test_get_weather_cities(city, expected_city_param, mocker):
    """參數化測試不同城市的預設行為"""
    # Mock WeatherAgent 實例
    mock_weather_agent = mocker.patch('multi_tool_agent.agent.weather_agent')
    mock_response = MagicMock()
    mock_response.to_dict.return_value = {
        "status": "success",
        "report": f"🌤️ {city or '台北'}: 🌦 +19°C",
        "data": {"city": city or "台北"}
    }
    mock_weather_agent.get_weather.return_value = mock_response

    result = await get_weather(city)

    assert result["status"] == "success"
    mock_weather_agent.get_weather.assert_called_once_with(city=expected_city_param)


@pytest.mark.parametrize("days,expected_days_param", [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("", ""),  # 空字串
])
@pytest.mark.asyncio
async def test_get_weather_forecast_days(days, expected_days_param, mocker):
    """參數化測試不同預報天數"""
    # Mock WeatherAgent 實例
    mock_weather_agent = mocker.patch('multi_tool_agent.agent.weather_agent')
    mock_response = MagicMock()
    mock_response.to_dict.return_value = {
        "status": "success",
        "report": f"🔮 未來{days or '3'}天天氣預報：東京: ⛅ +15°C +3 km/h",
        "data": {"city": "東京", "days": days or "3"}
    }
    mock_weather_agent.get_weather_forecast.return_value = mock_response

    result = await get_weather_forecast("東京", days)

    assert result["status"] == "success"
    mock_weather_agent.get_weather_forecast.assert_called_once_with(city="東京", days=expected_days_param)


class TestWeatherAgentIntegration:
    """測試天氣功能整合測試"""

    @pytest.mark.asyncio
    async def test_weather_workflow(self, mocker):
        """測試完整的天氣查詢工作流程"""
        # Mock WeatherAgent 實例
        mock_weather_agent = mocker.patch('multi_tool_agent.agent.weather_agent')

        # 設定連續呼叫的回應
        current_weather_response = MagicMock()
        current_weather_response.to_dict.return_value = {
            "status": "success",
            "report": "🌤️ 台北: 🌦 +19°C",
            "data": {"city": "台北"}
        }

        forecast_response = MagicMock()
        forecast_response.to_dict.return_value = {
            "status": "success",
            "report": "🔮 未來2天天氣預報：台北: ⛅ +15°C +3 km/h",
            "data": {"city": "台北", "days": "2"}
        }

        mock_weather_agent.get_weather.return_value = current_weather_response
        mock_weather_agent.get_weather_forecast.return_value = forecast_response

        # 執行工作流程
        current_result = await get_weather("台北")
        forecast_result = await get_weather_forecast("台北", "2")

        assert current_result["status"] == "success"
        assert forecast_result["status"] == "success"

        # 驗證呼叫次數和參數
        mock_weather_agent.get_weather.assert_called_once_with(city="台北")
        mock_weather_agent.get_weather_forecast.assert_called_once_with(city="台北", days="2")
