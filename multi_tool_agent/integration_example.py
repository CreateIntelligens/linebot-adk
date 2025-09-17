"""
整合現有 Agent 函數到新的中控台系統的範例
展示如何將現有的函數式 Agents 遷移到新的架構
"""

import asyncio
from multi_tool_agent.base import (
    BaseAgent,
    AgentResponse,
    register_agent,
    register_function_as_agent,
    get_global_registry
)
from multi_tool_agent.master_agent import get_global_master_agent


# 模擬現有的函數式 Agent（來自 multi_tool_agent/agent.py）
async def mock_weather_function(city: str) -> dict:
    """模擬現有的天氣查詢函數"""
    return {
        "status": "success",
        "report": f"{city}的天氣晴朗，溫度25度",
        "temperature": "25°C",
        "condition": "晴朗"
    }


async def mock_legal_function(question: str) -> dict:
    """模擬現有的法律諮詢函數"""
    return {
        "status": "success",
        "report": f"關於您的法律問題「{question}」，建議諮詢專業律師。",
        "advice": "請尋求專業法律協助"
    }


# 方法 1: 使用新的類別式 Agent
@register_agent(name="modern_weather", description="現代化天氣查詢 Agent")
class ModernWeatherAgent(BaseAgent):
    """使用新架構的天氣 Agent"""

    async def execute(self, **kwargs) -> AgentResponse:
        self.validate_params(['city'], **kwargs)
        city = kwargs['city']

        # 模擬 API 呼叫
        weather_data = {
            "city": city,
            "temperature": "26°C",
            "condition": "多雲",
            "humidity": "65%",
            "wind": "微風"
        }

        report = f"{city}天氣狀況：\n"
        report += f"溫度：{weather_data['temperature']}\n"
        report += f"天氣：{weather_data['condition']}\n"
        report += f"濕度：{weather_data['humidity']}\n"
        report += f"風況：{weather_data['wind']}"

        return AgentResponse.success(report, weather_data)


# 方法 2: 包裝現有函數為 Agent
class LegacyAgentWrapper(BaseAgent):
    """包裝現有函數的 Agent 類別"""

    def __init__(self, name: str, description: str, legacy_function):
        super().__init__(name, description)
        self.legacy_function = legacy_function

    async def execute(self, **kwargs) -> AgentResponse:
        try:
            result = await self.legacy_function(**kwargs)

            # 轉換現有函數的回傳格式
            if isinstance(result, dict):
                if result.get("status") == "success":
                    return AgentResponse.success(
                        result.get("report", ""),
                        {k: v for k, v in result.items()
                         if k not in ["status", "report", "error_message"]}
                    )
                elif result.get("status") == "error":
                    return AgentResponse.error(
                        result.get("error_message", "Unknown error")
                    )

            return AgentResponse.success(str(result))

        except Exception as e:
            return AgentResponse.error(f"執行錯誤: {str(e)}")


