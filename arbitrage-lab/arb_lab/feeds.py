"""Market data feeds: live public tickers and an offline demo generator.

All live feeds use public, unauthenticated endpoints — no API keys and no
accounts. Symbols are canonicalized as "BASE/QUOTE", e.g. "BTC/USDT".
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class Quote:
    exchange: str
    symbol: str
    bid: float
    ask: float
    ts: float


def _get_json(url: str, timeout: float = 8.0):
    req = urllib.request.Request(url, headers={"User-Agent": "arb-lab/0.1 (educational)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_binance(symbols: Iterable[str]) -> List[Quote]:
    wanted = {s.replace("/", ""): s for s in symbols}
    url = "https://api.binance.com/api/v3/ticker/bookTicker?symbols=" + urllib.parse.quote(
        json.dumps(list(wanted), separators=(",", ":"))
    )
    now = time.time()
    quotes = []
    for row in _get_json(url):
        sym = wanted.get(row["symbol"])
        if sym:
            quotes.append(Quote("binance", sym, float(row["bidPrice"]), float(row["askPrice"]), now))
    return quotes


def fetch_kraken(symbols: Iterable[str]) -> List[Quote]:
    # Kraken uses XBT for BTC and echoes pair names in its own format, so we
    # request one canonical name at a time and keep the mapping ourselves.
    quotes = []
    for sym in symbols:
        base, quote = sym.split("/")
        pair = ("XBT" if base == "BTC" else base) + quote
        try:
            data = _get_json(f"https://api.kraken.com/0/public/Ticker?pair={pair}")
        except urllib.error.HTTPError:
            continue
        if data.get("error"):
            continue
        for payload in data.get("result", {}).values():
            quotes.append(Quote("kraken", sym, float(payload["b"][0]), float(payload["a"][0]), time.time()))
    return quotes


def fetch_coinbase(symbols: Iterable[str]) -> List[Quote]:
    quotes = []
    for sym in symbols:
        product = sym.replace("/", "-")
        try:
            data = _get_json(f"https://api.exchange.coinbase.com/products/{product}/ticker")
        except urllib.error.HTTPError:
            continue  # product not listed on Coinbase
        if "bid" in data and "ask" in data:
            quotes.append(Quote("coinbase", sym, float(data["bid"]), float(data["ask"]), time.time()))
    return quotes


LIVE_FEEDS = {
    "binance": fetch_binance,
    "kraken": fetch_kraken,
    "coinbase": fetch_coinbase,
}


def fetch_live(symbols: Iterable[str]) -> Dict[str, List[Quote]]:
    """Fetch all live feeds, tolerating individual exchange failures."""
    out: Dict[str, List[Quote]] = {}
    for name, fn in LIVE_FEEDS.items():
        try:
            out[name] = fn(symbols)
        except Exception as exc:  # noqa: BLE001 — one dead feed must not kill the scan
            print(f"  [warn] {name} feed failed: {exc}")
            out[name] = []
    return out


class DemoFeed:
    """Synthetic quotes for offline runs.

    Each exchange quotes a shared random-walk mid price with its own small
    offset and spread; occasionally one exchange dislocates by a few basis
    points so the scanner and paper broker have something to react to.
    """

    BASE_PRICES = {"BTC/USDT": 78000.0, "ETH/USDT": 3600.0, "SOL/USDT": 190.0,
                   "XRP/USDT": 0.62, "LTC/USDT": 88.0}
    EXCHANGES = ("binance", "kraken", "coinbase")

    def __init__(self, symbols: Iterable[str], seed: int = 7):
        self.rng = random.Random(seed)
        self.mids = {s: self.BASE_PRICES.get(s, 100.0) for s in symbols}

    def fetch(self) -> Dict[str, List[Quote]]:
        now = time.time()
        out: Dict[str, List[Quote]] = {ex: [] for ex in self.EXCHANGES}
        for sym, mid in self.mids.items():
            mid *= 1 + self.rng.gauss(0, 0.0004)
            self.mids[sym] = mid
            for ex in self.EXCHANGES:
                offset_bps = self.rng.gauss(0, 2)
                if self.rng.random() < 0.03:  # occasional dislocation
                    offset_bps += self.rng.choice((-1, 1)) * self.rng.uniform(25, 60)
                ex_mid = mid * (1 + offset_bps / 10_000)
                half_spread = ex_mid * self.rng.uniform(0.5, 2.0) / 10_000
                out[ex].append(Quote(ex, sym, ex_mid - half_spread, ex_mid + half_spread, now))
        return out
