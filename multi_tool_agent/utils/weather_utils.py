"""天氣查詢工具函數 - 以 wttr.in 為資料來源"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

import aiohttp

logger = logging.getLogger(__name__)

_DEFAULT_FORECAST_DAYS = "3"


def _normalize_city(city: str) -> str:
    city = (city or "").strip()
    return city or "台北"


async def _resolve_async_cm(value: Any) -> Any:
    """等待 coroutine 物件，確保可以作為 async context manager 使用"""
    if asyncio.iscoroutine(value):
        return await value
    return value


async def _safe_json(response: aiohttp.ClientResponse) -> Dict[str, Any]:
    try:
        return await response.json()
    except aiohttp.ContentTypeError:
        text = await response.text()
        logger.debug("收到非 JSON 天氣回應: %s", text[:100])
        return {}


def _format_current_weather(data: Dict[str, Any], fallback_city: str) -> Dict[str, Any]:
    if "main" in data and "weather" in data:
        city_name = data.get("name") or fallback_city
        description = (data.get("weather") or [{}])[0].get("description", "天氣資訊缺失")
        temperature = data.get("main", {}).get("temp", "N/A")
        return {
            "status": "success",
            "report": f"🌤️ {city_name}: {description} {temperature}°C",
            "data": {
                "city": city_name,
                "description": description,
                "temperature": temperature,
            },
        }

    current = (data.get("current_condition") or [{}])[0]
    description = (current.get("weatherDesc") or [{}])[0].get("value", "天氣資訊缺失")
    temperature = current.get("temp_C", "N/A")

    area = (data.get("nearest_area") or [{}])[0]
    city_name = (area.get("areaName") or [{}])[0].get("value", fallback_city)

    return {
        "status": "success",
        "report": f"🌤️ {city_name}: {description} {temperature}°C",
        "data": {
            "city": city_name,
            "description": description,
            "temperature": temperature,
        },
    }


def _format_forecast(data: Dict[str, Any], days: str, city: str) -> Dict[str, Any]:
    try:
        days_int = int(days) if days else int(_DEFAULT_FORECAST_DAYS)
    except ValueError:
        days_int = int(_DEFAULT_FORECAST_DAYS)

    lines = []

    if "list" in data and data["list"]:
        entries = data["list"][:days_int]
        for entry in entries:
            temp = entry.get("main", {}).get("temp", "N/A")
            description = (entry.get("weather") or [{}])[0].get("description", "天氣資訊缺失")
            date = entry.get("dt_txt") or str(entry.get("dt", "未知時間"))
            lines.append(f"{date}: {description} {temp}°C")
    else:
        weather_list = data.get("weather", [])
        selected_days = weather_list[:days_int]
        for day in selected_days:
            date = day.get("date", "未知日期")
            hourly = (day.get("hourly") or [{}])[0]
            description = (hourly.get("weatherDesc") or [{}])[0].get("value", "天氣資訊缺失")
            temperature = hourly.get("tempC", "N/A")
            lines.append(f"{date}: {description} {temperature}°C")

    if not lines:
        return {
            "status": "error",
            "error_message": f"{city} 的天氣預報資料缺失",
        }

    report_body = "\n".join(lines)
    return {
        "status": "success",
        "report": f"🔮 未來{days_int}天天氣預報（{city}）：\n{report_body}",
        "data": {
            "city": city,
            "days": str(days_int),
        },
    }


async def get_weather(city: str) -> Dict[str, Any]:
    city = _normalize_city(city)
    url = f"https://wttr.in/{city}?format=j1"

    try:
        session_cm = await _resolve_async_cm(aiohttp.ClientSession())
        async with session_cm as session:
            request_cm = await _resolve_async_cm(session.get(url, timeout=aiohttp.ClientTimeout(total=15)))
            async with request_cm as response:
                if response.status != 200:
                    return {
                        "status": "error",
                        "error_message": f"無法獲取 {city} 的天氣資訊",
                    }

                data = await _safe_json(response)
                if not data:
                    return {
                        "status": "error",
                        "error_message": f"{city} 的天氣資料格式不正確",
                    }

                return _format_current_weather(data, city)
    except Exception as exc:  # pragma: no cover - 安全保護
        logger.error("查詢天氣時發生錯誤: %s", exc)
        return {
            "status": "error",
            "error_message": f"查詢天氣時發生錯誤：{str(exc)}",
        }


async def get_weather_forecast(city: str, days: str) -> Dict[str, Any]:
    city = _normalize_city(city)
    days = (days or "").strip() or _DEFAULT_FORECAST_DAYS
    url = f"https://wttr.in/{city}?format=j1"

    try:
        session_cm = await _resolve_async_cm(aiohttp.ClientSession())
        async with session_cm as session:
            request_cm = await _resolve_async_cm(session.get(url, timeout=aiohttp.ClientTimeout(total=15)))
            async with request_cm as response:
                if response.status != 200:
                    return {
                        "status": "error",
                        "error_message": f"無法獲取 {city} 的天氣預報",
                    }

                data = await _safe_json(response)
                if not data:
                    return {
                        "status": "error",
                        "error_message": f"{city} 的天氣預報資料格式不正確",
                    }

                return _format_forecast(data, days, city)
    except Exception as exc:  # pragma: no cover - 安全保護
        logger.error("查詢天氣預報時發生錯誤: %s", exc)
        return {
            "status": "error",
            "error_message": f"查詢天氣預報時發生錯誤：{str(exc)}",
        }


__all__ = ["get_weather", "get_weather_forecast"]
