"""
使用者名稱查詢測試 (Social Analyzer OSINT)
"""
import pytest
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.asyncio
async def test_username_lookup_client():
    """測試 Social Analyzer Client"""
    from multi_tool_agent.clients.id_query_client import IDQueryClient

    client = IDQueryClient()
    result = await client.analyze("csl426")

    print(f"\n=== Social Analyzer Client 測試 ===")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Username: {result.get('username')}")
        print(f"Social Media 找到: {len(result.get('social_media', []))} 個")
        print(f"字詞資訊: {len(result.get('word_info', []))} 項")
        print(f"搜尋結果: {len(result.get('search_results', []))} 筆")

    assert result["status"] == "success"
    assert "username" in result


@pytest.mark.asyncio
async def test_username_lookup_agent():
    """測試使用者名稱查詢 Agent"""
    from multi_tool_agent.agents.username_lookup_agent import UsernameLookupAgent

    agent = UsernameLookupAgent()
    result = await agent.execute(
        username="johndoe",
        user_id="test_user_001"
    )

    print(f"\n=== Username Lookup Agent 測試 ===")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report:\n{result['report']}")
    else:
        print(f"Error: {result.get('error_message')}")

    assert result["status"] == "success"
    assert "report" in result


@pytest.mark.asyncio
async def test_username_lookup_wrapper():
    """測試 agent.py 中的包裝函數"""
    from multi_tool_agent.agent import lookup_username, current_user_id
    import multi_tool_agent.agent as agent_module

    # 設定 current_user_id
    agent_module.current_user_id = "test_user_wrapper"

    result = await lookup_username("testuser123")

    print(f"\n=== Agent Wrapper 測試 ===")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report 長度: {len(result['report'])} 字元")
    else:
        print(f"Error: {result.get('error_message')}")

    assert result["status"] == "success"
    assert "report" in result


@pytest.mark.asyncio
async def test_parse_response():
    """測試回應解析功能"""
    from multi_tool_agent.clients.id_query_client import IDQueryClient

    client = IDQueryClient()

    # 模擬 API 回應
    mock_data = {
        "username": "testuser",
        "user_info_normal": {
            "data": [
                {
                    "found": 2,
                    "username": "testuser",
                    "link": "https://facebook.com/testuser",
                    "status": "good",
                    "rate": "%100.00"
                },
                {
                    "found": 0,
                    "username": "testuser",
                    "link": "https://twitter.com/testuser",
                    "status": "",
                    "rate": "%0.0"
                }
            ]
        },
        "words_info": [
            {
                "word": "test",
                "text": "A procedure for critical evaluation",
                "results": []
            }
        ],
        "table": {
            "number": [],
            "unknown": ["test", "user"],
            "maybe": []
        },
        "custom_search": []
    }

    result = client._parse_response(mock_data)

    print(f"\n=== 回應解析測試 ===")
    print(f"Status: {result['status']}")
    print(f"Username: {result.get('username')}")
    print(f"Social Media: {result.get('social_media')}")
    print(f"Word Info: {result.get('word_info')}")

    assert result["status"] == "success"
    assert result["username"] == "testuser"
    assert len(result["social_media"]) == 1  # 只保留 found > 0 的
    assert result["social_media"][0]["platform"] == "Facebook"


if __name__ == "__main__":
    # 直接執行測試
    import asyncio

    async def run_all_tests():
        print("=" * 60)
        print("開始測試使用者名稱查詢功能 (Social Analyzer)")
        print("=" * 60)

        await test_username_lookup_client()
        await test_username_lookup_agent()
        await test_username_lookup_wrapper()
        await test_parse_response()

        print("\n" + "=" * 60)
        print("所有測試完成!")
        print("=" * 60)

    asyncio.run(run_all_tests())
