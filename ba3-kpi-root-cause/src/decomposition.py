"""Decompose the change in SLA attainment into components that sum to the observed gap.

The whole value of this module is the word *exactly*. A root-cause analysis that offers
a list of contributing factors without reconciling them to the observed change cannot be
checked, and cannot be argued with productively: any factor can be added or dropped
without the total noticing. If the components sum to the gap to floating-point
precision, the analysis is falsifiable.

The identity implemented here is:

    reported gap = definition + mix + interaction + backlog + performance

built in two stages.

**Stage 1 -- restate the metric.** The reporting migration means the two halves are
measured on different clocks. H1 was reported on the governed clock (pending-customer
time excluded); H2 is reported on the strict clock (pending time included). So:

    definition = A2(strict) - A2(governed)

H1 needs no restatement, which is why the whole definitional distortion sits in H2.

**Stage 2 -- decompose the like-for-like gap.** With both halves on the governed clock,
the remaining gap splits over service tiers in the standard way:

    mix         = sum_t (w2_t - w1_t) * r1_t          the mix moved
    rate        = sum_t w1_t * (r2_t - r1_t)          performance within tiers moved
    interaction = sum_t (w2_t - w1_t) * (r2_t - r1_t) both moved together

and the rate term splits again using a third clock that excludes queue wait, isolating
how much of the within-tier change is queueing rather than work:

    performance = sum_t w1_t * (r2_t(work) - r1_t(work))
    backlog     = -sum_t w1_t * ((r2_t(work) - r2_t(net)) - (r1_t(work) - r1_t(net)))

Each of the three clocks is recorded per ticket by the generator:

    work    = handle                            what the work itself took
    net     = queue_wait + handle               the governed SLA clock
    strict  = queue_wait + handle + pending     what the new tool reports

Splitting the rate term is the step that separates a *stock* problem from a *flow*
problem. Backlog is a stock: it is created by a burst of demand and drains slowly, so it
depresses attainment for months after the causing event. Permanent capacity fixes a flow
problem. The two need different remedies, and the aggregate metric cannot tell them
apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The clock used by each half's *reported* figure. H1 predates the platform migration.
REPORTED_CLOCK = {"H1": "net", "H2": "strict"}
GOVERNED_CLOCK = "net"


@dataclass(frozen=True)
class TierStats:
    """Share of volume and attainment on each clock, for one tier in one half."""

    tier: str
    tickets: int
    share: float
    attainment_work: float
    attainment_net: float
    attainment_strict: float

    def attainment(self, clock: str) -> float:
        return {
            "work": self.attainment_work,
            "net": self.attainment_net,
            "strict": self.attainment_strict,
        }[clock]

    @property
    def backlog_drag(self) -> float:
        """Attainment lost to queue wait: what the work clock achieves, minus the net clock.

        Non-negative by construction -- removing queue wait can only move a ticket from
        breach to met, never the reverse.
        """
        return self.attainment_work - self.attainment_net

    @property
    def pending_drag(self) -> float:
        """Attainment lost by including pending-customer time in the clock."""
        return self.attainment_net - self.attainment_strict


@dataclass
class Component:
    key: str
    label: str
    value: float
    interpretation: str
    addressable_by_headcount: bool
    detail: list[str] = field(default_factory=list)

    @property
    def pp(self) -> float:
        return self.value * 100


@dataclass
class Decomposition:
    baseline_half: str
    current_half: str
    baseline_reported: float
    current_reported: float
    current_governed: float
    baseline_tiers: dict[str, TierStats]
    current_tiers: dict[str, TierStats]
    components: list[Component]

    @property
    def reported_gap(self) -> float:
        return self.current_reported - self.baseline_reported

    @property
    def governed_gap(self) -> float:
        """The gap that survives restating both halves on the same clock."""
        return self.current_governed - self.baseline_reported

    @property
    def total_of_components(self) -> float:
        return sum(c.value for c in self.components)

    @property
    def residual(self) -> float:
        """Must be zero. This is the property that makes the analysis checkable."""
        return self.reported_gap - self.total_of_components

    def component(self, key: str) -> Component:
        return next(c for c in self.components if c.key == key)

    @property
    def not_addressable_by_headcount(self) -> float:
        """Sum of the components that adding support engineers cannot move.

        The number the business case turns on. A measurement artefact and a structural
        mix shift do not respond to hiring, and saying so with a figure attached is more
        useful than saying the proposal is misdirected.
        """
        return sum(c.value for c in self.components
                   if not c.addressable_by_headcount and c.value < 0)


def summarise_tiers(rows: list[dict]) -> dict[str, TierStats]:
    """Build TierStats from aggregate rows produced by SQL.

    Each row needs: tier, tickets, met_work, met_net, met_strict.
    """
    total = sum(int(row["tickets"]) for row in rows)
    if total == 0:
        raise ValueError("no tickets in half")

    stats: dict[str, TierStats] = {}
    for row in rows:
        tickets = int(row["tickets"])
        stats[row["tier"]] = TierStats(
            tier=row["tier"],
            tickets=tickets,
            share=tickets / total,
            attainment_work=float(row["met_work"]) / tickets,
            attainment_net=float(row["met_net"]) / tickets,
            attainment_strict=float(row["met_strict"]) / tickets,
        )
    return stats


def attainment(tiers: dict[str, TierStats], clock: str) -> float:
    """Volume-weighted attainment across tiers on a given clock."""
    return sum(t.share * t.attainment(clock) for t in tiers.values())


def decompose(
    baseline_tiers: dict[str, TierStats],
    current_tiers: dict[str, TierStats],
    *,
    baseline_half: str = "H1",
    current_half: str = "H2",
) -> Decomposition:
    """Split the reported change in SLA attainment into five additive components."""
    tiers = sorted(set(baseline_tiers) | set(current_tiers))
    missing = [t for t in tiers if t not in baseline_tiers or t not in current_tiers]
    if missing:
        raise ValueError(
            f"tier(s) {missing} appear in only one half. A tier that did not exist in the "
            f"baseline cannot be decomposed into mix and rate, because it has no baseline "
            f"rate -- it needs to be reported separately as new business."
        )

    baseline_clock = REPORTED_CLOCK[baseline_half]
    current_clock = REPORTED_CLOCK[current_half]

    baseline_reported = attainment(baseline_tiers, baseline_clock)
    current_reported = attainment(current_tiers, current_clock)
    current_governed = attainment(current_tiers, GOVERNED_CLOCK)

    # -- stage 1: the measurement artefact ---------------------------------- #
    definition = current_reported - current_governed
    worst_tier = min(
        tiers, key=lambda t: current_tiers[t].share * current_tiers[t].pending_drag)

    # -- stage 2: mix, rate, interaction on the governed clock --------------- #
    mix = sum(
        (current_tiers[t].share - baseline_tiers[t].share)
        * baseline_tiers[t].attainment(GOVERNED_CLOCK)
        for t in tiers
    )
    interaction = sum(
        (current_tiers[t].share - baseline_tiers[t].share)
        * (current_tiers[t].attainment(GOVERNED_CLOCK)
           - baseline_tiers[t].attainment(GOVERNED_CLOCK))
        for t in tiers
    )

    # -- stage 3: split the rate term into queueing and work ---------------- #
    performance = sum(
        baseline_tiers[t].share
        * (current_tiers[t].attainment_work - baseline_tiers[t].attainment_work)
        for t in tiers
    )
    backlog = -sum(
        baseline_tiers[t].share
        * (current_tiers[t].backlog_drag - baseline_tiers[t].backlog_drag)
        for t in tiers
    )

    shift = {t: current_tiers[t].share - baseline_tiers[t].share for t in tiers}
    grew = max(tiers, key=lambda t: shift[t])
    shrank = min(tiers, key=lambda t: shift[t])

    components = [
        Component(
            key="definition",
            label="Measurement change (clock-pause rule lost in migration)",
            value=definition,
            interpretation=(
                "Not a change in performance. The current half is measured on a stricter "
                "clock than the baseline: the platform migration stopped excluding "
                "approved pending-customer time. Restating both halves on the governed "
                "definition removes this entirely."
            ),
            addressable_by_headcount=False,
            detail=[
                f"{current_tiers[t].tier}: including pending time costs "
                f"{current_tiers[t].pending_drag * 100:.1f}pp within the tier, "
                f"weighted {current_tiers[t].share * current_tiers[t].pending_drag * 100:.2f}pp"
                for t in sorted(tiers, key=lambda t: -current_tiers[t].share
                                * current_tiers[t].pending_drag)
            ],
        ),
        Component(
            key="mix",
            label="Service-tier mix shift",
            value=mix,
            interpretation=(
                f"Structural, not performance. {grew} volume share rose from "
                f"{baseline_tiers[grew].share:.1%} to {current_tiers[grew].share:.1%} while "
                f"{shrank} fell from {baseline_tiers[shrank].share:.1%} to "
                f"{current_tiers[shrank].share:.1%}. Tiers carry different SLA targets, so "
                f"identical operational performance scores worse against a harder mix."
            ),
            addressable_by_headcount=False,
            detail=[
                f"{t}: share {baseline_tiers[t].share:+.1%} -> {current_tiers[t].share:.1%} "
                f"({shift[t] * 100:+.1f}pp) at baseline attainment "
                f"{baseline_tiers[t].attainment(GOVERNED_CLOCK):.1%} "
                f"contributes {shift[t] * baseline_tiers[t].attainment(GOVERNED_CLOCK) * 100:+.2f}pp"
                for t in sorted(tiers, key=lambda t: shift[t])
            ],
        ),
        Component(
            key="backlog",
            label="Backlog carried forward from the release defect",
            value=backlog,
            interpretation=(
                "Transient, and the only component a capacity intervention can move. A "
                "three-week demand spike from a release defect created a backlog; queue wait "
                "rose while it drained. This is a stock problem, not a flow problem, and the "
                "backlog was back within normal range a month later -- so the remedy is "
                "preventing recurrence, not adding permanent capacity to sustain. Note which "
                "tier absorbed it: priority ordering protected the tightest SLA and pushed "
                "the damage onto the loosest one, so the tier detail below runs opposite to "
                "intuition."
            ),
            addressable_by_headcount=True,
            detail=[
                f"{t}: attainment lost to queue wait "
                f"{baseline_tiers[t].backlog_drag * 100:.1f}pp -> "
                f"{current_tiers[t].backlog_drag * 100:.1f}pp, weighted "
                f"{-baseline_tiers[t].share * (current_tiers[t].backlog_drag - baseline_tiers[t].backlog_drag) * 100:+.2f}pp"
                for t in tiers
            ],
        ),
        Component(
            key="performance",
            label="Within-tier work performance",
            value=performance,
            interpretation=(
                "The team got faster. Measured on the work clock, which excludes both "
                "queueing and pending-customer time, within-tier attainment moved in the "
                "opposite direction to the headline metric."
            ),
            addressable_by_headcount=True,
            detail=[
                f"{t}: work-clock attainment "
                f"{baseline_tiers[t].attainment_work:.1%} -> "
                f"{current_tiers[t].attainment_work:.1%} "
                f"({(current_tiers[t].attainment_work - baseline_tiers[t].attainment_work) * 100:+.1f}pp)"
                for t in tiers
            ],
        ),
        Component(
            key="interaction",
            label="Interaction between mix and rate",
            value=interaction,
            interpretation=(
                "The arithmetic residual of mix and rate moving at the same time. Reported "
                "separately rather than folded into either, because assigning it to one of "
                "them would overstate that component."
            ),
            addressable_by_headcount=False,
        ),
    ]

    del worst_tier
    return Decomposition(
        baseline_half=baseline_half,
        current_half=current_half,
        baseline_reported=baseline_reported,
        current_reported=current_reported,
        current_governed=current_governed,
        baseline_tiers=baseline_tiers,
        current_tiers=current_tiers,
        components=components,
    )
