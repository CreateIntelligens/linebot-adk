# LINE Bot with Google ADK - Multi-Tool Assistant

A versatile LINE bot powered by Google ADK (Agent Development Kit) and Gemini 2.0 Flash model, providing weather information, time queries, and URL shortening services.

## Features

- **🌤️ Weather Service**
  - Current weather conditions worldwide (powered by wttr.in)
  - Weather forecasts (1-3 days)
  - Intelligent city name recognition

- **🕐 Time Service**
  - Current time for any city worldwide
  - Smart timezone detection (powered by worldtimeapi.org)
  - Fallback to Taiwan timezone for unrecognized cities

- **🔗 URL Shortening**
  - Create short URLs using aiurl.tw service
  - Optional custom slug support
  - Automatic duplicate detection

- **🤖 Smart Conversation**
  - Natural language understanding
  - Traditional Chinese responses
  - Context-aware tool selection

## Technology Stack

- **Backend**: Python 3.10, FastAPI
- **AI**: Google ADK, Gemini 2.0 Flash model
- **Messaging**: LINE Messaging API
- **Containerization**: Docker, Docker Compose
- **APIs**: wttr.in (weather), worldtimeapi.org (time), aiurl.tw (URL shortening)

## Quick Start with Docker Compose

### Prerequisites

1. LINE Bot Channel (Channel Secret & Access Token)
2. Google AI Studio API Key
3. Docker and Docker Compose installed

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
   ChannelSecret=your_line_channel_secret
   ChannelAccessToken=your_line_channel_access_token
   GOOGLE_API_KEY=your_google_ai_studio_api_key
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
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

## Usage Examples

Send these messages to your LINE bot:

### Weather Queries
- "台北天氣如何？" (Current weather in Taipei)
- "東京明天會下雨嗎？" (Tomorrow's weather in Tokyo)
- "高雄未來三天天氣預報" (3-day forecast for Kaohsiung)

### Time Queries
- "現在幾點？" (Current time)
- "紐約現在幾點？" (Current time in New York)
- "今天幾號？" (Today's date)

### URL Shortening
- Send any URL: "https://github.com/example/repo"
- Custom slug: "幫我縮短網址，名稱用 my-link"

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ChannelSecret=your_channel_secret
export ChannelAccessToken=your_channel_access_token
export GOOGLE_API_KEY=your_google_api_key

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

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ChannelSecret` | LINE Channel Secret | Yes | - |
| `ChannelAccessToken` | LINE Channel Access Token | Yes | - |
| `GOOGLE_API_KEY` | Google AI Studio API Key | Yes | - |
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Vertex AI instead of AI Studio | No | FALSE |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID (if using Vertex AI) | No | - |
| `GOOGLE_CLOUD_LOCATION` | GCP Location (if using Vertex AI) | No | - |

### Customizing Agent Behavior

Edit the `instruction` parameter in `main.py` to customize the agent's behavior:

```python
instruction=(
    "I am a specialized assistant providing three services: weather, time, and URL shortening.\n"
    "Respond concisely in Traditional Chinese without asking too many confirmation questions."
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