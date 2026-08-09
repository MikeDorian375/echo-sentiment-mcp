# Echo Sentiment — MCP Server (XLM Market Sentiment)

A Model Context Protocol (MCP) server that exposes real-time XLM (Stellar)
market sentiment as a tool, computed from a **keyless composite**:

- Crypto Fear & Greed Index (public API, no key)
- Stellar SDEX order-flow imbalance (public order book)
- 24h price momentum (CoinGecko public API)

**No LLM in the loop, no API keys, no paid data feeds.** Rules + math only.

## Hosted endpoint (pay-per-call via x402)

Prefer using it rather than self-hosting? The same tool runs live at:

```
https://abstain-eliminate-unison.ngrok-free.dev/mcp
```

The full REST API behind it also offers `/v1/sentiment`, `/v1/quote`,
`/v1/arb-opportunities`, `/v1/multi-asset` and a premium
`/v1/sentiment-report`, all pay-per-call in USDC on Base via the
[x402 protocol](https://x402.org) (HTTP 402 → sign an EIP-3009 permit →
retry → 200). See [`/llms.txt`](https://abstain-eliminate-unison.ngrok-free.dev/llms.txt)
for the machine-readable summary.

## Tool

`get_xlm_sentiment` → JSON string:

```json
{
  "sentiment": -0.45,
  "sentiment_source": "FNG(30)+flow(-0.75)+mom(+0.39%)",
  "components": {"FNG(30)": -0.4, "flow(-0.75)": -0.75, "mom(+0.39%)": 0.078},
  "price_usd": 0.1619,
  "mid": 0.1620,
  "spread_pct": 0.09,
  "ts": 1786158508.1
}
```

`sentiment` is in [-1, 1]: positive = bullish, negative = bearish.

## Self-host

```bash
pip install -r requirements.txt
python mcp_bridge.py          # serves streamable HTTP MCP on 127.0.0.1:8010
```

Connect any MCP client (Claude Desktop, Cursor, custom agents) to
`http://127.0.0.1:8010/mcp` (or run it behind your own HTTPS).

**Agent-wallet ready**: agents that hold a wallet (e.g. MetaMask Agent
Wallet, GA Aug 2026) can pay per call with zero API keys — payment is the
auth, via the x402 protocol. Works with MetaMask's official
[`mcp-x402`](https://github.com/MetaMask/mcp-x402) header generator —
verified end-to-end on Base mainnet (Aug 8 2026): the raw V1 header their
server signs is accepted directly by this API via a server-side V1→V2
shim (no client-side remapping needed; settlement tx on-chain).

## Why

- **Rules-based**: deterministic scores, no model drift, cheap to run.
- **Keyless**: nothing to sign up for, nothing to leak.
- **Composite**: three independent signals weighted 0.3/0.4/0.3
  (configurable via `SENTIMENT_WEIGHT_*` env vars).

## License

MIT — see [LICENSE](LICENSE).
