# BA-3 · KPI framework and root-cause diagnosis

A support organisation's headline operational KPI fell **9.06 percentage points** in six
months. The proposal on the table is eight permanent engineers at **₹96 lakh a year.**

This project decomposes the decline into four causes that **sum exactly to the observed gap**,
tests twelve hypotheses in SQL, and rejects the proposal — because it cannot achieve the
objective at any spend level.

```bash
make all     # generate the dataset, run the full analysis
make test    # 36 tests
```

Runs in about 8 seconds. DuckDB, no external services.

---

## The finding

> **The enterprise 4-hour SLA target is unachievable at any staffing level.**

SLA attainment has three obstacles: the ticket waits in a queue, the customer takes time to
respond, and **the work itself takes time**. Capacity shrinks the first. Process shrinks the
second. Nothing shrinks the third.

So measure enterprise tickets on handling effort alone — zero queue, zero customer delay, a
perfectly staffed team responding instantly:

| Enterprise SLA target | Ceiling (perfect ops) | Governed (today) | Clears 95%? |
|---|---|---|---|
| **4h — current** | **85.60%** | 80.85% | ✗ |
| 6h | 95.34% | 92.67% | ✗ |
| **8h** | 98.36% | **97.20%** | **✓** |

**14.40% of enterprise tickets take longer than four hours of actual work.** The contractual
service-credit threshold is 95%. The gap is 14.15pp and **capacity closes at most 4.75pp of
it.**

The 4-hour commitment was agreed by Sales during contract negotiation **without a capacity
model**. It has never been achievable, and six months of pressure on the support team has been
spent chasing a number that does not exist.

## The decomposition reconciles exactly

A list of contributing factors that does not reconcile to the observed change cannot be
checked — any factor can be added or dropped without the total noticing.

| Cause | Effect | Share | Fixable by hiring? |
|---|---|---|---|
| Reporting migration dropped the SLA clock-pause rule | **−2.71pp** | 30% | ✗ not a real decline |
| Service-tier mix shifted toward tighter targets | **−4.11pp** | 45% | ✗ structural |
| Backlog from a three-week release defect | **−5.36pp** | 59% | ✓ already drained |
| **Within-tier work performance** | **+0.99pp** | −11% | the team got *faster* |
| Interaction between mix and rate | +2.15pp | −24% | — |
| **Total** | **−9.06pp** | | |
| **Residual** | **0.0000000000pp** | | |

**6.82pp of the 9.06pp decline — 75% — cannot be moved by adding people.**

The identity is built in three stages, each tested independently:

```
reported gap = definition                       (restate both halves on one clock)
             + mix + interaction                (volume moved between tiers)
             + backlog + performance            (split the rate term by clock)
```

Three clocks per ticket make the last split possible:

```
work    = handle                                   the ceiling any staffing could reach
net     = queue_wait + handle                      the governed SLA clock
strict  = queue_wait + handle + pending_customer    what the migrated tool reports
```

## Twelve hypotheses, and the five that were ruled out

Full audit trail in [`sql/01_hypotheses.sql`](sql/01_hypotheses.sql) — each with its query,
its numbers and a verdict computed in SQL against a materiality bar of 1.0pp **declared before
any result was seen.**

| | Hypothesis | Verdict |
|---|---|---|
| H01 | Demand outgrew capacity | ELIMINATED — utilisation flat at ~87–90% both halves |
| H02 | Headcount fell | ELIMINATED — grew 22 → 26, no net attrition |
| **H03** | **Agents became slower** | **ELIMINATED — mix-adjusted performance +0.99pp** |
| H04 | Rework rose | ELIMINATED — reopens 5.95% → 5.29% |
| H05 | Escalations rose | ELIMINATED — flat |
| H06 | Routing accuracy fell | PARTIAL — real, +0.17pp, immaterial |
| H07 | Tenure mix shifted | PARTIAL — new-hire share 13.2% → 18.7% |
| H08 | Tier mix tightened | **RETAINED** — quantified at −4.11pp |
| H09 | Clock definition changed | **RETAINED** — quantified at −2.71pp |
| H10 | One-off incident backlog | **RETAINED** — quantified at −5.36pp |
| H11 | Seasonality | REFRAMED — untestable with 12 months |
| **H12** | **Target unachievable at any staffing** | **RETAINED — ceiling 85.60% vs 95%** |

**The eliminated branches are in the deliverable on purpose.** An analysis that presents only
the causes it found gets relitigated by whoever's theory went unmentioned. "Did you check
escalations?" should have a five-minute answer, not reopen the investigation.

