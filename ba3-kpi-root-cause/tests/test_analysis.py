"""Tests for the Project ATLAS root-cause analysis.

Four groups:

1. **The decomposition identity.** The five components must sum to the observed gap to
   floating-point precision. This is the property that makes the analysis falsifiable, so
   it is tested on the real data and on synthetic edge cases.
2. **The generator planted what it claims.** The scenario config is ground truth. If the
   mix shift, the productivity gain, the definitional break and the backlog are not
   actually present and detectable, the analysis is reading back the author's intention.
3. **The hypothesis audit.** Verdicts, and specifically that H03 is eliminated on a
   MIX-ADJUSTED basis -- the blended version returns the wrong answer and there is a test
   asserting that too, because the trap is the point.
4. **Every documented number.** Each figure quoted in FINDINGS.md, README.md, LEARN.md and
   the metric dictionary is pinned, so a scenario change that invalidates the prose fails
   the build.
"""

from __future__ import annotations

import math

import pytest
import yaml

from data.generate_tickets import Calendar, ramp
from src.business_case import build_exposure, build_remedies, minimum_viable_target
from src.decomposition import (
    GOVERNED_CLOCK,
    TierStats,
    attainment,
    decompose,
    summarise_tiers,
)
from src.run import CONFIG_PATH, load_config, tier_rows
from src.warehouse import build, capacity_frame, query


@pytest.fixture(scope="module")
def config():
    return load_config()


@pytest.fixture(scope="module")
def connection(config):
    con = build(config)
    yield con
    con.close()


@pytest.fixture(scope="module")
def result(connection):
    return decompose(
        summarise_tiers(tier_rows(connection, "H1")),
        summarise_tiers(tier_rows(connection, "H2")),
    )


@pytest.fixture(scope="module")
def hypotheses(connection):
    frame = query(connection, "SELECT * FROM atlas.hypotheses")
    return {row.hypothesis_id: row for row in frame.itertuples(index=False)}


# --------------------------------------------------------------------------- #
# 1. The decomposition identity
# --------------------------------------------------------------------------- #
def test_components_sum_to_the_observed_gap(result):
    """The property the whole analysis rests on."""
    assert result.residual == pytest.approx(0.0, abs=1e-12)
    assert result.total_of_components == pytest.approx(result.reported_gap, abs=1e-12)


def test_definition_component_equals_the_restatement(result):
    """Stage 1 must exactly account for the clock change, and nothing else."""
    definition = result.component("definition").value
    assert definition == pytest.approx(result.current_reported - result.current_governed,
                                       abs=1e-12)
    # The baseline half predates the migration, so it needs no restatement.
    assert result.baseline_reported == pytest.approx(
        attainment(result.baseline_tiers, GOVERNED_CLOCK), abs=1e-12)


def test_mix_rate_interaction_sum_to_the_governed_gap(result):
    """Stage 2 must exactly account for the like-for-like gap."""
    mix = result.component("mix").value
    interaction = result.component("interaction").value
    backlog = result.component("backlog").value
    performance = result.component("performance").value
    assert mix + interaction + backlog + performance == pytest.approx(
        result.governed_gap, abs=1e-12)


def test_backlog_and_performance_sum_to_the_rate_term(result):
    """Stage 3 splits the rate term without changing its total."""
    rate = sum(
        result.baseline_tiers[t].share
        * (result.current_tiers[t].attainment(GOVERNED_CLOCK)
           - result.baseline_tiers[t].attainment(GOVERNED_CLOCK))
        for t in result.baseline_tiers
    )
    assert (result.component("backlog").value
            + result.component("performance").value) == pytest.approx(rate, abs=1e-12)


def test_identity_holds_when_nothing_changes():
    """A synthetic no-change case must produce a zero gap and zero components."""
    tiers = {
        "a": TierStats("a", 100, 0.5, 0.9, 0.9, 0.9),
        "b": TierStats("b", 100, 0.5, 0.8, 0.8, 0.8),
    }
    result = decompose(tiers, tiers)
    assert result.reported_gap == pytest.approx(0.0, abs=1e-12)
    for component in result.components:
        assert component.value == pytest.approx(0.0, abs=1e-12)


