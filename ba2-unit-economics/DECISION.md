# Decision memo — three proposals for the FY27 operating plan

**To:** CEO, CFO, VP Growth, VP Category
**From:** Business Analyst, Commercial Finance
**Re:** Store expansion, free-delivery threshold, retail media
**Model:** `outputs/unit_economics.xlsx` — every figure below is a live formula in it

---

## Recommendation

| Proposal | Proposed by | Annual CM3 impact | Capex | Decision |
|---|---|---|---|---|
| Raise retail media income ₹14 → ₹22/order | Category | **+₹4.73 Cr** | nil | ✅ **Proceed now** |
| Raise free-delivery threshold ₹299 → ₹499 | Pricing | **+₹4.28 Cr** | nil | ✅ **Proceed now** |
| Open 12 dark stores in the existing 3 cities | Growth | **−₹1.75 Cr** | ₹4.20 Cr | ❌ **Do not proceed** |

**Together the two approved proposals move annual EBITDA from −₹4.37 Cr to +₹4.45 Cr
with no capital expenditure.** The company can reach EBITDA break-even on pricing and
ancillary income alone, before it opens another store.

---

## The one thing to take from this

**Revenue and contribution move in opposite directions on two of these three
proposals.** Judged on revenue growth, the recommendations invert — the expansion is
approved and the threshold change is rejected. Both would be wrong.

| Proposal | Orders | Revenue | Monthly CM3 |
|---|---|---|---|
| 12 new dark stores | **+7.7%** | **+7.7%** | **−₹14.6 L** |
| Threshold ₹299 → ₹499 | −3.1% | −1.1% | **+₹35.6 L** |

Every proposal in this memo is therefore scored on **change in monthly CM3
contribution**, per the definitions agreed in `METRIC_DEFINITIONS.md`.

---

## 1. ❌ Do not open 12 dark stores in the existing three cities

**Store count is not scale. Order density is.**

Dark-store fixed cost is incurred per store — ₹4.60 lakh a month each. In a city we
already cover, most of a new store's volume is demand that moves off a neighbour rather
than demand that did not exist. Orders per store, the denominator that fixed cost is
spread over, therefore falls.

| | Now | After 12 stores |
|---|---|---|
| Dark stores | 48 | 60 |
| Orders per store per day | 420 | **362** |
| Dark-store fixed cost per order | ₹36.51 | **₹42.38** |
| CM3 per order | ₹26.97 | **₹22.81** |
| Monthly CM3 contribution | ₹1.63 Cr | **₹1.49 Cr** |

**The proposal has been credited with the benefit it genuinely earns.** Smaller
catchments mean shorter rides, cutting rider payout from ₹36.00 to ₹34.29 per order. It
still does not clear.

### The number this turns on

> **Break-even incrementality: 63.7%.** The two-store pilot measured **43.0%** — it
> misses by **20.7 percentage points.**

Incrementality was measured the right way: by what happened to *neighbouring store
volume*, not by comparing the new stores to their own forecast. Neighbours lost volume
equal to 57% of the pilot stores' throughput. Measured against forecast, the pilot would
have reported 100% incrementality and this programme would have been approved.

**Three effects are not modelled, and all three run against the proposal:** thinner
per-store inventory pooling raises spoilage, lower per-store volume worsens picking
efficiency, and new stores take months to reach even the assumed 300 orders a day.

### What would change this answer

The model turns positive above roughly 60% incrementality. **This is not an argument
against expansion — it is an argument against *infill*.** Reaching EBITDA break-even
needs about **59 stores at today's density of 420 orders a day**, which means genuinely
new catchments where incrementality approaches 100%, not deeper coverage of catchments
already served. A proposal for new cities or currently unserved pincodes would be
assessed on entirely different numbers, and I would expect it to clear.

---

## 2. ✅ Raise the free-delivery threshold from ₹299 to ₹499

Worth **+₹35.6 lakh a month, +₹4.28 Cr a year.**

A threshold acts on the *distribution* of basket values, not the average, so this was
modelled on a lognormal basket calibrated to our ₹465 AOV rather than on AOV itself:

- Fee-paying share of orders rises from **29.1% to 60.1%**, lifting delivery fee income
  from ₹7.28 to **₹15.03** per order.
- **6.3% of orders up-size** to clear the threshold, nudging average basket from ₹466.97
  to ₹469.18. Only baskets within 25% of the threshold are treated as capable of
  up-sizing — a customer with a ₹120 basket will not add ₹380 of groceries to avoid a
  ₹25 fee.

**Held at constant volume the gain would be ₹49.1 lakh a month.** Applying the volume
response we actually measured last time takes it to ₹35.6 lakh — **27% smaller, and
still clearly worth doing.**

### The number this turns on

