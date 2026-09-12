"""
Portfolio Stress Testing Framework
------------------------------------
A framework for stress testing a stock portfolio against real historical
crises and hypothetical shock scenarios - the kind of analysis a market
risk team runs alongside VaR, not instead of it.

WHAT THIS COVERS
- Historical scenario stress testing: replaying real crises (2008 GFC,
  COVID crash, 2022 rate hike cycle) on today's portfolio positions
- Hypothetical scenario construction: designing plausible-but-unobserved
  shocks that haven't happened yet but could
- P&L attribution under stress: which positions drove the loss, and why
- How regulators use stress testing: Basel III, FRTB, and RBI expectations
- The core difference between VaR and stress testing

NOTE ON THE SHOCK NUMBERS USED HERE
The historical scenario shocks below are approximate, sector-level
magnitudes based on how each sector broadly behaved during these crises
in the Indian market (financials/autos hit hardest in 2008 and COVID,
IT relatively more resilient in COVID but hit hard in 2022, energy
volatile both ways). They're illustrative for learning the FRAMEWORK,
not a substitute for pulling actual instrument-level historical returns,
which is what a real desk would use.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# 1. PORTFOLIO SETUP - 5 stocks across sectors, real weights, INR notional
# ---------------------------------------------------------------------

PORTFOLIO_NOTIONAL = 50_000_000  # Rs. 5 crore

portfolio = pd.DataFrame({
    "ticker": ["RELIANCE", "HDFCBANK", "INFY", "ITC", "TATAMOTORS"],
    "sector": ["Energy/Conglomerate", "Financials", "IT Services", "FMCG", "Auto"],
    "weight": [0.28, 0.25, 0.20, 0.15, 0.12],
})
portfolio["notional"] = portfolio["weight"] * PORTFOLIO_NOTIONAL

assert abs(portfolio["weight"].sum() - 1.0) < 1e-6, "weights must sum to 1"


# ---------------------------------------------------------------------
# 2. HISTORICAL SCENARIOS - approximate sector-level shocks
# ---------------------------------------------------------------------
# format: {scenario_name: {sector: shock_pct}}
# shock_pct is the peak-to-trough return over the crisis window (negative = loss)

HISTORICAL_SCENARIOS = {
    "2008 Global Financial Crisis (Jan-Oct 2008)": {
        "Energy/Conglomerate": -0.55,
        "Financials": -0.68,
        "IT Services": -0.52,
        "FMCG": -0.35,
        "Auto": -0.62,
    },
    "2020 COVID Crash (Jan-Mar 2020)": {
        "Energy/Conglomerate": -0.42,
        "Financials": -0.45,
        "IT Services": -0.26,
        "FMCG": -0.20,
        "Auto": -0.41,
    },
    "2022 Rate Hike Cycle (Jan-Oct 2022)": {
        "Energy/Conglomerate": 0.08,    # energy benefited from higher oil prices
        "Financials": -0.09,
        "IT Services": -0.27,           # global tech selloff + margin pressure
        "FMCG": -0.04,
        "Auto": -0.07,
    },
}


# ---------------------------------------------------------------------
# 3. HYPOTHETICAL SCENARIOS - plausible but unobserved shocks
# ---------------------------------------------------------------------

HYPOTHETICAL_SCENARIOS = {
    "Hypothetical: Simultaneous Rate Spike + Equity Crash": {
        # rates spike 200bps unexpectedly WHILE equities sell off broadly -
        # financials get a mixed effect (higher NIMs eventually, but immediate
        # mark-to-market/credit stress dominates), high-multiple IT hit hardest,
        # defensives hold up relatively better
        "Energy/Conglomerate": -0.20,
        "Financials": -0.30,
        "IT Services": -0.35,
        "FMCG": -0.12,
        "Auto": -0.25,
    },
    "Hypothetical: INR Currency Crisis + Oil Price Spike": {
        # rupee depreciates sharply + crude oil spikes - hurts import-heavy /
        # high fuel-cost sectors (auto, energy input costs), helps IT (export
        # revenue in USD becomes worth more in INR terms)
        "Energy/Conglomerate": -0.15,   # higher input costs offset refining margin gains
        "Financials": -0.18,
        "IT Services": 0.10,            # rupee depreciation is a tailwind for IT exporters
        "FMCG": -0.10,
        "Auto": -0.22,
    },
}


# ---------------------------------------------------------------------
# 4. APPLY A SCENARIO AND ATTRIBUTE P&L BY POSITION
# ---------------------------------------------------------------------

def apply_scenario(portfolio, scenario_shocks, scenario_name):
    df = portfolio.copy()
    df["shock_pct"] = df["sector"].map(scenario_shocks)
    df["pnl"] = df["notional"] * df["shock_pct"]
    df = df.sort_values("pnl")  # worst losses first

    total_pnl = df["pnl"].sum()
    total_pnl_pct = total_pnl / PORTFOLIO_NOTIONAL

    print("=" * 78)
    print(f"SCENARIO: {scenario_name}")
    print("=" * 78)
    print(f"{'Ticker':<12}{'Sector':<22}{'Weight':<10}{'Shock':<10}{'P&L (Rs.)':<16}")
    print("-" * 78)
    for _, row in df.iterrows():
        print(f"{row['ticker']:<12}{row['sector']:<22}{row['weight']:<10.0%}"
              f"{row['shock_pct']:<10.1%}{row['pnl']:<16,.0f}")
    print("-" * 78)
    print(f"{'TOTAL':<44}{total_pnl_pct:<10.1%}{total_pnl:<16,.0f}")

    worst = df.iloc[0]
    print(f"\nMost damaging position: {worst['ticker']} ({worst['sector']}) -> "
          f"Rs. {worst['pnl']:,.0f} ({worst['pnl']/PORTFOLIO_NOTIONAL:.1%} of portfolio)")
    print()

    return df, total_pnl, total_pnl_pct


# ---------------------------------------------------------------------
# 5. RUN ALL SCENARIOS AND BUILD A SUMMARY TABLE
# ---------------------------------------------------------------------

def run_all_scenarios(portfolio):
    all_scenarios = {**HISTORICAL_SCENARIOS, **HYPOTHETICAL_SCENARIOS}
    summary_rows = []
    detail_results = {}

    for name, shocks in all_scenarios.items():
        df, total_pnl, total_pnl_pct = apply_scenario(portfolio, shocks, name)
        detail_results[name] = df
        summary_rows.append({
            "scenario": name,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "worst_position": df.iloc[0]["ticker"],
            "worst_position_pnl": df.iloc[0]["pnl"],
        })

    summary = pd.DataFrame(summary_rows).sort_values("total_pnl")
    return summary, detail_results


def print_summary(summary):
    print("=" * 78)
    print("STRESS TEST SUMMARY - ALL SCENARIOS RANKED BY SEVERITY")
    print("=" * 78)
    for _, row in summary.iterrows():
        print(f"{row['scenario']:<50}Rs. {row['total_pnl']:>14,.0f}  "
              f"({row['total_pnl_pct']:>7.1%})")
    print()

    worst_scenario = summary.iloc[0]
    print(f"WORST-CASE SCENARIO: {worst_scenario['scenario']}")
    print(f"Portfolio loss: Rs. {worst_scenario['total_pnl']:,.0f} "
          f"({worst_scenario['total_pnl_pct']:.1%} of Rs. 5 crore notional)")
    print()


# ---------------------------------------------------------------------
# 6. SENSITIVITY: WHICH POSITIONS ARE MOST SENSITIVE ACROSS ALL SCENARIOS
# ---------------------------------------------------------------------

def position_sensitivity(portfolio, detail_results):
    print("=" * 78)
    print("POSITION SENSITIVITY ACROSS ALL SCENARIOS")
    print("=" * 78)

    sensitivity = pd.DataFrame({"ticker": portfolio["ticker"]})
    for name, df in detail_results.items():
        short_name = name.split("(")[0].strip()
        sensitivity[short_name] = sensitivity["ticker"].map(
            df.set_index("ticker")["shock_pct"]
        )

    sensitivity["avg_shock"] = sensitivity.drop(columns="ticker").mean(axis=1)
    sensitivity["worst_shock"] = sensitivity.drop(columns=["ticker", "avg_shock"]).min(axis=1)
    sensitivity = sensitivity.sort_values("worst_shock")

    pd.set_option("display.width", 160)
    print(sensitivity.round(3).to_string(index=False))
    print()
    print(f"Most consistently sensitive position: {sensitivity.iloc[0]['ticker']} "
          f"(avg shock across all scenarios: {sensitivity.iloc[0]['avg_shock']:.1%})")
    print()
    return sensitivity


# ---------------------------------------------------------------------
# 7. VaR vs STRESS TESTING - the conceptual difference, shown numerically
# ---------------------------------------------------------------------

def compare_var_vs_stress(summary):
    """
    VaR (even at 99% confidence) is built from NORMAL trading days and
    tells you the loss you'd expect NOT to exceed most of the time.
    Stress testing deliberately looks PAST that - at the extreme, rare
    events VaR is not designed to capture at all. This function makes
    that gap concrete using a rough illustrative VaR figure.
    """
    print("=" * 78)
    print("VaR vs STRESS TESTING - WHY YOU NEED BOTH")
    print("=" * 78)
    # illustrative: a 99% 1-day historical VaR on a diversified equity
    # portfolio is typically in the 2-4% of notional range on a normal day
    illustrative_var_99_pct = -0.035
    illustrative_var_amount = illustrative_var_99_pct * PORTFOLIO_NOTIONAL

    worst_stress = summary.iloc[0]

    print(f"Illustrative 99% 1-day VaR:        Rs. {illustrative_var_amount:>14,.0f} "
          f"({illustrative_var_99_pct:.1%})")
    print(f"Worst stress scenario loss:        Rs. {worst_stress['total_pnl']:>14,.0f} "
          f"({worst_stress['total_pnl_pct']:.1%})")
    multiple = worst_stress['total_pnl'] / illustrative_var_amount
    print(f"\nThe worst stress scenario is about {multiple:.1f}x larger than the 99% VaR estimate.")
    print()
    print("VaR answers: 'on a normal bad day, how much could I lose?' It's built")
    print("from the statistical behavior of recent historical returns, so by")
    print("construction it can't capture a scenario that's rarer or more extreme")
    print("than what's already in that historical window.")
    print()
    print("Stress testing answers a different question: 'if a specific, severe")
    print("event happened - one we've seen before, or one we can imagine - how")
    print("much would we lose?' It doesn't rely on probability at all, just on")
    print("designing the scenario and running the portfolio through it. That's")
    print("exactly why regulators require both: VaR for everyday capital/risk")
    print("management, and stress testing for tail scenarios VaR is blind to.")
    print()


# ---------------------------------------------------------------------
# 8. REGULATORY CONTEXT
# ---------------------------------------------------------------------

def print_regulatory_context():
    print("=" * 78)
    print("HOW REGULATORS USE STRESS TESTING")
    print("=" * 78)
    print(
        "Basel III requires banks to run stress tests alongside VaR-based\n"
        "capital calculations, specifically because regulators recognized after\n"
        "2008 that VaR models badly understated tail risk during the crisis.\n\n"
        "FRTB (Fundamental Review of the Trading Book) goes further, replacing\n"
        "VaR with Expected Shortfall for regulatory capital and requiring banks\n"
        "to run stressed calibrations - using the worst 12-month historical\n"
        "window for each risk factor, not just recent 'normal' data.\n\n"
        "In India, the RBI requires banks and NBFCs to run periodic stress\n"
        "tests covering credit risk, market risk, and liquidity risk, and to\n"
        "report the results as part of their ICAAP (Internal Capital Adequacy\n"
        "Assessment Process) - regulators want to see that a bank has enough\n"
        "capital to survive a severe scenario, not just an average bad day."
    )
    print()


# ---------------------------------------------------------------------
# 9. VISUALIZATION
# ---------------------------------------------------------------------

def plot_scenario_comparison(summary):
    fig, ax = plt.subplots(figsize=(11, 6))
    colors = ["#c0392b" if "Hypothetical" in s else "#2980b9" for s in summary["scenario"]]
    bars = ax.barh(summary["scenario"], summary["total_pnl"] / 1e6, color=colors)
    ax.set_xlabel("Portfolio P&L (Rs. crore)")
    ax.set_title("Stress Test Results — Portfolio P&L by Scenario")
    ax.axvline(0, color="black", linewidth=0.8)

    for bar, pct in zip(bars, summary["total_pnl_pct"]):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f"  {pct:.1%}", va="center",
                ha="left" if bar.get_width() >= 0 else "right")

    from matplotlib.patches import Patch
    legend_elems = [Patch(facecolor="#2980b9", label="Historical scenario"),
                    Patch(facecolor="#c0392b", label="Hypothetical scenario")]
    ax.legend(handles=legend_elems, loc="lower right")

    fig.tight_layout()
    fig.savefig("stress_test_results.png", dpi=150)
    print("saved chart to stress_test_results.png\n")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    print("PORTFOLIO STRESS TESTING FRAMEWORK")
    print(f"Portfolio notional: Rs. {PORTFOLIO_NOTIONAL:,.0f} (Rs. 5 crore)\n")
    print(portfolio.to_string(index=False))
    print()

    summary, detail_results = run_all_scenarios(portfolio)
    print_summary(summary)
    sensitivity = position_sensitivity(portfolio, detail_results)
    compare_var_vs_stress(summary)
    print_regulatory_context()
    plot_scenario_comparison(summary)

    summary.to_csv("stress_test_summary.csv", index=False)
    sensitivity.to_csv("position_sensitivity.csv", index=False)
    print("saved stress_test_summary.csv and position_sensitivity.csv")


if __name__ == "__main__":
    main()