async def migrate_existing_agents():
    """將現有的函數式 Agents 遷移到新系統"""

    print("=== 遷移現有 Agents 到新系統 ===\n")

    registry = get_global_registry()
    master = get_global_master_agent()

    # 方法 1: 使用函數註冊工具
    print("1. 使用函數註冊工具註冊現有函數:")
    register_function_as_agent(
        mock_weather_function,
        "legacy_weather",
        "傳統天氣查詢函數"
    )

    register_function_as_agent(
        mock_legal_function,
        "legacy_legal",
        "傳統法律諮詢函數"
    )

    # 方法 2: 使用包裝器類別
    print("2. 使用包裝器類別:")
    wrapped_weather = LegacyAgentWrapper(
        "wrapped_weather",
        "包裝的天氣查詢 Agent",
        mock_weather_function
    )
    registry.register_agent(wrapped_weather)

    wrapped_legal = LegacyAgentWrapper(
        "wrapped_legal",
        "包裝的法律諮詢 Agent",
        mock_legal_function
    )
    registry.register_agent(wrapped_legal)

    print(f"已註冊 {len(registry)} 個 Agents\n")

    # 測試所有 Agents
    print("3. 測試所有 Agents:")

    test_cases = [
        ("modern_weather", {"city": "台北"}),
        ("legacy_weather", {"city": "高雄"}),
        ("wrapped_weather", {"city": "台中"}),
        ("legacy_legal", {"question": "租賃合約糾紛"}),
        ("wrapped_legal", {"question": "交通事故賠償"})
    ]

    for agent_name, params in test_cases:
        try:
            result = await master.execute(agent_name, **params)
            print(f"   ✓ {agent_name}: {result.status}")
            print(f"     回應: {result.report[:50]}...")
        except Exception as e:
            print(f"   ✗ {agent_name}: 錯誤 - {str(e)}")

    print()

    # 4. 比較不同實作方式的效能
    print("4. 效能比較:")

    import time

    # 測試現代化 Agent
    start_time = time.time()
    for _ in range(100):
        await master.execute("modern_weather", city="台北")
    modern_time = time.time() - start_time

    # 測試包裝的 Agent
    start_time = time.time()
    for _ in range(100):
        await master.execute("wrapped_weather", city="台北")
    wrapped_time = time.time() - start_time

    # 測試函數註冊的 Agent
    start_time = time.time()
    for _ in range(100):
        await master.execute("legacy_weather", city="台北")
    legacy_time = time.time() - start_time

    print(f"   現代化 Agent: {modern_time:.4f}s (100次執行)")
    print(f"   包裝器 Agent: {wrapped_time:.4f}s (100次執行)")
    print(f"   函數註冊 Agent: {legacy_time:.4f}s (100次執行)")
    print()

    # 5. 展示統一的管理介面
    print("5. 統一管理介面:")
    agents_info = master.get_available_agents()

    print("   所有已註冊的 Agents:")
    for name, info in agents_info.items():
        agent = registry.get_agent(name)
        print(f"   - {name}: {info['description']} ({info['class']})")

    print(f"\n   總計: {len(agents_info)} 個 Agents")

    # 6. 智能路由測試
    print("\n6. 智能路由測試:")

    test_inputs = [
        "台北天氣怎麼樣？",
        "有法律問題需要諮詢",
        "查詢高雄的氣象"
    ]

    for user_input in test_inputs:
        result = await master.smart_route(user_input)
        print(f"   輸入: {user_input}")
        print(f"   路由結果: {result.status} - {result.report[:50]}...")
        print()


async def demonstrate_line_bot_integration():
    """展示如何整合到 LINE Bot 系統"""

    print("=== LINE Bot 整合示範 ===\n")

    master = get_global_master_agent()

    # 模擬 LINE Bot 訊息處理
    async def handle_line_message(user_message: str, user_id: str = "user123"):
        """模擬 LINE Bot 訊息處理流程"""

        print(f"收到用戶 {user_id} 的訊息: {user_message}")

        # 使用智能路由處理訊息
        result = await master.smart_route(user_message)

        # 準備回傳給 LINE 的訊息
        if result.status == "success":
            reply_message = result.report
        elif result.status == "error":
            reply_message = f"抱歉，處理您的請求時發生錯誤：{result.error_message}"
        else:  # not_relevant
            reply_message = result.report  # 包含可用功能的說明

        print(f"回傳訊息: {reply_message}")
        print("-" * 50)

        return reply_message

    # 模擬多個用戶訊息
    test_messages = [
        "台北天氣如何？",
        "我想問個法律問題",
        "計算 15 + 25",
        "不知道你能幫我做什麼？",
        "查詢高雄氣象"
    ]

    for message in test_messages:
        await handle_line_message(message)
        await asyncio.sleep(0.1)  # 模擬處理間隔


if __name__ == "__main__":
    async def main():
        await migrate_existing_agents()
        await demonstrate_line_bot_integration()

    asyncio.run(main())