def test_identity_holds_for_a_pure_mix_shift():
    """Shares move, within-tier rates do not: everything must land in the mix term."""
    baseline = {
        "a": TierStats("a", 900, 0.9, 1.0, 1.0, 1.0),
        "b": TierStats("b", 100, 0.1, 0.5, 0.5, 0.5),
    }
    current = {
        "a": TierStats("a", 500, 0.5, 1.0, 1.0, 1.0),
        "b": TierStats("b", 500, 0.5, 0.5, 0.5, 0.5),
    }
    result = decompose(baseline, current)
    assert result.residual == pytest.approx(0.0, abs=1e-12)
    assert result.component("mix").value == pytest.approx(result.reported_gap, abs=1e-12)
    for key in ("performance", "backlog", "interaction", "definition"):
        assert result.component(key).value == pytest.approx(0.0, abs=1e-12)


def test_a_tier_present_in_only_one_half_is_refused():
    """A new tier has no baseline rate, so it cannot be split into mix and rate."""
    baseline = {"a": TierStats("a", 100, 1.0, 0.9, 0.9, 0.9)}
    current = {
        "a": TierStats("a", 50, 0.5, 0.9, 0.9, 0.9),
        "new": TierStats("new", 50, 0.5, 0.7, 0.7, 0.7),
    }
    with pytest.raises(ValueError, match="only one half"):
        decompose(baseline, current)


def test_drag_measures_are_non_negative(result):
    """Removing queue wait or pending time can only help attainment, never hurt it."""
    for tiers in (result.baseline_tiers, result.current_tiers):
        for stats in tiers.values():
            assert stats.backlog_drag >= 0.0
            assert stats.pending_drag >= 0.0
            assert stats.attainment_work >= stats.attainment_net >= stats.attainment_strict


# --------------------------------------------------------------------------- #
# 2. The generator planted what the analysis claims to find
# --------------------------------------------------------------------------- #
def test_tier_mix_actually_shifted(result):
    baseline = result.baseline_tiers["enterprise"].share
    current = result.current_tiers["enterprise"].share
    assert current > baseline * 2, "the up-market push should be unmistakable"
    assert result.baseline_tiers["standard"].share > result.current_tiers["standard"].share


def test_every_tier_improved_on_the_work_clock(result):
    """The productivity gain has to be real and visible within every tier."""
    for tier in result.baseline_tiers:
        assert (result.current_tiers[tier].attainment_work
                > result.baseline_tiers[tier].attainment_work), tier


def test_the_definitional_break_exists_only_in_the_current_half(connection):
    frame = query(connection, """
        SELECT half, MAX(reported_clock) AS clock, COUNT(DISTINCT reported_clock) AS clocks
        FROM atlas.ticket_sla GROUP BY half ORDER BY half
    """)
    rows = {row.half: row for row in frame.itertuples(index=False)}
    assert rows["H1"].clock == "net"
    assert rows["H2"].clock == "strict"
    assert rows["H1"].clocks == 1
    assert rows["H2"].clocks == 1


def test_the_backlog_spiked_and_then_drained(connection, config):
    frame = query(connection, "SELECT * FROM atlas.backlog_trace ORDER BY month_index")
    incident_month = int(config["defect_spike"]["month"])
    rows = {int(row.month_index): row for row in frame.itertuples(index=False)}

    assert not rows[incident_month].backlog_within_normal, "the incident should be visible"
    assert rows[incident_month].vs_baseline_multiple > 3.0
    assert rows[incident_month + 1].backlog_within_normal, "it should drain within a month"
    # And it should be the worst month for attainment.
    worst = min(rows.values(), key=lambda r: r.attainment_governed)
    assert int(worst.month_index) == incident_month


