"""Paper broker for intraday NSE↔BSE round trips. No real orders, ever.

Intraday equity profits are speculative business income taxed at slab rate;
unlike crypto's s.115BBH, intraday losses DO offset intraday gains, so the
summary taxes the net (not just the winners).
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .scanner import ChargeStack, Opportunity


@dataclass
class Trade:
    ts: float
    symbol: str
    buy_exchange: str
    sell_exchange: str
    notional_inr: float
    gross_edge_bps: float
    net_edge_bps: float
    charges_inr: float
    pnl_inr: float


@dataclass
class PaperBroker:
    capital_per_exchange: float
    charges: ChargeStack
    tax_rate: float
    trades_csv: Path
    max_trade_fraction: float = 0.25
    trades: List[Trade] = field(default_factory=list)
    opportunities_seen: int = 0
    opportunities_net_positive: int = 0

    def __post_init__(self):
        if not self.trades_csv.exists():
            with self.trades_csv.open("w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp", "symbol", "buy_exchange", "sell_exchange", "notional_inr",
                     "gross_edge_bps", "net_edge_bps", "charges_inr", "pnl_inr"]
                )

    def consider(self, opp: Opportunity, min_edge_bps: float) -> Optional[Trade]:
        self.opportunities_seen += 1
        if opp.net_edge_bps <= 0:
            return None
        self.opportunities_net_positive += 1
        if opp.net_edge_bps < min_edge_bps:
            return None

        c = self.charges
        notional = self.capital_per_exchange * self.max_trade_fraction
        buy_fill = opp.buy_price * (1 + c.slippage_bps / 10_000)
        sell_fill = opp.sell_price * (1 - c.slippage_bps / 10_000)
        qty = notional / buy_fill
        buy_value, sell_value = qty * buy_fill, qty * sell_fill
        charges_inr = (
            buy_value * (c.brokerage_bps + c.other_bps + c.stamp_buy_bps) / 10_000
            + sell_value * (c.brokerage_bps + c.other_bps + c.stt_sell_bps) / 10_000
        )
        trade = Trade(
            ts=time.time(),
            symbol=opp.symbol,
            buy_exchange=opp.buy_exchange,
            sell_exchange=opp.sell_exchange,
            notional_inr=notional,
            gross_edge_bps=opp.gross_edge_bps,
            net_edge_bps=opp.net_edge_bps,
            charges_inr=charges_inr,
            pnl_inr=sell_value - buy_value - charges_inr,
        )
        self.trades.append(trade)
        with self.trades_csv.open("a", newline="") as f:
            csv.writer(f).writerow(
                [f"{trade.ts:.3f}", trade.symbol, trade.buy_exchange, trade.sell_exchange,
                 f"{trade.notional_inr:.2f}", f"{trade.gross_edge_bps:.2f}",
                 f"{trade.net_edge_bps:.2f}", f"{trade.charges_inr:.2f}", f"{trade.pnl_inr:.2f}"]
            )
        return trade

    @property
    def pnl_before_tax(self) -> float:
        return sum(t.pnl_inr for t in self.trades)

    @property
    def total_charges(self) -> float:
        return sum(t.charges_inr for t in self.trades)

    @property
    def tax(self) -> float:
        # Speculative business income: slab rate on the NET (losses offset gains).
        return max(self.pnl_before_tax, 0.0) * self.tax_rate

    def summary(self) -> str:
        survival = (
            f"{self.opportunities_net_positive}/{self.opportunities_seen}"
            if self.opportunities_seen else "0/0"
        )
        return (
            f"opportunities seen: {self.opportunities_seen} | "
            f"survived charges: {survival} | "
            f"paper trades: {len(self.trades)} | "
            f"P&L before tax: ₹{self.pnl_before_tax:+,.2f}"
        )

    def tax_summary(self) -> List[str]:
        return [
            f"Charges paid (STT, stamp, brokerage, fees): ₹{self.total_charges:,.2f}",
            f"P&L before tax:                             ₹{self.pnl_before_tax:+,.2f}",
            f"Tax @{self.tax_rate:.0%} slab on net intraday gains:      ₹{self.tax:,.2f}",
            f"After-tax P&L:                              ₹{self.pnl_before_tax - self.tax:+,.2f}",
        ]
