"""The unit economics model: basket distribution, CM ladder, cohorts, channels.

Three things here are worth reading before the arithmetic.

**The CM ladder is defined once and used everywhere.** CM1, CM2 and CM3 are used
loosely across the industry, and two people comparing "contribution margin" are
usually comparing different things. The definitions in `METRIC_DEFINITIONS.md`
are the ones implemented here, and the split point that matters is CM2 -> CM3:
CM2 stops before dark-store fixed cost, CM3 absorbs it. Which side of that line
you stand on changes whether several decisions in this model look good.

**Fixed costs are held fixed in rupees, not per order.** Dark-store rent, central
overhead and the marketing budget do not move when order volume moves. Modelling
them as a per-order rate and then holding that rate constant while volume changes
is the most common error in this kind of model, and it is precisely the error that
makes store expansion look free.

**The basket distribution is modelled, not averaged.** A free-delivery threshold
acts on the *distribution* of basket values, not on the mean. You cannot evaluate
a threshold change with an average order value, because the entire mechanism is
about which side of the threshold each order falls on.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .drivers import Channel, Drivers


# --------------------------------------------------------------------------- #
# Basket value distribution
# --------------------------------------------------------------------------- #
def normal_cdf(z: float) -> float:
    """Standard normal CDF. Excel's NORM.S.DIST(z, TRUE), implemented via erf.

    Deliberately stdlib. The workbook computes the same thing with NORM.S.DIST,
    and the test suite asserts the two agree, so this needs to be a plain
    mathematical identity rather than a library-specific implementation.
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


@dataclass(frozen=True)
class BasketDistribution:
    """Lognormal basket values calibrated so the mean equals observed AOV.

    Lognormal because basket values are positive, right-skewed, and have a median
    below the mean -- which is what grocery baskets look like. Calibrating on the
    mean (rather than the median) means the distribution reproduces the AOV the
    business actually reports.
    """

    mean: float
    sigma: float

    @property
    def mu(self) -> float:
        return math.log(self.mean) - 0.5 * self.sigma ** 2

    @property
    def median(self) -> float:
        return math.exp(self.mu)

    def z(self, value: float) -> float:
        return (math.log(value) - self.mu) / self.sigma

    def share_below(self, threshold: float) -> float:
        """P(basket < threshold)."""
        return normal_cdf(self.z(threshold))

    def partial_mean_below(self, threshold: float) -> float:
        """E[X . 1{X < threshold}] -- the value contributed by sub-threshold orders."""
        return self.mean * normal_cdf(self.z(threshold) - self.sigma)

    def band_share(self, low: float, high: float) -> float:
        return self.share_below(high) - self.share_below(low)

    def band_mean(self, low: float, high: float) -> float:
        """Average basket value of orders falling inside [low, high)."""
        share = self.band_share(low, high)
        if share <= 0:
            return 0.0
        value = self.partial_mean_below(high) - self.partial_mean_below(low)
        return value / share


def rider_payout_at_density(drivers: Drivers, stores: float) -> float:
    """Rider payout per order at a given store count in the same geography.

    Adding stores to a city the company already covers shrinks each catchment, so
    rides get shorter. Delivery distance is taken as proportional to the square
    root of area per store, which for fixed city area means distance scales with
    1/sqrt(stores). Only the distance-linked share of the payout moves; base fee,
    pickup and handover do not.

    This exists so the store-expansion proposal is evaluated with its real benefit
    included rather than dismissed on an unfair comparison.
    """
    base_stores = drivers["dark_stores"]
    share = drivers["rider_payout_distance_share"]
    ratio = math.sqrt(base_stores / stores)
    return drivers["rider_payout"] * (1.0 - share + share * ratio)


@dataclass(frozen=True)
class ThresholdEffect:
    """What a free-delivery threshold does to fee income and average basket."""

    threshold: float
    fee_paying_share_before_upsize: float
    upsize_band_low: float
    upsize_band_share: float
    upsize_band_mean: float
    upsized_share: float
    fee_paying_share: float
    gross_order_value: float
    delivery_fee_income: float


