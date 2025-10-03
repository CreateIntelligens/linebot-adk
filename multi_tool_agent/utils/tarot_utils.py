"""
塔羅牌工具模組

提供塔羅牌資料載入、圖片路徑處理等工具函數。
參考 https://github.com/krates98/tarotcardapi 的資料結構。
"""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_tarot_data_path() -> Path:
    """
    取得塔羅牌資料檔案路徑

    Returns:
        Path: tarot_cards.json 的完整路徑

    Raises:
        FileNotFoundError: 如果找不到資料檔案
    """
    # 先嘗試 multi_tool_agent/data/tarot_cards.json
    data_path = Path(__file__).resolve().parent.parent / "data" / "tarot_cards.json"
    if data_path.exists():
        return data_path

    # 如果不存在,嘗試專案根目錄的 data/tarot_cards.json
    root_data_path = Path(__file__).resolve().parent.parent.parent / "data" / "tarot_cards.json"
    if root_data_path.exists():
        return root_data_path

    raise FileNotFoundError(f"找不到塔羅牌資料檔案。已嘗試：{data_path}, {root_data_path}")


@lru_cache(maxsize=1)
def load_tarot_cards() -> List[Dict[str, Any]]:
    """
    載入所有塔羅牌資料（帶快取）

    Returns:
        List[Dict[str, Any]]: 塔羅牌資料列表

    Raises:
        FileNotFoundError: 找不到資料檔案
        ValueError: 資料格式錯誤
    """
    data_path = get_tarot_data_path()

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("塔羅牌資料格式錯誤，應為 JSON 陣列")

    if len(data) < 3:
        raise ValueError(f"塔羅牌資料不足，至少需要 3 張牌，目前只有 {len(data)} 張")

    return data


def resolve_image_directory() -> Optional[Path]:
    """
    解析塔羅牌圖片目錄

    優先順序：
    1. TAROT_IMAGE_DIR 環境變數
    2. 專案根目錄的 tarotdeck/
    3. asset/tarotdeck/

    Returns:
        Optional[Path]: 圖片目錄路徑，找不到則返回 None
    """
    # 1. 環境變數指定的目錄
    env_dir = os.getenv("TAROT_IMAGE_DIR", "").strip()
    if env_dir:
        path = Path(env_dir)
        if path.exists() and path.is_dir():
            logger.info(f"使用環境變數指定的塔羅牌圖片目錄：{path}")
            return path

    # 2. 預設目錄候選清單
    candidates = [
        Path("tarotdeck"),
        Path("asset") / "tarotdeck",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            logger.info(f"使用預設塔羅牌圖片目錄：{candidate}")
            return candidate

    logger.warning("⚠️ 找不到塔羅牌圖片目錄，請確認 TAROT_IMAGE_DIR 環境變數或檔案結構")
    return None


def get_image_base_url() -> Optional[str]:
    """
    取得塔羅牌圖片的基礎 URL（用於外部存取）

    Returns:
        Optional[str]: 基礎 URL，未設定則返回 None
    """
    base_url = os.getenv("TAROT_IMAGE_BASE_URL", "https://adkline.147.5gao.ai").strip()
    if base_url:
        return base_url.rstrip("/")
    return None


def build_image_url(image_path: str, base_url: Optional[str] = None) -> str:
    """
    建立塔羅牌圖片的完整 URL

    Args:
        image_path: 圖片相對路徑（如 "/tarotdeck/thefool.jpeg"）
        base_url: 可選的基礎 URL，未提供則使用環境變數

    Returns:
        str: 完整的圖片 URL
    """
    if not base_url:
        base_url = get_image_base_url()

    if base_url:
        # 移除開頭的斜線，避免重複
        clean_path = image_path.lstrip("/")
        return f"{base_url}/{clean_path}"

    # 沒有基礎 URL 時，返回原始路徑
    return image_path


def normalize_image_path(image_path: str) -> str:
    """
    正規化圖片路徑（移除 /tarotdeck/ 前綴用於本地檔案系統）

    Args:
        image_path: 原始圖片路徑

    Returns:
        str: 正規化後的路徑
    """
    # 移除開頭的斜線
    path = image_path.lstrip("/")

    # 移除 tarotdeck/ 前綴（如果存在）
    if path.startswith("tarotdeck/"):
        path = path[len("tarotdeck/"):]

    return path


def enrich_card_with_image_url(
    card: Dict[str, Any],
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    為塔羅牌資料加上完整的圖片 URL

    Args:
        card: 塔羅牌資料字典
        base_url: 可選的基礎 URL

    Returns:
        Dict[str, Any]: 加上 image_url 欄位的塔羅牌資料
    """
    card_copy = dict(card)
    image_path = card_copy.get("image", "")

    if image_path:
        card_copy["image_url"] = build_image_url(image_path, base_url)

    return card_copy


def validate_tarot_card(card: Dict[str, Any]) -> bool:
    """
    驗證塔羅牌資料結構是否正確

    Args:
        card: 塔羅牌資料字典

    Returns:
        bool: 資料是否有效
    """
    required_fields = ["name", "description"]
    return all(field in card for field in required_fields)
