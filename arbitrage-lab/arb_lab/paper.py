"""Paper broker: executes simulated round trips and keeps honest books.

No real orders are ever placed. Fills are assumed at the quoted price worsened
by the slippage allowance, with taker fees charged on both legs.
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .scanner import Opportunity


@dataclass
class Trade:
    ts: float
    symbol: str
    buy_exchange: str
    sell_exchange: str
    notional_usdt: float
    gross_edge_bps: float
    net_edge_bps: float
    pnl_usdt: float


@dataclass
class PaperBroker:
    capital_per_exchange: float
    fee_bps: float
    slippage_bps: float
    trades_csv: Path
    max_trade_fraction: float = 0.25  # of per-exchange capital, per trade
    trades: List[Trade] = field(default_factory=list)
    opportunities_seen: int = 0
    opportunities_net_positive: int = 0

    def __post_init__(self):
        if not self.trades_csv.exists():
            with self.trades_csv.open("w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp", "symbol", "buy_exchange", "sell_exchange",
                     "notional_usdt", "gross_edge_bps", "net_edge_bps", "pnl_usdt"]
                )

    def consider(self, opp: Opportunity, min_edge_bps: float) -> Trade | None:
        self.opportunities_seen += 1
        if opp.net_edge_bps <= 0:
            return None
        self.opportunities_net_positive += 1
        if opp.net_edge_bps < min_edge_bps:
            return None

        notional = self.capital_per_exchange * self.max_trade_fraction
        # Fill worse than the quote by the slippage allowance, fee on each leg.
        buy_fill = opp.buy_price * (1 + self.slippage_bps / 10_000)
        sell_fill = opp.sell_price * (1 - self.slippage_bps / 10_000)
        qty = notional / buy_fill
        cost = qty * buy_fill * (1 + self.fee_bps / 10_000)
        proceeds = qty * sell_fill * (1 - self.fee_bps / 10_000)
        trade = Trade(
            ts=time.time(),
            symbol=opp.symbol,
            buy_exchange=opp.buy_exchange,
            sell_exchange=opp.sell_exchange,
            notional_usdt=notional,
            gross_edge_bps=opp.gross_edge_bps,
            net_edge_bps=opp.net_edge_bps,
            pnl_usdt=proceeds - cost,
        )
        self.trades.append(trade)
        with self.trades_csv.open("a", newline="") as f:
            csv.writer(f).writerow(
                [f"{trade.ts:.3f}", trade.symbol, trade.buy_exchange, trade.sell_exchange,
                 f"{trade.notional_usdt:.2f}", f"{trade.gross_edge_bps:.2f}",
                 f"{trade.net_edge_bps:.2f}", f"{trade.pnl_usdt:.4f}"]
            )
        return trade

    @property
    def total_pnl(self) -> float:
        return sum(t.pnl_usdt for t in self.trades)

    def summary(self) -> str:
        survival = (
            f"{self.opportunities_net_positive}/{self.opportunities_seen}"
            if self.opportunities_seen else "0/0"
        )
        return (
            f"opportunities seen: {self.opportunities_seen} | "
            f"survived fees+slippage: {survival} | "
            f"paper trades: {len(self.trades)} | "
            f"simulated P&L: {self.total_pnl:+.4f} USDT"
        )
