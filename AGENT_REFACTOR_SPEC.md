# LINE Bot ADK - Agent 重構規格文件

## 1. 現狀分析

### 目前架構問題
- `multi_tool_agent/agent.py` 檔案過長 (1000+ 行)
- 功能混雜，包含多種不同領域的工具
- 部分 agent 已獨立 (如 `meme_agent.py`)
- 缺乏統一的 agent 介面標準
- 維護困難，新增功能時需要修改大檔案

### 現有功能清單
```
multi_tool_agent/agent.py:
├── 天氣相關
│   ├── get_weather()                    # 當前天氣查詢
│   └── get_weather_forecast()           # 天氣預報查詢
├── 時間相關
│   └── get_current_time()               # 時間查詢
├── 知識庫相關
│   ├── query_knowledge_base()           # hihi導覽先生知識庫
│   └── query_set_knowledge_base()       # SET三立電視知識庫
├── 網路工具
│   └── create_short_url()               # 短網址生成
├── 影片相關
│   ├── process_video()                  # 影片處理/轉錄
│   ├── generate_ai_video()              # AI影片生成
│   └── ComfyUI 相關函數
├── 法律諮詢
│   └── call_legal_ai()                  # 法律問題諮詢
└── 輔助函數
    ├── push_video_to_user()
    ├── upload_video_to_https_server()
    └── 其他工具函數

獨立檔案:
├── meme_agent.py                        # Meme 圖片生成
├── legal_agent.py                       # 法律專業邏輯
└── comfyui_agent.py                     # ComfyUI 工作流程
```

## 2. 重構目標

### 主要目標
1. **模塊化設計**: 每個 agent 負責單一領域
2. **統一介面**: 標準化的 agent 介面和返回格式
3. **易於維護**: 獨立檔案，降低耦合度
4. **易於擴展**: 新增 agent 不影響現有功能
5. **保持相容**: 不破壞現有的 API 調用

### 設計原則
- **單一職責原則**: 每個 agent 專注一個領域
- **開放封閉原則**: 對擴展開放，對修改封閉
- **依賴倒置**: 依賴抽象而非具體實現
- **介面隔離**: 最小化 agent 間的依賴

## 3. 新架構設計

### 目錄結構
```
multi_tool_agent/
├── __init__.py                          # 匯入所有 agents
├── base/
│   ├── __init__.py
│   ├── agent_base.py                    # Agent 基類
│   ├── types.py                         # 通用類型定義
│   └── exceptions.py                    # 自定義異常
├── agents/
│   ├── __init__.py
│   ├── weather_agent.py                 # 天氣相關
│   ├── time_agent.py                    # 時間查詢
│   ├── knowledge_agent.py               # 知識庫查詢
│   ├── url_agent.py                     # 短網址工具
│   ├── video_agent.py                   # 影片處理
│   ├── ai_video_agent.py                # AI影片生成
│   ├── legal_agent.py                   # 法律諮詢 (現有)
│   ├── meme_agent.py                    # Meme生成 (現有)
│   └── comfyui_agent.py                 # ComfyUI (現有)
├── utils/
│   ├── __init__.py
│   ├── http_client.py                   # HTTP 請求工具
│   ├── file_handler.py                  # 檔案處理工具
│   └── line_bot_helper.py               # LINE Bot 輔助函數
└── registry.py                          # Agent 註冊中心
```

### Agent 基類設計
```python
# base/agent_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from .types import AgentResponse

class BaseAgent(ABC):
    """所有 Agent 的基礎類別"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResponse:
        """執行 Agent 功能的抽象方法"""
        pass

    def validate_params(self, required_params: list, **kwargs):
        """驗證必要參數"""
        missing = [p for p in required_params if p not in kwargs]
        if missing:
            raise ValueError(f"缺少必要參數: {missing}")
```

### 標準返回格式
```python
# base/types.py
from typing import Dict, Any, Literal
from dataclasses import dataclass

@dataclass
class AgentResponse:
    status: Literal["success", "error", "not_relevant"]
    report: str = ""
    error_message: str = ""
    data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "report": self.report,
            "error_message": self.error_message,
            **self.data or {}
        }
```

### Agent 註冊機制
```python
# registry.py
from typing import Dict, Type
from .base.agent_base import BaseAgent

class AgentRegistry:
    """Agent 註冊中心"""

    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}

    def register(self, agent_class: Type[BaseAgent]):
        """註冊 Agent"""
        self._agents[agent_class.name] = agent_class

    def get_agent(self, name: str) -> Type[BaseAgent]:
        """取得 Agent"""
        return self._agents.get(name)

    def list_agents(self) -> list:
        """列出所有 Agent"""
        return list(self._agents.keys())

# 全域註冊實例
registry = AgentRegistry()
```

## 4. 實作範例

