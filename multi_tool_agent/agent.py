import datetime
from zoneinfo import ZoneInfo
import aiohttp
import asyncio
from typing import Optional


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    return {
        "status": "success",
        "report": (
            f"The weather in {city} is sunny with a temperature of 25 degrees"
            " Celsius (41 degrees Fahrenheit)."
        ),
    }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    
    # 常見城市的時區對應
    city_timezones = {
        "new york": "America/New_York",
        "紐約": "America/New_York",
        "taipei": "Asia/Taipei",
        "台北": "Asia/Taipei",
        "tokyo": "Asia/Tokyo",
        "東京": "Asia/Tokyo",
        "london": "Europe/London",
        "倫敦": "Europe/London",
        "paris": "Europe/Paris",
        "巴黎": "Europe/Paris",
        "beijing": "Asia/Shanghai",
        "北京": "Asia/Shanghai",
        "shanghai": "Asia/Shanghai",
        "上海": "Asia/Shanghai",
        "hong kong": "Asia/Hong_Kong",
        "香港": "Asia/Hong_Kong",
        "singapore": "Asia/Singapore",
        "新加坡": "Asia/Singapore",
        "sydney": "Australia/Sydney",
        "雪梨": "Australia/Sydney",
        "los angeles": "America/Los_Angeles",
        "洛杉磯": "America/Los_Angeles",
    }
    
    city_key = city.lower()
    tz_identifier = city_timezones.get(city_key)
    
    if not tz_identifier:
        return {
            "status": "error",
            "error_message": (
                f"抱歉，我沒有 {city} 的時區資訊。\n"
                f"目前支援的城市：台北、紐約、東京、倫敦、巴黎、北京、上海、香港、新加坡、雪梨、洛杉磯"
            ),
        }

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = f'{city} 目前時間：{now.strftime("%Y-%m-%d %H:%M:%S %Z")}'
        return {"status": "success", "report": report}
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"取得 {city} 時間時發生錯誤：{str(e)}"
        }


async def create_short_url(url: str, slug: Optional[str] = None) -> dict:
    """Creates a short URL using aiurl.tw service.

    Args:
        url (str): The long URL to be shortened.
        slug (str, optional): Custom slug for the short URL.

    Returns:
        dict: status and shortened URL or error msg.
    """
    api_url = "https://aiurl.tw/api/link/create"
    headers = {
        "authorization": "Bearer ToNf.360",
        "content-type": "application/json"
    }
    
    data = {"url": url}
    if slug:
        data["slug"] = slug
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=data, headers=headers) as response:
                if response.status == 201:
                    result = await response.json()
                    link_info = result.get("link", {})
                    short_url = f"https://aiurl.tw/{link_info.get('slug', '')}"
                    return {
                        "status": "success",
                        "report": f"短網址已建立：{short_url}",
                        "short_url": short_url,
                        "original_url": url
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error_message": f"建立短網址失敗：{response.status} - {error_text}"
                    }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"建立短網址時發生錯誤：{str(e)}"
        }
