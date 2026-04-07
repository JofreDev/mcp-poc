# server.py
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Python_Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add an addition tool
@mcp.tool()
def createPyramid(base: int) -> str:
    """Build a pyramid with a variable base"""

    result = ""
    aux = ""
    decrease = base


    for i in range(base):
        for e in range(i+1):
            if e == 0:
                aux += " "*decrease + "*"
            elif e >= 1:
                aux += " " + "*"
        decrease -= 1
        result = result + aux + "\n"
        aux = ""
        

    return "\n"+result


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

# Add a dynamic greeting resource
@mcp.resource("greeting://person/{name}/age/{age}")
def get_custom_greeting(name: str, age: int) -> str:
    """Get greeting with name and age"""
    return f"Hello {name}, you are {age}!"
