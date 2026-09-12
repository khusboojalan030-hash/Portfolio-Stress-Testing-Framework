# Portfolio Stress Testing Framework

A framework for stress testing a stock portfolio against real historical
crises and hypothetical shock scenarios - the analysis market risk teams
run alongside VaR, not instead of it.

Target role: Market Risk Analyst / Risk Manager

## What it teaches

- **Historical scenario stress testing** - replaying real crises (2008
  GFC, COVID crash, 2022 rate hike cycle) on a current portfolio to see
  what would happen if that exact event repeated
- **Hypothetical scenario construction** - designing plausible-but-
  unobserved shocks (e.g. a rate spike hitting at the same time as an
  equity crash) that haven't happened yet but reasonably could
- **P&L attribution under stress** - breaking the total portfolio loss
  down by position, so you know exactly which holdings drove the damage
  and why
- **How regulators use stress testing** - Basel III, FRTB, and RBI
  requirements, and why they exist
- **VaR vs stress testing** - the fundamental difference between "how
  bad is a normal bad day" (VaR) and "how bad is a specific severe
  event" (stress testing)

## How it's built

1. A 5-stock portfolio across sectors (Energy, Financials, IT, FMCG,
   Auto) with real weights and a Rs. 5 crore notional
2. Three historical scenarios applied using approximate sector-level
   shock magnitudes based on how each sector behaved during that crisis:
   - 2008 Global Financial Crisis
   - 2020 COVID Crash
   - 2022 Rate Hike Cycle
3. Two hypothetical scenarios designed from scratch:
   - Simultaneous rate spike + equity crash
   - INR currency crisis + oil price spike
4. P&L attribution per position for every scenario
5. A cross-scenario sensitivity table showing which positions are
   consistently the most exposed
6. A numeric comparison of stress-test losses against an illustrative
   99% VaR figure, to make the VaR-vs-stress-testing gap concrete

**On the shock numbers**: these are illustrative, sector-level
approximations of how each sector broadly moved during these crises in
the Indian market - not pulled from an actual historical return series
for these five specific stocks. That's a genuine simplification worth
being upfront about (and a good next step, listed below).

## Why you need both VaR and stress testing

VaR answers: *"on a normal bad day, how much could I lose?"* It's built
from the statistical distribution of recent historical returns, so by
construction it can't capture something rarer or more extreme than
what's already in that data.

Stress testing answers a different question: *"if this specific severe
event happened, how much would I lose?"* It doesn't rely on probability
at all - just on designing the scenario and running the portfolio
through it. In this project, the worst stress scenario (2008 GFC) comes
out to roughly **15x larger** than an illustrative 99% VaR estimate -
exactly the kind of gap that made regulators require both after 2008.

## Regulatory context

- **Basel III** requires stress testing alongside VaR-based capital
  calculations, specifically because VaR models badly understated tail
  risk during the 2008 crisis
- **FRTB** (Fundamental Review of the Trading Book) replaces VaR with
  Expected Shortfall for regulatory capital and requires stressed
  calibrations using the worst historical 12-month window per risk
  factor
- **RBI** requires Indian banks/NBFCs to run periodic stress tests
  covering credit, market, and liquidity risk, reported as part of
  ICAAP (Internal Capital Adequacy Assessment Process)

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python stress_testing.py
```

To change the portfolio, edit the setup block at the top:
```python
PORTFOLIO_NOTIONAL = 50_000_000  # Rs. 5 crore
portfolio = pd.DataFrame({
    "ticker": ["RELIANCE", "HDFCBANK", "INFY", "ITC", "TATAMOTORS"],
    "sector": [...],
    "weight": [0.28, 0.25, 0.20, 0.15, 0.12],
})
```

## Sample output

```
STRESS TEST SUMMARY - ALL SCENARIOS RANKED BY SEVERITY
2008 Global Financial Crisis (Jan-Oct 2008)       Rs.    -27,745,000  (-55.5%)
2020 COVID Crash (Jan-Mar 2020)                   Rs.    -18,065,000  (-36.1%)
Hypothetical: Simultaneous Rate Spike + Equity Crash Rs. -12,450,000  (-24.9%)
Hypothetical: INR Currency Crisis + Oil Price Spike  Rs.  -5,420,000  (-10.8%)
2022 Rate Hike Cycle (Jan-Oct 2022)               Rs.     -3,425,000  (-6.9%)

Most consistently sensitive position: HDFCBANK (avg shock across all scenarios: -34.0%)
```

## Project structure

```
portfolio-stress-testing/
├── stress_testing.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Possible extensions

- Replace the sector-level shock approximations with actual historical
  daily returns for each ticker over the real crisis windows
- Add a reverse stress test - work backward from a target loss (e.g.
  "what scenario would wipe out 30% of the portfolio?")
- Model correlation breakdown during crises (correlations tend to spike
  toward 1 in a crash, reducing the diversification benefit assumed in
  calmer periods)
- Add liquidity-adjusted stress testing (wider bid-ask spreads and
  slower execution during stress, not just price moves)
