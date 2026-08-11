# Arbitrage Lab — an honest crypto arbitrage paper-trader

This is the system from the viral "19-year-old turned $68 into $750K" posts —
except this one tells you the truth.

It scans multiple markets across multiple exchanges in real time, detects price
dislocations, and executes trades the moment an arbitrage window opens. The one
difference: **it trades simulated money**, and it accounts for the two things
the viral posts always leave out — **fees and slippage**. That difference is
exactly why the viral numbers are fiction.

## Why the viral post is fake

- **$68 → $6,732 in one night is a 99x return.** Real arbitrage edges are
  measured in *basis points* (hundredths of a percent). Even trading your full
  balance 100 times per night with a generous 0.1% net edge per round trip
  yields ~10%, not 9,900%.
- **Fees eat the spread.** A cross-exchange round trip costs ~0.2% in taker
  fees alone (0.1% per side on Binance, more elsewhere). Most "dislocations"
  you'll see are smaller than that. This lab shows you gross vs. net edge on
  every opportunity so you can see it yourself.
- **You are racing HFT firms.** Real dislocations are closed in milliseconds by
  firms with servers co-located in the exchanges' data centers. A bot polling
  over home internet sees the gap *after* it has been arbitraged away.
- **The funnel is the product.** "Comment, like, repost, follow, and I'll DM
  you the setup" is an engagement-farming scheme. Nobody gives away a working
  money printer for retweets.

## What this lab actually does

- Polls live public tickers from **Binance, Kraken, and Coinbase** (no API
  keys, no accounts, no funds at risk).
- Scans a configurable list of symbols across all exchange pairs.
- Computes **gross edge** (raw price gap) and **net edge** (after taker fees on
  both legs plus a slippage allowance).
- When net edge is positive, the paper broker "executes" the round trip and
  logs it to `trades.csv` with simulated P&L.
- Prints a running summary: opportunities seen, how many survived fees, and
  simulated profit — which will usually be a very small number. That is the
  lesson.

## Quickstart

Requires Python 3.9+. No third-party dependencies.

```bash
cd arbitrage-lab

# Live mode: real public market data (run on your own machine)
python3 -m arb_lab --mode live --duration 300

# Demo mode: synthetic data with occasional dislocations, works offline
python3 -m arb_lab --mode demo --duration 30
```

Useful flags:

| Flag | Default | Meaning |
|---|---|---|
| `--symbols` | `BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT,LTC/USDT` | Markets to scan |
| `--interval` | `2.0` | Seconds between scans |
| `--duration` | `60` | Total run time in seconds (`0` = run until Ctrl-C) |
| `--capital` | `1000` | Simulated USDT per exchange |
| `--fee-bps` | `10` | Taker fee per leg, in basis points (10 = 0.10%) |
| `--slippage-bps` | `5` | Slippage allowance per leg, in basis points |
| `--min-edge-bps` | `1` | Minimum *net* edge required to paper-trade |
| `--trades-csv` | `trades.csv` | Where executed paper trades are logged |

## What to expect

Run it for an hour and look at the summary. Typically you will see hundreds of
gross "dislocations" and almost none that survive fees — and the few that do
are usually stale-quote artifacts that a real order would have missed. If a
strategy can't make paper money against zero-latency fills, it will lose real
money against real fills.

**This project is educational. It is not financial advice, it places no real
orders, and nothing here should be connected to real funds.**
