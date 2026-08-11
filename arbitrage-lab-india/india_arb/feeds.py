"""Market data feeds for Indian exchanges, plus an offline demo generator.

All live feeds use public, unauthenticated endpoints — no API keys, no
accounts. Symbols are canonicalized as "BASE/INR", e.g. "BTC/INR". Endpoints
do change; every fetcher is called behind a try/except so one broken feed
never kills a scan.
"""

from __future__ import annotations

import json
import random
import time
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass
class Quote:
    exchange: str
    symbol: str
    bid: float
    ask: float
    ts: float


def _get_json(url: str, timeout: float = 8.0):
    req = urllib.request.Request(url, headers={"User-Agent": "india-arb-lab/0.1 (educational)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_coindcx(symbols: Iterable[str]) -> List[Quote]:
    wanted = {s.replace("/", ""): s for s in symbols}  # "BTCINR" -> "BTC/INR"
    quotes = []
    for row in _get_json("https://api.coindcx.com/exchange/ticker"):
        sym = wanted.get(row.get("market", ""))
        if sym and row.get("bid") and row.get("ask"):
            quotes.append(Quote("coindcx", sym, float(row["bid"]), float(row["ask"]), time.time()))
    return quotes


def fetch_wazirx(symbols: Iterable[str]) -> List[Quote]:
    wanted = {s.replace("/", "").lower(): s for s in symbols}  # "btcinr" -> "BTC/INR"
    data = _get_json("https://api.wazirx.com/api/v2/tickers")
    quotes = []
    for key, row in data.items():
        sym = wanted.get(key)
        if sym and row.get("buy") and row.get("sell"):
            quotes.append(Quote("wazirx", sym, float(row["buy"]), float(row["sell"]), time.time()))
    return quotes


def fetch_zebpay(symbols: Iterable[str]) -> List[Quote]:
    wanted = {s.replace("/", "-"): s for s in symbols}  # "BTC-INR" -> "BTC/INR"
    quotes = []
    for row in _get_json("https://www.zebapi.com/pro/v1/market"):
        sym = wanted.get(row.get("pair", ""))
        if sym and row.get("buy") and row.get("sell"):
            quotes.append(Quote("zebpay", sym, float(row["buy"]), float(row["sell"]), time.time()))
    return quotes


def fetch_bitbns(symbols: Iterable[str]) -> List[Quote]:
    # Bitbns keys its ticker by base asset; INR is the implied quote currency.
    wanted = {s.split("/")[0]: s for s in symbols if s.endswith("/INR")}
    data = _get_json("https://bitbns.com/order/getTickerWithVolume/")
    quotes = []
    for base, row in data.items():
        sym = wanted.get(base)
        if sym and row.get("highest_buy_bid") and row.get("lowest_sell_bid"):
            quotes.append(Quote("bitbns", sym, float(row["highest_buy_bid"]),
                                float(row["lowest_sell_bid"]), time.time()))
    return quotes


LIVE_FEEDS = {
    "coindcx": fetch_coindcx,
    "wazirx": fetch_wazirx,
    "zebpay": fetch_zebpay,
    "bitbns": fetch_bitbns,
}


def fetch_live(symbols: Iterable[str]) -> Dict[str, List[Quote]]:
    out: Dict[str, List[Quote]] = {}
    for name, fn in LIVE_FEEDS.items():
        try:
            out[name] = fn(symbols)
        except Exception as exc:  # noqa: BLE001 — one dead feed must not kill the scan
            print(f"  [warn] {name} feed failed: {exc}")
            out[name] = []
    return out


def fetch_global_btc_usdt() -> Optional[float]:
    """Binance BTC/USDT mid, for the India-premium display only."""
    try:
        row = _get_json("https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT")
        return (float(row["bidPrice"]) + float(row["askPrice"])) / 2
    except Exception:
        return None


class DemoFeed:
    """Synthetic INR quotes for offline runs.

    Indian books are thinner than global ones, so the demo uses wider spreads
    and slightly larger, more frequent dislocations than the global lab.
    """

    BASE_PRICES = {"BTC/INR": 6_850_000.0, "ETH/INR": 317_000.0, "SOL/INR": 16_700.0,
                   "XRP/INR": 55.0, "DOGE/INR": 20.0}
    EXCHANGES = ("coindcx", "wazirx", "zebpay", "bitbns")

    def __init__(self, symbols: Iterable[str], seed: int = 11):
        self.rng = random.Random(seed)
        self.mids = {s: self.BASE_PRICES.get(s, 1000.0) for s in symbols}
        self.global_btc_usdt = 78_000.0

    def fetch(self) -> Dict[str, List[Quote]]:
        now = time.time()
        self.global_btc_usdt *= 1 + self.rng.gauss(0, 0.0004)
        out: Dict[str, List[Quote]] = {ex: [] for ex in self.EXCHANGES}
        for sym, mid in self.mids.items():
            mid *= 1 + self.rng.gauss(0, 0.0005)
            self.mids[sym] = mid
            for ex in self.EXCHANGES:
                offset_bps = self.rng.gauss(0, 4)
                if self.rng.random() < 0.04:  # dislocations: larger, but so are the costs
                    offset_bps += self.rng.choice((-1, 1)) * self.rng.uniform(40, 140)
                ex_mid = mid * (1 + offset_bps / 10_000)
                half_spread = ex_mid * self.rng.uniform(2.0, 8.0) / 10_000
                out[ex].append(Quote(ex, sym, ex_mid - half_spread, ex_mid + half_spread, now))
        return out
