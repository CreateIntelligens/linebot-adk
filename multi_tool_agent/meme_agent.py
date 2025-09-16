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


async def generate_meme(meme_idea: str, user_id: str) -> dict:
    """
    生成 meme 圖片

    根據用戶的想法，使用 AI 生成合適的 meme 文字，然後調用 ImgFlip API 創建 meme。

    Args:
        meme_idea (str): 用戶的 meme 想法或描述
        user_id (str): 用戶 ID

    Returns:
        dict: 包含以下鍵的字典
            - status (str): "success" 或 "error"
            - meme_url (str): 生成的 meme 圖片 URL（僅在成功時存在）
            - report (str): 成功時的報告文字（僅在成功時存在）
            - error_message (str): 錯誤時的錯誤訊息（僅在錯誤時存在）

    Example:
        >>> result = await generate_meme("老闆說要加班但薪水沒有增加", "user123")
        >>> print(result["meme_url"])
        https://i.imgflip.com/abc123.jpg
    """
    try:
        # 檢查 Google API 金鑰
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return {
                "status": "error",
                "error_message": "抱歉，meme 生成服務暫時無法使用。"
            }

        print(f"[Meme Generator] 開始處理: {meme_idea}")

        # 第一步：使用 AI 分析 meme 想法並生成文字
        meme_texts = await generate_meme_text(meme_idea, google_api_key)
        if not meme_texts:
            return {
                "status": "error",
                "error_message": "無法生成合適的 meme 文字，請嘗試其他想法。"
            }

        # 第二步：選擇合適的 meme 模板
        template_id = await select_meme_template(meme_idea, google_api_key)
        if not template_id:
            # 使用預設的熱門模板
            template_id = "61579"  # One Does Not Simply

        print(f"[Meme Generator] 使用模板 ID: {template_id}")
        print(f"[Meme Generator] 上文字: {meme_texts.get('top', '')}")
        print(f"[Meme Generator] 下文字: {meme_texts.get('bottom', '')}")

        # 第三步：使用 ImgFlip API 生成 meme
        meme_url = await create_meme_imgflip(
            template_id=template_id,
            top_text=meme_texts.get("top", ""),
            bottom_text=meme_texts.get("bottom", "")
        )

        if meme_url:
            return {
                "status": "success",
                "meme_url": meme_url,
                "report": f"🎭 Meme 已生成！\n主題：{meme_idea}\n\n{meme_url}"
            }
        else:
            return {
                "status": "error",
                "error_message": "Meme 生成失敗，請稍後再試。"
            }

    except Exception as e:
        print(f"[Meme Generator] 錯誤: {str(e)}")
        return {
            "status": "error",
            "error_message": "Meme 生成服務發生錯誤，請稍後再試。"
        }


async def generate_meme_text(meme_idea: str, api_key: str) -> Optional[dict]:
    """
    使用 Google Gemini AI 生成 meme 的上下文字

    根據用戶提供的 meme 想法，使用 AI 生成適合的上下文字內容，
    以便後續用於 meme 圖片創作。

    Args:
        meme_idea (str): 用戶的 meme 想法或主題描述
        api_key (str): Google Gemini API 金鑰

    Returns:
        Optional[dict]: 包含以下鍵的字典，失敗時返回 None
            - top (str): 上方文字內容
            - bottom (str): 下方文字內容

    Raises:
        aiohttp.ClientError: 網路連線錯誤
        asyncio.TimeoutError: API 請求超時
        json.JSONDecodeError: API 回應解析錯誤

    Example:
        >>> result = await generate_meme_text("老闆說要加班但薪水沒有增加", "api_key")
        >>> print(result)
        {'top': 'WHEN BOSS SAYS OVERTIME', 'bottom': 'BUT SALARY STAYS THE SAME'}

    Note:
        生成的文字為英文格式，以符合 ImgFlip API 的要求。
        如果 AI 無法生成適當內容，函數會返回 None。
        使用較高的 temperature 值以增加創意性。
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

        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
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


async def select_meme_template(meme_idea: str, api_key: str) -> Optional[str]:
    """
    根據 meme 想法智能選擇最適合的模板 ID

    使用 Google Gemini AI 分析用戶的 meme 想法，根據內容主題自動選擇最合適的 meme 模板，
    以確保生成的 meme 具有最佳的視覺效果和諷刺效果。

    Args:
        meme_idea (str): 用戶的 meme 想法或主題描述
        api_key (str): Google Gemini API 金鑰

    Returns:
        Optional[str]: ImgFlip 模板 ID 字串，選擇失敗時返回預設模板 ID

    Raises:
        aiohttp.ClientError: 網路連線錯誤
        asyncio.TimeoutError: API 請求超時
        json.JSONDecodeError: API 回應解析錯誤

    Example:
        >>> template_id = await select_meme_template("老闆說要加班但薪水沒有增加", "api_key")
        >>> print(template_id)
        181913649

    Note:
        內建多種熱門 meme 模板供選擇。
        如果 AI 選擇失敗，會自動返回預設的 "One Does Not Simply" 模板。
        使用較低的 temperature 值以確保選擇的穩定性。
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

        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
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


async def create_meme_imgflip(template_id: str, top_text: str, bottom_text: str) -> Optional[str]:
    """
    使用 ImgFlip API 創建和上傳 meme 圖片

    將生成的 meme 文字應用到指定的模板上，通過 ImgFlip API 創建最終的 meme 圖片，
    並返回生成的圖片 URL 以供後續使用。

    Args:
        template_id (str): ImgFlip 模板 ID
        top_text (str): 上方文字內容
        bottom_text (str): 下方文字內容

    Returns:
        Optional[str]: 生成的 meme 圖片 URL，失敗時返回 None

    Raises:
        aiohttp.ClientError: 網路連線錯誤
        asyncio.TimeoutError: API 請求超時

    Example:
        >>> url = await create_meme_imgflip("61579", "TOP TEXT", "BOTTOM TEXT")
        >>> print(url)
        https://i.imgflip.com/abc123.jpg

    Note:
        需要設定 IMGFLIP_USERNAME 和 IMGFLIP_PASSWORD 環境變數。
        生成的圖片會自動上傳到 ImgFlip 伺服器並返回公開 URL。
        如果 API 呼叫失敗，會記錄錯誤訊息但不拋出異常。
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

        async with aiohttp.ClientSession() as session:
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


# 備用 meme 生成（如果主要服務失敗）
async def fallback_meme_generator(meme_idea: str, user_id: str) -> dict:
    """
    備用 meme 生成器 - 提供創作建議而不是實際生成圖片

    當主要 meme 生成服務無法使用時，提供實用的 meme 創作建議和模板推薦，
    引導用戶使用外部工具手動創作 meme。

    Args:
        meme_idea (str): 用戶的 meme 想法或主題描述
        user_id (str): 用戶 ID，用於日誌記錄

    Returns:
        dict: 包含以下鍵的字典
            - status (str): 始終為 "success"
            - report (str): 包含創作建議和外部連結的回應文字

    Example:
        >>> result = await fallback_meme_generator("老闆說要加班但薪水沒有增加", "user123")
        >>> print(result["report"])
        💡 Meme 創作建議：
        主題：老闆說要加班但薪水沒有增加
        🎭 可以試試 Drake 模板：上面寫不想要的，下面寫想要的
        你可以到 https://imgflip.com/memetemplates 手動創作！

    Note:
        此為備用服務，不依賴外部 API，始終可用。
        隨機從預設建議列表中選擇一個建議。
        建議用戶使用外部 meme 創作工具。
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
