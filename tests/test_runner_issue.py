
import asyncio
import os
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Minimal agent definition
test_agent = Agent(
    name="test_agent",
    model="gemini-1.5-flash-exp",
    description="A test agent",
    instruction="You are a test agent.",
    tools=[],
)

# Services
session_service = InMemorySessionService()
runner = Runner(
    app_name="test_app",
    agent=test_agent,
    session_service=session_service
)

async def run_test():
    print("-- Running Test --")
    user_id = "test_user"
    session = await session_service.create_session(
        app_name="test_app",
        user_id=user_id,
        session_id="test_session"
    )
    query = "早安"

    test_formats = {
        "string": query,
        "types.Part": [types.Part(text=query)],
        "dict": {"parts": [{"text": query}]}
    }

    for name, message_format in test_formats.items():
        print(f"\n--- Testing format: {name} ---")
        try:
            events = runner.run(
                user_id=user_id,
                session_id=session.id,
                new_message=message_format
            )
            
            print("Runner executed. Iterating events...")
            for event in events:
                print(f"Event: {type(event).__name__}, Content: {getattr(event, 'content', 'N/A')}")
            print(f"SUCCESS: Format '{name}' worked.")

        except Exception as e:
            print(f"ERROR with format '{name}': {type(e).__name__} - {e}")
            # import traceback
            # traceback.print_exc()

if __name__ == "__main__":
    # This is needed because the runner starts its own asyncio loop in a thread
    # and it can conflict with an existing one.
    # We run our test in a way that avoids this conflict for this specific test.
    # This is a workaround for testing runner.run() directly.
    from threading import Thread
    import time

    # The runner initializes its own event loop in a background thread.
    # We need to give it a moment to start up before we can run our test.
    # This is a known complexity when interacting with the ADK runner's sync API.
    time.sleep(1) # Allow runner background thread to initialize

    asyncio.run(run_test())
