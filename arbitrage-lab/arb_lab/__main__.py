"""CLI entry point: python3 -m arb_lab --mode live|demo"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from .feeds import DemoFeed, fetch_live
from .paper import PaperBroker
from .scanner import find_opportunities

DISCLAIMER = (
    "Arbitrage Lab — PAPER TRADING ONLY. No real orders are placed, no keys, "
    "no funds. Educational; not financial advice."
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="arb_lab", description=DISCLAIMER)
    p.add_argument("--mode", choices=("live", "demo"), default="live")
    p.add_argument("--symbols", default="BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT,LTC/USDT")
    p.add_argument("--interval", type=float, default=2.0, help="seconds between scans")
    p.add_argument("--duration", type=float, default=60, help="run time in seconds; 0 = until Ctrl-C")
    p.add_argument("--capital", type=float, default=1000, help="simulated USDT per exchange")
    p.add_argument("--fee-bps", type=float, default=10, help="taker fee per leg (basis points)")
    p.add_argument("--slippage-bps", type=float, default=5, help="slippage allowance per leg (bps)")
    p.add_argument("--min-edge-bps", type=float, default=1, help="minimum net edge to paper-trade")
    p.add_argument("--trades-csv", default="trades.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    print(DISCLAIMER)
    print(f"mode={args.mode} symbols={','.join(symbols)} fee={args.fee_bps}bps/leg "
          f"slippage={args.slippage_bps}bps/leg min-net-edge={args.min_edge_bps}bps\n")

    demo = DemoFeed(symbols) if args.mode == "demo" else None
    broker = PaperBroker(
        capital_per_exchange=args.capital,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        trades_csv=Path(args.trades_csv),
    )

    started = time.time()
    scan = 0
    try:
        while not args.duration or time.time() - started < args.duration:
            scan += 1
            quotes = demo.fetch() if demo else fetch_live(symbols)
            best_gross = 0.0
            for opp in find_opportunities(quotes, args.fee_bps, args.slippage_bps):
                best_gross = max(best_gross, opp.gross_edge_bps)
                trade = broker.consider(opp, args.min_edge_bps)
                if trade:
                    print(f"  PAPER TRADE {trade.symbol}: buy {trade.buy_exchange} / "
                          f"sell {trade.sell_exchange} | gross {trade.gross_edge_bps:.1f}bps "
                          f"net {trade.net_edge_bps:.1f}bps | P&L {trade.pnl_usdt:+.4f} USDT")
            if scan % 10 == 0:
                print(f"[scan {scan}] best gross edge this scan: {best_gross:.1f}bps | {broker.summary()}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass

    elapsed = time.time() - started
    print(f"\n=== Session summary ({elapsed:.0f}s, {scan} scans) ===")
    print(broker.summary())
    if broker.trades:
        rate = broker.total_pnl / args.capital * 100
        print(f"return on one exchange's simulated capital: {rate:+.3f}%")
    print("Compare that to the viral post's claims — this is what the math actually allows.")


if __name__ == "__main__":
    main()
