"""Paper broker with Indian books: fees, slippage, TDS lockup, and 30% tax.

No real orders are ever placed. TDS is tracked as withheld working capital
(recoverable at ITR filing, not a fee), and the summary applies the flat
Section 115BBH tax to gains — with no loss offset, exactly as the law works.
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .scanner import Opportunity


@dataclass
class Trade:
    ts: float
    symbol: str
    buy_exchange: str
    sell_exchange: str
    notional_inr: float
    gross_edge_bps: float
    net_edge_bps: float
    pnl_inr: float          # before tax; excludes TDS (recoverable)
    tds_withheld_inr: float


@dataclass
class PaperBroker:
    capital_per_exchange: float
    fee_bps: float
    slippage_bps: float
    tds_bps: float
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
                     "gross_edge_bps", "net_edge_bps", "pnl_inr", "tds_withheld_inr"]
                )

    def consider(self, opp: Opportunity, min_edge_bps: float) -> Optional[Trade]:
        self.opportunities_seen += 1
        if opp.net_edge_bps <= 0:
            return None
        self.opportunities_net_positive += 1
        if opp.net_edge_bps < min_edge_bps:
            return None

        notional = self.capital_per_exchange * self.max_trade_fraction
        buy_fill = opp.buy_price * (1 + self.slippage_bps / 10_000)
        sell_fill = opp.sell_price * (1 - self.slippage_bps / 10_000)
        qty = notional / buy_fill
        cost = qty * buy_fill * (1 + self.fee_bps / 10_000)
        gross_proceeds = qty * sell_fill
        proceeds_after_fee = gross_proceeds * (1 - self.fee_bps / 10_000)
        tds = gross_proceeds * self.tds_bps / 10_000
        trade = Trade(
            ts=time.time(),
            symbol=opp.symbol,
            buy_exchange=opp.buy_exchange,
            sell_exchange=opp.sell_exchange,
            notional_inr=notional,
            gross_edge_bps=opp.gross_edge_bps,
            net_edge_bps=opp.net_edge_bps,
            pnl_inr=proceeds_after_fee - cost,
            tds_withheld_inr=tds,
        )
        self.trades.append(trade)
        with self.trades_csv.open("a", newline="") as f:
            csv.writer(f).writerow(
                [f"{trade.ts:.3f}", trade.symbol, trade.buy_exchange, trade.sell_exchange,
                 f"{trade.notional_inr:.2f}", f"{trade.gross_edge_bps:.2f}",
                 f"{trade.net_edge_bps:.2f}", f"{trade.pnl_inr:.2f}",
                 f"{trade.tds_withheld_inr:.2f}"]
            )
        return trade

    @property
    def pnl_before_tax(self) -> float:
        return sum(t.pnl_inr for t in self.trades)

    @property
    def tds_withheld(self) -> float:
        return sum(t.tds_withheld_inr for t in self.trades)

    @property
    def tax_on_gains(self) -> float:
        # Section 115BBH: 30% on gains, losses cannot offset — tax winners only.
        return sum(t.pnl_inr for t in self.trades if t.pnl_inr > 0) * self.tax_rate

    def summary(self) -> str:
        survival = (
            f"{self.opportunities_net_positive}/{self.opportunities_seen}"
            if self.opportunities_seen else "0/0"
        )
        return (
            f"opportunities seen: {self.opportunities_seen} | "
            f"survived fees+slippage: {survival} | "
            f"paper trades: {len(self.trades)} | "
            f"P&L before tax: ₹{self.pnl_before_tax:+,.2f}"
        )

    def tax_summary(self) -> List[str]:
        after_tax = self.pnl_before_tax - self.tax_on_gains
        return [
            f"P&L before tax:                    ₹{self.pnl_before_tax:+,.2f}",
            f"TDS withheld (locked until ITR):   ₹{self.tds_withheld:,.2f}",
            f"Tax @{self.tax_rate:.0%} on gains (no loss offset): ₹{self.tax_on_gains:,.2f}",
            f"After-tax P&L:                     ₹{after_tax:+,.2f}",
            f"Cash actually free right now:      ₹{after_tax - self.tds_withheld:+,.2f}",
        ]