def threshold_effect(drivers: Drivers, threshold: float, *,
                     apply_upsizing: bool = True) -> ThresholdEffect:
    """Resolve a threshold into the two figures the CM ladder needs.

    Raising a threshold does two things that pull in opposite directions for the
    customer and the same direction for us: more orders pay the fee, and some
    customers add items to escape it. Both are computed off the basket
    distribution rather than assumed.
    """
    basket = BasketDistribution(drivers["gross_order_value"], drivers["basket_log_sigma"])
    fee = drivers["delivery_fee"]

    share_below = basket.share_below(threshold)
    band_low = threshold * (1.0 - drivers["upsize_band_width"])
    band_share = basket.band_share(band_low, threshold)
    band_mean = basket.band_mean(band_low, threshold)

    propensity = drivers["upsize_propensity"] if apply_upsizing else 0.0
    upsized_share = band_share * propensity

    # Up-sizers cross the threshold, so they stop paying the fee and their basket
    # rises to the threshold value.
    fee_paying_share = share_below - upsized_share
    gov = basket.mean + upsized_share * (threshold - band_mean)

    return ThresholdEffect(
        threshold=threshold,
        fee_paying_share_before_upsize=share_below,
        upsize_band_low=band_low,
        upsize_band_share=band_share,
        upsize_band_mean=band_mean,
        upsized_share=upsized_share,
        fee_paying_share=fee_paying_share,
        gross_order_value=gov,
        delivery_fee_income=fee_paying_share * fee,
    )


# --------------------------------------------------------------------------- #
# The contribution margin ladder
# --------------------------------------------------------------------------- #
@dataclass
class UnitEconomics:
    """Per-order P&L plus the monthly rollup, for one configuration of drivers."""

    label: str

    # volume
    stores: float
    orders_per_store_per_day: float
    orders_per_month: float

    # revenue
    gross_order_value: float
    platform_funded_discount: float
    net_order_value: float
    delivery_fee_income: float
    handling_fee: float
    retail_media_income: float
    total_revenue: float

    # to CM1
    cogs: float
    payment_gateway: float
    packaging: float
    cm1: float

    # to CM2
    rider_payout: float
    picking_labour: float
    spoilage: float
    cm2: float

    # to CM3
    store_fixed_per_order: float
    cm3: float

    # below the line
    central_overhead_per_order: float
    marketing_per_order: float
    ebitda_per_order: float

    # monthly totals
    store_fixed_total: float
    central_overhead_total: float
    marketing_total: float
    cm2_total: float
    cm3_total: float
    ebitda_total: float

    fee_paying_share: float = 0.0

    def pct_of_nov(self, value: float) -> float:
        return value / self.net_order_value

    def as_ladder(self) -> list[tuple[str, float, float]]:
        """(line, per-order value, % of NOV) in presentation order."""
        rows = [
            ("Net order value", self.net_order_value),
            ("Delivery fee income", self.delivery_fee_income),
            ("Handling fee income", self.handling_fee),
            ("Retail media income", self.retail_media_income),
            ("Total revenue", self.total_revenue),
            ("Cost of goods sold", -self.cogs),
            ("Payment gateway", -self.payment_gateway),
            ("Packaging material", -self.packaging),
            ("CM1 (gross contribution)", self.cm1),
            ("Rider payout", -self.rider_payout),
            ("Picking labour", -self.picking_labour),
            ("Spoilage and shrinkage", -self.spoilage),
            ("CM2 (store contribution)", self.cm2),
            ("Dark store fixed, allocated", -self.store_fixed_per_order),
            ("CM3 (fully loaded store)", self.cm3),
            ("Central overhead", -self.central_overhead_per_order),
            ("Marketing", -self.marketing_per_order),
            ("EBITDA per order", self.ebitda_per_order),
        ]
        return [(name, value, value / self.net_order_value) for name, value in rows]


