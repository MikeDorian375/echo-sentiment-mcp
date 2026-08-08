"""Minimal MCP client example — connect to the hosted sentiment server.

Usage:
    python client_call.py [mcp_url]

Default URL is the hosted endpoint. Requires: pip install mcp
"""
import asyncio
import json
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "https://abstain-eliminate-unison.ngrok-free.dev/mcp"


async def main():
    from mcp.client.client import Client

    async with Client(URL) as session:
        tools = await session.list_tools()
        print("tools:", [t.name for t in (tools.tools if hasattr(tools, "tools") else tools)])

        result = await session.call_tool("get_xlm_sentiment", {})
        content = getattr(result, "content", None) or result[0].content
        data = json.loads(content[0].text)
        print(f"sentiment: {data['sentiment']:+.4f}")
        print(f"price:     ${data['price_usd']}")
        print(f"source:    {data['sentiment_source']}")


if __name__ == "__main__":
    asyncio.run(main())
