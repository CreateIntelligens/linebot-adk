# Agent 中控台系統

這是一個完整的 Agent 中控台系統，提供統一的 Agent 管理、註冊、執行和智能路由功能。

## 🏗️ 架構概覽

```
multi_tool_agent/
├── base/                     # 基礎架構
│   ├── __init__.py          # 模組匯出
│   ├── agent_base.py        # BaseAgent 基礎類別
│   ├── types.py             # AgentResponse 類型定義
│   └── registry.py          # AgentRegistry 註冊中心
├── master_agent.py          # MasterAgent 中控台
├── agents/                  # 具體的 Agent 實作
├── utils/                   # 工具模組
├── example_usage.py         # 使用範例
├── integration_example.py   # 整合範例
└── README.md               # 這個文檔
```

## 🚀 核心組件

### 1. BaseAgent 基礎類別
所有 Agent 都必須繼承的抽象基礎類別：

```python
from multi_tool_agent.base import BaseAgent, AgentResponse

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent", "我的 Agent 描述")

    async def execute(self, **kwargs) -> AgentResponse:
        # 實作 Agent 邏輯
        return AgentResponse.success("執行成功", {"data": "結果"})
```

### 2. AgentRegistry 註冊中心
管理所有 Agent 的註冊、查詢和執行：

```python
from multi_tool_agent.base import get_global_registry

registry = get_global_registry()

# 註冊 Agent
registry.register_agent(my_agent)

# 執行 Agent
result = await registry.execute_agent("my_agent", param1="value1")
```

### 3. MasterAgent 中控台
統一的 Agent 執行入口，提供智能路由功能：

```python
from multi_tool_agent.master_agent import get_global_master_agent

master = get_global_master_agent()

# 直接執行
result = await master.execute("weather", city="台北")

# 智能路由
result = await master.smart_route("台北天氣如何？")
```

### 4. AgentResponse 統一回應格式
標準化的 Agent 回應格式：

```python
# 成功回應
return AgentResponse.success("操作成功", {"data": "結果"})

# 錯誤回應
return AgentResponse.error("發生錯誤")

# 不相關回應
return AgentResponse.not_relevant("此請求與當前 Agent 無關")
```

## 📝 使用方式

### 方式 1：使用裝飾器自動註冊

```python
from multi_tool_agent.base import register_agent, BaseAgent, AgentResponse

@register_agent(name="weather", description="天氣查詢 Agent")
class WeatherAgent(BaseAgent):
    async def execute(self, **kwargs) -> AgentResponse:
        city = kwargs.get('city', '台北')
        # 實作天氣查詢邏輯
        return AgentResponse.success(f"{city}的天氣...")
```

### 方式 2：手動註冊

```python
from multi_tool_agent.base import BaseAgent, get_global_registry

class WeatherAgent(BaseAgent):
    def __init__(self):
        super().__init__("weather", "天氣查詢 Agent")

    async def execute(self, **kwargs) -> AgentResponse:
        # 實作邏輯
        pass

# 註冊 Agent
registry = get_global_registry()
registry.register_agent(WeatherAgent())
```

### 方式 3：包裝現有函數

```python
from multi_tool_agent.base import register_function_as_agent

async def weather_function(city: str) -> dict:
    return {"status": "success", "report": f"{city}的天氣..."}

# 將函數註冊為 Agent
register_function_as_agent(
    weather_function,
    "weather",
    "天氣查詢函數"
)
```

## 🔧 智能路由

MasterAgent 提供智能路由功能，可以根據用戶輸入自動選擇合適的 Agent：

```python
master = get_global_master_agent()

# 這些輸入會自動路由到天氣 Agent
await master.smart_route("台北天氣如何？")
await master.smart_route("查詢高雄氣象")

# 這些輸入會自動路由到法律 Agent
await master.smart_route("我有法律問題")
await master.smart_route("需要律師協助")
```

### 支援的關鍵字映射
- **天氣相關**: "天氣", "氣象", "weather" → 天氣 Agents
- **法律相關**: "法律", "律師", "訴訟", "legal" → 法律 Agents
- **計算相關**: "計算", "算", "數學" → 計算器 Agent
- **範例相關**: "範例", "測試", "example" → 範例 Agent

## 🔄 遷移現有函數

如果你有現有的函數式 Agent，可以輕鬆遷移到新系統：

