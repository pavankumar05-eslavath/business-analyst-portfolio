"""Cost the remedies against what each one can actually achieve.

A business case that only prices options is half a business case. The other half is
whether the option can deliver the objective at all, and that is where this one turns:
the executive proposal is not merely expensive, it is **incapable** of reaching the
contractual threshold at any spend level, because the binding constraint is handling
effort rather than capacity.

So every option here is scored on three things:

1. **Cost** -- and whether it is recurring or one-off, which matters more than the
   headline figure.
2. **Achievable attainment** -- the best outcome the option can produce, taken from the
   work-clock ceiling rather than from optimism.
3. **Whether it clears the threshold** -- a boolean, because service credits are a step
   function, not a gradient. An option that gets 90% of the way to 95% saves nothing.

The third column is the one that ends the argument.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class CreditExposure:
    """Annual service-credit cost of missing the contractual threshold."""

    accounts: int
    arr_per_account: float
    credit_pct: float
    threshold: float
    current_attainment: float

    @property
    def total_arr(self) -> float:
        return self.accounts * self.arr_per_account

    @property
    def monthly_fees(self) -> float:
        return self.total_arr / 12

    @property
    def in_breach(self) -> bool:
        return self.current_attainment < self.threshold

    @property
    def monthly_credit(self) -> float:
        return self.monthly_fees * self.credit_pct if self.in_breach else 0.0

    @property
    def annual_credit(self) -> float:
        return self.monthly_credit * 12


@dataclass
class Remedy:
    key: str
    name: str
    proposer: str
    one_off_cost: float
    recurring_annual_cost: float
    achievable_attainment: float
    threshold: float
    rationale: str
    limits: list[str] = field(default_factory=list)

    @property
    def clears_threshold(self) -> bool:
        return self.achievable_attainment >= self.threshold

    @property
    def shortfall_pp(self) -> float:
        return (self.threshold - self.achievable_attainment) * 100

    def annual_credit_avoided(self, exposure: CreditExposure) -> float:
        """Service credits are a step function, so partial improvement saves nothing."""
        return exposure.annual_credit if self.clears_threshold else 0.0

    def year_one_net(self, exposure: CreditExposure) -> float:
        return (self.annual_credit_avoided(exposure)
                - self.recurring_annual_cost - self.one_off_cost)

    def steady_state_net(self, exposure: CreditExposure) -> float:
        """From year two onward, once one-off costs are behind you."""
        return self.annual_credit_avoided(exposure) - self.recurring_annual_cost

    @property
    def verdict(self) -> str:
        if not self.clears_threshold:
            return "REJECT -- cannot reach the threshold"
        return "RECOMMEND"


def build_exposure(config: dict, enterprise_attainment: float) -> CreditExposure:
    commercial = config["commercial"]
    return CreditExposure(
        accounts=int(commercial["enterprise_accounts"]),
        arr_per_account=float(commercial["enterprise_arr_per_account"]),
        credit_pct=float(commercial["service_credit_pct"]),
        threshold=float(commercial["service_credit_threshold"]),
        current_attainment=enterprise_attainment,
    )


def minimum_viable_target(ceiling: pd.DataFrame, tier: str, threshold: float) -> dict:
    """The tightest SLA target this tier can already meet on the governed clock.

    Read off the ceiling table rather than assumed. Two columns matter and they answer
    different questions: `today_clears_threshold` is what the target could be changed to
    with no operational change at all, and `ceiling_clears_threshold` is what would be
    possible with perfect operations. Recommending the second without funding the
    operations change is how a target gets agreed and then missed.
    """
    rows = ceiling[ceiling["tier"] == tier].sort_values("candidate_target_hours")
    today = rows[rows["today_clears_threshold"]]
    ceiling_only = rows[rows["ceiling_clears_threshold"]]

    return {
        "current_target": float(rows["current_target_hours"].iloc[0]),
        "current_ceiling": float(
            rows[rows["is_current_target"]]["attainment_work_ceiling"].iloc[0]),
        "current_governed": float(
            rows[rows["is_current_target"]]["attainment_governed"].iloc[0]),
        "min_target_achievable_today": (
            float(today["candidate_target_hours"].iloc[0]) if len(today) else None),
        "attainment_at_that_target": (
            float(today["attainment_governed"].iloc[0]) if len(today) else None),
        "min_target_achievable_at_ceiling": (
            float(ceiling_only["candidate_target_hours"].iloc[0])
            if len(ceiling_only) else None),
        "attainment_at_ceiling_target": (
            float(ceiling_only["attainment_work_ceiling"].iloc[0])
            if len(ceiling_only) else None),
        "threshold": threshold,
    }


def build_remedies(config: dict, ceiling: pd.DataFrame,
                   exposure: CreditExposure) -> list[Remedy]:
    """The three courses of action, scored on cost and on capability."""
    executive = config["remedies"]["executive_proposal"]
    recommended = config["remedies"]["recommended"]
    viable = minimum_viable_target(ceiling, "enterprise", exposure.threshold)

    headcount = int(executive["headcount"])
    annual_per_engineer = float(executive["annual_cost_per_engineer"])

    # What can more capacity buy? At best it removes queue wait entirely, taking
    # attainment from where it is today to the work-clock ceiling. Not one point beyond.
    ceiling_at_current_target = viable["current_ceiling"]
    governed_today = viable["current_governed"]

    recommended_one_off = (
        float(recommended["capacity_model_cost"])
        + float(recommended["defect_prevention_cost"])
        + float(recommended["restatement_cost"])
    )
    contractor_cost = (
        int(recommended["contractor_count"])
        * int(recommended["contractor_weeks"])
        * float(recommended["contractor_weekly_cost"])
    )

    remedies = [
        Remedy(
            key="executive",
            name=f"Add {headcount} permanent support engineers",
            proposer="VP Support",
            one_off_cost=0.0,
            recurring_annual_cost=headcount * annual_per_engineer,
            # Capacity can remove queueing. It cannot make the work shorter.
            achievable_attainment=ceiling_at_current_target,
            threshold=exposure.threshold,
            rationale=(
                "Premised on the team having become slower. The mix-adjusted work clock "
                "shows the opposite -- within-tier handling performance improved."
            ),
            limits=[
                f"Best case removes ALL queue wait, taking enterprise attainment from "
                f"{governed_today:.2%} to the work-clock ceiling of "
                f"{ceiling_at_current_target:.2%}. That is "
                f"{(ceiling_at_current_target - governed_today) * 100:.2f}pp of the "
                f"{(exposure.threshold - governed_today) * 100:.2f}pp gap to the threshold.",
                f"The remaining "
                f"{(exposure.threshold - ceiling_at_current_target) * 100:.2f}pp is handling "
                f"effort. No headcount removes it, so service credits continue to be paid "
                f"in full at a cost of INR {exposure.annual_credit:,.0f} a year.",
                "Recurring, not one-off: the cost repeats every year and the objective is "
                "never met.",
            ],
        ),
        Remedy(
            key="recommended",
            name=(
                f"Restate the metric, re-baseline the enterprise target to "
                f"{viable['min_target_achievable_today']:.0f}h, and prevent recurrence"
                if viable["min_target_achievable_today"] else
                "Restate the metric and re-baseline the enterprise target"
            ),
            proposer="Business Analysis",
            one_off_cost=recommended_one_off,
            recurring_annual_cost=0.0,
            achievable_attainment=viable["attainment_at_that_target"] or 0.0,
            threshold=exposure.threshold,
            rationale=(
                "Three of the four causes are not capacity problems. Restating the clock "
                "removes the measurement artefact at zero cost; re-baselining the target "
                "against what the work actually takes removes the structural gap; fixing "
                "the release-testing gap prevents the incident recurring."
            ),
            limits=[
                f"Requires a commercial conversation, not an operational one. The "
                f"{viable['current_target']:.0f}h commitment was sold by Sales without a "
                f"capacity model, and moving it to "
                f"{viable['min_target_achievable_today']:.0f}h needs customer agreement.",
                f"At {viable['min_target_achievable_today']:.0f}h, enterprise attainment is "
                f"already {viable['attainment_at_that_target']:.2%} on the governed clock "
                f"with no operational change at all -- "
                f"{(viable['attainment_at_that_target'] - exposure.threshold) * 100:.2f}pp "
                f"of headroom above the threshold.",
                f"A contractor burst to clear backlog was considered and is NOT included: "
                f"INR {contractor_cost:,.0f} of spend against a backlog that had already "
                f"drained. Recommending it would have been treating a resolved symptom.",
            ],
        ),
        Remedy(
            key="do_nothing",
            name="Change nothing",
            proposer="—",
            one_off_cost=0.0,
            recurring_annual_cost=0.0,
            achievable_attainment=governed_today,
            threshold=exposure.threshold,
            rationale=(
                "Included as the baseline every option is measured against. Doing nothing "
                "is not free: the service credits continue."
            ),
            limits=[
                f"Service credits of INR {exposure.annual_credit:,.0f} a year continue "
                f"indefinitely.",
                "The reported metric also continues to be wrong, so the next review "
                "reaches the same incorrect diagnosis.",
            ],
        ),
    ]
    return remedies


def summarise(remedies: list[Remedy], exposure: CreditExposure) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "option": r.name,
            "one_off": r.one_off_cost,
            "recurring_annual": r.recurring_annual_cost,
            "achievable_attainment": r.achievable_attainment,
            "clears_threshold": r.clears_threshold,
            "credits_avoided_annual": r.annual_credit_avoided(exposure),
            "year_one_net": r.year_one_net(exposure),
            "steady_state_net": r.steady_state_net(exposure),
            "verdict": r.verdict,
        }
        for r in remedies
    ])
