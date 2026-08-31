# Findings — why SLA attainment fell

**To:** COO, VP Support, VP Sales, CFO
**From:** Business Analysis
**Re:** Support SLA attainment, H1 vs H2 — root cause and remedy
**Reproduce:** `make all`

---

## Summary

SLA attainment as reported fell from **95.02% to 85.96%** — a **9.06 percentage point**
decline. The proposal on the table is eight permanent support engineers at **₹96 lakh a year**.

**I recommend rejecting it.** Not because it is expensive, but because it **cannot achieve the
objective at any spend level.**

Four causes account for the decline. Three of them are not capacity problems, and the support
team's actual handling performance **improved** over the period.

| Cause | Effect | Fixable by hiring? |
|---|---|---|
| Reporting migration dropped the SLA clock-pause rule | **−2.71pp** | ✗ Not a real decline |
| Service-tier mix shifted toward tighter targets | **−4.11pp** | ✗ Structural |
| Backlog from a three-week release defect | **−5.36pp** | ✓ But already drained |
| **Within-tier work performance** | **+0.99pp** | The team got *faster* |
| Interaction between mix and rate | +2.15pp | — |
| **Total** | **−9.06pp** | residual **0.0000000000** |

**6.82pp of the 9.06pp decline — 75% — cannot be moved by adding people.**

---

## The finding that decides the remedy

> **The enterprise 4-hour SLA target is unachievable at any staffing level.**

SLA attainment has three obstacles: the ticket waits in a queue, the customer takes time to
respond, and **the work itself takes time**. Capacity shrinks the first. Process shrinks the
second. Nothing shrinks the third.

Measuring enterprise tickets on handling effort alone — zero queue, zero customer delay, a
perfectly staffed team responding instantly:

| Enterprise SLA target | Ceiling (perfect ops) | Governed (today) | Clears 95%? |
|---|---|---|---|
| **4h — current** | **85.60%** | 80.85% | ✗ |
| 6h | 95.34% | 92.67% | ✗ |
| **8h** | 98.36% | **97.20%** | **✓** |

**14.40% of enterprise tickets take longer than four hours of actual work.** The contractual
service-credit threshold is 95%. The gap is 14.15pp and **capacity can close at most
4.75pp of it.**

The 4-hour commitment was agreed by Sales during contract negotiation **without a capacity
model**. It has never been achievable. Six months of escalating pressure on the support team
has been spent chasing a number that does not exist.

**At an 8-hour target we are already at 97.20% today**, with 2.20pp of headroom and no
operational change whatsoever.

---

## What the executive diagnosis gets wrong

The proposal rests on the team having become slower. Tested on the work clock — handling
effort, excluding queueing, customer delay and mix:

| Tier | Work-clock attainment H1 → H2 |
|---|---|
| standard | 99.4% → 99.5% (+0.1pp) |
| business | 93.0% → 95.2% (+2.2pp) |
| enterprise | 81.0% → 85.6% (+4.6pp) |
| **Mix-adjusted total** | **96.39% → 97.38% (+0.99pp)** |

**Every tier improved.** Median handle time fell after the knowledge base and macro library
shipped in month 7 — and it improved *despite* the share of tickets handled by agents under
six months' tenure rising from 13.2% to 18.7%.

> **The blended work-clock figure appears to fall (96.39% → 94.89%),** purely because
> enterprise volume grew from 8.1% to 26.9% and enterprise carries a tighter target. My own
> first version of this test used the blended figure and returned the wrong verdict. It is the
> same aggregation trap that produced the original misdiagnosis, and it is worth knowing that
> it survives one level of sophistication.

---

## Cause 1 — the metric changed, not the performance (−2.71pp)

The platform migration at the start of month 7 replaced the reporting pipeline. The new one
computes resolution time as `resolved_at − created_at` and **no longer subtracts approved
pending-customer time**. The prior period was never restated.

| Period | Clock actually reported |
|---|---|
| Months 1–6 | Governed — pending time excluded |
| Months 7–12 | Strict — no pause at all |

**Every comparison made in this business for six months compared two different metrics.**
Restated on the governed definition, H2 attainment is **88.67%, not 85.96%**.

Cost to fix: **zero**. It is a query, because both clocks are computed per ticket.

## Cause 2 — the mix moved, not the performance (−4.11pp)

| Tier | SLA target | Share H1 → H2 | Baseline attainment | Mix contribution |
|---|---|---|---|---|
| standard | 24h | 68.2% → 52.5% | 98.6% | −15.48pp |
| business | 8h | 23.7% → 20.6% | 91.3% | −2.79pp |
| enterprise | **4h** | **8.1% → 26.9%** | 75.5% | **+14.16pp** |