### H03 is the row that matters, and my first version of it was wrong

H03 is the hypothesis the executive proposal rests on. My first test compared **blended**
work-clock attainment, which fell 96.39% → 94.89% — returning RETAINED and endorsing the
headcount request.

That figure falls because enterprise volume grew from 8.1% to 26.9% and enterprise carries a
tighter target. Holding volume shares at baseline reverses the verdict: **every tier improved,
mix-adjusted +0.99pp.**

> The aggregation trap the whole investigation exists to expose was sitting inside its own
> hypothesis test. There is now a test asserting the blended version returns the wrong answer,
> because that property is the point.

## Business case

Enterprise book: **34 accounts, ₹14.28 crore ARR**, with a **5% monthly service credit** below
95% attainment. Enterprise sits at 80.85% — in breach. **Exposure: ₹71.4 lakh a year.**

Service credits are a **step function, not a gradient.** An option that closes most of the gap
saves nothing.

| Option | One-off | Recurring/yr | Achievable | Clears? | Steady-state net |
|---|---|---|---|---|---|
| Add 8 permanent engineers | — | **₹96,00,000** | 85.60% | ✗ | **−₹96,00,000** |
| **Restate + re-baseline to 8h + prevent** | **₹12,50,000** | — | **97.20%** | **✓** | **+₹71,40,000** |
| Change nothing | — | — | 80.85% | ✗ | ₹0 |

A contractor burst to clear the backlog was costed at ₹17.6 lakh and **deliberately not
recommended** — the backlog was back within normal range one month after the incident.
Recommending it would have been spend against a resolved symptom.

Full memo: **[FINDINGS.md](FINDINGS.md)**.

## What is in here

| File | What it is |
|---|---|
| [FINDINGS.md](FINDINGS.md) | The memo — causes, business case, recommendation, and what would change it |
| [METRIC_DICTIONARY.md](METRIC_DICTIONARY.md) | The governance decision on which clock the company reports, and why blended attainment is not a reportable metric |
| [KPI_TREE.md](KPI_TREE.md) | KPI tree (what determines the metric) and MECE issue tree (what might have moved it) — two different diagrams that get confused constantly |
| [LEARN.md](LEARN.md) | How it fits together, plus the interview questions it invites |
| `config/scenario.yml` | The ground truth. Every planted effect, with its size and basis |
| `data/generate_tickets.py` | Generator with a **day-by-day priority queue simulation** |
| `sql/00_definitions.sql` | The three clocks, defined once |
| `sql/01_hypotheses.sql` | The audit trail — twelve hypotheses, verdicts computed in SQL |
| `sql/02_sla_ceiling.sql` | Achievable attainment by target and clock — the H12 evidence |
| `sql/03_incident_isolation.sql` | How much of the decline is one month, and did the backlog drain |
| `src/decomposition.py` | The five-component identity |
| `src/business_case.py` | Options scored on cost **and on capability** |

## Why the effects are simulated rather than asserted

It is easy to fabricate a table where a metric falls and then "discover" why. That proves
nothing — the analysis is reading back the author's intention. So each planted effect has its
own mechanism:

- **Mix shift** is a monthly ramp in tier shares. Nothing about attainment is touched; the
  tiers simply have different targets.
- **Backlog is not a parameter.** It emerges from a day-by-day priority queue with finite
  capacity. Remove the simulation and the component vanishes.
- **Productivity** is a reduction in handle time only.
- **The definitional break is not in the data at all** — it is a choice of clock applied to the
  current half. The tickets are unchanged.

Two bugs this surfaced, both fixed and documented:

**Strict priority starved the lowest tier.** The first queue simulation had no ageing, so
standard-tier tickets were never served while any backlog existed — losing 35pp of attainment
to queue wait alone. That is a pathology, not a backlog. Tickets now age up the priority
order, as every real support queue does.

**Capacity was over-provisioned by ~80%,** so no backlog ever formed and the component was
zero. Capacity is now calibrated to hold utilisation near 87% in both halves — which is also
what lets the demand and headcount hypotheses be *eliminated on evidence* rather than
dismissed.

## What this is not

- Not a real company's ticket data. The organisation, volumes and cost base are constructed;
  the effects are planted with known sizes so the decomposition can be *verified* rather than
  merely believed.
- Not a dashboard. No charts. Every claim is a number with a reconciliation next to it.
- Not a capacity model. It establishes that one is needed and what it must answer.
