"""
天氣查詢 Agent
提供當前天氣和天氣預報查詢功能
"""

import aiohttp
from typing import Dict, Any
from ..base.agent_base import BaseAgent
from ..base.types import AgentResponse


class WeatherAgent(BaseAgent):
    """天氣查詢 Agent"""

    def __init__(self, name="weather", description="提供天氣查詢和預報服務"):
        super().__init__(name, description)

    async def execute(self, **kwargs) -> AgentResponse:
        """
        執行天氣查詢功能
        根據傳入的參數決定是查詢當前天氣還是天氣預報

        Args:
            **kwargs: 可能包含以下參數
                - action: "current" 或 "forecast"
                - city: 城市名稱
                - days: 預報天數（僅在 forecast 時使用）

        Returns:
            AgentResponse: 查詢結果
        """
        action = kwargs.get("action", "current")

        if action == "current":
            return await self.get_weather(**kwargs)
        elif action == "forecast":
            return await self.get_weather_forecast(**kwargs)
        else:
            return AgentResponse.error(f"不支援的操作: {action}")

    async def get_weather(self, city: str, **kwargs) -> AgentResponse:
        """
        獲取指定城市的當前天氣資訊

        使用 wttr.in API 服務查詢指定城市的即時天氣狀況。
        該 API 提供簡潔的天氣格式，包含溫度、濕度、風速等資訊。

        Args:
            city (str): 要查詢天氣的城市名稱（支援中文和英文）

        Returns:
            AgentResponse: 天氣查詢結果

        Example:
            >>> agent = WeatherAgent()
            >>> result = await agent.get_weather("台北")
            >>> print(result.report)
            🌤️ 台北: 🌦 +19°C
        """
        try:
            self.validate_params(["city"], city=city)

            # 建構 wttr.in API 請求 URL
            # format=3: 簡潔格式，m: 公制單位，lang=zh-tw: 繁體中文
            api_url = f"https://wttr.in/{city}?format=3&m&lang=zh-tw"

            # 使用 aiohttp 非同步 HTTP 客戶端發送請求
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        # 成功取得回應，讀取文字內容
                        weather_text = await response.text()
                        weather_text = weather_text.strip()  # 移除前後空白字元

                        # 返回成功結果，包含表情符號和天氣資訊
                        return AgentResponse.success(
                            report=f"🌤️ {weather_text}",
                            data={"city": city, "weather": weather_text}
                        )
                    else:
                        # API 回應狀態碼不是 200，可能是城市名稱錯誤
                        return AgentResponse.error(
                            f"無法取得 {city} 的天氣資訊，請確認城市名稱正確。"
                        )

        except ValueError as e:
            # 參數驗證錯誤
            return AgentResponse.error(str(e))
        except Exception as e:
            # 捕獲所有異常，包括網路錯誤、解析錯誤等
            return AgentResponse.error(f"查詢天氣時發生錯誤：{str(e)}")

    async def get_weather_forecast(self, city: str, days: str = "3", **kwargs) -> AgentResponse:
        """
        獲取指定城市的天氣預報資訊

        使用 wttr.in API 服務查詢指定城市未來數天的天氣預報。
        支援 1-3 天的預報查詢，預設為 3 天。

        Args:
            city (str): 要查詢預報的城市名稱（支援中文和英文）
            days (str): 預報天數，可選值："1", "2", "3"，預設為 "3"

        Returns:
            AgentResponse: 天氣預報查詢結果

        Example:
            >>> agent = WeatherAgent()
            >>> result = await agent.get_weather_forecast("東京", "2")
            >>> print(result.report)
            🔮 未來2天天氣預報：
            東京: ⛅ +15°C +3 km/h
            東京: 🌦 +12°C +5 km/h
        """
        try:
            self.validate_params(["city"], city=city)

            # 驗證和設定預設值
            if not days or days not in ["1", "2", "3"]:
                days = "3"  # 預設 3 天預報

            # 建構 wttr.in API 請求 URL
            # {days}: 預報天數，m: 公制單位，lang=zh-tw: 繁體中文
            # format: 自訂格式，包含地點、天氣、溫度、風速等
            api_url = f"https://wttr.in/{city}?{days}&m&lang=zh-tw&format=%l:+%c+%t+%w+%p\n"

            # 使用 aiohttp 發送請求，設定 10 秒超時
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        # 成功取得回應
                        forecast_text = await response.text()
                        forecast_text = forecast_text.strip()

                        # 處理多行輸出，只保留指定天數的預報
                        lines = forecast_text.split('\n')[:int(days)]
                        simplified_forecast = '\n'.join(lines)

                        return AgentResponse.success(
                            report=f"🔮 未來{days}天天氣預報：\n{simplified_forecast}",
                            data={
                                "city": city,
                                "days": days,
                                "forecast": simplified_forecast
                            }
                        )
                    else:
                        # API 回應錯誤，可能是城市名稱有誤
                        return AgentResponse.error(
                            f"無法取得 {city} 的天氣預報，請確認城市名稱正確。"
                        )

        except ValueError as e:
            # 參數驗證錯誤
            return AgentResponse.error(str(e))
        except Exception as e:
            # 捕獲所有異常，包括網路超時、解析錯誤等
            return AgentResponse.error(f"查詢天氣預報時發生錯誤：{str(e)}")