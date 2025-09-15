# =============================================================================
# 法律諮詢 Agent
# 提供多專業角色的法律諮詢服務
# =============================================================================

import os
import aiohttp
import asyncio


def classify_legal_question(question: str) -> str:
    """分類法律問題類型"""
    # 契約相關關鍵詞
    contract_keywords = ["合約", "契約", "合同", "協議", "條款", "簽約", "違約", "履約", "保證金", "定金"]
    if any(keyword in question for keyword in contract_keywords):
        return "contract"

    # 糾紛相關關鍵詞
    dispute_keywords = ["糾紛", "爭議", "訴訟", "法院", "告", "賠償", "和解", "調解", "仲裁", "上訴"]
    if any(keyword in question for keyword in dispute_keywords):
        return "dispute"

    # 法律研究相關關鍵詞
    research_keywords = ["法條", "法規", "條文", "什麼是", "如何定義", "法律規定", "憲法", "民法", "刑法"]
    if any(keyword in question for keyword in research_keywords):
        return "research"

    # 企業法務相關
    business_keywords = ["公司法", "勞基法", "營業", "稅務", "智慧財產", "專利", "商標", "著作權"]
    if any(keyword in question for keyword in business_keywords):
        return "business"

    return "general"


async def legal_ai(question: str, user_id: str) -> dict:
    """
    法律諮詢 AI 服務
    """
    try:
        # 檢查 API 金鑰
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return {
                "status": "error",
                "error_message": "抱歉，法律諮詢服務暫時無法使用，請稍後再試。"
            }

        # 分析問題類型
        analysis_type = classify_legal_question(question)

        # 根據問題類型設定專業提示
        specialist_prompts = {
            "contract": {
                "emoji": "📑",
                "role": "契約分析師",
                "prompt": f"""你是專業的契約分析師。請針對以下契約相關問題提供專業建議：

問題：{question}

請提供：
1. 🔍 關鍵條款分析
2. ⚠️ 潛在風險評估
3. 💡 具體建議措施
4. 📋 相關法條依據

請用繁體中文回應，內容要實用且易懂。"""
            },

            "dispute": {
                "emoji": "⚖️",
                "role": "法律策略師",
                "prompt": f"""你是經驗豐富的法律策略師。請針對以下糾紛問題提供戰略建議：

問題：{question}

請提供：
1. 🎯 爭議核心分析
2. 📊 法律依據評估
3. 🤝 解決策略建議
4. ⏱️ 處理時程規劃

請用繁體中文回應，提供實際可行的建議。"""
            },

            "research": {
                "emoji": "🔍",
                "role": "法律研究員",
                "prompt": f"""你是專業的法律研究員。請針對以下法律問題提供深度解析：

問題：{question}

請提供：
1. 📚 相關法條解釋
2. 🏛️ 立法背景說明
3. 📖 實務案例參考
4. 📈 最新法規動態

請用繁體中文回應，引用具體法條和案例。"""
            },

            "business": {
                "emoji": "🏢",
                "role": "企業法務顧問",
                "prompt": f"""你是企業法務顧問。請針對以下企業營運法律問題提供建議：

問題：{question}

請提供：
1. 🏗️ 法規要求分析
2. 📊 合規風險評估
3. 🛡️ 預防措施建議
4. 📋 內控制度要點

請用繁體中文回應，提供實務可行的建議。"""
            },

            "general": {
                "emoji": "🏛️",
                "role": "法律顧問",
                "prompt": f"""你是專業的法律顧問。請針對以下法律問題提供綜合建議：

問題：{question}

請提供：
1. ⚖️ 問題核心分析
2. 📖 適用法規說明
3. 💡 實務處理建議
4. 🚨 注意事項提醒

請用繁體中文回應，提供專業但易懂的法律建議。"""
            }
        }

        config = specialist_prompts.get(analysis_type, specialist_prompts["general"])

        # 使用 Google Gemini API
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": google_api_key
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": config["prompt"]
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048
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

                        return {
                            "status": "success",
                            "report": f"{config['emoji']} **{config['role']}** 專業分析：\n\n{content}"
                        }
                    else:
                        return {
                            "status": "error",
                            "error_message": "抱歉，無法獲取法律諮詢回應。"
                        }
                else:
                    error_text = await response.text()
                    print(f"[法律諮詢] API 錯誤 {response.status}: {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"法律諮詢服務暫時忙碌中，請稍後再試。"
                    }

    except Exception as e:
        print(f"[法律諮詢] 錯誤: {str(e)}")
        return {
            "status": "error",
            "error_message": "抱歉，法律諮詢服務暫時發生問題，請稍後再試。"
        }


async def fallback_legal(question: str, user_id: str) -> dict:
    """
    備用簡化法律諮詢
    """
    basic_responses = {
        "contract": "📑 契約問題建議尋求專業律師協助，注意保留相關文件證據。",
        "dispute": "⚖️ 糾紛處理建議先嘗試協商，必要時可考慮調解或訴訟途徑。",
        "research": "🔍 法律條文查詢建議參考全國法規資料庫 https://law.moj.gov.tw",
        "business": "🏢 企業法務問題建議諮詢專業法務顧問或律師事務所。",
        "general": "🏛️ 一般法律問題建議諮詢當地法律扶助基金會或律師公會。"
    }

    analysis_type = classify_legal_question(question)
    response = basic_responses.get(analysis_type, basic_responses["general"])

    return {
        "status": "success",
        "report": f"🏛️ 法律助理回答：\n\n{response}\n\n⚠️ 以上為一般性建議，具體情況請諮詢專業律師。"
    }