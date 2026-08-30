"""CLI: run the analysis, build the workbook, or both.

    python -m src.run analyse   # print the analysis
    python -m src.run build     # write outputs/unit_economics.xlsx
    python -m src.run all       # both
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from . import drivers as drivers_module
from .decisions import (
    build_scenarios,
    cm3_sensitivity,
    compute_break_even,
    evaluate_all,
    evaluate_combined,
    expansion_sensitivity,
)
from .drivers import Drivers
from .model import (
    BasketDistribution,
    build_channel_portfolio,
    build_unit_economics,
    threshold_effect,
)
from .workbook import build as build_workbook

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
WORKBOOK_PATH = OUTPUT_DIR / "unit_economics.xlsx"
ANALYSIS_PATH = OUTPUT_DIR / "analysis.txt"

WIDTH = 92


def rule(char: str = "-") -> str:
    return char * WIDTH


def heading(text: str) -> str:
    return f"\n{rule('=')}\n{text}\n{rule('=')}"


def lakh(value: float) -> str:
    return f"{value / 1e5:>+10,.1f}L"


def crore(value: float) -> str:
    return f"{value / 1e7:>+7,.2f}Cr"


def analyse(d: Drivers, out: io.TextIOBase) -> None:
    def say(text: str = "") -> None:
        print(text, file=out)

    base = build_unit_economics(d)
    basket = BasketDistribution(d["gross_order_value"], d["basket_log_sigma"])

    say(heading("QUICKCART -- UNIT ECONOMICS AND THREE PROPOSALS"))
    say(f"{len(d.all())} drivers, {len(d.assumptions)} flagged ASSUMPTION, "
        f"{len(d.measured)} flagged MEASURED, {len(d.channels)} acquisition channels.")
    say(f"Estate: {base.stores:,.0f} dark stores at {base.orders_per_store_per_day:,.0f} "
        f"orders/store/day = {base.orders_per_month:,.0f} orders/month.")

    # -- basket ------------------------------------------------------------ #
    say(heading("1. BASKET DISTRIBUTION"))
    say(f"Lognormal, calibrated to mean GOV of INR {basket.mean:,.2f}; "
        f"implied median INR {basket.median:,.2f}.")
    say("A free-delivery threshold acts on the distribution, not the average, which is why")
    say("this model cannot be built on AOV alone.")
    say()
    say(f"  {'Threshold':>12}  {'Below':>8}  {'Up-size':>8}  {'Fee-paying':>11}  "
        f"{'Avg basket':>11}  {'Fee income':>11}")
    for label, threshold in (("current", d["free_delivery_threshold"]),
                             ("proposed", d["proposed_threshold"])):
        e = threshold_effect(d, threshold)
        say(f"  {label:>12}  {e.fee_paying_share_before_upsize:>7.1%}  "
            f"{e.upsized_share:>7.1%}  {e.fee_paying_share:>10.1%}  "
            f"{e.gross_order_value:>11,.2f}  {e.delivery_fee_income:>11,.2f}")

    # -- ladder ------------------------------------------------------------ #
    say(heading("2. CONTRIBUTION MARGIN LADDER (per order, base case)"))
    say(f"  {'Line':<36}{'INR':>12}{'% of NOV':>12}")
    say(f"  {rule('-')[:60]}")
    for name, value, pct in base.as_ladder():
        marker = "  " if not name.startswith(("CM", "Total", "EBITDA")) else "* "
        say(f"{marker}{name:<36}{value:>12,.2f}{pct:>12.2%}")
    say()
    say(f"  Monthly CM2 contribution   {base.cm2_total:>18,.0f}")
    say(f"  Monthly CM3 contribution   {base.cm3_total:>18,.0f}")
    say(f"  Monthly EBITDA             {base.ebitda_total:>18,.0f}")
    say()
    say("Benchmark check against public disclosure: CM1 lands at "
        f"{base.pct_of_nov(base.cm1):.1%} of net order value against Blinkit's reported")
    say("26.6% gross profit margin, and CM2 at "
        f"{base.pct_of_nov(base.cm2):.1%} against an industry benchmark of roughly 13%")
    say(f"for a mature dark store. EBITDA of INR {base.ebitda_per_order:,.2f} per order sits "
        "between Zepto's")
    say("reported FY26 and Q4 FY26 figures. The model is in the right postcode.")

    # -- break-even -------------------------------------------------------- #
    be = compute_break_even(d, base)
    say(heading("3. BREAK-EVEN DENSITY"))
    say("Expressed in orders per store per day, because that is the number an operator can")
    say("act on and the number the business already tracks.")
    say()
    say(f"  CM3 turns positive at        {be.cm3_orders_per_store_per_day:>7,.0f} orders/store/day"
        f"   (currently {be.current_orders_per_store_per_day:,.0f}, "
        f"{be.cm3_headroom:+.0%} headroom)")
    say(f"  EBITDA turns positive at     {be.ebitda_orders_per_store_per_day:>7,.0f} orders/store/day"
        f"   ({be.ebitda_gap:+.1%} from here)")
    say(f"  Stores supportable at current density: "
        f"{be.ebitda_stores_at_current_density:,.1f}")
    say()
    say("That last figure is the strategic point. Breaking even needs roughly "
        f"{be.ebitda_stores_at_current_density:,.0f} stores")
    say(f"*at today's density of {be.current_orders_per_store_per_day:,.0f} orders a day* -- which "
        "means genuinely new catchments, not")
    say("infill of catchments already covered. Infill adds stores and subtracts density.")

    # -- channels ---------------------------------------------------------- #
    portfolio = build_channel_portfolio(d, base.cm3, base.cm2)
    say(heading("4. ACQUISITION CHANNELS"))
    say(f"  {'Channel':<18}{'CAC':>9}{'Orders':>8}{'LTV CM3':>10}{'CM3 x':>8}"
        f"{'LTV CM2':>10}{'CM2 x':>8}{'Payback':>9}")
    say(f"  {rule('-')[:80]}")
    for r in portfolio.results:
        payback = "never" if r.payback_month is None else f"m{r.payback_month}"
        ratio3 = "  n/a" if r.cac == 0 else f"{r.ratio_cm3:.2f}"
        ratio2 = "  n/a" if r.cac == 0 else f"{r.ratio_cm2:.2f}"
        flag = "  <-- flips on definition" if r.verdict_flips_on_definition else ""
        say(f"  {r.name:<18}{r.cac:>9,.0f}{r.cohort_cm3.total_orders_per_customer:>8,.1f}"
            f"{r.ltv_cm3:>10,.0f}{ratio3:>8}{r.ltv_cm2:>10,.0f}{ratio2:>8}{payback:>9}{flag}")
    say()
    say(f"  Blended CAC     INR {portfolio.blended_cac:>7,.2f}   ->  LTV:CAC "
        f"{portfolio.blended_ratio:.2f}x   reads healthy")
    say(f"  Paid-only CAC   INR {portfolio.paid_cac:>7,.2f}   ->  LTV:CAC "
        f"{portfolio.paid_ratio:.2f}x   reads marginal")
    say(f"  Blended overstates paid efficiency by "
        f"{portfolio.blended_ratio / portfolio.paid_ratio - 1:.0%}, because "
        f"{portfolio.organic_share_of_customers:.0%} of acquired")
    say("  customers are organic and cost nothing. Any decision about *incremental* spend has")
    say("  to be made on channel-level or paid-only figures.")
    say()
    say(f"  Channels below 1.0x on CM3: "
        f"{', '.join(r.name for r in portfolio.sub_unity) or 'none'}")
    say(f"  They hold INR {portfolio.sub_unity_spend:,.0f} of spend = "
        f"{portfolio.sub_unity_spend_share:.1%} of the marketing budget.")
    flips = [r.name for r in portfolio.results if r.verdict_flips_on_definition]
    if flips:
        say(f"  {', '.join(flips)} clear 1.0x on CM2 and fail on CM3. The same channel is")
        say("  fundable or not depending on which contribution margin the deck uses. That is a")
        say("  governance problem, and it is why METRIC_DEFINITIONS.md exists.")

    # -- decisions --------------------------------------------------------- #
    say(heading("5. THE THREE PROPOSALS"))
    decisions = evaluate_all(d, base)
    say(f"  {'Proposal':<38}{'Orders':>9}{'Revenue':>9}{'Monthly CM3':>14}"
        f"{'Annual':>11}{'Verdict':>10}")
    say(f"  {rule('-')[:91]}")
    for dec in decisions:
        say(f"  {dec.short_title:<38}{dec.order_growth:>+9.1%}{dec.revenue_growth:>+9.1%}"
            f"{lakh(dec.monthly_delta):>14}{crore(dec.annual_delta):>11}{dec.verdict:>10}")
    say()
    say("  Read the first two rows together. Store expansion grows revenue and shrinks")
    say("  contribution; the threshold change shrinks revenue and grows contribution. Revenue")
    say("  is not the objective function, and either proposal judged on it gets the wrong answer.")

    for dec in decisions:
        say()
        say(rule())
        say(f"{dec.verdict}  --  {dec.title}   [proposed by {dec.proposer}]")
        say(rule())
        say(f"  CM3 per order        INR {dec.base.cm3:>8,.2f}  ->  INR {dec.proposed.cm3:,.2f}")
        say(f"  Monthly CM3 change   {lakh(dec.monthly_delta)}"
            f"        Annualised {crore(dec.annual_delta)}")
        if dec.capex:
            say(f"  Capital expenditure  INR {dec.capex:,.0f}"
                f"   payback: {'never' if dec.payback_months is None else f'{dec.payback_months:.1f} months'}")
        if dec.recurring_cost_monthly:
            say(f"  Recurring cost       INR {dec.recurring_cost_monthly:,.0f} per month")
        say()
        say(f"  {dec.break_even_label}: {dec.break_even_value:.1%}")
        margin = dec.margin_of_safety_pp
        if dec.observed_value is not None and margin is not None:
            direction = "clears it by" if margin > 0 else "misses it by"
            say(f"  {dec.observed_label}: {dec.observed_value:.1%}"
                f"  --  {direction} {abs(margin):.1f} percentage points")
        say()
        for note in dec.notes:
            say(f"  - {note}")

    # -- scenarios --------------------------------------------------------- #
    say(heading("6. SCENARIOS"))
    say(f"  {'Scenario':<10}{'CM1':>9}{'CM2':>9}{'CM3':>9}{'EBITDA/order':>15}"
        f"{'Monthly EBITDA':>18}")
    say(f"  {rule('-')[:70]}")
    for s in build_scenarios(d, base):
        say(f"  {s.label:<10}{s.cm1:>9,.2f}{s.cm2:>9,.2f}{s.cm3:>9,.2f}"
            f"{s.ebitda_per_order:>15,.2f}{s.ebitda_total:>18,.0f}")
    say()
    say("  The spread is wide because unit economics are leveraged on order density. This is a")
    say("  bet on orders per store, not on store count -- which is exactly why proposal 1 fails.")

    # -- sensitivity ------------------------------------------------------- #
    say(heading("7. TWO-WAY SENSITIVITY"))
    for grid in (cm3_sensitivity(d, base), expansion_sensitivity(d, base)):
        say()
        say(f"  {grid.title}")
        say(f"  rows: {grid.row_label}   columns: {grid.col_label}")
        say("        " + "".join(grid.col_format.format(v).rjust(10) for v in grid.col_values))
        for row_value, row in zip(grid.row_values, grid.cells, strict=True):
            say(f"  {grid.row_format.format(row_value):>6}"
                + "".join(grid.cell_format.format(c).rjust(10) for c in row))

    say()
    say(f"  In the second table, every cell at the pilot's measured {d['incrementality']:.0%} "
        "incrementality is")
    say("  negative -- which is the argument for a larger pilot rather than for a bigger guess.")

    # Which lever is worth more depends on which line you optimise, and the answer
    # reverses between CM3 and EBITDA. Worth computing rather than asserting.
    say()
    say("  Density versus margin -- and why the answer depends on the line you optimise:")
    say()
    reference = build_unit_economics(d, baseline_orders_per_month=base.orders_per_month)
    plus_margin = build_unit_economics(
        d, product_gross_margin_pct=d["product_gross_margin_pct"] + 0.01,
        baseline_orders_per_month=base.orders_per_month,
    )
    plus_density = build_unit_economics(
        d, orders_per_store_per_day=base.orders_per_store_per_day + 40,
        baseline_orders_per_month=base.orders_per_month,
    )
    say(f"  {'Lever':<26}{'CM3/order':>12}{'EBITDA/order':>15}{'Monthly EBITDA':>17}")
    say(f"  {rule('-')[:70]}")
    for label, case in (("+1.0pp gross margin", plus_margin),
                        ("+40 orders/store/day", plus_density)):
        say(f"  {label:<26}{case.cm3 - reference.cm3:>+12.2f}"
            f"{case.ebitda_per_order - reference.ebitda_per_order:>+15.2f}"
            f"{lakh(case.ebitda_total - reference.ebitda_total):>17}")
    say()
    say("  A percentage point of gross margin beats 40 extra orders a day on CM3, and loses to")
    say("  it on EBITDA. Density does double duty -- it lifts CM3 and dilutes fixed central")
    say("  overhead across more orders -- while margin only does the first. The same structural")
    say("  trap as the channel verdicts: which option looks better depends on which line you")
    say("  optimise, so the line has to be agreed before the options are compared.")

    say(heading("RECOMMENDATION"))
    approved = [dec for dec in decisions if dec.approved]
    rejected = [dec for dec in decisions if not dec.approved]
    for dec in sorted(approved, key=lambda x: -x.annual_delta):
        say(f"  PROCEED   {dec.short_title:<40}{crore(dec.annual_delta)} a year")
    for dec in rejected:
        say(f"  DO NOT    {dec.short_title:<40}{crore(dec.annual_delta)} a year"
            f"  plus {dec.capex / 1e7:,.2f}Cr capex")

    combined = evaluate_combined(d, base, approved)
    say()
    say("  The two approved proposals are NOT additive, and the business case should not add")
    say("  them:")
    say(f"    Sum of the two individual cases   {crore(combined.sum_of_parts_monthly * 12)} a year")
    say(f"    Modelled together                 {crore(combined.annual_delta)} a year")
    say(f"    Interaction                       {crore(combined.interaction * 12)} a year")
    say()
    say("  Retail media income is earned per order and the threshold change removes 3.1% of")
    say("  orders, so adding the two cases claims income on orders that will not exist. The")
    say("  error is small here, and it is the kind that compounds across a plan built by")
    say("  stapling business cases together.")

    annual_ebitda = base.ebitda_total * 12
    combined_ebitda = combined.combined.ebitda_total * 12
    say()
    say(f"  Current annual EBITDA           {annual_ebitda / 1e7:>+8,.2f}Cr")
    say(f"  After both approved proposals   {combined_ebitda / 1e7:>+8,.2f}Cr")
    if combined_ebitda > 0:
        say("  Both approved levers together take the business EBITDA-positive without opening a")
        say("  single new store or spending a rupee of capex -- which is the argument for doing")
        say("  them before, not alongside, any expansion programme.")
    else:
        say(f"  That closes {1 - combined_ebitda / annual_ebitda:.0%} of the gap to break-even "
            "with no capex.")
    say()
    say("  See DECISION.md for the one-page version.")
    say()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["analyse", "build", "all"], nargs="?", default="all")
    parser.add_argument("--config", default=None, help="path to an alternative driver file")
    args = parser.parse_args(argv)

    d = drivers_module.load(args.config)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.command in {"analyse", "all"}:
        buffer = io.StringIO()
        analyse(d, buffer)
        text = buffer.getvalue()
        sys.stdout.write(text)
        ANALYSIS_PATH.write_text(text, encoding="utf-8")
        print(f"analysis written to {ANALYSIS_PATH.relative_to(Path.cwd())}")

    if args.command in {"build", "all"}:
        path = build_workbook(d, WORKBOOK_PATH)
        size = path.stat().st_size
        print(f"workbook written to {path.relative_to(Path.cwd())} ({size:,} bytes)")
        print("every calculated cell is a formula -- change a driver and it recalculates")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
