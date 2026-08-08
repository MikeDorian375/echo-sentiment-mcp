"""Configuration for the XLM paper-trading agent.

All values overridable via environment variables (no secrets in code).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"

# --- Markets ---
SYMBOL = "XLM"
QUOTE = "USDC"
# Mainnet USDC issuer (Centaurus/Stellar USDC). Used only for order-book reads in paper mode.
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"
HORIZON = os.environ.get("HORIZON_URL", "https://horizon.stellar.org")
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=stellar&vs_currencies=usd"

# --- Virtual wallet (paper only) ---
INITIAL_QUOTE = float(os.environ.get("INITIAL_USDC", "1000.0"))

# --- Strategy (deterministic rules; LLM/sentiment only scores, rules move money) ---
BUY_THRESHOLD = float(os.environ.get("BUY_THRESHOLD", "0.25"))      # sentiment >= this -> buy
SELL_THRESHOLD = float(os.environ.get("SELL_THRESHOLD", "-0.2"))    # sentiment <= this -> sell
POSITION_PCT = float(os.environ.get("POSITION_PCT", "0.5"))         # max % of quote per buy
STOP_LOSS_PCT = float(os.environ.get("STOP_LOSS_PCT", "0.08"))      # sell if price drops 8% below entry
COOLDOWN_MIN = float(os.environ.get("COOLDOWN_MIN", "30"))          # min minutes between trades
SLIPPAGE_BPS = float(os.environ.get("SLIPPAGE_BPS", "25"))          # simulated spread/slippage (0.25%)

# --- Loop ---
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "300"))

# --- Sentiment composite (all keyless; weights must sum to 1.0) ---
SENTIMENT_WEIGHT_FNG = float(os.environ.get("SENTIMENT_WEIGHT_FNG", "0.3"))      # Fear & Greed
SENTIMENT_WEIGHT_FLOW = float(os.environ.get("SENTIMENT_WEIGHT_FLOW", "0.4"))    # SDEX order-flow imbalance
SENTIMENT_WEIGHT_MOMENTUM = float(os.environ.get("SENTIMENT_WEIGHT_MOMENTUM", "0.3"))  # 24h price momentum

# --- Arb scanner ---
KRAKEN_FEE_BPS = float(os.environ.get("KRAKEN_FEE_BPS", "26"))       # Kraken taker fee (0.26%)
ARB_MIN_NET_PCT = float(os.environ.get("ARB_MIN_NET_PCT", "0.5"))    # flag spreads >= this
ARB_WATCH_SECONDS = float(os.environ.get("ARB_WATCH_SECONDS", "60"))

# --- Future hook: MoltCanvas (platform currently offline, auto-detected). ---
MOLTCANVAS_API_KEY = os.environ.get("MOLTCANVAS_API_KEY", "")