def build_unit_economics(
    drivers: Drivers,
    *,
    label: str = "Base",
    stores: float | None = None,
    orders_per_store_per_day: float | None = None,
    gross_order_value: float | None = None,
    delivery_fee_income: float | None = None,
    retail_media_income: float | None = None,
    fee_paying_share: float = 0.0,
    extra_fixed_monthly: float = 0.0,
    baseline_orders_per_month: float | None = None,
    rider_payout: float | None = None,
    product_gross_margin_pct: float | None = None,
) -> UnitEconomics:
    """Compute the ladder for one configuration.

    `baseline_orders_per_month` matters. Central overhead and the marketing budget
    are stated per order in the driver file for readability, but they are fixed
    rupee amounts. They are converted to absolute monthly figures using the
    *baseline* volume and then held constant, so that a scenario which changes
    volume correctly sees overhead per order move.
    """
    days = drivers.days_per_month
    stores = drivers["dark_stores"] if stores is None else stores
    opd = (drivers["orders_per_store_per_day"]
           if orders_per_store_per_day is None else orders_per_store_per_day)
    orders_per_month = stores * opd * days

    if baseline_orders_per_month is None:
        baseline_orders_per_month = (
            drivers["dark_stores"] * drivers["orders_per_store_per_day"] * days
        )

    if delivery_fee_income is None:
        effect = threshold_effect(drivers, drivers["free_delivery_threshold"])
        delivery_fee_income = effect.delivery_fee_income
        fee_paying_share = effect.fee_paying_share
        if gross_order_value is None:
            gross_order_value = effect.gross_order_value

    gov = drivers["gross_order_value"] if gross_order_value is None else gross_order_value
    media = (drivers["retail_media_income"]
             if retail_media_income is None else retail_media_income)

    discount = drivers["platform_funded_discount"]
    nov = gov - discount
    handling = drivers["handling_fee"]

    total_revenue = nov + delivery_fee_income + handling + media

    margin = (drivers["product_gross_margin_pct"]
              if product_gross_margin_pct is None else product_gross_margin_pct)
    cogs = nov * (1.0 - margin)
    # Retail media is invoiced to brands, not collected through the consumer
    # payment rail, so it carries no MDR. Charging gateway fees against it would
    # understate the highest-margin line in the model.
    collected = nov + delivery_fee_income + handling
    payment_gateway = collected * drivers["payment_gateway_pct"]
    packaging = drivers["packaging_material"]
    cm1 = total_revenue - cogs - payment_gateway - packaging

    rider = drivers["rider_payout"] if rider_payout is None else rider_payout
    picking = drivers["picking_labour"]
    spoilage = gov * drivers["spoilage_pct"]
    cm2 = cm1 - rider - picking - spoilage

    store_fixed_per_store = (
        drivers["rent"] + drivers["utilities"]
        + drivers["store_staff"] + drivers["security_and_other"]
    )
    store_fixed_total = stores * store_fixed_per_store + extra_fixed_monthly
    store_fixed_per_order = store_fixed_total / orders_per_month
    cm3 = cm2 - store_fixed_per_order

    central_total = drivers["central_overhead_per_order"] * baseline_orders_per_month
    marketing_total = drivers["marketing_per_order"] * baseline_orders_per_month
    central_per_order = central_total / orders_per_month
    marketing_per_order = marketing_total / orders_per_month
    ebitda_per_order = cm3 - central_per_order - marketing_per_order

    return UnitEconomics(
        label=label,
        stores=stores,
        orders_per_store_per_day=opd,
        orders_per_month=orders_per_month,
        gross_order_value=gov,
        platform_funded_discount=discount,
        net_order_value=nov,
        delivery_fee_income=delivery_fee_income,
        handling_fee=handling,
        retail_media_income=media,
        total_revenue=total_revenue,
        cogs=cogs,
        payment_gateway=payment_gateway,
        packaging=packaging,
        cm1=cm1,
        rider_payout=rider,
        picking_labour=picking,
        spoilage=spoilage,
        cm2=cm2,
        store_fixed_per_order=store_fixed_per_order,
        cm3=cm3,
        central_overhead_per_order=central_per_order,
        marketing_per_order=marketing_per_order,
        ebitda_per_order=ebitda_per_order,
        store_fixed_total=store_fixed_total,
        central_overhead_total=central_total,
        marketing_total=marketing_total,
        cm2_total=cm2 * orders_per_month,
        cm3_total=cm2 * orders_per_month - store_fixed_total,
        ebitda_total=cm2 * orders_per_month - store_fixed_total - central_total - marketing_total,
        fee_paying_share=fee_paying_share,
    )


