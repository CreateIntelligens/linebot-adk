"""
測試稅務對話流程 - 驗證 Agent 不會反問
"""
import pytest
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.asyncio
async def test_tax_conversation_no_questions():
    """
    測試稅務對話 - Agent 應該直接呼叫工具,不反問

    模擬對話:
    User: "你能查稅嗎"
    Agent: 應該直接用 call_tax_ai("你能查稅嗎")

    User: "好 幫我查"
    Agent: 應該直接用 call_tax_ai("好 幫我查")

    User: "我要繳多少稅"
    Agent: 應該直接用 call_tax_ai("我要繳多少稅")
    """
    from multi_tool_agent.agents.tax_ai_agent import TaxAIAgent

    agent = TaxAIAgent()
    user_id = "test_conversation_user"

    print("\n" + "="*60)
    print("測試對話流程 - Agent 應該直接呼叫工具")
    print("="*60)

    # 第一輪
    print("\n[User] 你能查稅嗎")
    result1 = await agent.execute(
        question="你能查稅嗎",
        user_id=user_id
    )
    print(f"[Agent] {result1.get('report', result1.get('error_message'))}")
    assert result1["status"] == "success"

    # 第二輪
    print("\n[User] 好 幫我查")
    result2 = await agent.execute(
        question="好 幫我查",
        user_id=user_id
    )
    print(f"[Agent] {result2.get('report', result2.get('error_message'))}")
    assert result2["status"] == "success"

    # 第三輪
    print("\n[User] 我要繳多少稅")
    result3 = await agent.execute(
        question="我要繳多少稅",
        user_id=user_id
    )
    print(f"[Agent] {result3.get('report', result3.get('error_message'))}")
    assert result3["status"] == "success"

    # 第四輪 - 提供資訊
    print("\n[User] 今年")
    result4 = await agent.execute(
        question="今年",
        user_id=user_id
    )
    print(f"[Agent] {result4.get('report', result4.get('error_message'))}")
    assert result4["status"] == "success"

    # 第五輪 - 提供金額
    print("\n[User] 所得40萬")
    result5 = await agent.execute(
        question="所得40萬",
        user_id=user_id
    )
    print(f"[Agent] {result5.get('report', result5.get('error_message'))}")
    assert result5["status"] == "success"

    # 第六輪 - 確認沒有其他扣除額
    print("\n[User] 都沒有")
    result6 = await agent.execute(
        question="都沒有",
        user_id=user_id
    )
    print(f"[Agent] {result6.get('report', result6.get('error_message'))}")
    assert result6["status"] == "success"

    print("\n" + "="*60)
    print("對話測試完成!")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tax_conversation_no_questions())
