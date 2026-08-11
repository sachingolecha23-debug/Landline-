"""Quote feeds: delayed Yahoo Finance data for NSE/BSE, plus an offline demo.

There is no free real-time NSE/BSE feed. Yahoo's public chart endpoint serves
delayed quotes (~15 min) without authentication, which is honest enough for a
paper lab whose whole point is showing why delayed data can't arbitrage.
Symbols are plain NSE tickers ("RELIANCE"); the feed queries both listings
(RELIANCE.NS and RELIANCE.BO).
"""

from __future__ import annotations

import datetime
import json
import random
import time
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


@dataclass
class Quote:
    exchange: str   # "NSE" or "BSE"
    symbol: str     # "RELIANCE"
    last: float     # last traded price (delayed in live mode)
    quote_ts: Optional[float]  # exchange timestamp of the print, if known
    ts: float       # when we fetched it


def market_is_open(now: Optional[datetime.datetime] = None) -> bool:
    now = now or datetime.datetime.now(IST)
    if now.weekday() >= 5:  # Sat/Sun; exchange holidays not modeled
        return False
    minutes = now.hour * 60 + now.minute
    return 9 * 60 + 15 <= minutes <= 15 * 60 + 30


def _get_json(url: str, timeout: float = 8.0):
    req = urllib.request.Request(url, headers={"User-Agent": "stock-arb-lab/0.1 (educational)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_yahoo_last(ticker: str) -> Optional[tuple]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
    try:
        meta = _get_json(url)["chart"]["result"][0]["meta"]
        return float(meta["regularMarketPrice"]), float(meta.get("regularMarketTime") or 0) or None
    except Exception:
        return None


def fetch_live(symbols: Iterable[str]) -> Dict[str, List[Quote]]:
    out: Dict[str, List[Quote]] = {"NSE": [], "BSE": []}
    for sym in symbols:
        for exchange, suffix in (("NSE", ".NS"), ("BSE", ".BO")):
            got = _fetch_yahoo_last(sym + suffix)
            if got:
                last, quote_ts = got
                out[exchange].append(Quote(exchange, sym, last, quote_ts, time.time()))
            else:
                print(f"  [warn] no quote for {sym}{suffix}")
            time.sleep(0.2)  # be polite to the free endpoint
    return out


class DemoFeed:
    """Synthetic NSE/BSE prints for offline runs.

    Liquid Indian equities track each other across exchanges within a few
    basis points; dislocations are rarer and smaller than in crypto — and the
    occasional big one is modeled as a stale print, just like real life.
    """

    BASE_PRICES = {"RELIANCE": 2900.0, "TCS": 4200.0, "INFY": 1900.0,
                   "HDFCBANK": 1700.0, "SBIN": 850.0}

    def __init__(self, symbols: Iterable[str], seed: int = 21):
        self.rng = random.Random(seed)
        self.mids = {s: self.BASE_PRICES.get(s, 1000.0) for s in symbols}

    def fetch(self) -> Dict[str, List[Quote]]:
        now = time.time()
        out: Dict[str, List[Quote]] = {"NSE": [], "BSE": []}
        for sym, mid in self.mids.items():
            mid *= 1 + self.rng.gauss(0, 0.0003)
            self.mids[sym] = mid
            for exchange in ("NSE", "BSE"):
                offset_bps = self.rng.gauss(0, 1.5)
                if exchange == "BSE":
                    offset_bps += self.rng.gauss(0, 1.5)  # thinner book, noisier prints
                if self.rng.random() < 0.02:  # rare dislocation / stale print
                    offset_bps += self.rng.choice((-1, 1)) * self.rng.uniform(8, 30)
                out[exchange].append(
                    Quote(exchange, sym, mid * (1 + offset_bps / 10_000), now, now)
                )
        return out