def test_capacity_kept_pace_with_trend_demand(connection):
    """If capacity had lagged, the executive proposal would be right."""
    frame = query(connection, """
        SELECT m.half,
               SUM(m.tickets) / SUM(d.days) / AVG(c.capacity_per_day) AS utilisation
        FROM atlas.monthly_attainment m
        JOIN atlas.capacity c USING (month_index)
        JOIN (SELECT month_index, COUNT(DISTINCT arrival_day) AS days
              FROM atlas.ticket_sla GROUP BY month_index) d USING (month_index)
        GROUP BY m.half ORDER BY m.half
    """)
    utilisation = dict(zip(frame["half"], frame["utilisation"], strict=True))
    assert 0.80 < utilisation["H1"] < 0.95
    assert 0.80 < utilisation["H2"] < 0.95
    assert abs(utilisation["H2"] - utilisation["H1"]) < 0.06, (
        "utilisation should be roughly flat, so a chronic capacity shortfall can be ruled out"
    )


def test_quality_signals_did_not_degrade_materially(connection):
    frame = query(connection, """
        SELECT half,
               AVG(CASE WHEN reopened  THEN 1.0 ELSE 0.0 END) AS reopen,
               AVG(CASE WHEN escalated THEN 1.0 ELSE 0.0 END) AS escalate
        FROM atlas.ticket_sla GROUP BY half ORDER BY half
    """)
    rows = {row.half: row for row in frame.itertuples(index=False)}
    assert rows["H2"].reopen <= rows["H1"].reopen + 0.01
    assert rows["H2"].escalate <= rows["H1"].escalate + 0.01


def test_ramp_endpoints_and_monotonicity():
    """Shares must interpolate, not step, and must respect their endpoints."""
    values = [ramp(m, 12, 6, 0.06, 0.31) for m in range(1, 13)]
    assert values[0] == pytest.approx(0.06)
    assert values[-1] == pytest.approx(0.31)
    assert values == sorted(values)


def test_calendar_resolves_months_correctly():
    import datetime as dt
    calendar = Calendar(start=dt.date(2025, 3, 1), months=12)
    assert calendar.month_start(1) == dt.date(2025, 3, 1)
    assert calendar.month_start(11) == dt.date(2026, 1, 1)
    assert calendar.month_days(1) == 31
    assert calendar.month_of(dt.date(2026, 1, 15)) == 11


def test_capacity_frame_ramps_between_its_endpoints(config):
    frame = capacity_frame(config)
    assert frame["agents"].iloc[0] == pytest.approx(
        config["capacity"]["agents_first_month"])
    assert frame["agents"].iloc[-1] == pytest.approx(
        config["capacity"]["agents_final_month"])
    assert list(frame["agents"]) == sorted(frame["agents"])


# --------------------------------------------------------------------------- #
# 3. The hypothesis audit
# --------------------------------------------------------------------------- #
def test_all_twelve_hypotheses_are_evaluated(hypotheses):
    assert len(hypotheses) == 12
    assert set(hypotheses) == {f"H{n:02d}" for n in range(1, 13)}


def test_verdicts_are_as_documented(hypotheses):
    expected = {
        "H01": "ELIMINATED",   # demand outgrew capacity
        "H02": "ELIMINATED",   # headcount fell
        "H03": "ELIMINATED",   # agents got slower -- the executive premise
        "H04": "ELIMINATED",   # rework rose
        "H05": "ELIMINATED",   # escalations rose
        "H06": "PARTIAL",      # routing accuracy
        "H07": "PARTIAL",      # tenure mix
        "H08": "RETAINED",     # tier mix
        "H09": "RETAINED",     # clock definition
        "H10": "RETAINED",     # incident backlog
        "H11": "REFRAMED",     # seasonality -- untestable
        "H12": "RETAINED",     # target unachievable
    }
    actual = {key: row.verdict for key, row in hypotheses.items()}
    assert actual == expected


def test_h03_is_eliminated_on_a_mix_adjusted_basis(hypotheses, result):
    """The executive premise, tested the right way.

    The value carried on H03 must match the decomposition's performance component,
    because they are the same construction: within-tier rates held at baseline shares.
    """
    row = hypotheses["H03"]
    assert row.verdict == "ELIMINATED"
    assert row.h2_value > row.h1_value, "performance improved"
    measured = row.h2_value - row.h1_value
    assert measured == pytest.approx(result.component("performance").value, abs=1e-9)


