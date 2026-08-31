"""CLI: run the full root-cause analysis.

    python -m src.run            # everything
    python -m src.run --section decomposition
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pandas as pd
import yaml

from .business_case import build_exposure, build_remedies, minimum_viable_target
from .decomposition import decompose, summarise_tiers
from .warehouse import PROJECT_ROOT, build, query

CONFIG_PATH = PROJECT_ROOT / "config" / "scenario.yml"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
ANALYSIS_PATH = OUTPUT_DIR / "analysis.txt"

WIDTH = 96


def rule(char: str = "-") -> str:
    return char * WIDTH


def heading(text: str) -> str:
    return f"\n{rule('=')}\n{text}\n{rule('=')}"


def pp(value: float) -> str:
    return f"{value * 100:+.2f}pp"


def inr(value: float) -> str:
    return f"INR {value:,.0f}"


def load_config(path: Path | str | None = None) -> dict:
    path = Path(path) if path else CONFIG_PATH
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def tier_rows(connection, half: str) -> list[dict]:
    frame = query(connection, f"""
        SELECT tier, tickets, met_work, met_net, met_strict
        FROM atlas.tier_half WHERE half = '{half}' ORDER BY tier
    """)
    return frame.to_dict("records")


def analyse(config: dict, out: io.TextIOBase, sections: set[str] | None = None) -> dict:
    def say(text: str = "") -> None:
        print(text, file=out)

    def wanted(name: str) -> bool:
        return sections is None or name in sections

    connection = build(config)
    baseline = summarise_tiers(tier_rows(connection, "H1"))
    current = summarise_tiers(tier_rows(connection, "H2"))
    result = decompose(baseline, current)

    monthly = query(connection, "SELECT * FROM atlas.monthly_attainment ORDER BY month_index")
    hypotheses = query(connection, "SELECT * FROM atlas.hypotheses")
    ceiling = query(connection, "SELECT * FROM atlas.sla_ceiling")
    composition = query(connection, "SELECT * FROM atlas.time_composition WHERE half = 'H2'")
    incident = query(connection, "SELECT * FROM atlas.incident_isolation")
    backlog = query(connection, "SELECT * FROM atlas.backlog_trace ORDER BY month_index")

    enterprise_attainment = current["enterprise"].attainment_net
    exposure = build_exposure(config, enterprise_attainment)
    remedies = build_remedies(config, ceiling, exposure)
    viable = minimum_viable_target(ceiling, "enterprise", exposure.threshold)

    # ---------------------------------------------------------------- header #
    say(heading("PROJECT ATLAS -- WHY SLA ATTAINMENT FELL"))
    say(f"{config['meta']['organisation']}")
    say(f"{len(query(connection, 'SELECT 1 FROM atlas.tickets')):,} tickets over "
        f"{config['meta']['months']} months. "
        f"H1 = months 1-{config['meta']['baseline_months']} (baseline), "
        f"H2 = months {config['meta']['baseline_months'] + 1}-{config['meta']['months']} "
        f"(current).")
    say()
    say(f"  SLA attainment as reported     {result.baseline_reported:.2%}  ->  "
        f"{result.current_reported:.2%}     {pp(result.reported_gap)}")
    say(f"  On the governed definition     {result.baseline_reported:.2%}  ->  "
        f"{result.current_governed:.2%}     {pp(result.governed_gap)}")
    say()
    say("The executive read is that the support team has become slower and needs more people.")
    say("Every number below contradicts that, and the decomposition says by how much.")

    # ----------------------------------------------------------- 1. headline #
    if wanted("trend"):
        say(heading("1. THE MONTHLY SERIES"))
        say(f"  {'month':>6}{'tickets':>9}{'ent %':>8}{'reported':>10}{'governed':>10}"
            f"{'work':>8}{'queue h':>9}{'backlog':>9}")
        say(f"  {rule('-')[:69]}")
        for row in monthly.itertuples(index=False):
            marker = " <-- incident" if row.month_index == config["defect_spike"]["month"] else ""
            say(f"  {row.month_index:>6}{row.tickets:>9,}{row.enterprise_share:>8.1%}"
                f"{row.attainment_as_reported:>10.2%}{row.attainment_governed:>10.2%}"
                f"{row.attainment_work:>8.2%}{row.mean_queue_wait_hours:>9.2f}"
                f"{row.peak_backlog:>9,}{marker}")
        say()
        say("Two different things are visible here and they need separating. One month collapses")
        say("and recovers. And underneath that, a slow drift downward as the enterprise share")
        say("climbs. The 'work' column -- handling effort alone -- barely moves throughout.")

    # ------------------------------------------------------ 2. hypothesis audit #
    if wanted("hypotheses"):
        say(heading("2. ISSUE TREE -- EVERY HYPOTHESIS TESTED, INCLUDING THE ONES RULED OUT"))
        say("Verdicts are computed in SQL against a materiality bar of 1.0pp, declared before")
        say("any result was seen. Recording the eliminated branches is what stops this being")
        say("relitigated by whoever's favourite theory went unmentioned.")
        say()
        counts = hypotheses["verdict"].value_counts()
        say("  " + "   ".join(f"{verdict}: {count}" for verdict, count in counts.items()))
        say()
        for row in hypotheses.itertuples(index=False):
            say(f"  [{row.verdict:^10}] {row.hypothesis_id}  {row.hypothesis}")
            say(f"               test: {row.test}")
            if pd.notna(row.h1_value) and pd.notna(row.h2_value):
                say(f"               {row.h1_value:,.4f} -> {row.h2_value:,.4f} ({row.unit})")
            for line in _wrap(row.evidence, WIDTH - 15):
                say(f"               {line}")
            say()

    # ------------------------------------------------------- 3. decomposition #
    if wanted("decomposition"):
        say(heading("3. DECOMPOSITION -- THE COMPONENTS SUM TO THE OBSERVED GAP"))
        say("A list of contributing factors that does not reconcile to the change cannot be")
        say("checked. These five do, exactly.")
        say()
        say(f"  {'component':<52}{'effect':>12}{'share':>9}{'hiring?':>10}")
        say(f"  {rule('-')[:83]}")
        for component in result.components:
            share = component.value / result.reported_gap if result.reported_gap else 0
            fixable = "yes" if component.addressable_by_headcount else "no"
            say(f"  {component.label[:51]:<52}{pp(component.value):>12}{share:>9.0%}"
                f"{fixable:>10}")
        say(f"  {rule('-')[:83]}")
        say(f"  {'TOTAL':<52}{pp(result.total_of_components):>12}")
        say(f"  {'Observed gap':<52}{pp(result.reported_gap):>12}")
        say(f"  {'Residual':<52}{result.residual * 100:>+12.10f}pp")
        say()
        say(f"  Not addressable by headcount: {pp(result.not_addressable_by_headcount)} of "
            f"{pp(result.reported_gap)} "
            f"({result.not_addressable_by_headcount / result.reported_gap:.0%} of the decline)")
        say()
        for component in result.components:
            say(f"  {component.label}  {pp(component.value)}")
            for line in _wrap(component.interpretation, WIDTH - 6):
                say(f"      {line}")
            for detail in component.detail:
                say(f"        - {detail}")
            say()

    # --------------------------------------------------------- 4. the ceiling #
    if wanted("ceiling"):
        say(heading("4. IS THE TARGET ACHIEVABLE AT ALL?"))
        say("SLA attainment has three obstacles: queueing, waiting on the customer, and the")
        say("work itself. Capacity shrinks the first. Nothing shrinks the third. So the work")
        say("clock is a hard ceiling on what any level of staffing could deliver.")
        say()
        say(f"  {'tier':<12}{'target':>8}{'handle':>9}{'queue':>8}{'pending':>9}"
            f"{'lost:queue':>12}{'lost:pending':>14}{'lost:work':>11}")
        say(f"  {rule('-')[:83]}")
        for row in composition.itertuples(index=False):
            say(f"  {row.tier:<12}{row.sla_target_hours:>7.0f}h{row.mean_handle_hours:>8.2f}h"
                f"{row.mean_queue_hours:>7.2f}h{row.mean_pending_hours:>8.2f}h"
                f"{row.pp_lost_to_queue:>11.2f}pp{row.pp_lost_to_pending:>13.2f}pp"
                f"{row.pp_lost_to_work_itself:>10.2f}pp")
        say()
        enterprise = ceiling[ceiling["tier"] == "enterprise"]
        say(f"  Enterprise attainment achievable at each candidate target "
            f"(threshold {exposure.threshold:.0%}):")
        say()
        say(f"  {'target':>8}{'ceiling (perfect ops)':>24}{'governed (today)':>19}"
            f"{'clears today?':>15}")
        say(f"  {rule('-')[:66]}")
        for row in enterprise.itertuples(index=False):
            marker = "  <-- current" if row.is_current_target else ""
            clears = "YES" if row.today_clears_threshold else "no"
            say(f"  {row.candidate_target_hours:>7.0f}h"
                f"{row.attainment_work_ceiling:>24.2%}{row.attainment_governed:>19.2%}"
                f"{clears:>15}{marker}")
        say()
        say(f"  THE FINDING: at the current {viable['current_target']:.0f}h target the ceiling is "
            f"{viable['current_ceiling']:.2%}, against a")
        say(f"  contractual threshold of {exposure.threshold:.0%}. Even with instant pickup and no "
            f"customer delay,")
        say(f"  {(1 - viable['current_ceiling']) * 100:.1f}% of enterprise tickets take longer "
            f"than {viable['current_target']:.0f}h of actual work. The target is")
        say("  unreachable at any staffing level. This is not an operational problem.")
        say()
        say(f"  At {viable['min_target_achievable_today']:.0f}h, attainment is already "
            f"{viable['attainment_at_that_target']:.2%} on the governed clock -- "
            f"{(viable['attainment_at_that_target'] - exposure.threshold) * 100:.2f}pp")
        say("  above the threshold, with no operational change whatsoever.")

    # -------------------------------------------------------- 5. the incident #
    if wanted("incident"):
        say(heading("5. HOW MUCH OF THE DECLINE IS ONE MONTH?"))
        say(f"  {'half':<6}{'attainment':>12}{'excl. incident':>16}{'incident drag':>15}")
        say(f"  {rule('-')[:49]}")
        for row in incident.itertuples(index=False):
            say(f"  {row.half:<6}{row.attainment_governed:>12.2%}"
                f"{row.attainment_excl_incident:>16.2%}{row.incident_drag * 100:>14.2f}pp")
        say()
        incident_month = int(incident["incident_month"].iloc[0])
        say("  Backlog trace -- did it drain, or is it still there?")
        say()
        say(f"  {'month':>6}{'peak backlog':>14}{'vs baseline':>13}{'queue h':>9}"
            f"{'governed':>10}{'normal?':>9}")
        say(f"  {rule('-')[:61]}")
        for row in backlog.itertuples(index=False):
            marker = " <-- incident" if row.is_incident_month else ""
            normal = "yes" if row.backlog_within_normal else "NO"
            say(f"  {row.month_index:>6}{row.peak_backlog:>14,}"
                f"{row.vs_baseline_multiple:>12.1f}x{row.mean_queue_wait_hours:>9.2f}"
                f"{row.attainment_governed:>10.2%}{normal:>9}{marker}")
        say()
        drained = backlog[(backlog["month_index"] > incident_month)
                          & backlog["backlog_within_normal"]]
        if len(drained):
            say(f"  The backlog was back within normal range by month "
                f"{int(drained['month_index'].iloc[0])}, one month after the incident.")
            say("  That changes the remedy: a backlog still growing needs capacity, a backlog")
            say("  that drained needs prevention. A contractor burst was considered and rejected")
            say("  on this evidence -- it would have been spend against a resolved symptom.")

        # Flag any later month that is drifting back out of range. Reporting only the
        # recovery would be selective: the whole point of this section is that a single
        # month can distort a half-average, and that cuts both ways.
        late = backlog[(backlog["month_index"] > incident_month)
                       & ~backlog["backlog_within_normal"]]
        if len(late):
            months = ", ".join(str(int(m)) for m in late["month_index"])
            say()
            say(f"  Worth watching rather than acting on: month(s) {months} drift back above "
                f"1.5x the")
            say("  baseline norm. Not an incident, but the enterprise share is still climbing, so")
            say("  capacity headroom is thinning. This is the case for the capacity model in the")
            say("  recommendation -- not for the headcount request.")

    # ----------------------------------------------------- 6. business case #
    if wanted("business_case"):
        say(heading("6. BUSINESS CASE"))
        say(f"  Enterprise book: {exposure.accounts} accounts, "
            f"{inr(exposure.total_arr)} ARR")
        say(f"  Contract terms:  {exposure.credit_pct:.0%} monthly service credit if attainment "
            f"< {exposure.threshold:.0%}")
        say(f"  Current:         {exposure.current_attainment:.2%} -- "
            f"{'IN BREACH' if exposure.in_breach else 'compliant'}")
        say(f"  Exposure:        {inr(exposure.monthly_credit)} per month = "
            f"{inr(exposure.annual_credit)} per year")
        say()
        say("  Service credits are a step function, not a gradient. An option that closes most")
        say("  of the gap saves nothing, which is why 'achievable' matters more than 'better'.")
        say()
        short = {
            "executive": f"Add {int(config['remedies']['executive_proposal']['headcount'])} "
                         f"permanent engineers",
            "recommended": f"Restate + re-baseline to "
                           f"{viable['min_target_achievable_today']:.0f}h + prevent",
            "do_nothing": "Change nothing",
        }
        say(f"  {'option':<40}{'one-off':>16}{'recurring/yr':>16}{'achievable':>13}"
            f"{'clears?':>10}")
        say(f"  {rule('-')[:95]}")
        for remedy in remedies:
            clears = "YES" if remedy.clears_threshold else "no"
            say(f"  {short[remedy.key]:<40}{inr(remedy.one_off_cost):>16}"
                f"{inr(remedy.recurring_annual_cost):>16}"
                f"{remedy.achievable_attainment:>13.2%}{clears:>10}")
        say()
        say(f"  {'option':<40}{'credits avoided':>18}{'year 1 net':>18}"
            f"{'steady state/yr':>18}")
        say(f"  {rule('-')[:94]}")
        for remedy in remedies:
            say(f"  {short[remedy.key]:<40}"
                f"{inr(remedy.annual_credit_avoided(exposure)):>18}"
                f"{inr(remedy.year_one_net(exposure)):>18}"
                f"{inr(remedy.steady_state_net(exposure)):>18}")
        say()
        for remedy in remedies:
            say(f"  {remedy.verdict}  --  {remedy.name}   [{remedy.proposer}]")
            for line in _wrap(remedy.rationale, WIDTH - 6):
                say(f"      {line}")
            for limit in remedy.limits:
                for index, line in enumerate(_wrap(limit, WIDTH - 10)):
                    say(f"      {'- ' if index == 0 else '  '}{line}")
            say()

    # ------------------------------------------------------ recommendation #
    say(heading("RECOMMENDATION"))
    recommended = next(r for r in remedies if r.key == "recommended")
    executive = next(r for r in remedies if r.key == "executive")
    say("  1. Restate SLA attainment on the governed clock and report it BY TIER, not blended.")
    say(f"     Removes {pp(result.component('definition').value)} of apparent decline at zero cost, and stops the")
    say("     blended figure hiding that every tier improved.")
    say()
    say(f"  2. Re-baseline the enterprise target from {viable['current_target']:.0f}h to "
        f"{viable['min_target_achievable_today']:.0f}h. At "
        f"{viable['current_target']:.0f}h the ceiling is")
    say(f"     {viable['current_ceiling']:.2%} against a {exposure.threshold:.0%} threshold -- "
        f"unreachable at any spend. At "
        f"{viable['min_target_achievable_today']:.0f}h we are at "
        f"{viable['attainment_at_that_target']:.2%} today.")
    say(f"     Worth {inr(exposure.annual_credit)} a year in avoided service credits.")
    say()
    say(f"  3. Fix the release-testing gap that caused the incident. "
        f"{inr(float(config['remedies']['recommended']['defect_prevention_cost']))} one-off,")
    say(f"     against a {pp(result.component('backlog').value)} hit to the half-average when it "
        f"last happened.")
    say()
    say(f"  4. Do NOT add {int(config['remedies']['executive_proposal']['headcount'])} permanent "
        f"engineers. {inr(executive.recurring_annual_cost)} a year, recurring, and it")
    say(f"     cannot reach the threshold: capacity closes "
        f"{(viable['current_ceiling'] - viable['current_governed']) * 100:.2f}pp of a "
        f"{(exposure.threshold - viable['current_governed']) * 100:.2f}pp gap.")
    say()
    say(f"  Total: {inr(recommended.one_off_cost)} one-off against "
        f"{inr(exposure.annual_credit)} a year recovered, versus")
    say(f"  the {inr(executive.recurring_annual_cost)}-a-year alternative that does not "
        f"achieve the objective.")
    say()
    say("  See FINDINGS.md for the one-page version.")
    say()

    connection.close()
    return {
        "decomposition": result,
        "exposure": exposure,
        "remedies": remedies,
        "viable": viable,
    }


def _wrap(text: str, width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if sum(len(w) + 1 for w in current) + len(word) > width and current:
            lines.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--section", action="append", default=None,
        choices=["trend", "hypotheses", "decomposition", "ceiling", "incident",
                 "business_case"],
        help="restrict output to one or more sections",
    )
    parser.add_argument("--config", default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    buffer = io.StringIO()
    analyse(config, buffer, set(args.section) if args.section else None)
    text = buffer.getvalue()
    sys.stdout.write(text)
    ANALYSIS_PATH.write_text(text, encoding="utf-8")
    print(f"analysis written to {ANALYSIS_PATH.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