### 天氣 Agent 範例
```python
# agents/weather_agent.py
import aiohttp
from ..base.agent_base import BaseAgent
from ..base.types import AgentResponse

class WeatherAgent(BaseAgent):
    def __init__(self):
        super().__init__("weather", "天氣查詢服務")

    async def get_weather(self, city: str, **kwargs) -> AgentResponse:
        """查詢當前天氣"""
        self.validate_params(["city"], city=city)

        try:
            # 天氣查詢邏輯
            weather_data = await self._fetch_weather(city)
            return AgentResponse(
                status="success",
                report=f"📍 {city} 天氣：{weather_data['description']}"
            )
        except Exception as e:
            return AgentResponse(
                status="error",
                error_message=f"天氣查詢失敗：{str(e)}"
            )

    async def get_forecast(self, city: str, days: str = "1", **kwargs) -> AgentResponse:
        """查詢天氣預報"""
        # 實作邏輯...
        pass
```

### 知識庫 Agent 範例
```python
# agents/knowledge_agent.py
class KnowledgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("knowledge", "知識庫查詢服務")

    async def query_hihi(self, question: str, user_id: str, **kwargs) -> AgentResponse:
        """查詢 hihi 導覽先生知識庫"""
        # 現有邏輯移植
        pass

    async def query_set(self, question: str, user_id: str, **kwargs) -> AgentResponse:
        """查詢 SET 三立電視知識庫"""
        # 現有邏輯移植
        pass
```

## 5. 整合介面

### 統一匯入檔案
```python
# multi_tool_agent/__init__.py
from .agents.weather_agent import WeatherAgent
from .agents.time_agent import TimeAgent
from .agents.knowledge_agent import KnowledgeAgent
# ... 其他 agents

# 建立實例
weather_agent = WeatherAgent()
time_agent = TimeAgent()
knowledge_agent = KnowledgeAgent()
# ...

# 保持向後相容的函數介面
async def get_weather(city: str, **kwargs):
    return await weather_agent.get_weather(city=city, **kwargs)

async def get_current_time(city: str = "台北", **kwargs):
    return await time_agent.get_current_time(city=city, **kwargs)

async def query_knowledge_base(question: str, user_id: str, **kwargs):
    return await knowledge_agent.query_hihi(question=question, user_id=user_id, **kwargs)

# 匯出所有函數供 main.py 使用
__all__ = [
    'get_weather',
    'get_weather_forecast',
    'get_current_time',
    'query_knowledge_base',
    'query_set_knowledge_base',
    'create_short_url',
    'process_video',
    'call_legal_ai',
    'generate_meme',
    'generate_ai_video',
    # ... 其他函數
]
```

## 6. 重構計劃

### Phase 1: 基礎架構 (Week 1)
1. 建立目錄結構
2. 實作基類和類型定義
3. 建立註冊機制
4. 建立測試框架

### Phase 2: 核心 Agents (Week 2-3)
1. 重構天氣相關功能 → `weather_agent.py`
2. 重構時間查詢功能 → `time_agent.py`
3. 重構知識庫功能 → `knowledge_agent.py`
4. 重構網址工具功能 → `url_agent.py`

### Phase 3: 複雜 Agents (Week 4-5)
1. 重構影片處理功能 → `video_agent.py`
2. 重構 AI 影片生成 → `ai_video_agent.py`
3. 整合現有的獨立 agents
4. 建立統一的工具函數庫

### Phase 4: 測試與最佳化 (Week 6)
1. 單元測試
2. 整合測試
3. 效能最佳化
4. 文件更新

## 7. 相容性保證

### 向後相容策略
1. 保持現有函數介面不變
2. 在 `__init__.py` 中提供包裝函數
3. 漸進式替換，不影響線上服務
4. 完整的測試覆蓋

### 版本管理
- 使用語意化版本控制
- 主版本號變更時才允許破壞性變更
- 提供遷移指南和工具

## 8. 測試策略

### 測試層級
1. **單元測試**: 每個 agent 的個別測試
2. **整合測試**: agent 間協作測試
3. **端對端測試**: 完整的 LINE Bot 功能測試

### 測試工具
- pytest: 測試框架
- pytest-asyncio: 非同步測試支援
- pytest-mock: 模擬外部服務
- coverage: 測試覆蓋率

## 9. 部署注意事項

### 環境變數管理
- 每個 agent 管理自己的環境變數
- 統一的配置驗證機制
- 敏感資訊加密存儲

### 監控與日誌
- 每個 agent 獨立的日誌配置
- 統一的錯誤追蹤
- 效能監控指標

## 10. 未來擴展

### 可能的新 Agents
- `news_agent.py`: 新聞查詢
- `translate_agent.py`: 翻譯服務
- `image_agent.py`: 圖片處理
- `schedule_agent.py`: 排程管理

### 進階功能
- Agent 間的協作機制
- 動態 Agent 載入
- 分散式 Agent 架構
- AI 自動選擇最佳 Agent

---

**重構完成後的好處:**
- 程式碼可讀性大幅提升
- 維護成本降低
- 新功能開發更快速
- 團隊協作更容易
- 測試和除錯更簡單