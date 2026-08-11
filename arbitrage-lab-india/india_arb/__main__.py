"""CLI entry point: python3 -m india_arb --mode live|demo"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from .feeds import DemoFeed, fetch_global_btc_usdt, fetch_live
from .paper import PaperBroker
from .scanner import find_opportunities

DISCLAIMER = (
    "Arbitrage Lab (India) — PAPER TRADING ONLY. No real orders, no keys, no funds. "
    "Educational; not investment or tax advice. Consult a CA before trading VDAs."
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="india_arb", description=DISCLAIMER)
    p.add_argument("--mode", choices=("live", "demo"), default="live")
    p.add_argument("--symbols", default="BTC/INR,ETH/INR,SOL/INR,XRP/INR,DOGE/INR")
    p.add_argument("--interval", type=float, default=3.0, help="seconds between scans")
    p.add_argument("--duration", type=float, default=60, help="run time in seconds; 0 = until Ctrl-C")
    p.add_argument("--capital", type=float, default=100_000, help="simulated INR per exchange")
    p.add_argument("--fee-bps", type=float, default=45, help="taker fee per leg (basis points)")
    p.add_argument("--slippage-bps", type=float, default=10, help="slippage allowance per leg (bps)")
    p.add_argument("--tds-bps", type=float, default=100, help="TDS on sell proceeds (100 = 1%%, s.194S)")
    p.add_argument("--tax-rate", type=float, default=0.30, help="flat tax on gains (s.115BBH)")
    p.add_argument("--min-edge-bps", type=float, default=1, help="minimum net edge to paper-trade")
    p.add_argument("--usdinr", type=float, default=88.0, help="USD/INR rate for premium display")
    p.add_argument("--no-premium", action="store_true", help="skip India-premium check vs Binance")
    p.add_argument("--trades-csv", default="trades_inr.csv")
    return p.parse_args()


def india_premium_bps(inr_btc_mid: float, usdt_btc_mid: float, usdinr: float) -> float:
    implied_inr = usdt_btc_mid * usdinr
    return (inr_btc_mid - implied_inr) / implied_inr * 10_000


def main() -> None:
    args = parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    print(DISCLAIMER)
    print(f"mode={args.mode} symbols={','.join(symbols)} fee={args.fee_bps}bps/leg "
          f"slippage={args.slippage_bps}bps/leg TDS={args.tds_bps}bps on sells "
          f"tax={args.tax_rate:.0%} min-net-edge={args.min_edge_bps}bps\n")

    demo = DemoFeed(symbols) if args.mode == "demo" else None
    broker = PaperBroker(
        capital_per_exchange=args.capital,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        tds_bps=args.tds_bps,
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
            for opp in find_opportunities(quotes, args.fee_bps, args.slippage_bps, args.tds_bps):
                best_gross = max(best_gross, opp.gross_edge_bps)
                trade = broker.consider(opp, args.min_edge_bps)
                if trade:
                    print(f"  PAPER TRADE {trade.symbol}: buy {trade.buy_exchange} / "
                          f"sell {trade.sell_exchange} | gross {opp.gross_edge_bps:.1f}bps "
                          f"net {opp.net_edge_bps:.1f}bps (after TDS {opp.net_after_tds_bps:.1f}bps) "
                          f"| P&L ₹{trade.pnl_inr:+.2f}, TDS locked ₹{trade.tds_withheld_inr:.2f}")
            if scan % 10 == 0:
                line = f"[scan {scan}] best gross edge: {best_gross:.1f}bps | {broker.summary()}"
                if not args.no_premium:
                    btc_quotes = [q for qs in quotes.values() for q in qs if q.symbol == "BTC/INR"]
                    global_mid = (demo.global_btc_usdt if demo else fetch_global_btc_usdt())
                    if btc_quotes and global_mid:
                        inr_mid = sum((q.bid + q.ask) / 2 for q in btc_quotes) / len(btc_quotes)
                        prem = india_premium_bps(inr_mid, global_mid, args.usdinr)
                        line += f" | India premium vs global: {prem:+.0f}bps (not capturable: FEMA/LRS + TDS)"
                print(line)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass

    elapsed = time.time() - started
    print(f"\n=== Session summary ({elapsed:.0f}s, {scan} scans) ===")
    print(broker.summary())
    print("\n--- The Indian tax reality ---")
    for line in broker.tax_summary():
        print(f"  {line}")
    print("\nCompare that to the viral posts — this is what the math (and the Income Tax Act) allows.")


if __name__ == "__main__":
    main()
