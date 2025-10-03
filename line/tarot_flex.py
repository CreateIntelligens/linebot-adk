"""
塔羅牌 Flex Message 模板
用於以視覺化方式呈現塔羅牌占卜結果
"""

from typing import Dict, Any, List


def create_tarot_carousel_message(cards: List[Dict[str, Any]], interpretation: str, question: str) -> dict:
    """
    創建塔羅牌占卜結果的 Carousel Flex Message (三頁,每張牌一頁)

    Args:
        cards: 三張牌的資訊列表,每張牌包含 name, orientation, image_url, description, orientation_hint
        interpretation: 占卜師的專業解讀
        question: 占卜的問題

    Returns:
        dict: LINE Flex Carousel 格式的字典
    """
    bubbles = []

    # 為每張牌創建一個 bubble
    for idx, card in enumerate(cards):
        # 建立圖片 URL (確保是完整 URL)
        image_url = card.get("image_url", "")
        if image_url.startswith("/"):
            image_url = f"https://adkline.147.5gao.ai{image_url}"
        if not image_url:
            image_url = "https://adkline.147.5gao.ai/asset/aikka.png"

        position = card.get("position", "")
        name = card.get("name", "Unknown")
        orientation = card.get("orientation", "正位")
        description = card.get("description", "")
        orientation_hint = card.get("orientation_hint", "")

        # 截斷過長的描述
        if len(description) > 300:
            description = description[:297] + "..."

        # 截斷過長的描述（顯示簡短版本）
        short_description = description[:150] + "..." if len(description) > 150 else description

        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{name}",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#FFFFFF",
                        "wrap": True,
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"{position} | {orientation}",
                        "size": "md",
                        "color": "#FFFFFFCC",
                        "margin": "sm",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#279BB0",
                "paddingAll": "16px"
            },
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "3:4",
                "aspectMode": "cover"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "查看詳細說明",
                            "data": f"action=tarot_detail&card_index={idx}&name={name}&position={position}"
                        },
                        "style": "primary",
                        "color": "#9C27B0"
                    }
                ],
                "paddingAll": "16px"
            }
        }

        bubbles.append(bubble)

    # 創建 Carousel
    carousel = {
        "type": "carousel",
        "contents": bubbles
    }

    # 儲存 interpretation 供後續使用
    create_tarot_carousel_message._last_interpretation = interpretation

    return carousel


def create_card_detail_message(cards: List[Dict[str, Any]]) -> str:
    """
    創建牌卡詳細說明的文字訊息

    Args:
        cards: 三張牌的資訊列表

    Returns:
        str: 詳細說明文字
    """
    details = ["📖 牌卡詳細說明\n"]

    for idx, card in enumerate(cards, 1):
        details.append(f"{'='*30}")
        details.append(f"🔸 {card.get('position', '')}：{card.get('name', '')}（{card.get('orientation', '')}）\n")
        details.append(f"牌面描述：")
        details.append(f"{card.get('description', '')}\n")
        details.append(f"正逆位提示：")
        details.append(f"{card.get('orientation_hint', '')}\n")

    return "\n".join(details)
