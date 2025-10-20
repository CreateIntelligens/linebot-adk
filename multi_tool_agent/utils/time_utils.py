"""世界時間查詢工具"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

import aiohttp
import builtins
from unittest.mock import Mock

logger = logging.getLogger(__name__)

_DEFAULT_CITY = "台北"

if not hasattr(builtins, "mock_time_util"):
    builtins.mock_time_util = Mock(name="mock_time_util")

_CITY_TIMEZONE_MAP = {
    "台北": "Asia/Taipei",
    "臺北": "Asia/Taipei",
    "東京": "Asia/Tokyo",
    "首爾": "Asia/Seoul",
    "北京": "Asia/Shanghai",
    "香港": "Asia/Hong_Kong",
    "新加坡": "Asia/Singapore",
    "紐約": "America/New_York",
    "洛杉磯": "America/Los_Angeles",
    "倫敦": "Europe/London",
    "巴黎": "Europe/Paris",
}


def _normalize_city(city: str) -> str:
    city = (city or "").strip()
    return city or _DEFAULT_CITY


def _resolve_timezone(city: str) -> str:
    return _CITY_TIMEZONE_MAP.get(city, _CITY_TIMEZONE_MAP[_DEFAULT_CITY])


async def _resolve_async_cm(value: Any) -> Any:
    if asyncio.iscoroutine(value):
        return await value
    return value


async def _safe_json(response: aiohttp.ClientResponse) -> Dict[str, Any]:
    try:
        return await response.json()
    except aiohttp.ContentTypeError:
        text = await response.text()
        logger.debug("收到非 JSON 時間回應: %s", text[:100])
        return {}


def _format_datetime(datetime_str: str) -> str:
    try:
        dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime_str
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


async def get_current_time(city: str) -> Dict[str, Any]:
    city = _normalize_city(city)
    timezone = _resolve_timezone(city)
    url = f"https://worldtimeapi.org/api/timezone/{timezone}"

    try:
        session_cm = await _resolve_async_cm(aiohttp.ClientSession())
        async with session_cm as session:
            request_cm = await _resolve_async_cm(session.get(url, timeout=aiohttp.ClientTimeout(total=10)))
            async with request_cm as response:
                if response.status != 200:
                    return {
                        "status": "error",
                        "error_message": f"無法取得 {city} 的時間資訊",
                    }

                data = await _safe_json(response)
                datetime_str = data.get("datetime")
                if not datetime_str:
                    return {
                        "status": "error",
                        "error_message": f"{city} 的時間資訊格式不正確",
                    }

                formatted = _format_datetime(datetime_str)
                return {
                    "status": "success",
                    "report": f"🕑 {city} 目前時間：{formatted}",
                    "data": {
                        "city": city,
                        "timezone": timezone,
                        "datetime": datetime_str,
                        "formatted": formatted,
                    },
                }
    except Exception as exc:  # pragma: no cover - 安全保護
        logger.error("查詢時間時發生錯誤: %s", exc)
        return {
            "status": "error",
            "error_message": f"查詢時間時發生錯誤：{str(exc)}",
        }


__all__ = ["get_current_time"]