### 選項 1：使用函數註冊工具
```python
# 現有函數
async def get_weather(city: str) -> dict:
    return {"status": "success", "report": "..."}

# 註冊為 Agent
register_function_as_agent(get_weather, "weather", "天氣查詢")
```

### 選項 2：使用包裝器類別
```python
class LegacyAgentWrapper(BaseAgent):
    def __init__(self, name: str, description: str, legacy_function):
        super().__init__(name, description)
        self.legacy_function = legacy_function

    async def execute(self, **kwargs) -> AgentResponse:
        result = await self.legacy_function(**kwargs)
        # 轉換回應格式
        if result.get("status") == "success":
            return AgentResponse.success(result.get("report", ""))
        else:
            return AgentResponse.error(result.get("error_message", ""))
```

## 🚦 並行執行

Master Agent 支援並行執行多個 Agents：

```python
requests = [
    {"agent_name": "weather", "city": "台北"},
    {"agent_name": "weather", "city": "高雄"},
    {"agent_name": "legal", "question": "合約問題"}
]

results = await master.execute_multiple(requests)
```

## 📊 監控和管理

### 查看已註冊的 Agents
```python
agents_info = master.get_available_agents()
for name, info in agents_info.items():
    print(f"{name}: {info['description']}")
```

### 執行歷史
```python
history = master.get_execution_history(limit=10)
for record in history:
    print(f"{record['agent_name']}: {record['status']}")
```

### 健康檢查
```python
health_result = await master.health_check()
print(health_result.report)
```

### 系統狀態
```python
status = master.get_agent_status()
print(f"已註冊 Agents: {status['registered_agents_count']} 個")
```

## 🔧 LINE Bot 整合

在 LINE Bot 中使用這個系統：

```python
from multi_tool_agent.master_agent import get_global_master_agent

async def handle_message(event):
    user_message = event.message.text
    master = get_global_master_agent()

    # 使用智能路由處理訊息
    result = await master.smart_route(user_message)

    if result.status == "success":
        reply_text = result.report
    elif result.status == "error":
        reply_text = f"抱歉，發生錯誤：{result.error_message}"
    else:
        reply_text = result.report  # 包含可用功能說明

    # 回傳給 LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
```

## 🔄 擴展新功能

添加新的 Agent 非常簡單：

1. **創建新的 Agent 類別**：
```python
@register_agent(name="calculator", description="數學計算 Agent")
class CalculatorAgent(BaseAgent):
    async def execute(self, **kwargs) -> AgentResponse:
        expression = kwargs.get('expression', '')
        result = eval(expression)  # 注意：實際應用中需要安全計算
        return AgentResponse.success(f"計算結果: {result}")
```

2. **更新智能路由（如需要）**：
在 `master_agent.py` 的 `smart_route` 方法中添加新的關鍵字映射。

3. **註冊並使用**：
Agent 會自動註冊到全域註冊中心，立即可用。

## 🛡️ 錯誤處理

系統提供完整的錯誤處理機制：

- **類型安全**：使用 Python 類型提示
- **參數驗證**：BaseAgent 提供 `validate_params` 方法
- **異常捕捉**：Registry 和 MasterAgent 會捕捉並處理所有異常
- **統一錯誤格式**：使用 AgentResponse.error 統一錯誤回應

## 📋 最佳實踐

1. **命名規範**：使用清晰、描述性的 Agent 名稱
2. **參數驗證**：在 `execute` 方法開始時驗證必要參數
3. **錯誤處理**：適當捕捉和處理異常
4. **文檔撰寫**：為每個 Agent 提供清晰的描述
5. **測試**：為每個 Agent 編寫單元測試

## 🔮 未來擴展

這個架構支援進一步擴展：

1. **進階 NLP 路由**：整合更複雜的自然語言理解模型
2. **Agent 鏈接**：支援 Agent 之間的協作和數據傳遞
3. **持久化存儲**：添加資料庫支援以保存執行歷史
4. **性能監控**：添加詳細的性能指標和監控
5. **動態配置**：支援運行時動態添加和移除 Agents

## 📚 範例代碼

完整的使用範例請參考：
- `example_usage.py` - 基本使用範例
- `integration_example.py` - 整合和遷移範例

這些範例展示了如何：
- 創建和註冊 Agents
- 使用智能路由
- 並行執行 Agents
- 整合現有函數
- 監控系統狀態