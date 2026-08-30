"""The three proposals, their break-even points, scenarios and sensitivity grids.

A decision memo needs three things a model usually does not provide:

1. **The answer under the numbers we believe.**
2. **The break-even value of the driver the answer turns on.** This is the part
   that survives disagreement. Nobody has to accept my incrementality estimate if
   I can say "this works only above 74%, and the pilot measured 43%".
3. **What would change the recommendation.** Stated up front, so that the decision
   can be revisited on evidence rather than relitigated on opinion.

Each proposal below is measured against the same yardstick: change in **monthly
CM3 contribution**, because that is the level at which dark-store fixed costs are
real and central overhead is not yet allocated. Comparing proposals on CM2 would
flatter anything that adds stores; comparing on EBITDA would penalise everything
equally with overhead none of these decisions changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .drivers import Drivers
from .model import (
    UnitEconomics,
    build_unit_economics,
    rider_payout_at_density,
    threshold_effect,
)


@dataclass
class Decision:
    """One proposal, evaluated."""

    key: str
    title: str
    short_title: str
    proposer: str
    base: UnitEconomics
    proposed: UnitEconomics
    monthly_delta: float
    annual_delta: float
    capex: float = 0.0
    recurring_cost_monthly: float = 0.0
    verdict: str = ""
    break_even_label: str = ""
    break_even_value: float = 0.0
    observed_value: float | None = None
    observed_label: str = ""
    # Whether a *higher* observed value is favourable. True for incrementality
    # (more genuinely new demand is better), False for a volume decline (a smaller
    # drop is better). Without this the safety margin reads backwards on one of the
    # three proposals, which is exactly the kind of sign error that survives review.
    higher_is_better: bool = True
    notes: list[str] = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.verdict.startswith("APPROVE")

    @property
    def margin_of_safety_pp(self) -> float | None:
        """Percentage points of headroom between observed and break-even."""
        if self.observed_value is None:
            return None
        gap = self.observed_value - self.break_even_value
        return (gap if self.higher_is_better else -gap) * 100

    @property
    def clears_break_even(self) -> bool:
        margin = self.margin_of_safety_pp
        return margin is not None and margin > 0

    @property
    def payback_months(self) -> float | None:
        if self.capex <= 0:
            return None
        if self.monthly_delta <= 0:
            return None
        return self.capex / self.monthly_delta

    @property
    def order_growth(self) -> float:
        return self.proposed.orders_per_month / self.base.orders_per_month - 1.0

    @property
    def revenue_growth(self) -> float:
        base_rev = self.base.total_revenue * self.base.orders_per_month
        new_rev = self.proposed.total_revenue * self.proposed.orders_per_month
        return new_rev / base_rev - 1.0


# --------------------------------------------------------------------------- #
# Decision 1 -- open 12 more dark stores in the existing three cities
# --------------------------------------------------------------------------- #
def evaluate_store_expansion(drivers: Drivers, base: UnitEconomics) -> Decision:
    """The proposal that looks like scale and is not.

    Order volume rises and so does revenue, which is why this proposal reads well
    in a growth deck. But dark-store fixed cost is incurred *per store*, and most
    of a new store's volume in an already-covered city is demand that moved off a
    neighbour rather than demand that did not exist. Orders per store -- the
    denominator that fixed cost is spread over -- therefore falls.
    """
    days = drivers.days_per_month
    base_stores = drivers["dark_stores"]
    new_stores = drivers["new_stores"]
    total_stores = base_stores + new_stores
    new_store_opd = drivers["orders_per_new_store_per_day"]
    incrementality = drivers["incrementality"]

    # Only the incremental share is genuinely new demand. The rest is cannibalised.
    incremental_orders_per_day = new_stores * new_store_opd * incrementality
    total_orders_per_day = base_stores * base.orders_per_store_per_day + incremental_orders_per_day
    opd_per_store = total_orders_per_day / total_stores

    rider = rider_payout_at_density(drivers, total_stores)

    proposed = build_unit_economics(
        drivers,
        label=f"{int(new_stores)} new stores",
        stores=total_stores,
        orders_per_store_per_day=opd_per_store,
        rider_payout=rider,
        baseline_orders_per_month=base.orders_per_month,
    )

    monthly_delta = proposed.cm3_total - base.cm3_total
    capex = new_stores * drivers["capex_per_store"]

    # Break-even incrementality: the share of a new store's orders that must be
    # genuinely new for contribution to be unchanged. Solved on CM2, which does not
    # depend on incrementality, against the higher fixed base of a larger estate.
    store_fixed_per_store = (
        drivers["rent"] + drivers["utilities"]
        + drivers["store_staff"] + drivers["security_and_other"]
    )
    fixed_after = total_stores * store_fixed_per_store
    required_orders_per_month = (base.cm3_total + fixed_after) / proposed.cm2
    required_orders_per_day = required_orders_per_month / days
    break_even_incrementality = (
        (required_orders_per_day - base_stores * base.orders_per_store_per_day)
        / (new_stores * new_store_opd)
    )

    return Decision(
        key="store_expansion",
        title=f"Open {int(new_stores)} dark stores in the existing three cities",
        short_title=f"Open {int(new_stores)} dark stores (infill)",
        proposer="Growth",
        base=base,
        proposed=proposed,
        monthly_delta=monthly_delta,
        annual_delta=monthly_delta * 12,
        capex=capex,
        verdict="REJECT" if monthly_delta < 0 else "APPROVE",
        break_even_label="Incrementality required to break even",
        break_even_value=break_even_incrementality,
        observed_value=incrementality,
        observed_label="Incrementality measured in the 2-store pilot",
        higher_is_better=True,
        notes=[
            f"Orders per store per day falls from {base.orders_per_store_per_day:,.0f} to "
            f"{opd_per_store:,.0f} because {(1 - incrementality) * 100:.0f}% of each new "
            f"store's volume is cannibalised from a neighbour.",
            f"Dark-store fixed cost per order therefore rises from "
            f"INR {base.store_fixed_per_order:.2f} to INR {proposed.store_fixed_per_order:.2f}.",
            f"The proposal is credited with the densification benefit it genuinely earns: "
            f"shorter rides cut rider payout from INR {base.rider_payout:.2f} to "
            f"INR {rider:.2f} per order. It still does not clear.",
            "Not modelled, and all three run against the proposal: thinner per-store "
            "inventory pooling raises spoilage, lower per-store volume worsens picking "
            "efficiency, and new stores take months to reach even the assumed volume.",
        ],
    )


# --------------------------------------------------------------------------- #
# Decision 2 -- raise the free-delivery threshold
# --------------------------------------------------------------------------- #
def evaluate_threshold_change(drivers: Drivers, base: UnitEconomics) -> Decision:
    """Small lever, real money, and the risk is measurable rather than assumed."""
    proposed_threshold = drivers["proposed_threshold"]
    effect = threshold_effect(drivers, proposed_threshold)
    observed_decline = drivers["observed_volume_response"]

    at_constant_volume = build_unit_economics(
        drivers,
        label=f"Threshold INR {proposed_threshold:,.0f}, volume held",
        gross_order_value=effect.gross_order_value,
        delivery_fee_income=effect.delivery_fee_income,
        fee_paying_share=effect.fee_paying_share,
        baseline_orders_per_month=base.orders_per_month,
    )

    # The honest version applies the volume response measured the last time this
    # lever moved. A delivery fee is a friction, and friction suppresses order
    # frequency even when the rupee amount is small.
    proposed = build_unit_economics(
        drivers,
        label=f"Threshold INR {proposed_threshold:,.0f}",
        orders_per_store_per_day=base.orders_per_store_per_day * (1.0 - observed_decline),
        gross_order_value=effect.gross_order_value,
        delivery_fee_income=effect.delivery_fee_income,
        fee_paying_share=effect.fee_paying_share,
        baseline_orders_per_month=base.orders_per_month,
    )

    monthly_delta = proposed.cm3_total - base.cm3_total

    # Break-even volume decline: how much order volume can fall before the
    # threshold change stops paying for itself.
    break_even_decline = 1.0 - (
        (base.cm3_total + base.store_fixed_total)
        / (at_constant_volume.cm2 * base.orders_per_month)
    )

    naive_monthly = at_constant_volume.cm3_total - base.cm3_total

    return Decision(
        key="threshold_change",
        title=(
            f"Raise the free-delivery threshold from "
            f"INR {drivers['free_delivery_threshold']:,.0f} to INR {proposed_threshold:,.0f}"
        ),
        short_title=(
            f"Threshold INR {drivers['free_delivery_threshold']:,.0f} -> "
            f"INR {proposed_threshold:,.0f}"
        ),
        proposer="Pricing",
        base=base,
        proposed=proposed,
        monthly_delta=monthly_delta,
        annual_delta=monthly_delta * 12,
        verdict="APPROVE" if monthly_delta > 0 else "REJECT",
        break_even_label="Order-volume decline that would wipe out the gain",
        break_even_value=break_even_decline,
        observed_value=observed_decline,
        observed_label="Volume decline observed at the last threshold move",
        # A *smaller* decline is favourable here, unlike incrementality.
        higher_is_better=False,
        notes=[
            f"Fee-paying share of orders rises from {base.fee_paying_share * 100:.1f}% to "
            f"{effect.fee_paying_share * 100:.1f}%, lifting delivery fee income from "
            f"INR {base.delivery_fee_income:.2f} to INR {effect.delivery_fee_income:.2f} per order.",
            f"{effect.upsized_share * 100:.1f}% of orders up-size to clear the threshold, "
            f"raising average basket from INR {base.gross_order_value:.2f} to "
            f"INR {effect.gross_order_value:.2f}.",
            f"Held at constant volume the gain would be INR {naive_monthly / 1e5:,.1f} lakh a "
            f"month. Applying the measured volume response takes it to "
            f"INR {monthly_delta / 1e5:,.1f} lakh -- still positive, but "
            f"{(1 - monthly_delta / naive_monthly) * 100:.0f}% smaller.",
            "The recommendation rests on a measured number, not an elasticity assumption: "
            "the break-even decline is several times the decline actually observed when "
            "this lever last moved.",
        ],
    )


# --------------------------------------------------------------------------- #
# Decision 3 -- raise retail media income
# --------------------------------------------------------------------------- #
def evaluate_retail_media(drivers: Drivers, base: UnitEconomics) -> Decision:
    """The boring proposal that beats both of the interesting ones."""
    proposed_income = drivers["proposed_income"]
    recurring = drivers["delivery_cost"]

    proposed = build_unit_economics(
        drivers,
        label=f"Retail media INR {proposed_income:.0f}/order",
        retail_media_income=proposed_income,
        extra_fixed_monthly=recurring,
        baseline_orders_per_month=base.orders_per_month,
    )

    monthly_delta = proposed.cm3_total - base.cm3_total
    uplift = proposed_income - base.retail_media_income

    # Break-even: how much of the proposed uplift must actually land.
    break_even_uplift = recurring / base.orders_per_month
    break_even_share = break_even_uplift / uplift if uplift else 0.0

    return Decision(
        key="retail_media",
        title=(
            f"Raise retail media income from INR {base.retail_media_income:.0f} to "
            f"INR {proposed_income:.0f} per order"
        ),
        short_title=f"Retail media INR {base.retail_media_income:.0f} -> "
                    f"INR {proposed_income:.0f}/order",
        proposer="Category",
        base=base,
        proposed=proposed,
        monthly_delta=monthly_delta,
        annual_delta=monthly_delta * 12,
        recurring_cost_monthly=recurring,
        verdict="APPROVE" if monthly_delta > 0 else "REJECT",
        break_even_label="Share of the proposed uplift that must land to break even",
        break_even_value=break_even_share,
        observed_value=None,
        observed_label="",
        notes=[
            f"Brand-funded income is invoiced, not collected through the consumer payment "
            f"rail, so it carries no gateway fee and no fulfilment cost. The full "
            f"INR {uplift:.2f} per order reaches CM1.",
            f"Only INR {break_even_uplift:.2f} of the INR {uplift:.2f} uplift is needed to "
            f"cover the INR {recurring / 1e5:.1f} lakh monthly cost of the team and ad-serving "
            f"build -- {break_even_share * 100:.0f}% of the target.",
            "No customer-facing change, so no volume risk. This is the only one of the "
            "three proposals whose downside is bounded by its own cost.",
        ],
    )


# --------------------------------------------------------------------------- #
# Break-even and scenario analysis
# --------------------------------------------------------------------------- #
@dataclass
class BreakEven:
    cm3_orders_per_store_per_day: float
    ebitda_orders_per_store_per_day: float
    ebitda_stores_at_current_density: float
    current_orders_per_store_per_day: float

    @property
    def cm3_headroom(self) -> float:
        return (self.current_orders_per_store_per_day
                / self.cm3_orders_per_store_per_day - 1.0)

    @property
    def ebitda_gap(self) -> float:
        return (self.ebitda_orders_per_store_per_day
                / self.current_orders_per_store_per_day - 1.0)


def compute_break_even(drivers: Drivers, base: UnitEconomics) -> BreakEven:
    """Order density at which CM3 and then EBITDA turn positive.

    Expressed in orders per store per day rather than in rupees, because that is
    the number an operator can act on and the number the business already tracks.
    """
    days = drivers.days_per_month
    stores = base.stores
    store_fixed_per_store = base.store_fixed_total / stores

    # CM3 = 0 when CM2 per order covers store fixed cost per order.
    cm3_opd = store_fixed_per_store / (base.cm2 * days)

    # EBITDA = 0 when CM2 covers store fixed, central overhead and marketing.
    fixed_total = base.store_fixed_total + base.central_overhead_total + base.marketing_total
    ebitda_opd = fixed_total / (base.cm2 * days * stores)

    # Alternatively, hold density and ask how many stores the current cost base
    # could support -- the "grow into the overhead" question.
    ebitda_stores = (base.central_overhead_total + base.marketing_total) / (
        base.cm2 * base.orders_per_store_per_day * days - store_fixed_per_store
    )

    return BreakEven(
        cm3_orders_per_store_per_day=cm3_opd,
        ebitda_orders_per_store_per_day=ebitda_opd,
        ebitda_stores_at_current_density=ebitda_stores,
        current_orders_per_store_per_day=base.orders_per_store_per_day,
    )


def build_scenarios(drivers: Drivers, base: UnitEconomics) -> list[UnitEconomics]:
    """Base, bull and bear, driven off the scenario block in the driver file."""
    results = [base]
    for name, spec in drivers.scenarios.items():
        opd = base.orders_per_store_per_day * (1.0 + spec.get("orders_per_store_per_day_pct", 0.0))
        margin = drivers["product_gross_margin_pct"] + spec.get(
            "product_gross_margin_pct_delta", 0.0)
        rider = drivers["rider_payout"] * (1.0 + spec.get("rider_payout_pct", 0.0))
        gov_multiplier = 1.0 + spec.get("gross_order_value_pct", 0.0)
        effect = threshold_effect(drivers, drivers["free_delivery_threshold"])

        results.append(build_unit_economics(
            drivers,
            label=name.title(),
            orders_per_store_per_day=opd,
            gross_order_value=effect.gross_order_value * gov_multiplier,
            delivery_fee_income=effect.delivery_fee_income,
            fee_paying_share=effect.fee_paying_share,
            rider_payout=rider,
            product_gross_margin_pct=margin,
            baseline_orders_per_month=base.orders_per_month,
        ))
    return results


# --------------------------------------------------------------------------- #
# Two-way sensitivity grids
# --------------------------------------------------------------------------- #
@dataclass
class SensitivityGrid:
    title: str
    row_label: str
    col_label: str
    row_values: list[float]
    col_values: list[float]
    cells: list[list[float]]
    unit: str
    row_format: str = "{:,.0f}"
    col_format: str = "{:.1%}"
    cell_format: str = "{:,.2f}"


def cm3_sensitivity(drivers: Drivers, base: UnitEconomics) -> SensitivityGrid:
    """CM3 per order against order density and product gross margin.

    These two drivers are chosen because they are the model's largest exposures:
    one is operational and slow to move, the other is commercial and negotiated
    annually. Everything else is second order by comparison.
    """
    densities = [300.0, 340.0, 380.0, 420.0, 460.0, 500.0, 540.0]
    margins = [0.185, 0.200, 0.215, 0.230, 0.245]
    cells = [
        [
            build_unit_economics(
                drivers,
                orders_per_store_per_day=density,
                product_gross_margin_pct=margin,
                baseline_orders_per_month=base.orders_per_month,
            ).cm3
            for margin in margins
        ]
        for density in densities
    ]
    return SensitivityGrid(
        title="CM3 per order (INR)",
        row_label="Orders per store per day",
        col_label="Product gross margin",
        row_values=densities,
        col_values=margins,
        cells=cells,
        unit="INR per order",
    )


def expansion_sensitivity(drivers: Drivers, base: UnitEconomics) -> SensitivityGrid:
    """Monthly contribution change from the expansion, across the two unknowns.

    Incrementality and steady-state volume per new store are the only two things
    that matter for this decision, and both are measurable in a pilot. The grid is
    the argument for running a bigger pilot rather than for guessing harder.
    """
    base_stores = drivers["dark_stores"]
    new_stores = drivers["new_stores"]
    total_stores = base_stores + new_stores
    rider = rider_payout_at_density(drivers, total_stores)

    incrementalities = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
    volumes = [200.0, 250.0, 300.0, 350.0, 400.0]

    def delta_lakh(incrementality: float, volume: float) -> float:
        orders_per_day = (base_stores * base.orders_per_store_per_day
                          + new_stores * volume * incrementality)
        proposed = build_unit_economics(
            drivers,
            stores=total_stores,
            orders_per_store_per_day=orders_per_day / total_stores,
            rider_payout=rider,
            baseline_orders_per_month=base.orders_per_month,
        )
        return (proposed.cm3_total - base.cm3_total) / 1e5

    cells = [
        [delta_lakh(incrementality, volume) for volume in volumes]
        for incrementality in incrementalities
    ]

    return SensitivityGrid(
        title="Change in monthly CM3 contribution (INR lakh)",
        row_label="Incrementality of new store volume",
        col_label="Orders per new store per day",
        row_values=incrementalities,
        col_values=volumes,
        cells=cells,
        unit="INR lakh per month",
        row_format="{:.0%}",
        col_format="{:,.0f}",
        cell_format="{:+,.1f}",
    )


def evaluate_all(drivers: Drivers, base: UnitEconomics) -> list[Decision]:
    return [
        evaluate_store_expansion(drivers, base),
        evaluate_threshold_change(drivers, base),
        evaluate_retail_media(drivers, base),
    ]


@dataclass
class CombinedResult:
    """Both approved proposals applied together, plus the interaction they carry."""

    combined: UnitEconomics
    monthly_delta: float
    sum_of_parts_monthly: float

    @property
    def annual_delta(self) -> float:
        return self.monthly_delta * 12

    @property
    def interaction(self) -> float:
        """Combined effect minus the sum of the individual effects.

        Negative because retail media income is earned per order, and the threshold
        change removes some orders. Adding the two business cases together
        double-counts income on orders that will no longer exist.
        """
        return self.monthly_delta - self.sum_of_parts_monthly


def evaluate_combined(
    drivers: Drivers, base: UnitEconomics, approved: list[Decision]
) -> CombinedResult:
    """Apply every approved proposal at once rather than adding their business cases.

    Two accretive levers are almost never additive, and the direction of the error
    is predictable: anything measured per order is overstated by a lever that
    reduces order count. Presenting the sum of the parts would overstate the
    recommendation, which is the failure mode this function exists to avoid.
    """
    keys = {d.key for d in approved}
    effect = threshold_effect(drivers, drivers["proposed_threshold"])

    opd = base.orders_per_store_per_day
    gov = None
    fee_income = None
    fee_share = 0.0
    media = None
    extra_fixed = 0.0

    if "threshold_change" in keys:
        opd = opd * (1.0 - drivers["observed_volume_response"])
        gov = effect.gross_order_value
        fee_income = effect.delivery_fee_income
        fee_share = effect.fee_paying_share
    if "retail_media" in keys:
        media = drivers["proposed_income"]
        extra_fixed = drivers["delivery_cost"]

    combined = build_unit_economics(
        drivers,
        label="Both approved",
        orders_per_store_per_day=opd,
        gross_order_value=gov,
        delivery_fee_income=fee_income,
        fee_paying_share=fee_share,
        retail_media_income=media,
        extra_fixed_monthly=extra_fixed,
        baseline_orders_per_month=base.orders_per_month,
    )

    return CombinedResult(
        combined=combined,
        monthly_delta=combined.cm3_total - base.cm3_total,
        sum_of_parts_monthly=sum(d.monthly_delta for d in approved),
    )
