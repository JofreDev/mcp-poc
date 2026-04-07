import os
import json
import asyncio
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# =========================================================
# 1) Load environment variables from .env
#    Azure v1 API with the OpenAI client uses:
#    - OPENAI_API_KEY
#    - OPENAI_BASE_URL
#    - OPENAI_MODEL_NAME
# =========================================================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env")

if not OPENAI_BASE_URL:
    raise ValueError("Missing OPENAI_BASE_URL in .env")

if not OPENAI_MODEL_NAME:
    raise ValueError("Missing OPENAI_MODEL_NAME in .env")


# =========================================================
# 2) Resolve local MCP server path
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
SERVER_PATH = (BASE_DIR / "../mcp-server-python/server.py").resolve()


# =========================================================
# 3) Configure local MCP server execution over stdio
# =========================================================
server_params = StdioServerParameters(
    command="mcp",
    args=["run", str(SERVER_PATH)],
    env=None,
)


# =========================================================
# 4) Create OpenAI client using Azure v1 endpoint
#    Official Azure v1 pattern:
#    OpenAI(base_url="https://.../openai/v1/", api_key="...")
# =========================================================
client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
)


# =========================================================
# 5) Convert MCP tool metadata into OpenAI chat tool format
#    Chat Completions expects tools of type "function"
# =========================================================
def convert_mcp_tool_to_openai_function(tool: Any) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


# =========================================================
# 6) Convert MCP CallToolResult into plain text
# =========================================================
def mcp_result_to_text(result: Any) -> str:
    parts: list[str] = []

    for item in result.content:
        if getattr(item, "type", None) == "text":
            parts.append(item.text)
        else:
            parts.append(str(item))

    return "\n".join(parts).strip()


# =========================================================
# 7) Execute tool calls requested by the model through MCP
#    and append proper "tool" messages back into chat history
# =========================================================
async def execute_tool_calls_via_mcp(
    session: ClientSession,
    assistant_message: Any,
    messages: list[dict[str, Any]],
) -> None:
    """
    Reads tool_calls from the assistant message, executes them against the local MCP server,
    and appends tool result messages to the conversation history.
    """
    tool_calls = assistant_message.tool_calls or []

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        print(f"[LLM] Requested tool: {tool_name} with args: {tool_args}")

        mcp_result = await session.call_tool(tool_name, arguments=tool_args)
        tool_output_text = mcp_result_to_text(mcp_result)

        print(f"[MCP] Result for '{tool_name}':\n{tool_output_text}\n")

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output_text,
            }
        )


# =========================================================
# 8) Main orchestration flow
#
#    End-to-end behavior:
#    1. Connect to local MCP server
#    2. Discover tools from MCP
#    3. Convert them to OpenAI chat tools
#    4. Ask the model to solve the prompt
#    5. If the model requests tools, execute them locally via MCP
#    6. Append tool outputs as "tool" messages
#    7. Call the model again until it stops asking for tools
# =========================================================
async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[MCP] Connected to local MCP server.")

            # -------------------------------------------------
            # Step A: Discover tools from MCP server
            # -------------------------------------------------
            tools_response = await session.list_tools()

            print("[MCP] Available tools:")
            for tool in tools_response.tools:
                print(f" - {tool.name}: {tool.description}")

            openai_tools = [
                convert_mcp_tool_to_openai_function(tool)
                for tool in tools_response.tools
            ]

            # -------------------------------------------------
            # Step B: Initial conversation history
            # -------------------------------------------------
            messages: list[dict[str, Any]] = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Use tools when needed."
                },
                {
                    "role": "user",
                    "content": (
                        "Add 25 and 17, then build a pyramid with base 5, "
                        "and finally explain the results."
                    )
                },
            ]

            # -------------------------------------------------
            # Step C: Tool-calling loop using Chat Completions
            # -------------------------------------------------
            while True:
                completion = client.chat.completions.create(
                    model=OPENAI_MODEL_NAME,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )

                assistant_message = completion.choices[0].message

                # Add the assistant response to conversation history
                assistant_dict: dict[str, Any] = {
                    "role": "assistant",
                    "content": assistant_message.content or "",
                }

                if assistant_message.tool_calls:
                    assistant_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ]

                messages.append(assistant_dict)

                # If there are no tool calls, we are done
                if not assistant_message.tool_calls:
                    print("[LLM] Final answer:")
                    print(assistant_message.content)
                    break

                # Execute the requested tools via MCP
                await execute_tool_calls_via_mcp(session, assistant_message, messages)


# =========================================================
# 9) Script entry point
# =========================================================
if __name__ == "__main__":
    asyncio.run(run())