Volume moved from a tier with a 24-hour target to one with a 4-hour target. **Identical
operational performance scores worse against a harder mix.** This was the deliberate outcome
of a successful up-market push — the commercial strategy is working, and the operational
metric was never re-baselined to reflect it.

## Cause 3 — one bad month, already over (−5.36pp)

Release 24.3 shipped a data-sync regression on day 4 of month 8. Volume in that category ran
at 2.8x for three weeks.

| Month | Peak backlog | vs baseline | Attainment |
|---|---|---|---|
| 7 | 28 | 0.9x | 94.70% |
| **8** | **146** | **4.6x** | **73.39%** |
| 9 | 36 | 1.1x | 92.25% |

**Month 8 alone drags the six-month average down 3.50pp.** The backlog was back within normal
range by month 9.

A contractor burst to clear backlog was costed at ₹17.6 lakh and **is not recommended** — the
backlog has already drained. Spending against it would be treating a resolved symptom. The
remedy is preventing recurrence.

Worth noting for its counter-intuitiveness: the damage landed on the **standard** tier
(−5.26pp of the −5.36pp), not enterprise. Priority ordering protected the tightest SLA and
pushed the queue onto the loosest one.

---

## Business case

Enterprise book: **34 accounts, ₹14.28 crore ARR.** Contracts carry a **5% monthly service
credit** if attainment falls below 95%. Enterprise attainment is 80.85% — **in breach**.

**Exposure: ₹5.95 lakh per month = ₹71.4 lakh per year.**

Service credits are a **step function, not a gradient.** An option that closes most of the gap
saves nothing.

| Option | One-off | Recurring/yr | Achievable | Clears 95%? | Steady-state net |
|---|---|---|---|---|---|
| Add 8 permanent engineers | — | **₹96,00,000** | 85.60% | ✗ | **−₹96,00,000** |
| **Restate + re-baseline to 8h + prevent** | **₹12,50,000** | — | **97.20%** | **✓** | **+₹71,40,000** |
| Change nothing | — | — | 80.85% | ✗ | ₹0 |

The executive proposal spends ₹96 lakh a year, every year, buys at most 4.75pp of a 14.15pp
gap, and **never stops the service credits.**

---

## Recommendation

**1. Restate SLA attainment on the governed clock and report it by tier.** Zero cost, one
week. Removes 2.71pp of apparent decline and stops a blended figure that moves opposite to
all of its components.

**2. Re-baseline the enterprise target from 4h to 8h — ₹71.4 lakh a year.** This is a
commercial conversation, not an operational one, and Sales must own it: they sold a
commitment that has never been deliverable. At 8h we are at 97.20% today.

**3. Fix the release-testing gap — ₹9,00,000 one-off.** Against a 5.36pp hit to the
half-average the last time it happened.

**4. Do not add 8 permanent engineers.** ₹96 lakh a year that cannot reach the threshold.

**Total: ₹12.5 lakh one-off against ₹71.4 lakh a year recovered.**

### What I would monitor

Months 11 and 12 show backlog drifting back above 1.5x the baseline norm. Not an incident, but
enterprise share is still climbing and capacity headroom is thinning. **This is the case for
the capacity model — not for the headcount request.** If enterprise share passes ~35% the
arithmetic changes and a targeted enterprise pod becomes worth costing.

---

## What would change my recommendation

| If this were true | Effect |
|---|---|
| Customers will not renegotiate the 4h target | Recommendation 2 fails. Then the only route to 95% is cutting enterprise handle time ~35% through specialist tooling — a larger investment that must be costed against ₹71.4 lakh a year, and still not a blanket headcount case |
| Enterprise share keeps climbing past ~35% | Capacity headroom becomes genuinely binding. A targeted enterprise pod, not general hiring |
| The pending-customer flag is being gamed | The governed clock is overstated and the definitional component is smaller. Audit is unaudited today — recommend sampling |
| Standard tier gets a business-hours calendar | Standard attainment rises, the mix effect grows, and the case for re-baselining strengthens |

### Where this analysis is weakest

All three clocks run on **calendar hours**. That is right for enterprise and business, which
are contracted 24/7, and **too harsh for standard**, whose customers do not expect weekend
service. Standard attainment is understated, which means the mix effect is if anything
larger than reported. Fixing it needs a per-region business-hours calendar and is the next
change I would make.
