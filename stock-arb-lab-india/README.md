# Stock Arb Lab (India) — an honest NSE↔BSE arbitrage paper-trader

Third lab in the series ([crypto global](../arbitrage-lab),
[crypto India](../arbitrage-lab-india)), this one for the **Indian equity
market**. Most liquid Indian stocks trade on *both* NSE and BSE, so their
prices dislocate constantly — which makes NSE↔BSE spread capture the most
seductive-looking arbitrage in India. This lab scans those spreads live,
paper-trades them with the complete Indian equity charge stack applied, and
shows you why the gap you can see is not a gap you can keep.

**Paper trading only. No broker account, no orders, no money — ever.**

## Why this doesn't work for retail (the honest math)

1. **The spreads are tiny and the charges are not.** NSE↔BSE gaps on liquid
   names are typically 1–10 bps. A cross-exchange intraday round trip costs
   roughly: brokerage (~2 bps/leg for discount brokers, worse in ₹20-flat
   terms on small orders), STT 2.5 bps on the intraday sell, stamp duty on the
   buy, exchange transaction charges + SEBI fees + 18% GST, and real slippage
   on thin BSE books. Call it **15–25 bps round trip** — more than almost
   every gap that ever appears.
2. **Your free data is ~15 minutes old.** There is no free real-time feed for
   NSE/BSE. This lab's live mode uses Yahoo Finance quotes (`RELIANCE.NS` vs
   `RELIANCE.BO`), which are delayed. You are looking at the past; the
   arbitrage desks that matter are co-located inside the exchange, trading the
   present. Real-time data means a paid broker API (Zerodha Kite, Upstox,
   etc.) — and even that puts you seconds behind the prop desks.
3. **Automating live orders is regulated.** Under SEBI's algorithmic trading
   framework for retail investors (circular of Feb 2025, in force since
   2025), algo orders through broker APIs must be tagged, and algos beyond
   modest order rates need to be registered with the exchange through your
   broker. You cannot legally wire a homemade bot to a broker API and let it
   rip. This lab therefore has no order-placement code at all.
4. **The professionals already ate it.** NSE↔BSE spread capture and
   cash–futures arbitrage are real institutional strategies — run by
   arbitrage mutual funds and prop desks with exchange co-location,
   sub-paisa costs, and margin-funded inventory on both exchanges. What's
   left over after them is smaller than retail costs by construction.
5. **Then there's tax.** Intraday equity profits are *speculative business
   income*, taxed at your slab rate. (Unlike crypto's s.115BBH, intraday
   losses can at least offset intraday gains.) The summary applies this so
   the after-tax number is real.

## What it does

- Live mode: polls delayed Yahoo Finance quotes for each stock on both
  exchanges (`.NS` and `.BO`), no keys or accounts needed.
- Detects NSE↔BSE dislocations; computes **gross edge** and **net edge** after
  the full charge stack + slippage.
- Paper-trades surviving edges (buy cheap exchange, sell rich exchange,
  intraday) and logs to `trades_stocks.csv`.
- Knows Indian market hours (9:15–15:30 IST, Mon–Fri) and warns when the
  market is closed and quotes are frozen.
- Demo mode generates realistic synthetic NSE/BSE quotes offline.

## Quickstart

Python 3.9+, stdlib only.

```bash
cd stock-arb-lab-india

# Live (delayed) data — run on your own machine, during market hours
python3 -m stock_arb --mode live --duration 600

# Offline demo
python3 -m stock_arb --mode demo --duration 30
```

Useful flags:

| Flag | Default | Meaning |
|---|---|---|
| `--symbols` | `RELIANCE,TCS,INFY,HDFCBANK,SBIN` | Stocks listed on both NSE & BSE |
| `--interval` | `60` (live) | Seconds between scans (data is delayed anyway) |
| `--duration` | `300` | Run time in seconds (`0` = until Ctrl-C) |
| `--capital` | `100000` | Simulated INR per exchange (₹1,00,000) |
| `--brokerage-bps` | `2` | Brokerage per leg, bps |
| `--stt-sell-bps` | `2.5` | STT on intraday sell, bps |
| `--stamp-buy-bps` | `0.3` | Stamp duty on buy, bps |
| `--other-bps` | `0.5` | Exchange txn + SEBI fees + GST per leg, bps |
| `--slippage-bps` | `5` | Slippage allowance per leg, bps |
| `--tax-rate` | `0.30` | Slab rate applied to net intraday gains |
| `--min-edge-bps` | `1` | Minimum net edge to paper-trade |
| `--trades-csv` | `trades_stocks.csv` | Paper trade log |

## What to expect

Run it through a full market session. You will see plenty of 1–8 bps gross
gaps, almost none that clear ~18 bps of round-trip cost, and the occasional
"huge" dislocation that is really just one exchange's delayed print lagging
the other — the exact illusion that screenshots well and trades terribly.

**Educational only. Not investment or tax advice. Places no orders. Yahoo
quote fields are unofficial and may change.**
