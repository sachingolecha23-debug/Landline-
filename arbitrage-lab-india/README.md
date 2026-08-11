# Arbitrage Lab (India) — an honest INR crypto arbitrage paper-trader

Companion to [`../arbitrage-lab`](../arbitrage-lab), rebuilt for the Indian
market: it scans INR pairs across **CoinDCX, WazirX, Zebpay and Bitbns**,
detects price dislocations, and paper-trades them with the full Indian cost
stack applied. No API keys, no accounts, **no real money — ever**.

## Why arbitrage is even harder in India

Everything in the global lab's README still applies (fees eat the spread, HFT
firms close real gaps in milliseconds, viral "₹5,000 → ₹6 crore" posts are
engagement scams). India then adds four more layers:

1. **1% TDS on every sell (Section 194S).** Deducted from the sale proceeds of
   every VDA trade above the threshold. It is a tax *credit*, not a fee — you
   can claim it back when you file your ITR — but until then it is working
   capital gone. Churn your capital 100 times and your entire balance is
   sitting with the Income Tax Department waiting for a refund.
2. **Flat 30% tax on gains, no loss offset (Section 115BBH).** Profitable
   trades are taxed at 30% (+ cess); losing trades cannot be set off against
   winners or carried forward. A strategy that wins ₹100 and loses ₹80 nets
   ₹20 pre-tax but owes ₹30 in tax — a real after-tax loss.
3. **Higher exchange fees and wider spreads.** Indian exchanges typically
   charge ~0.4–0.5% taker per leg (vs Binance's 0.1%) and INR books are far
   thinner, so slippage is worse.
4. **The "India premium" is a trap.** INR prices often sit a few percent above
   global USDT prices. You cannot legally capture that gap: FEMA/LRS rules
   restrict moving money abroad to buy crypto, INR banking rails to exchanges
   are unreliable, and the TDS applies on the India leg anyway. This lab
   *displays* the premium against Binance so you can watch a gap that looks
   like free money and understand why it persists — because nobody can
   arbitrage it away.

Add it up: a round trip costs roughly **0.8–1.0% in fees and slippage plus 1%
of proceeds locked as TDS**, against dislocations that are usually a few
hundredths of a percent. That is the whole story.

## Quickstart

Python 3.9+, stdlib only.

```bash
cd arbitrage-lab-india

# Live mode: real public tickers (run on your own machine)
python3 -m india_arb --mode live --duration 300

# Demo mode: synthetic INR data with occasional dislocations, works offline
python3 -m india_arb --mode demo --duration 30
```

Useful flags:

| Flag | Default | Meaning |
|---|---|---|
| `--symbols` | `BTC/INR,ETH/INR,SOL/INR,XRP/INR,DOGE/INR` | INR markets to scan |
| `--interval` | `3.0` | Seconds between scans |
| `--duration` | `60` | Run time in seconds (`0` = until Ctrl-C) |
| `--capital` | `100000` | Simulated INR per exchange (₹1,00,000) |
| `--fee-bps` | `45` | Taker fee per leg, basis points (45 = 0.45%) |
| `--slippage-bps` | `10` | Slippage allowance per leg, bps |
| `--tds-bps` | `100` | TDS withheld on sell proceeds (100 = 1%) |
| `--tax-rate` | `0.30` | Flat tax applied to net gains in the summary |
| `--min-edge-bps` | `1` | Minimum net edge (after fees+slippage) to trade |
| `--usdinr` | `88.0` | USD/INR rate for the India-premium display |
| `--no-premium` | off | Skip the Binance global-price premium check |
| `--trades-csv` | `trades_inr.csv` | Paper trade log |

The summary separates the three numbers Indian traders must never conflate:
**P&L before tax**, **TDS withheld** (recoverable at ITR time, illiquid until
then), and **estimated 30% tax** on the gains — giving an honest after-tax,
after-lockup picture.

Notes: WazirX's platform has been unreliable since its 2024 hack; its feed (and
any other that fails) is skipped with a warning rather than killing the scan.
Public endpoints occasionally change — each feed is isolated so one break
doesn't take down the lab.

**Educational only. Not investment, legal, or tax advice. Places no real
orders. Consult a CA before trading VDAs — the tax treatment here is a
simplified model.**
