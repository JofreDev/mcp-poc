from pathlib import Path
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

## for loading environment variables from .env file
import os
from dotenv import load_dotenv

load_dotenv()


API_KEY = os.getenv("API_KEY")
BASE_DIR = Path(__file__).resolve().parent
SERVER_PATH = (BASE_DIR / "../mcp-server-python/server.py").resolve()


# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="mcp",  # Executable
    args=["run", str(SERVER_PATH)],  # Optional command line arguments
    env=None,  # Optional environment variables
)



async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # Initialize the connection
            await session.initialize() 
            # List available resources
            resources_result = await session.list_resources()
            print("LISTING RESOURCES")
            for resource in resources_result.resources:
            
        
                print("Resource:", resource)

            # List available tools
            tools = await session.list_tools()
            print("LISTING TOOLS")
            for tool in tools.tools:
                print("Tool: ", tool.name)

            # Read a resource
            print("READING RESOURCE")
            content, mime_type = await session.read_resource("greeting://hello")

            # Call a tool
            print("CALL TOOL 1 ")
            result = await session.call_tool("add", arguments={"a": 1, "b": 7})
            print(result.content)

            print("CALL TOOL 2 ")
            result = await session.call_tool("createPyramid", arguments={"base": 10})
            for content in result.content:
                if content.type == "text":
                    print(content.text)
                else:
                    print(content)



if __name__ == "__main__":
    import asyncio

    asyncio.run(run())