def test_the_blended_version_of_h03_would_have_returned_the_wrong_answer(result):
    """The trap, asserted explicitly.

    Blended work-clock attainment falls while every tier improves, because volume moved
    to a tier with a tighter target. If this test ever fails, the scenario has lost the
    property that makes the project interesting.
    """
    blended_h1 = attainment(result.baseline_tiers, "work")
    blended_h2 = attainment(result.current_tiers, "work")
    assert blended_h2 < blended_h1, "the blended figure should fall"
    assert result.component("performance").value > 0, "while mix-adjusted performance rises"


def test_retained_hypotheses_are_the_ones_in_the_decomposition(hypotheses, result):
    retained = {key for key, row in hypotheses.items() if row.verdict == "RETAINED"}
    assert retained == {"H08", "H09", "H10", "H12"}
    # And each of the three quantified ones is a negative component.
    for key in ("mix", "definition", "backlog"):
        assert result.component(key).value < 0


# --------------------------------------------------------------------------- #
# 4. Every documented number
# --------------------------------------------------------------------------- #
def test_headline_attainment_matches_the_documents(result):
    assert result.baseline_reported == pytest.approx(0.9502, abs=0.0002)
    assert result.current_reported == pytest.approx(0.8596, abs=0.0002)
    assert result.current_governed == pytest.approx(0.8867, abs=0.0002)
    assert result.reported_gap == pytest.approx(-0.0906, abs=0.0003)


def test_component_values_match_the_documents(result):
    expected = {
        "definition": -0.0271,
        "mix": -0.0411,
        "backlog": -0.0536,
        "performance": +0.0099,
        "interaction": +0.0215,
    }
    for key, value in expected.items():
        assert result.component(key).value == pytest.approx(value, abs=0.0004), key


def test_three_quarters_of_the_decline_is_not_addressable_by_headcount(result):
    share = result.not_addressable_by_headcount / result.reported_gap
    assert result.not_addressable_by_headcount == pytest.approx(-0.0682, abs=0.0006)
    assert share == pytest.approx(0.75, abs=0.02)


def test_the_enterprise_target_is_unachievable(connection, config):
    ceiling = query(connection, "SELECT * FROM atlas.sla_ceiling")
    threshold = float(config["commercial"]["service_credit_threshold"])
    viable = minimum_viable_target(ceiling, "enterprise", threshold)

    assert viable["current_target"] == 4.0
    assert viable["current_ceiling"] == pytest.approx(0.8560, abs=0.0015)
    assert viable["current_ceiling"] < threshold, (
        "the whole recommendation rests on the ceiling sitting below the threshold"
    )
    # And the minimum target that clears it today.
    assert viable["min_target_achievable_today"] == 8.0
    assert viable["attainment_at_that_target"] == pytest.approx(0.9720, abs=0.0015)
    assert viable["attainment_at_that_target"] > threshold


def test_capacity_closes_only_a_third_of_the_enterprise_gap(connection, config):
    ceiling = query(connection, "SELECT * FROM atlas.sla_ceiling")
    threshold = float(config["commercial"]["service_credit_threshold"])
    viable = minimum_viable_target(ceiling, "enterprise", threshold)

    closable = viable["current_ceiling"] - viable["current_governed"]
    total_gap = threshold - viable["current_governed"]
    assert closable == pytest.approx(0.0475, abs=0.0015)
    assert total_gap == pytest.approx(0.1415, abs=0.0015)
    assert closable / total_gap < 0.40


def test_service_credit_exposure(config, result):
    exposure = build_exposure(config, result.current_tiers["enterprise"].attainment_net)
    assert exposure.in_breach
    assert exposure.total_arr == pytest.approx(142_800_000)
    assert exposure.monthly_credit == pytest.approx(595_000)
    assert exposure.annual_credit == pytest.approx(7_140_000)


def test_business_case_rejects_the_executive_proposal(connection, config, result):
    ceiling = query(connection, "SELECT * FROM atlas.sla_ceiling")
    exposure = build_exposure(config, result.current_tiers["enterprise"].attainment_net)
    remedies = {r.key: r for r in build_remedies(config, ceiling, exposure)}

    executive = remedies["executive"]
    assert not executive.clears_threshold
    assert executive.verdict.startswith("REJECT")
    assert executive.recurring_annual_cost == pytest.approx(9_600_000)
    # It saves nothing, because service credits are a step function.
    assert executive.annual_credit_avoided(exposure) == 0.0
    assert executive.steady_state_net(exposure) == pytest.approx(-9_600_000)


