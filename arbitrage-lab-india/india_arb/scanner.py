"""Cross-exchange arbitrage detection with the Indian cost stack.

Reports three edges per opportunity so nothing is hidden:
  gross            — the raw price gap the viral posts screenshot
  net              — after taker fees and slippage on both legs
  net_after_tds    — the cash-flow reality once 1% TDS is withheld on the sell
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .feeds import Quote


@dataclass
class Opportunity:
    symbol: str
    buy_exchange: str
    buy_price: float
    sell_exchange: str
    sell_price: float
    gross_edge_bps: float
    net_edge_bps: float
    net_after_tds_bps: float


def find_opportunities(
    quotes_by_exchange: Dict[str, List[Quote]],
    fee_bps: float,
    slippage_bps: float,
    tds_bps: float,
) -> List[Opportunity]:
    by_symbol: Dict[str, List[Quote]] = {}
    for quotes in quotes_by_exchange.values():
        for q in quotes:
            by_symbol.setdefault(q.symbol, []).append(q)

    round_trip_cost_bps = 2 * (fee_bps + slippage_bps)
    opportunities = []
    for symbol, quotes in by_symbol.items():
        if len(quotes) < 2:
            continue
        cheapest = min(quotes, key=lambda q: q.ask)
        richest = max(quotes, key=lambda q: q.bid)
        if cheapest.exchange == richest.exchange:
            continue
        gross_bps = (richest.bid - cheapest.ask) / cheapest.ask * 10_000
        net_bps = gross_bps - round_trip_cost_bps
        opportunities.append(
            Opportunity(
                symbol=symbol,
                buy_exchange=cheapest.exchange,
                buy_price=cheapest.ask,
                sell_exchange=richest.exchange,
                sell_price=richest.bid,
                gross_edge_bps=gross_bps,
                net_edge_bps=net_bps,
                net_after_tds_bps=net_bps - tds_bps,
            )
        )
    opportunities.sort(key=lambda o: o.net_edge_bps, reverse=True)
    return opportunities
