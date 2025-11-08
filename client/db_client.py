import asyncio
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
from typing import Optional


class TaskRequest(BaseModel):
    task_type: Optional[str] = Field(description="The type of task to perform")
    description: Optional[str] = Field(description="Detailed description of the task")
    priority: Optional[str] = Field(description="Priority level: low, medium, high")


async def structured_chat_loop():
    """Chat loop that can handle both natural language and structured inputs."""
    # Load environment variables
    load_dotenv()

    # MCP server configuration
    config = {
        "mcpServers": {
            "postgres": {
                "command": "uv",
                "args": [
                    "run",
                    "D:\Projects\mcp-server-project\mcp-server-client\server\postgres_db.py",
                    "--db-url", os.getenv("DB_URL")
                ]
            }
        }
    }

    # Create client and agent
    client = MCPClient(config)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))

    agent = MCPAgent(
        llm=llm,
        client=client,
        memory_enabled=True,  # Enable memory to track conversation history
        max_steps=20
    )

    # Initial messages
    print("🤖 MCP Agent Chat (Structured)")
    print("You can chat naturally or request structured task analysis")
    print("Type 'task' to create a structured task request")

    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break

            try:
                if user_input.lower() == 'task':
                    print("\n📋 Creating structured task...")
                    task_description = input("Describe your task: ")

                    task: TaskRequest = await agent.run(
                        f"Analyze a task with the following description: {task_description}",
                        output_schema=TaskRequest
                    )

                    # Print task analysis
                    print(f"\n✅ Task Analysis:")
                    print(f"• Type: {task.task_type}")
                    print(f"• Description: {task.description}")
                    print(f"• Priority: {task.priority or 'low'}")

                    proceed = input("\nDo you want to proceed with this task? (y/n)")
                    if proceed.lower() == 'y':
                        response = await agent.run(
                            f"Execute the following task: {task.description}"
                        )
                        print(f"\n🤖 Assistant: {response}")
                else:
                    # Regular conversation
                    response = await agent.run(user_input)
                    print(f"\n🤖 Assistant: {response}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again or type 'exit' to quit.")

    finally:
        await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(structured_chat_loop())