def test_business_case_recommends_restating_and_rebaselining(connection, config, result):
    ceiling = query(connection, "SELECT * FROM atlas.sla_ceiling")
    exposure = build_exposure(config, result.current_tiers["enterprise"].attainment_net)
    remedies = {r.key: r for r in build_remedies(config, ceiling, exposure)}

    recommended = remedies["recommended"]
    assert recommended.clears_threshold
    assert recommended.verdict == "RECOMMEND"
    assert recommended.one_off_cost == pytest.approx(1_250_000)
    assert recommended.recurring_annual_cost == 0.0
    assert recommended.year_one_net(exposure) == pytest.approx(5_890_000)
    assert recommended.steady_state_net(exposure) == pytest.approx(7_140_000)
    # And it beats the executive proposal by more than a crore a year.
    assert (recommended.steady_state_net(exposure)
            - remedies["executive"].steady_state_net(exposure)) > 10_000_000


def test_doing_nothing_is_not_free(connection, config, result):
    ceiling = query(connection, "SELECT * FROM atlas.sla_ceiling")
    exposure = build_exposure(config, result.current_tiers["enterprise"].attainment_net)
    remedies = {r.key: r for r in build_remedies(config, ceiling, exposure)}
    do_nothing = remedies["do_nothing"]
    assert not do_nothing.clears_threshold
    assert do_nothing.annual_credit_avoided(exposure) == 0.0


def test_incident_month_drags_the_half_average(connection):
    frame = query(connection, "SELECT * FROM atlas.incident_isolation ORDER BY half")
    rows = {row.half: row for row in frame.itertuples(index=False)}
    assert rows["H1"].incident_drag == pytest.approx(0.0, abs=1e-9)
    assert rows["H2"].incident_drag == pytest.approx(-0.0350, abs=0.001)
    assert rows["H2"].attainment_excl_incident > rows["H2"].attainment_governed


def test_margins_and_clocks_are_ordered_as_documented(connection):
    frame = query(connection, "SELECT * FROM atlas.half_summary ORDER BY half")
    rows = {row.half: row for row in frame.itertuples(index=False)}
    # Work is the ceiling, strict is the harshest, governed sits between.
    for half in ("H1", "H2"):
        row = rows[half]
        assert row.attainment_work > row.attainment_governed > row.attainment_strict
    # H1 reported the governed clock; H2 reported the strict one.
    assert rows["H1"].attainment_as_reported == pytest.approx(rows["H1"].attainment_governed)
    assert rows["H2"].attainment_as_reported == pytest.approx(rows["H2"].attainment_strict)


def test_config_is_internally_consistent(config):
    """Guards the ground truth itself."""
    tiers = config["tiers"]
    assert sum(t["share_start"] for t in tiers.values()) == pytest.approx(1.0)
    assert sum(t["share_end"] for t in tiers.values()) == pytest.approx(1.0)
    assert sum(c["weight"] for c in config["categories"]) == pytest.approx(1.0)
    # Enterprise must be the tightest target and the highest queue priority.
    assert tiers["enterprise"]["sla_target_hours"] == min(
        t["sla_target_hours"] for t in tiers.values())
    assert tiers["enterprise"]["queue_priority"] == min(
        t["queue_priority"] for t in tiers.values())
    # The definitional break must fall at the start of the current half.
    assert (config["definition_change"]["effective_month"]
            == config["meta"]["baseline_months"] + 1)
    # The incident must fall inside the current half.
    assert config["defect_spike"]["month"] > config["meta"]["baseline_months"]


def test_config_path_resolves():
    assert CONFIG_PATH.exists()
    assert yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["meta"]["months"] == 12


def test_attainment_helper_is_a_weighted_average():
    tiers = {
        "a": TierStats("a", 750, 0.75, 1.0, 1.0, 1.0),
        "b": TierStats("b", 250, 0.25, 0.0, 0.0, 0.0),
    }
    assert attainment(tiers, "net") == pytest.approx(0.75)
    assert not math.isnan(attainment(tiers, "work"))
