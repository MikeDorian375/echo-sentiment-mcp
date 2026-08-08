"""Signal layer: market data (Stellar + CoinGecko) and sentiment (composite of live sources).

Sentiment composite — all keyless, all verified alive 2026-08-07:
  - Fear & Greed Index         (crypto market mood, alternative.me)
  - SDEX order-book imbalance  (bid vs ask depth — money voting with real order flow)
  - XLM 24h price momentum     (CoinGecko)

MoltCanvas (agent visual diary) and Moltbook (agent social) remain optional future
components: they are probed for availability and would be added as extra weights when
their APIs come back online. If every composite source is down, a clearly-labeled MOCK
feed keeps the machinery honest.
"""
import math
import time

import requests

import config

FNG_URL = "https://api.alternative.me/fng/?limit=1"

# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------

def get_xlm_price_usd() -> float | None:
    """Current XLM/USD price from CoinGecko (free, no key)."""
    try:
        r = requests.get(config.COINGECKO_PRICE_URL, timeout=10)
        r.raise_for_status()
        return float(r.json()["stellar"]["usd"])
    except Exception as e:  # noqa: BLE001
        print(f"  [signals] CoinGecko failed: {e}")
        return None


def get_order_book() -> dict:
    """Best bid/ask + depth on SDEX XLM/USDC from Horizon."""
    url = (
        f"{config.HORIZON}/order_book"
        f"?selling_asset_type=native"
        f"&buying_asset_type=credit_alphanum4"
        f"&buying_asset_code={config.QUOTE}"
        f"&buying_asset_issuer={config.USDC_ISSUER}"
        f"&limit=10"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        bids = data.get("bids", [])   # people buying XLM with USDC
        asks = data.get("asks", [])   # people selling XLM for USDC
        bid = float(bids[0]["price"]) if bids else None
        ask = float(asks[0]["price"]) if asks else None
        bid_depth = sum(float(b["amount"]) for b in bids)
        ask_depth = sum(float(a["amount"]) for a in asks)
        mid = (bid + ask) / 2 if bid and ask else None
        spread = ((ask - bid) / mid) if mid else None
        return {"bid": bid, "ask": ask, "mid": mid, "spread": spread,
                "bid_depth": bid_depth, "ask_depth": ask_depth}
    except Exception as e:  # noqa: BLE001
        print(f"  [signals] Horizon order book failed: {e}")
        return {"bid": None, "ask": None, "mid": None, "spread": None,
                "bid_depth": None, "ask_depth": None}


# ---------------------------------------------------------------------------
# MoltCanvas availability (platform flaky/offline — watch for return)
# ---------------------------------------------------------------------------

MOLTCANVAS_HOSTS = [
    "https://moltcanvas.app",
    "https://api.moltcanvas.app",
    "https://moltcanvas-production.up.railway.app",
]


def check_moltcanvas_available() -> bool:
    """True if any known MoltCanvas host responds with a real app (HTTP 200).

    Railway returns 404 "Application not found" when the service is gone;
    DNS failures are caught below. Only a live app counts as available.
    """
    for host in MOLTCANVAS_HOSTS:
        try:
            r = requests.get(host, timeout=8)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            continue
    return False


# ---------------------------------------------------------------------------
# Sentiment composite
# ---------------------------------------------------------------------------

class _MockSentiment:
    """Seeded random-walk stand-in so the machinery can be exercised.

    Clearly labeled as MOCK everywhere it surfaces. Only used when EVERY
    composite source is unreachable.
    """

    def __init__(self):
        self._seed = int(time.time()) // 300  # changes every 5 min
        self._t = 0

    def score(self) -> float:
        self._t += 1
        x = math.sin(self._seed + self._t * 1.7) * math.sin(self._seed * 0.31 + self._t)
        return max(-1.0, min(1.0, x))


def get_fear_greed() -> tuple[float | None, str]:
    """Crypto Fear & Greed Index (0-100) mapped to [-1, 1]. No key needed."""
    try:
        r = requests.get(FNG_URL, timeout=10)
        r.raise_for_status()
        value = float(r.json()["data"][0]["value"])
        return (value - 50) / 50, f"FNG({value:.0f})"
    except Exception as e:  # noqa: BLE001
        print(f"  [signals] FNG failed: {e}")
        return None, "FNG(down)"


def get_order_flow(book: dict) -> tuple[float | None, str]:
    """Order-book imbalance in [-1, 1]: (bid_depth - ask_depth) / (bid_depth + ask_depth).

    Positive = more XLM buy demand on the book; negative = more sell supply.
    """
    b, a = book.get("bid_depth"), book.get("ask_depth")
    if b is None or a is None or (b + a) <= 0:
        return None, "flow(down)"
    imbalance = (b - a) / (b + a)
    return imbalance, f"flow({imbalance:+.2f})"


def get_momentum() -> tuple[float | None, str]:
    """24h price change scaled to [-1, 1]: a +/-5% daily move = full score."""
    try:
        r = requests.get(config.COINGECKO_PRICE_URL + "&include_24hr_change=true", timeout=10)
        r.raise_for_status()
        chg = float(r.json()["stellar"]["usd_24h_change"])
        return max(-1.0, min(1.0, chg / 5.0)), f"mom({chg:+.2f}%)"
    except Exception as e:  # noqa: BLE001
        print(f"  [signals] momentum failed: {e}")
        return None, "mom(down)"


def get_sentiment_score(book: dict) -> tuple[float, str, dict]:
    """Composite sentiment in [-1, 1] from all live sources.

    Returns (score, source_label, components). MOCK only if every source is down.
    Weights are configurable (SENTIMENT_WEIGHT_*).
    """
    candidates = [
        (config.SENTIMENT_WEIGHT_FNG, *get_fear_greed()),
        (config.SENTIMENT_WEIGHT_FLOW, *get_order_flow(book)),
        (config.SENTIMENT_WEIGHT_MOMENTUM, *get_momentum()),
    ]
    live = [(w, v, label) for w, v, label in candidates if v is not None]
    if not live:
        score = _MockSentiment().score()
        return score, "MOCK (all sources down)", {}

    total_w = sum(w for w, _, _ in live)
    score = sum(w * v for w, v, _ in live) / total_w
    source = "+".join(label for _, _, label in live)
    components = {label: round(v, 3) for _, v, label in live}
    return score, source, components


# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------

def collect_signal() -> dict:
    """Gather everything the strategy needs in one shot."""
    print("  [signals] collecting...")
    price = get_xlm_price_usd()
    book = get_order_book()
    sentiment, src, components = get_sentiment_score(book)
    return {
        "ts": time.time(),
        "price_usd": price,
        "mid": book.get("mid"),
        "spread": book.get("spread"),
        "bid_depth": book.get("bid_depth"),
        "ask_depth": book.get("ask_depth"),
        "sentiment": sentiment,
        "sentiment_source": src,
        "sentiment_components": components,
    }


def signal_summary(s: dict) -> str:
    comps = " ".join(f"{k}={v:+.2f}" for k, v in s.get("sentiment_components", {}).items())
    return (
        f"XLM ${s['price_usd']:.4f} | mid ${s['mid']:.6f} (spread {s['spread']*100:.2f}%) "
        f"| sentiment {s['sentiment']:+.2f} [{s['sentiment_source']} {comps}]"
    )
