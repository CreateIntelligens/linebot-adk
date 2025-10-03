"""
塔羅牌占卜 Agent

提供三張塔羅牌占卜（過去、現在、未來）。
使用本地塔羅牌資料，透過 Gemini 翻譯成繁體中文並提供專業解讀。
"""

import logging
import os
import random
from typing import Any, Dict, List

from google import genai
from google.genai import types

from ..utils.tarot_utils import load_tarot_cards, build_image_url

logger = logging.getLogger(__name__)


class TarotAgent:
    """塔羅牌占卜代理程式"""

    def __init__(self):
        """初始化塔羅牌 Agent"""
        # 初始化 Gemini 客戶端
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY 環境變數未設定")

        self.client = genai.Client(api_key=self.api_key)

        # 載入塔羅牌資料
        try:
            self.cards = load_tarot_cards()
            logger.info(f"成功載入 {len(self.cards)} 張塔羅牌資料")
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"載入塔羅牌資料失敗: {e}")
            raise

    async def _translate_to_traditional_chinese(self, text: str) -> str:
        """
        使用 Gemini 將英文翻譯成繁體中文

        Args:
            text: 要翻譯的英文文字

        Returns:
            str: 繁體中文翻譯結果
        """
        try:
            prompt = f"""請將以下文字翻譯成繁體中文，保持原有的格式和段落：

{text}

翻譯要求：
1. 使用台灣常用的繁體中文用語
2. 保持原文的語氣和風格
3. 塔羅牌名稱可以保留英文或翻譯，以易懂為主
4. 只輸出翻譯結果，不要加上任何前綴或後綴"""

            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2000,
                )
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"翻譯時發生錯誤: {e}")
            return text  # 翻譯失敗時返回原文

    async def _generate_interpretation(
        self,
        question: str,
        cards_info: List[Dict[str, Any]]
    ) -> str:
        """
        使用 Gemini 生成塔羅牌解讀

        Args:
            question: 使用者的問題
            cards_info: 抽到的三張牌資訊

        Returns:
            str: 專業的塔羅牌解讀
        """
        try:
            # 組合三張牌的詳細資訊
            cards_detail = "\n".join([
                f"{i+1}. {info['position']}：{info['name']}（{info['orientation']}）\n"
                f"   牌面描述：{info['description']}\n"
                f"   正逆位提示：{info['orientation_hint']}"
                for i, info in enumerate(cards_info)
            ])

            prompt = f"""你是一位專業的塔羅牌占卜師。使用者問了以下問題：

問題：{question}

抽到的三張牌：
{cards_detail}

請提供一段溫暖、專業且具有洞察力的解讀（約150-200字），幫助使用者理解這些牌卡對他們問題的啟示。

解讀應該：
1. 結合三張牌的意義和位置（過去-現在-未來）
2. 針對使用者的問題提供具體建議
3. 語氣友善、正面且鼓勵
4. 使用繁體中文
5. 不要重複牌義，而是提供更深層的洞察"""

            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                )
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"生成解讀時發生錯誤: {e}")
            return "抱歉，無法生成解讀。"

    def _draw_three_cards(self) -> List[Dict[str, Any]]:
        """
        隨機抽取三張塔羅牌

        Returns:
            List[Dict[str, Any]]: 三張牌的資訊（過去、現在、未來）
        """
        # 隨機抽取三張不重複的牌
        sampled_cards = random.sample(self.cards, 3)
        position_names = ["過去", "現在", "未來"]

        cards_info = []

        for index, card in enumerate(sampled_cards):
            # 隨機決定正位或逆位
            is_upright = random.random() > 0.5
            orientation = "正位" if is_upright else "逆位"

            # 正逆位提示
            orientation_hint = (
                "正位能量：聚焦在這張牌帶來的支持與擴展。"
                if is_upright
                else "逆位能量：留意此牌揭示的阻礙、延遲或需要內在調整的課題。"
            )

            # 建立圖片 URL
            image_path = card.get("image", "")
            image_url = build_image_url(image_path) if image_path else ""

            # 優先使用中文翻譯,若無則使用英文原文
            description = card.get("description_zh", card.get("description", "")).strip()

            # 正逆位提示的中文版本
            orientation_hint_zh = (
                "正位能量：聚焦在這張牌帶來的支持與擴展。"
                if is_upright
                else "逆位能量：留意此牌揭示的阻礙、延遲或需要內在調整的課題。"
            )

            card_info = {
                "position": position_names[index],
                "name": card.get("name", "Unknown"),
                "orientation": orientation,
                "description": description,
                "orientation_hint": orientation_hint_zh,
                "image_path": image_path,
                "image_url": image_url,
            }

            cards_info.append(card_info)

        return cards_info

    async def execute(
        self,
        question: str,
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        執行三張塔羅牌占卜

        Args:
            question: 塔羅牌占卜的問題
            user_id: 使用者 ID

        Returns:
            Dict[str, Any]: 包含占卜結果的字典
                - status: "success" 或 "error"
                - report: 完整的占卜結果（包含翻譯和解讀）
                - cards: 三張牌的詳細資訊
                - images: 圖片 URL 列表（如果有）
                - error_message: 錯誤訊息（僅在失敗時）
        """
        logger.info(f"用戶 {user_id} 請求塔羅牌占卜，問題：{question}")

        try:
            # 1. 抽取三張牌
            cards_info = self._draw_three_cards()

            # 2. 組合英文版占卜結果（用於翻譯）
            english_sections = []
            for info in cards_info:
                orientation_hint_en = (
                    "Focus on the supportive qualities and forward momentum of the card."
                    if info["orientation"] == "正位"
                    else "Reflect on the lessons, delays, or inner work highlighted by the reversal."
                )

                block = [
                    f"📍 {info['position']}: {info['name']} ({info['orientation']})",
                    f"Description: {info['description']}",
                    f"Orientation Hint: {orientation_hint_en}",
                ]

                if info["image_url"]:
                    block.append(f"Image URL: {info['image_url']}")

                english_sections.append("\n".join(block))

            english_reading = (
                "🔮 Three-Card Tarot Reading 🔮\n\n"
                f"Question: {question}\n\n"
                + "\n\n".join(english_sections)
            )

            # 3. 翻譯成繁體中文（僅翻譯整體閱讀）
            chinese_reading = await self._translate_to_traditional_chinese(english_reading)

            # 4. 生成專業解讀
            interpretation = await self._generate_interpretation(question, cards_info)

            # 5. 組合最終回應
            cards_summary = "\n".join([
                f"🔸 {info['position']}｜{info['name']}（{info['orientation']}）\n"
                f"   {info['orientation_hint']}"
                for info in cards_info
            ])

            image_section = "\n".join([
                f"🔸 {info['position']}｜{info['name']}：{info['image_url']}"
                for info in cards_info
                if info.get("image_url")
            ])

            final_parts = [
                chinese_reading,
                f"💫 占卜師解讀：\n{interpretation}",
                f"📌 牌卡重點：\n{cards_summary}",
            ]

            if image_section:
                final_parts.append(f"🖼️ 牌卡圖片：\n{image_section}")

            final_reading = "\n\n".join(final_parts)

            # 6. 建立回應物件
            response = {
                "status": "success",
                "report": final_reading,
                "cards": cards_info,
            }

            # 加入圖片 URL（如果有）
            image_urls = [
                info["image_url"]
                for info in cards_info
                if info.get("image_url")
            ]
            if image_urls:
                response["images"] = image_urls

            logger.info(f"塔羅牌占卜成功：用戶 {user_id}")
            return response

        except Exception as e:
            logger.error(f"塔羅牌占卜時發生錯誤: {e}", exc_info=True)
            return {
                "status": "error",
                "error_message": f"塔羅牌占卜時發生錯誤：{str(e)}"
            }
