# LINE Bot with Google ADK - 多功能智慧助手

基於 Google ADK (Agent Development Kit) 和 Gemini 2.0 Flash 模型的多功能 LINE 機器人，提供豐富的生活服務和娛樂功能。

## 🌟 主要功能

- **🌤️ 天氣查詢服務**
  - 全球即時天氣資訊 (powered by wttr.in)
  - 未來 1-3 天天氣預報
  - 智慧城市名稱辨識

- **🕐 時間查詢服務**
  - 全球各城市當前時間
  - 智慧時區偵測 (powered by worldtimeapi.org)
  - 預設台灣時區

- **🔗 短網址服務**
  - aiurl.tw 短網址生成
  - 自訂 slug 支援
  - 自動重複檢測

- **🧠 知識庫查詢**
  - **SET三立電視** - 節目、藝人、戲劇等相關資訊
  - **hihi導覽先生** - 公視台語節目資訊
  - FastGPT 整合的專業知識查詢
  - 上下文感知對話記憶

- **⚖️ 法律諮詢服務**
  - 專業法律問題解答
  - 合約條文分析
  - 法院程序指引

- **🎭 梗圖生成器**
  - AI 驅動的迷因圖片生成
  - 流行梗圖範本
  - 自訂文字內容

- **🎬 AI 影片生成**
  - ComfyUI 整合的 AI 影片生成
  - AI 代言人影片製作
  - 自動影片推送和下載

- **🎥 影片轉錄摘要**
  - YouTube 影片內容轉錄
  - 智慧摘要生成
  - 多語言支援

- **🌏 阿美族語學習**
  - 每日一字詞推薦
  - 原住民語言文化推廣

- **🔍 網路搜尋**
  - Google 搜尋整合
  - 即時資訊查詢
  - 智慧結果篩選

- **📋 任務狀態查詢**
  - 通用 ID 查詢系統
  - 並行任務監控
  - 自動結果推送

- **🤖 智慧對話**
  - 自然語言理解
  - 繁體中文回應
  - 情境感知工具選擇
  - 主動執行，減少確認步驟

## 🛠️ 技術架構

- **後端框架**: Python 3.10, FastAPI
- **AI 模型**: Google ADK, Gemini 2.0 Flash
- **訊息平台**: LINE Messaging API
- **影片生成**: ComfyUI, AnimateDiff
- **容器化**: Docker, Docker Compose
- **外部 API**:
  - wttr.in (天氣)
  - worldtimeapi.org (時間)
  - aiurl.tw (短網址)
  - FastGPT (知識庫)
  - Google Search API (搜尋)
  - YouTube API (影片轉錄)

## Quick Start with Docker Compose

### Prerequisites

1. LINE Bot Channel (Channel Secret & Access Token)
2. Google AI Studio API Key
3. FastGPT API Key and URL (optional, for knowledge base features)
4. Docker and Docker Compose installed

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/linebot-adk.git
   cd linebot-adk
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` file with your credentials:
   ```env
   # LINE Bot Configuration
   ChannelSecret=your_line_channel_secret
   ChannelAccessToken=your_line_channel_access_token

   # Google ADK Configuration
   GOOGLE_API_KEY=your_google_ai_studio_api_key

   # FastGPT Knowledge Base (Optional)
   FASTGPT_API_URL=your_fastgpt_api_url
   FASTGPT_API_KEY=your_fastgpt_api_key

   # ComfyUI Video Generation (Optional)
   COMFYUI_API_URL=http://your-comfyui-server:8188
   COMFYUI_TTS_API_URL=http://your-tts-server:8001/tts_url

   # Video Processing (Optional)
   VIDEO_API_BASE_URL=http://your-video-api-server

   # URL Shortening (Optional)
   AIURL_API_TOKEN=your_aiurl_token

   # Google Search (Optional)
   GOOGLE_CSE_ID=your_custom_search_engine_id
   GOOGLE_API_KEY_SEARCH=your_google_search_api_key
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Check the service**
   ```bash
   curl http://localhost:8892/docs  # View API documentation
   docker-compose logs -f linebot-adk  # View logs
   ```

### LINE Bot Configuration

