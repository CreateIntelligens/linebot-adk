# =============================================================================
# Meme Generator Agent
# 改寫自 awesome-llm-apps 的 meme generator，適用於 LINE Bot
# 使用 ImgFlip API 替代瀏覽器自動化
# =============================================================================

import os
import aiohttp
import asyncio
import re
from typing import Optional


class MemeAgent:
    """
    Meme 生成 Agent

    根據用戶的想法，使用 AI 生成合適的 meme 文字，然後調用 ImgFlip API 創建 meme。
    """

    def __init__(self, name: str = "meme", description: str = "根據使用者的想法生成有趣的 meme 圖片，支援多種熱門模板"):
        self.name = name
        self.description = description

    async def execute(self, meme_idea: str, user_id: str) -> dict:
        """
        生成 meme 圖片

        Args:
            meme_idea (str): 用戶的 meme 想法或描述
            user_id (str): 用戶 ID

        Returns:
            dict: meme 生成結果字典
                - status: "success" 或 "error"
                - report: 成功時的報告訊息
                - error_message: 錯誤時的錯誤訊息
                - data: 額外資料 (成功時)
        """
        try:
            # 檢查必要參數
            if not meme_idea or not user_id:
                return {
                    "status": "error",
                    "error_message": "缺少必要參數：meme_idea 或 user_id"
                }

            # 檢查 Google API 金鑰
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                return await self._fallback_meme_generator(meme_idea, user_id)

            print(f"[Meme Generator] 開始處理: {meme_idea}")

            # 第一步：使用 AI 分析 meme 想法並生成文字
            meme_texts = await self._generate_meme_text(meme_idea, google_api_key)
            if not meme_texts:
                return await self._fallback_meme_generator(meme_idea, user_id)

            # 第二步：選擇合適的 meme 模板
            template_id = await self._select_meme_template(meme_idea, google_api_key)
            if not template_id:
                # 使用預設的熱門模板
                template_id = "61579"  # One Does Not Simply

            print(f"[Meme Generator] 使用模板 ID: {template_id}")
            print(f"[Meme Generator] 上文字: {meme_texts.get('top', '')}")
            print(f"[Meme Generator] 下文字: {meme_texts.get('bottom', '')}")

            # 第三步：使用 ImgFlip API 生成 meme
            meme_url = await self._create_meme_imgflip(
                template_id=template_id,
                top_text=meme_texts.get("top", ""),
                bottom_text=meme_texts.get("bottom", "")
            )

            if meme_url:
                return {
                    "status": "success",
                    "report": f"🎭 Meme 已生成！\n主題：{meme_idea}\n\n{meme_url}",
                    "data": {"meme_url": meme_url}
                }
            else:
                return await self._fallback_meme_generator(meme_idea, user_id)

        except Exception as e:
            print(f"[Meme Generator] 錯誤: {str(e)}")
            return await self._fallback_meme_generator(meme_idea, user_id)

    async def _generate_meme_text(self, meme_idea: str, api_key: str) -> Optional[dict]:
        """
        使用 Google Gemini AI 生成 meme 的上下文字
        """
        try:
            prompt = f"""You are a professional meme creator. Create a funny meme based on this idea:

Idea: {meme_idea}

Generate:
1. Top Text - Setup or context
2. Bottom Text - Punchline or conclusion

Requirements:
- English only (for compatibility)
- Short and punchy
- Follows meme culture
- Funny and relatable

Format your response as:
Top Text: [your text]
Bottom Text: [your text]"""

            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }

            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.8,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024
                }
            }

            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.post(
                    api_url,
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        if "candidates" in result and result["candidates"]:
                            content = result["candidates"][0]["content"]["parts"][0]["text"]

                            # 解析生成的文字
                            top_match = re.search(r'Top Text:\s*(.+)', content, re.IGNORECASE)
                            bottom_match = re.search(r'Bottom Text:\s*(.+)', content, re.IGNORECASE)

                            if top_match and bottom_match:
                                return {
                                    "top": top_match.group(1).strip(),
                                    "bottom": bottom_match.group(1).strip()
                                }
                            else:
                                # 如果格式不對，嘗試按行分割
                                lines = [line.strip() for line in content.split('\n') if line.strip()]
                                if len(lines) >= 2:
                                    return {
                                        "top": lines[0],
                                        "bottom": lines[1]
                                    }

        except Exception as e:
            print(f"[Meme Text Generation] 錯誤: {str(e)}")

        return None

    async def _select_meme_template(self, meme_idea: str, api_key: str) -> Optional[str]:
        """
        根據 meme 想法智能選擇最適合的模板 ID
        """
        # 熱門 meme 模板 ID (ImgFlip)
        popular_templates = {
            "drake": "181913649",          # Drake Pointing
            "distracted_boyfriend": "112126428",  # Distracted Boyfriend
            "woman_yelling_at_cat": "188390779",  # Woman Yelling At Cat
            "two_buttons": "87743020",      # Two Buttons
            "one_does_not_simply": "61579", # One Does Not Simply
            "most_interesting": "61532",    # The Most Interesting Man
            "success_kid": "61544",         # Success Kid
            "disaster_girl": "97984",       # Disaster Girl
            "hide_the_pain": "27813981",    # Hide the Pain Harold
            "expanding_brain": "93895088",   # Expanding Brain
        }

        try:
            # 使用 AI 選擇最合適的模板
            prompt = f"""根據這個 meme 想法，選擇最合適的模板：

想法：{meme_idea}

可選模板：
- drake: 適合「喜歡/不喜歡」「選擇」主題
- distracted_boyfriend: 適合「分心」「誘惑」主題
- woman_yelling_at_cat: 適合「爭論」「抗議」主題
- two_buttons: 適合「困難選擇」「兩難」主題
- one_does_not_simply: 適合「這不容易」「不可能」主題
- most_interesting: 適合「我很少...但是」主題
- success_kid: 適合「成功」「勝利」主題
- disaster_girl: 適合「破壞」「災難」主題
- hide_the_pain: 適合「假裝沒事」「痛苦微笑」主題
- expanding_brain: 適合「層層遞進」「越來越聰明」主題

請只回答模板名稱，例如：drake"""

            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }

            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 20,
                    "topP": 0.8,
                    "maxOutputTokens": 50
                }
            }

            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=15)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.post(
                    api_url,
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        if "candidates" in result and result["candidates"]:
                            content = result["candidates"][0]["content"]["parts"][0]["text"].strip().lower()

                            # 尋找匹配的模板
                            for template_name, template_id in popular_templates.items():
                                if template_name in content:
                                    return template_id

        except Exception as e:
            print(f"[Template Selection] 錯誤: {str(e)}")

        # 如果選擇失敗，返回預設模板
        return popular_templates["one_does_not_simply"]

    async def _create_meme_imgflip(self, template_id: str, top_text: str, bottom_text: str) -> Optional[str]:
        """
        使用 ImgFlip API 創建和上傳 meme 圖片
        """
        try:
            # ImgFlip API 端點
            api_url = "https://api.imgflip.com/caption_image"

            # 使用環境變數中的帳號
            username = os.getenv("IMGFLIP_USERNAME")
            password = os.getenv("IMGFLIP_PASSWORD")

            if not username or not password:
                print("[ImgFlip] 缺少帳號密碼環境變數")
                return None

            data = {
                "template_id": template_id,
                "username": username,
                "password": password,
                "text0": top_text,
                "text1": bottom_text
            }

            connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(api_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()

                        if result.get("success"):
                            return result["data"]["url"]
                        else:
                            print(f"[ImgFlip] API 錯誤: {result.get('error_message', 'Unknown error')}")
                    else:
                        print(f"[ImgFlip] HTTP 錯誤: {response.status}")

        except Exception as e:
            print(f"[ImgFlip API] 錯誤: {str(e)}")

        return None

    async def _fallback_meme_generator(self, meme_idea: str, user_id: str):
        """
        備用 meme 生成器 - 提供創作建議而不是實際生成圖片
        """
        suggestions = [
            "🎭 可以試試 Drake 模板：上面寫不想要的，下面寫想要的",
            "🤔 試試兩個按鈕模板：寫出兩個困難的選擇",
            "😏 用「我很少...但當我...時」的模板",
            "🧠 用層層遞進的大腦模板展示想法升級",
            "😂 用分心男友模板：忠誠 vs 誘惑"
        ]

        import random
        suggestion = random.choice(suggestions)

        return {
            "status": "success",
            "report": f"💡 Meme 創作建議：\n\n主題：{meme_idea}\n\n{suggestion}\n\n你可以到 https://imgflip.com/memetemplates 手動創作！"
        }
