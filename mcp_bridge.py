"""MCP bridge — expose Echo Sentiment engine as an MCP tool (streamable HTTP).

Mounts into api_server.py at /mcp. MCP Hive (or any MCP client) calls
tools/list + tools/call against this endpoint. The engine is the same
keyless composite used by the x402 API (no LLM in the loop).
"""
import json
import time
from mcp.server.mcpserver import MCPServer
import signals

server = MCPServer("echo-sentiment", version="0.1.0",
                   instructions="Real-time XLM market sentiment from a keyless composite "
                                "(Fear & Greed + SDEX order-flow + 24h momentum) plus live price. "
                                "Returns JSON. No keys needed.")


def get_xlm_sentiment() -> str:
    book = signals.get_order_book()
    score, source, components = signals.get_sentiment_score(book)
    price = signals.get_xlm_price_usd()
    mid = None
    spread = None
    try:
        bid = book.get("best_bid")
        ask = book.get("best_ask")
        if bid is None and isinstance(book.get("bids"), (list, tuple)) and book["bids"]:
            bid = book["bids"][0][0] if isinstance(book["bids"][0], (list, tuple)) else book["bids"][0]
        if ask is None and isinstance(book.get("asks"), (list, tuple)) and book["asks"]:
            ask = book["asks"][0][0] if isinstance(book["asks"][0], (list, tuple)) else book["asks"][0]
        if bid is not None and ask is not None:
            bid, ask = float(bid), float(ask)
            mid = (bid + ask) / 2
            spread = (ask - bid) / mid * 100 if mid else None
    except Exception:
        pass
    return json.dumps({
        "sentiment": round(score, 4),
        "sentiment_source": source,
        "components": components,
        "price_usd": price,
        "mid": mid,
        "spread_pct": round(spread, 3) if spread is not None else None,
        "ts": time.time(),
    })


server.add_tool(
    get_xlm_sentiment,
    name="get_xlm_sentiment",
    description="Composite XLM market sentiment in [-1, 1] (positive = bullish), "
                "with per-component breakdown, live XLM price, and bid/ask spread. "
                "Output is a JSON string with keys: sentiment, sentiment_source, "
                "components, price_usd, mid, spread_pct, ts.",
)

mcp_app = server.streamable_http_app(streamable_http_path="/mcp")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp_app, host="127.0.0.1", port=8010, log_level="warning")
