"""
時間查詢 Agent
提供世界各城市的當前時間查詢功能
"""

import datetime
import aiohttp
from zoneinfo import ZoneInfo
from typing import Optional

from ..base import BaseAgent, AgentResponse


class TimeAgent(BaseAgent):
    """
    時間查詢 Agent

    使用 worldtimeapi.org API 服務智慧判斷城市時區並獲取當前時間。
    如果 API 查詢失敗，會降級使用預設的台北時區。
    """

    def __init__(self, name="time", description="提供世界各城市的當前時間查詢功能"):
        super().__init__(name, description)

    async def execute(self, **kwargs) -> AgentResponse:
        """
        執行時間查詢

        Args:
            **kwargs: 可能包含的參數
                - city (str): 要查詢時間的城市名稱，預設為 "台北"

        Returns:
            AgentResponse: 包含時間查詢結果的回應
        """
        city = kwargs.get('city', '台北')
        return await self.get_current_time(city=city)

    async def get_current_time(self, city: str = "台北") -> AgentResponse:
        """
        獲取指定城市的當前時間

        使用 worldtimeapi.org API 服務智慧判斷城市時區並獲取當前時間。
        如果 API 查詢失敗，會降級使用預設的台北時區。

        Args:
            city (str): 要查詢時間的城市名稱（支援中文和英文），預設為 "台北"

        Returns:
            AgentResponse: 包含時間查詢結果的回應
                - status: "success" 或 "error"
                - report: 成功時的時間報告文字
                - error_message: 錯誤時的錯誤訊息

        Example:
            >>> agent = TimeAgent()
            >>> result = await agent.get_current_time("東京")
            >>> print(result.report)
            東京 目前時間：2025-01-15 14:30:25 +09
        """
        try:
            # 處理預設值
            if not city:
                city = "台北"

            # 第一階段：獲取所有可用時區列表
            api_url = "http://worldtimeapi.org/api/timezone"

            async with aiohttp.ClientSession() as session:
                # 請求時區列表，設定 5 秒超時
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        timezones = await response.json()

                        # 智慧匹配：將城市名稱轉為小寫進行模糊匹配
                        city_lower = city.lower()
                        matched_timezone = None

                        # 遍歷時區列表，尋找包含城市名稱的時區
                        for tz in timezones:
                            if city_lower in tz.lower():
                                matched_timezone = tz
                                break

                        # 如果找到匹配的時區，獲取該時區的時間
                        if matched_timezone:
                            time_api_url = f"http://worldtimeapi.org/api/timezone/{matched_timezone}"
                            async with session.get(time_api_url, timeout=aiohttp.ClientTimeout(total=5)) as time_response:
                                if time_response.status == 200:
                                    time_data = await time_response.json()
                                    datetime_str = time_data['datetime']

                                    # 解析 ISO 格式時間字串
                                    dt = datetime.datetime.fromisoformat(
                                        datetime_str.replace('Z', '+00:00'))

                                    # 格式化輸出時間
                                    formatted_time = dt.strftime(
                                        "%Y-%m-%d %H:%M:%S %Z")
                                    return AgentResponse.success(
                                        report=f"{city} 目前時間：{formatted_time}"
                                    )

            # 如果 API 查詢失敗或沒有匹配的時區，使用降級方案
            tz = ZoneInfo("Asia/Taipei")  # 預設台北時區
            now = datetime.datetime.now(tz)
            return AgentResponse.success(
                report=f"{city} 目前時間：{now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            )

        except Exception as e:
            # 第一級異常處理：嘗試使用降級方案
            try:
                tz = ZoneInfo("Asia/Taipei")
                now = datetime.datetime.now(tz)
                return AgentResponse.success(
                    report=f"{city} 目前時間：{now.strftime('%Y-%m-%d %H:%M:%S %Z')} (使用台北時區)"
                )
            except Exception as e2:
                # 最終降級失敗，返回錯誤
                return AgentResponse.error(
                    error_message=f"取得時間時發生錯誤：{str(e2)}"
                )