"""
Agent 中控台系統使用範例
展示如何使用 Master Agent、Agent Registry 和裝飾器
"""

import asyncio
from multi_tool_agent.base import BaseAgent, AgentResponse, register_agent
from multi_tool_agent.master_agent import MasterAgent, get_global_master_agent


# 方法 1: 使用裝飾器自動註冊 Agent
@register_agent(name="example", description="範例 Agent")
class ExampleAgent(BaseAgent):
    """範例 Agent，展示基本功能"""

    async def execute(self, **kwargs) -> AgentResponse:
        message = kwargs.get('message', '沒有提供訊息')
        return AgentResponse.success(f"範例 Agent 收到訊息: {message}")


# 方法 2: 手動創建和註冊 Agent
class WeatherAgent(BaseAgent):
    """天氣查詢 Agent"""

    def __init__(self):
        super().__init__("weather", "查詢天氣資訊", auto_register=True)

    async def execute(self, **kwargs) -> AgentResponse:
        city = kwargs.get('city', '台北')
        # 模擬天氣查詢
        weather_data = {
            "city": city,
            "temperature": "25°C",
            "condition": "晴朗",
            "humidity": "60%"
        }
        return AgentResponse.success(
            f"{city}的天氣: {weather_data['temperature']}, {weather_data['condition']}",
            weather_data
        )


class CalculatorAgent(BaseAgent):
    """計算器 Agent"""

    def __init__(self):
        super().__init__("calculator", "執行數學計算")

    async def execute(self, **kwargs) -> AgentResponse:
        try:
            expression = kwargs.get('expression', '')
            if not expression:
                return AgentResponse.error("請提供數學表達式")

            # 安全的數學計算（僅支援基本運算）
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                return AgentResponse.error("表達式包含不允許的字符")

            result = eval(expression)
            return AgentResponse.success(
                f"計算結果: {expression} = {result}",
                {"expression": expression, "result": result}
            )

        except Exception as e:
            return AgentResponse.error(f"計算錯誤: {str(e)}")


async def main():
    """主要演示函數"""
    print("=== Agent 中控台系統演示 ===\n")

    # 獲取全域 Master Agent
    master = get_global_master_agent()

    # 手動註冊 Calculator Agent
    calc_agent = CalculatorAgent()
    master.register_agent(calc_agent)

    # 創建並註冊 Weather Agent (使用 auto_register)
    weather_agent = WeatherAgent()

    # 1. 查看已註冊的 Agents
    print("1. 已註冊的 Agents:")
    agents_info = master.get_available_agents()
    for name, info in agents_info.items():
        print(f"   - {name}: {info['description']}")
    print()

    # 2. 執行單個 Agent
    print("2. 執行單個 Agent:")

    # 執行範例 Agent
    result = await master.execute("example", message="Hello World!")
    print(f"   範例 Agent: {result.report}")

    # 執行天氣 Agent
    result = await master.execute("weather", city="台北")
    print(f"   天氣 Agent: {result.report}")

    # 執行計算器 Agent
    result = await master.execute("calculator", expression="2 + 3 * 4")
    print(f"   計算器 Agent: {result.report}")
    print()

    # 3. 智能路由測試
    print("3. 智能路由測試:")

    test_inputs = [
        "台北天氣如何？",
        "計算 10 + 20",
        "幫我查看範例功能"
    ]

    for user_input in test_inputs:
        print(f"   輸入: {user_input}")
        result = await master.smart_route(user_input)
        print(f"   結果: {result.report}")
        print()

    # 4. 並行執行多個 Agents
    print("4. 並行執行多個 Agents:")

    requests = [
        {"agent_name": "weather", "city": "台北"},
        {"agent_name": "weather", "city": "高雄"},
        {"agent_name": "calculator", "expression": "5 * 6"},
        {"agent_name": "example", "message": "並行測試"}
    ]

    results = await master.execute_multiple(requests)
    for i, result in enumerate(results):
        print(f"   請求 {i+1}: {result.report}")
    print()

    # 5. 健康檢查
    print("5. 系統健康檢查:")
    health_result = await master.health_check()
    print(f"   {health_result.report}")
    print()

    # 6. 查看執行歷史
    print("6. 執行歷史 (最近 5 筆):")
    history = master.get_execution_history(limit=5)
    for record in history:
        print(f"   - {record['agent_name']}: {record['status']} ({record.get('duration', 0):.3f}s)")
    print()

    # 7. 系統狀態
    print("7. 系統狀態:")
    status = master.get_agent_status()
    print(f"   已註冊 Agents: {status['registered_agents_count']} 個")
    print(f"   執行歷史: {status['execution_history_count']} 筆")
    print(f"   可用 Agents: {', '.join(status['available_agents'])}")


if __name__ == "__main__":
    asyncio.run(main())