# Metric dictionary — support SLA attainment

This document exists because the organisation spent six months arguing about a number that
was never one number.

"SLA attainment" depends entirely on **which clock you measure**, and this investigation
found three defensible clocks giving three different answers for the same six months:

| Clock | H2 attainment | What it measures |
|---|---|---|
| **Strict** — `resolved_at − created_at` | **85.96%** | Everything, including time waiting on the customer |
| **Governed** — excludes approved pending-customer time | **88.67%** | What the SLA policy actually specifies |
| **Work** — handling effort only | **94.89%** | The ceiling any staffing level could achieve |

Nobody was lying. Three teams quoted three figures, each correct on its own definition, and
the gap between them is larger than the decline everyone was trying to explain.

---

## The governance decision

> **The company reports SLA attainment on the GOVERNED clock, disaggregated BY SERVICE
> TIER. Blended attainment is not a reportable metric.**

Both halves of that sentence are load-bearing.

**Governed clock**, because it is what the contracts specify and the only one the support
team can be held to. Pending-customer time is time spent waiting for a customer to supply
logs, credentials or reproduction steps. Holding a team accountable for it creates an
incentive to close tickets prematurely.

**By tier**, because the blended figure is what caused this whole investigation to start
with the wrong diagnosis. Blended attainment fell while **every tier improved** on the work
clock. Any metric that can move opposite to all of its components is a reporting hazard, not
a KPI.

---

## Definitions

### SLA attainment

```
attainment = tickets resolved within their tier's SLA target / all resolved tickets
```

Measured on the **governed clock**:

```
governed_hours = queue_wait_hours + handle_hours
```

**Excluded** from the governed clock:

| Excluded | Why |
|---|---|
| Approved pending-customer time | Outside the team's control. Requires an agent to have requested specific information and logged the request |
| — | Nothing else. There is no other pause condition, deliberately |

**Included**, and often assumed otherwise:

| Included | Why |
|---|---|
| Queue wait before first touch | The customer is waiting. A ticket sitting unassigned is a ticket not being served |
| Time on reopened tickets | A reopened ticket was not resolved. Counting the first closure would reward premature closure |
| Weekends and holidays | Enterprise and business tiers are contracted 24/7. See the known limitation below |

### The three clocks, formally

```
work_hours   = handle_hours                                          -- effort only
governed     = queue_wait_hours + handle_hours                       -- the SLA clock
strict       = queue_wait_hours + handle_hours + pending_customer     -- resolved − created
```

`work_hours` is not a reportable metric. It exists as a **diagnostic ceiling**: if
attainment on the work clock is below the contractual threshold, the target cannot be met at
any staffing level, and that is a commercial problem rather than an operational one. It is
the calculation that produced the central finding of this analysis.

### SLA targets by tier

| Tier | Target | Set by | Capacity-modelled? |
|---|---|---|---|
| standard | 24h | Support policy | Yes |
| business | 8h | Support policy | Yes |
| enterprise | **4h** | Sales, during contract negotiation | **No** |

The last row is the finding. **The 4-hour enterprise target has a ceiling of 85.60%** — even
with instant pickup and zero customer delay, 14.40% of enterprise tickets take longer than
four hours of actual work. The contractual threshold for service credits is 95%.

**A target that was never checked against the work it governs is not a target, it is a
liability.** Any future SLA commitment must be signed off against the work-clock
distribution before it is offered to a customer.

---

## The measurement discontinuity

**The reported series contains a break at month 7 and was never restated.**

The support platform migration replaced the reporting pipeline. The new pipeline computes
resolution time as `resolved_at − created_at` and does not subtract approved
pending-customer time. So:

| Period | Clock actually reported |
|---|---|
| Months 1–6 | Governed (pending time excluded) |
| Months 7–12 | Strict (no pause at all) |

Every H2-vs-H1 comparison made in the business over six months compared **two different
metrics**. This accounts for **2.71 percentage points** of an apparent 9.06pp decline.

**Controls added as a result:**

1. Any change to a metric definition requires the prior period to be restated in the same
   release, or the change does not ship.
2. The metric dictionary version is stamped on every report. A report cannot be compared to
   one with a different stamp.
3. Both clocks are computed and stored per ticket, so a restatement is a query rather than a
   backfill.

The third control is the one that matters operationally. The reason this went unnoticed for
six months is that restating the baseline was expensive; storing both clocks makes it free.

---

## Metrics deliberately not used

| Not used | Why |
|---|---|
| **Blended SLA attainment** | Moved opposite to every one of its components. It is the reason the diagnosis was wrong |
| First response time | A real metric, but not what the contracts specify and not what the escalations were about |
| Average resolution time | An average conceals the distribution, and SLA attainment is a threshold question. Two teams with identical means can have very different attainment |
| CSAT | Genuinely important, and out of scope here. Mixing a satisfaction measure into an SLA investigation invites attributing an SLA miss to sentiment |
| Tickets per agent per day | Used as a **capacity input**, never as a performance measure. As a target it rewards closing easy tickets |

**The exclusion list matters as much as the inclusion list.** Every metric left undefined
stays available to whoever wants to argue with the conclusion.

---

## Known limitations

Stated because a dictionary that claims no weaknesses is not being read carefully.

1. **Calendar hours, not business hours.** All three clocks run continuously. This is correct
   for the enterprise and business tiers, which are contracted 24/7, and it is **too harsh
   for the standard tier**, whose customers do not expect weekend service. Standard-tier
   attainment is therefore understated. Fixing it requires a business-hours calendar per
   customer region, which is the right next change to this model.
2. **Pending-customer time is trusted as logged.** If an agent marks a ticket pending without
   a genuine information request, the governed clock is gamed. There is no audit of that
   flag today, and it should be sampled.
3. **Reopens are attributed to the original ticket.** This is the conservative choice, and it
   means a single hard problem can breach twice.
4. **Queue wait is modelled at daily granularity**, so within-day prioritisation is not
   captured. It understates the variance of wait times without biasing the mean.
