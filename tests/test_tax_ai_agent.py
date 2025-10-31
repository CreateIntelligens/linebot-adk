"""
稅務 AI Agent 測試
"""
import pytest
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.asyncio
async def test_tax_ai_basic_question():
    """測試基本稅務問題"""
    from multi_tool_agent.agents.tax_ai_agent import TaxAIAgent

    agent = TaxAIAgent()
    result = await agent.execute(
        question="個人所得稅有哪些扣除額?",
        user_id="test_user_001"
    )

    print(f"\n=== 稅務 AI 回應 ===")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report: {result['report']}")
    else:
        print(f"Error: {result.get('error_message')}")

    assert result["status"] == "success"
    assert "report" in result
    assert len(result["report"]) > 0


@pytest.mark.asyncio
async def test_tax_ai_out_of_scope():
    """測試超出範圍的問題 (營業稅)"""
    from multi_tool_agent.agents.tax_ai_agent import TaxAIAgent

    agent = TaxAIAgent()
    result = await agent.execute(
        question="營業稅如何申報?",
        user_id="test_user_002"
    )

    print(f"\n=== 稅務 AI 超出範圍測試 ===")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report: {result['report']}")
        # 應該回應說只能處理個人所得稅
        assert "個人所得稅" in result['report'] or "只能" in result['report']
    else:
        print(f"Error: {result.get('error_message')}")


@pytest.mark.asyncio
async def test_tax_ai_session_persistence():
    """測試會話持久性 (同一個 user_id 應該維持對話上下文)"""
    from multi_tool_agent.agents.tax_ai_agent import TaxAIAgent

    agent = TaxAIAgent()
    user_id = "test_user_003"

    # 第一個問題
    result1 = await agent.execute(
        question="我年收入100萬,要繳多少稅?",
        user_id=user_id
    )

    print(f"\n=== 第一個問題 ===")
    print(f"Status: {result1['status']}")
    if result1['status'] == 'success':
        print(f"Report: {result1['report']}")

    # 第二個問題 (應該會記得前面的上下文)
    result2 = await agent.execute(
        question="那如果我有扶養兩個小孩呢?",
        user_id=user_id
    )

    print(f"\n=== 第二個問題 (有上下文) ===")
    print(f"Status: {result2['status']}")
    if result2['status'] == 'success':
        print(f"Report: {result2['report']}")

    assert result1["status"] == "success"
    assert result2["status"] == "success"


@pytest.mark.asyncio
async def test_tax_ai_client_directly():
    """直接測試 TaxAIClient"""
    from multi_tool_agent.clients.tax_ai_client import TaxAIClient

    client = TaxAIClient()
    result = await client.chat(
        message="請問免稅額是多少?",
        session_id="test_session_001"
    )

    print(f"\n=== Tax AI Client 直接測試 ===")
    print(f"Status: {result['status']}")
    print(f"Message: {result.get('message')}")
    if result.get('fact_graph_data'):
        print(f"Fact Graph Data: {result['fact_graph_data']}")

    assert result["status"] == "success"
    assert "message" in result


@pytest.mark.asyncio
async def test_tax_ai_agent_wrapper():
    """測試 agent.py 中的包裝函數"""
    from multi_tool_agent.agent import call_tax_ai, current_user_id
    import multi_tool_agent.agent as agent_module

    # 設定 current_user_id
    agent_module.current_user_id = "test_user_wrapper"

    result = await call_tax_ai("標準扣除額是多少?")

    print(f"\n=== Agent Wrapper 測試 ===")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report: {result['report']}")
    else:
        print(f"Error: {result.get('error_message')}")

    assert result["status"] == "success"
    assert "report" in result


if __name__ == "__main__":
    # 直接執行測試
    import asyncio

    async def run_all_tests():
        print("=" * 60)
        print("開始測試稅務 AI Agent")
        print("=" * 60)

        await test_tax_ai_basic_question()
        await test_tax_ai_out_of_scope()
        await test_tax_ai_session_persistence()
        await test_tax_ai_client_directly()
        await test_tax_ai_agent_wrapper()

        print("\n" + "=" * 60)
        print("所有測試完成!")
        print("=" * 60)

    asyncio.run(run_all_tests())