> **Break-even volume decline: 11.3%.** When the threshold last moved (₹249 → ₹299) we
> observed a **3.1%** decline — **8.2 percentage points of headroom.**

This recommendation rests on a measured response, not an assumed elasticity. That
matters: a delivery fee is a friction, and friction suppresses order frequency even when
the rupee amount is small.

### What would change this answer

A volume decline above 11.3%. The step from ₹299 to ₹499 is larger than the step we
measured, so **implement in two stages — ₹299 → ₹399, hold four weeks, measure, then
₹399 → ₹499** — and treat the first stage as the test that licenses the second.

---

## 3. ✅ Raise retail media income from ₹14 to ₹22 per order

Worth **+₹39.4 lakh a month, +₹4.73 Cr a year** — the largest of the three, and the only
one whose downside is bounded by its own cost.

Brand-funded placement income is invoiced to brands, not collected through the consumer
payment rail, so it carries **no payment gateway fee and no fulfilment cost**. The full
₹8.00 per order reaches CM1.

### The number this turns on

> **Only 18.6% of the proposed uplift needs to land.** ₹1.49 of the ₹8.00 covers the
> ₹9 lakh a month for two category managers and the ad-serving build.

**No customer-facing change, so no volume risk.** This is the cheapest option to test
and the most valuable if it works, which is why it goes first despite being the least
interesting proposal on the table.

---

## Do not add the two approved business cases together

| | Annual |
|---|---|
| Sum of the two individual cases | +₹9.00 Cr |
| **Modelled together** | **+₹8.82 Cr** |
| Interaction | −₹0.18 Cr |

Retail media income is earned per order, and the threshold change removes 3.1% of
orders. Adding the cases claims income on orders that will not exist. The error is small
here — 2% — and it is the kind that compounds across a plan assembled by stapling
business cases together.

---

## Also requiring a decision: ₹1.07 Cr a month of marketing spend

Not one of the three proposals, but it surfaced from the same model and is larger than
all of them.

**Blended LTV:CAC of 2.20x reads healthy. Paid-only LTV:CAC is 1.28x.** Blended CAC
divides total spend by *all* acquired customers, including the **42% who arrive
organically and cost nothing** — so it overstates paid efficiency by **72%**,
structurally rather than by accident.

At channel level:

| Channel | CAC | LTV (CM3) | LTV:CAC | Payback |
|---|---|---|---|---|
| organic | — | ₹611 | not bought | — |
| referral | ₹120 | ₹569 | 4.74x | month 2 |
| paid_search | ₹365 | ₹493 | 1.35x | month 10 |
| paid_social | ₹410 | ₹458 | 1.12x | month 16 |
| **affiliate_coupon** | ₹545 | ₹303 | **0.56x** | **never** |
| **offline_ooh** | ₹690 | ₹394 | **0.57x** | **never** |

**The two channels below 1.0x hold ₹1.07 Cr a month — 46% of the marketing budget — and
neither pays back within 24 months.** Coupon-acquired customers place 11.2 orders over
24 months against 22.6 for organic: customers acquired by a discount behave like
customers who wanted the discount.

**Recommended:** halt `affiliate_coupon` and `offline_ooh`, reallocate to `referral`
(4.74x, payback month 2) up to its saturation point, and bring a separate paper on
saturation limits.

> ⚠️ **Both channels clear 1.0x on CM2 (1.31x and 1.34x) and fail on CM3.** The same
> spend is defensible or indefensible depending on which contribution margin the deck
> uses. `METRIC_DEFINITIONS.md` fixes CM3 as the company standard for funding decisions
> so that this is settled once rather than argued per channel.

---

## What I am least confident about

Stated plainly, because a memo that sounds certain about everything invites the reader
to find the weak point themselves.

| Assumption | Why it is soft | Effect if wrong |
|---|---|---|
| **Up-size propensity 35%** | Judgement, not measured. No experiment has isolated it | Lowers the threshold gain. At 0% the gain is still positive, so it does not change the decision |
| **Volume response 3.1%** | Measured on a smaller step (₹249 → ₹299) and may not scale linearly to ₹499 | The whole basis for the staged rollout in §2 |
| **Retail media ₹22 achievable** | Category team target; no signed commitments | Break-even needs only 18.6% of it, so the decision survives a large miss |
| **New-store volume 300/day** | Pilot-based, small sample | Sensitivity grid in the workbook covers 200–400; the expansion is negative across all of them at measured incrementality |
| **24-month LTV horizon** | Longest period we have real cohort data for | A longer horizon raises every LTV:CAC. Held fixed deliberately so it cannot be used as a dial |

**The recommendations are robust to all five.** The expansion is negative across every
cell of the sensitivity grid at the pilot's measured incrementality, and both approved
proposals clear their break-even by a wide margin.