# --------------------------------------------------------------------------- #
# Cohort retention, LTV and payback
# --------------------------------------------------------------------------- #
@dataclass
class Cohort:
    """A retention curve and the contribution it generates over the horizon."""

    label: str
    months: list[int]
    retention_rate: list[float]
    survival: list[float]
    orders_per_survivor: list[float]
    orders_per_original: list[float]
    contribution: list[float]
    cumulative: list[float]
    cm_per_order: float
    cac: float = 0.0

    @property
    def ltv(self) -> float:
        return self.cumulative[-1]

    @property
    def total_orders_per_customer(self) -> float:
        return sum(self.orders_per_original)

    @property
    def payback_month(self) -> int | None:
        """First month where cumulative contribution covers CAC, else None.

        Returning None rather than the horizon is deliberate: "does not pay back
        within 24 months" is a different statement from "pays back in month 24",
        and collapsing the two is how unprofitable channels survive review.
        """
        if self.cac <= 0:
            return 1
        for month, cumulative in zip(self.months, self.cumulative, strict=True):
            if cumulative >= self.cac:
                return month
        return None

    @property
    def ltv_cac_ratio(self) -> float:
        return math.inf if self.cac <= 0 else self.ltv / self.cac


def build_cohort(
    drivers: Drivers,
    cm_per_order: float,
    *,
    label: str = "Blended",
    retention_multiplier: float = 1.0,
    cac: float = 0.0,
    horizon_months: int | None = None,
) -> Cohort:
    """Build the retention curve and cumulative contribution for one cohort.

    The curve climbs from a month-1 shock toward an asymptote, which is the shape
    quick commerce actually shows: most of the loss happens immediately, and the
    survivors are habitual. A flat monthly retention rate -- the usual shortcut --
    understates LTV early and overstates it late.
    """
    horizon = int(horizon_months or drivers["horizon_months"])
    asymptote = drivers["asymptotic_retention"]
    decay = drivers["retention_decay"]
    base_orders = drivers["orders_per_customer_per_month"]
    uplift = drivers["tenure_frequency_uplift"]

    # The channel multiplier moves month-1 retention only; every channel then
    # converges to the same asymptote.
    #
    # This is a modelling choice with a behavioural argument and a numerical one.
    # Behaviourally, channel quality shows up as an immediate sorting effect --
    # someone who came for a coupon leaves once the coupon is spent -- and a
    # coupon-acquired customer who is still ordering in month 6 behaves like any
    # other month-6 customer. Numerically, scaling every month's retention rate
    # compounds over a 24-month horizon and produced a 6x spread in LTV between
    # the best and worst channel, which is not a finding, it is an artefact of
    # applying a multiplier 24 times.
    initial = min(
        max(drivers["month_1_retention"] * retention_multiplier, 0.05),
        asymptote - 0.01,
    )

    months = list(range(1, horizon + 1))
    retention_rate = [
        min(asymptote - (asymptote - initial) * decay ** (month - 1), 0.97)
        for month in months
    ]

    survival = [1.0]
    for month in range(1, horizon):
        survival.append(survival[-1] * retention_rate[month - 1])

    orders_per_survivor = [
        base_orders * (1.0 + uplift * min(month - 1, 6) / 6.0) for month in months
    ]
    orders_per_original = [s * o for s, o in zip(survival, orders_per_survivor, strict=True)]
    contribution = [o * cm_per_order for o in orders_per_original]

    cumulative: list[float] = []
    running = 0.0
    for value in contribution:
        running += value
        cumulative.append(running)

    return Cohort(
        label=label,
        months=months,
        retention_rate=retention_rate,
        survival=survival,
        orders_per_survivor=orders_per_survivor,
        orders_per_original=orders_per_original,
        contribution=contribution,
        cumulative=cumulative,
        cm_per_order=cm_per_order,
        cac=cac,
    )