1. Go to [LINE Developers Console](https://developers.line.biz/console/)
2. Select your bot channel
3. Set the Webhook URL to: `https://your-domain.com/` (note the trailing slash)
4. Enable "Use webhook" and disable "Auto-reply messages"

## 📱 使用範例

發送以下訊息給你的 LINE 機器人：

### 🌤️ 天氣查詢
- "台北天氣如何？"
- "東京明天會下雨嗎？"
- "高雄未來三天天氣預報"

### 🕐 時間查詢
- "現在幾點？"
- "紐約現在幾點？"
- "今天幾號？"

### 🔗 短網址
- 直接發送任何網址："https://github.com/example/repo"
- 自訂名稱："幫我縮短網址，名稱用 my-link"

### 🧠 知識庫查詢
**SET三立電視：**
- "三立在哪裡？"
- "三立有什麼節目？"
- "炮仔聲演員有誰？"

**hihi導覽先生：**
- "hihi先生是誰？"
- "節目內容是什麼？"
- "有多少集？"

### ⚖️ 法律諮詢
- "租房合約要注意什麼？"
- "交通事故該怎麼處理？"
- "勞動法規定加班費如何計算？"

### 🎭 梗圖生成
- "生成一個貓咪梗圖"
- "幫我做一個「我太難了」的圖"
- "隨便來個搞笑圖片"

### 🎬 AI 影片生成
- "幫我用影片回覆這個問題"
- "生成一段AI影片說明這件事"
- "做個影片介紹三立電視"

### 🎥 影片轉錄摘要
- 發送 YouTube 連結
- "幫我轉錄這個影片"
- "這個影片在講什麼？"

### 🌏 阿美族語學習
- "每日一字"
- "阿美族語學習"
- "今天教什麼字？"

### 🔍 網路搜尋
- "搜尋台灣最新新聞"
- "查詢 ChatGPT 最新功能"
- "找找看 Python 教學"

### 📋 任務查詢
- 直接發送任務 ID：`550e8400-e29b-41d4-a716-446655440000`
- "查詢任務狀態"
- "我的影片生成好了嗎？"

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ChannelSecret=your_channel_secret
export ChannelAccessToken=your_channel_access_token
export GOOGLE_API_KEY=your_google_api_key
export FASTGPT_API_URL=your_fastgpt_api_url  # Optional
export FASTGPT_API_KEY=your_fastgpt_api_key  # Optional

# Run the application
uvicorn main:app --host=0.0.0.0 --port=8892 --reload
```

### Testing

```bash
# Test the webhook endpoint
curl -X POST http://localhost:8892/ \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'

# View API documentation
open http://localhost:8892/docs
```

## Docker Commands

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f linebot-adk

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose down
docker-compose build
docker-compose up -d
```

## Configuration

### 🔧 環境變數設定

| 變數名稱 | 說明 | 必要性 | 預設值 |
|----------|------|--------|--------|
| `ChannelSecret` | LINE Channel Secret | ✅ 必要 | - |
| `ChannelAccessToken` | LINE Channel Access Token | ✅ 必要 | - |
| `GOOGLE_API_KEY` | Google AI Studio API Key | ✅ 必要 | - |
| `FASTGPT_API_URL` | FastGPT API 端點 URL | ❌ 選用 | - |
| `FASTGPT_API_KEY` | FastGPT API 認證金鑰 | ❌ 選用 | - |
| `COMFYUI_API_URL` | ComfyUI 服務器 URL | ❌ 選用 | http://localhost:8188 |
| `COMFYUI_TTS_API_URL` | TTS 服務器 URL | ❌ 選用 | - |
| `VIDEO_API_BASE_URL` | 影片處理 API 基礎 URL | ❌ 選用 | - |
| `AIURL_API_TOKEN` | aiurl.tw API Token | ❌ 選用 | - |
| `GOOGLE_CSE_ID` | Google 自訂搜尋引擎 ID | ❌ 選用 | - |
| `GOOGLE_API_KEY_SEARCH` | Google 搜尋 API Key | ❌ 選用 | - |

### Customizing Agent Behavior

Edit the `instruction` parameter in `main.py` to customize the agent's behavior:

```python
instruction=(
    "I am a specialized assistant providing four services: weather, time, URL shortening, and knowledge base queries.\n"
    "Respond concisely in Traditional Chinese without asking too many confirmation questions.\n"
    "For knowledge base queries, I specialize in Public TV hihi character information."
)
```

## Deployment

### Production Deployment

1. **Set up a reverse proxy** (nginx, Cloudflare, etc.)
2. **Configure HTTPS** for the webhook URL
3. **Set up monitoring** and log management
4. **Configure auto-restart** policies
5. **Set up backup** for environment configurations

### Cloud Deployment

The application can be deployed to various cloud platforms:
- Google Cloud Run
- AWS ECS/Fargate
- Azure Container Instances
- Railway, Render, or similar PaaS platforms

## Troubleshooting

### Common Issues

1. **Webhook returns 404**
   - Ensure webhook URL ends with `/` (e.g., `https://domain.com/`)
   - Check that the service is running on the correct port

2. **Invalid signature errors**
   - Verify `ChannelSecret` in environment variables
   - Check that webhook URL matches exactly

3. **AI responses not working**
   - Verify `GOOGLE_API_KEY` is valid
   - Check Google AI Studio quota and billing

4. **Weather/Time services failing**
   - Check internet connectivity from container
   - External APIs (wttr.in, worldtimeapi.org) might be temporarily unavailable

5. **Knowledge base not responding**
   - Verify `FASTGPT_API_KEY` and `FASTGPT_API_URL` are set correctly
   - Check FastGPT service availability
   - Knowledge base feature is optional; other functions will still work

### Debug Mode

Enable detailed logging by modifying the print statements in the code or check container logs:

```bash
docker-compose logs -f linebot-adk
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Google ADK](https://developers.google.com/adk) for the agent framework
- [wttr.in](https://wttr.in) for weather data
- [worldtimeapi.org](https://worldtimeapi.org) for timezone information
- [aiurl.tw](https://aiurl.tw) for URL shortening service
- [FastGPT](https://fastgpt.in/) for knowledge base integration