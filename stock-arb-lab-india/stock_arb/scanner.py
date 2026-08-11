"""NSE↔BSE dislocation detection with the full equity charge stack.

Yahoo's free feed carries last-traded prices, not bid/ask, so the gross edge
here already overstates reality — the slippage allowance per leg stands in
for crossing each exchange's spread. That bias is documented, not hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .feeds import Quote


@dataclass
class ChargeStack:
    brokerage_bps: float   # per leg
    stt_sell_bps: float    # intraday STT, sell leg only
    stamp_buy_bps: float   # stamp duty, buy leg only
    other_bps: float       # exchange txn + SEBI fees + GST, per leg
    slippage_bps: float    # per leg; also stands in for the bid/ask spread

    @property
    def round_trip_bps(self) -> float:
        per_leg = self.brokerage_bps + self.other_bps + self.slippage_bps
        return 2 * per_leg + self.stt_sell_bps + self.stamp_buy_bps


@dataclass
class Opportunity:
    symbol: str
    buy_exchange: str
    buy_price: float
    sell_exchange: str
    sell_price: float
    gross_edge_bps: float
    net_edge_bps: float


def find_opportunities(
    quotes_by_exchange: Dict[str, List[Quote]],
    charges: ChargeStack,
) -> List[Opportunity]:
    by_symbol: Dict[str, List[Quote]] = {}
    for quotes in quotes_by_exchange.values():
        for q in quotes:
            by_symbol.setdefault(q.symbol, []).append(q)

    opportunities = []
    for symbol, quotes in by_symbol.items():
        if len(quotes) < 2:
            continue
        cheap = min(quotes, key=lambda q: q.last)
        rich = max(quotes, key=lambda q: q.last)
        if cheap.exchange == rich.exchange:
            continue
        gross_bps = (rich.last - cheap.last) / cheap.last * 10_000
        opportunities.append(
            Opportunity(
                symbol=symbol,
                buy_exchange=cheap.exchange,
                buy_price=cheap.last,
                sell_exchange=rich.exchange,
                sell_price=rich.last,
                gross_edge_bps=gross_bps,
                net_edge_bps=gross_bps - charges.round_trip_bps,
            )
        )
    opportunities.sort(key=lambda o: o.net_edge_bps, reverse=True)
    return opportunities
