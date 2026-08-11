"""CLI entry point: python3 -m stock_arb --mode live|demo"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from .feeds import DemoFeed, fetch_live, market_is_open
from .paper import PaperBroker
from .scanner import ChargeStack, find_opportunities

DISCLAIMER = (
    "Stock Arb Lab (India) — PAPER TRADING ONLY. No broker account, no orders, no funds. "
    "Live data is ~15-min delayed Yahoo quotes. Educational; not investment or tax advice. "
    "Automated live trading requires SEBI/exchange-compliant algo registration via a broker."
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="stock_arb", description=DISCLAIMER)
    p.add_argument("--mode", choices=("live", "demo"), default="live")
    p.add_argument("--symbols", default="RELIANCE,TCS,INFY,HDFCBANK,SBIN")
    p.add_argument("--interval", type=float, default=None,
                   help="seconds between scans (default: 60 live, 1 demo)")
    p.add_argument("--duration", type=float, default=300, help="run time in seconds; 0 = until Ctrl-C")
    p.add_argument("--capital", type=float, default=100_000, help="simulated INR per exchange")
    p.add_argument("--brokerage-bps", type=float, default=2, help="brokerage per leg (bps)")
    p.add_argument("--stt-sell-bps", type=float, default=2.5, help="intraday STT on sell (bps)")
    p.add_argument("--stamp-buy-bps", type=float, default=0.3, help="stamp duty on buy (bps)")
    p.add_argument("--other-bps", type=float, default=0.5, help="exchange+SEBI+GST per leg (bps)")
    p.add_argument("--slippage-bps", type=float, default=5, help="slippage per leg (bps)")
    p.add_argument("--tax-rate", type=float, default=0.30, help="slab rate on net intraday gains")
    p.add_argument("--min-edge-bps", type=float, default=1, help="minimum net edge to paper-trade")
    p.add_argument("--trades-csv", default="trades_stocks.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    interval = args.interval if args.interval is not None else (1.0 if args.mode == "demo" else 60.0)
    charges = ChargeStack(
        brokerage_bps=args.brokerage_bps,
        stt_sell_bps=args.stt_sell_bps,
        stamp_buy_bps=args.stamp_buy_bps,
        other_bps=args.other_bps,
        slippage_bps=args.slippage_bps,
    )
    print(DISCLAIMER)
    print(f"\nmode={args.mode} symbols={','.join(symbols)} | round-trip cost: "
          f"{charges.round_trip_bps:.1f}bps (brokerage {args.brokerage_bps}x2 + STT {args.stt_sell_bps} "
          f"+ stamp {args.stamp_buy_bps} + other {args.other_bps}x2 + slippage {args.slippage_bps}x2)\n")
    if args.mode == "live" and not market_is_open():
        print("NOTE: Indian market is CLOSED (9:15-15:30 IST, Mon-Fri). "
              "Quotes will be frozen at the last session's prints; gaps you see are not tradeable.\n")

    demo = DemoFeed(symbols) if args.mode == "demo" else None
    broker = PaperBroker(
        capital_per_exchange=args.capital,
        charges=charges,
        tax_rate=args.tax_rate,
        trades_csv=Path(args.trades_csv),
    )

    started = time.time()
    scan = 0
    try:
        while not args.duration or time.time() - started < args.duration:
            scan += 1
            quotes = demo.fetch() if demo else fetch_live(symbols)
            best_gross = 0.0
            for opp in find_opportunities(quotes, charges):
                best_gross = max(best_gross, opp.gross_edge_bps)
                trade = broker.consider(opp, args.min_edge_bps)
                if trade:
                    print(f"  PAPER TRADE {trade.symbol}: buy {trade.buy_exchange} / "
                          f"sell {trade.sell_exchange} | gross {trade.gross_edge_bps:.1f}bps "
                          f"net {trade.net_edge_bps:.1f}bps | charges ₹{trade.charges_inr:.2f} "
                          f"| P&L ₹{trade.pnl_inr:+.2f}")
            if scan % 10 == 0:
                print(f"[scan {scan}] best gross NSE-BSE gap: {best_gross:.1f}bps | {broker.summary()}")
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    elapsed = time.time() - started
    print(f"\n=== Session summary ({elapsed:.0f}s, {scan} scans) ===")
    print(broker.summary())
    print("\n--- Charges and tax reality ---")
    for line in broker.tax_summary():
        print(f"  {line}")
    print("\nRemember: live quotes were ~15 minutes old, and the biggest 'gaps' are "
          "usually one exchange's stale print. The desks that really do this are "
          "co-located at the exchange. This is why the lab trades paper.")


if __name__ == "__main__":
    main()