# --------------------------------------------------------------------------- #
# Acquisition channels
# --------------------------------------------------------------------------- #
@dataclass
class ChannelResult:
    channel: Channel
    cohort_cm3: Cohort
    cohort_cm2: Cohort

    @property
    def name(self) -> str:
        return self.channel.name

    @property
    def cac(self) -> float:
        return self.channel.cac

    @property
    def ltv_cm3(self) -> float:
        return self.cohort_cm3.ltv

    @property
    def ltv_cm2(self) -> float:
        return self.cohort_cm2.ltv

    @property
    def ratio_cm3(self) -> float:
        return self.cohort_cm3.ltv_cac_ratio

    @property
    def ratio_cm2(self) -> float:
        return self.cohort_cm2.ltv_cac_ratio

    @property
    def payback_month(self) -> int | None:
        return self.cohort_cm3.payback_month

    @property
    def verdict_flips_on_definition(self) -> bool:
        """True where CM2 clears 1.0x and CM3 does not.

        This is a governance problem disguised as an arithmetic one: the same
        channel is fundable or not depending on which contribution margin the
        deck happens to use.
        """
        return self.ratio_cm2 >= 1.0 > self.ratio_cm3


@dataclass
class ChannelPortfolio:
    results: list[ChannelResult]
    blended_cac: float
    paid_cac: float
    blended_ltv_cm3: float
    total_spend: float
    total_new_customers: float
    paid_new_customers: float
    sub_unity: list[ChannelResult] = field(default_factory=list)

    @property
    def blended_ratio(self) -> float:
        return self.blended_ltv_cm3 / self.blended_cac if self.blended_cac else math.inf

    @property
    def paid_ratio(self) -> float:
        return self.blended_ltv_cm3 / self.paid_cac if self.paid_cac else math.inf

    @property
    def sub_unity_spend(self) -> float:
        return sum(r.channel.spend for r in self.sub_unity)

    @property
    def sub_unity_spend_share(self) -> float:
        return self.sub_unity_spend / self.total_spend if self.total_spend else 0.0

    @property
    def organic_share_of_customers(self) -> float:
        organic = sum(r.channel.new_customers for r in self.results if not r.channel.is_paid)
        return organic / self.total_new_customers if self.total_new_customers else 0.0


def build_channel_portfolio(drivers: Drivers, cm3: float, cm2: float) -> ChannelPortfolio:
    """Per-channel LTV:CAC, plus the blended and paid-only views.

    The blended/paid split is the point. Blended CAC divides total spend by total
    acquired customers -- including the organic ones nobody paid for -- so it is
    arithmetically guaranteed to flatter paid performance. Any decision about
    *incremental* spend has to be made on paid or channel-level figures.
    """
    results = [
        ChannelResult(
            channel=channel,
            cohort_cm3=build_cohort(
                drivers, cm3, label=channel.name,
                retention_multiplier=channel.retention_multiplier, cac=channel.cac,
            ),
            cohort_cm2=build_cohort(
                drivers, cm2, label=channel.name,
                retention_multiplier=channel.retention_multiplier, cac=channel.cac,
            ),
        )
        for channel in drivers.channels
    ]

    total_spend = sum(r.channel.spend for r in results)
    total_customers = sum(r.channel.new_customers for r in results)
    paid_customers = sum(r.channel.new_customers for r in results if r.channel.is_paid)

    blended_ltv = (
        sum(r.ltv_cm3 * r.channel.new_customers for r in results) / total_customers
        if total_customers else 0.0
    )

    return ChannelPortfolio(
        results=results,
        blended_cac=total_spend / total_customers if total_customers else 0.0,
        paid_cac=total_spend / paid_customers if paid_customers else 0.0,
        blended_ltv_cm3=blended_ltv,
        total_spend=total_spend,
        total_new_customers=total_customers,
        paid_new_customers=paid_customers,
        sub_unity=[r for r in results if r.channel.is_paid and r.ratio_cm3 < 1.0],
    )
