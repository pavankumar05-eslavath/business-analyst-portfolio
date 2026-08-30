# Change Control Log and Impact Assessments

**Project ORIGIN** · Version 1.3 · Baselined
**Change authority:** SH-01 Head of Retail Lending (scope, schedule, cost) · SH-02 Chief Risk Officer (credit rules) · SH-04 Compliance Head (regulatory)

---

## Why this document exists

A requirements package without a change log is a snapshot of one day's understanding. Requirements
change; the question is whether the change is **assessed** or simply absorbed.

Absorbed change is how projects fail quietly. Someone agrees to "a small addition" in a corridor, the
team builds it, and three sprints later the schedule has slipped with no single decision anyone can
point to. The purpose of this log is to make every change cost something visible.

Three changes were raised after the FRD was baselined. **One was rejected, two were approved.** Each
has a worked impact assessment covering scope, schedule, cost, risk and the downstream artefacts that
had to change.

### Change authority — who can approve what

| Change type | Assessed by | Approved by | Rationale |
|---|---|---|---|
| Credit rule **tightening** | BA + SH-03 | **SH-02 CRO** | Credit policy is not a project decision |
| Credit rule **loosening** | BA + SH-03 | **SH-02 CRO** + SH-01 | Both risk and commercial owners |
| Regulatory obligation | BA + SH-04 | **SH-04 Compliance** | Not a negotiation; scope must absorb it |
| New product or segment | BA + SH-08 | **SH-01 Sponsor** | Scope and schedule sit with the sponsor |
| Anything consuming > 5 story points | BA + SH-08 | **SH-01 Sponsor** | Below 5 points the BA and EM absorb it in refinement |

**The distinction between tightening and loosening a credit rule is deliberate.** Tightening needs
only the CRO, because a more conservative rule cannot create credit risk. Loosening needs the CRO
*and* the sponsor, because it trades risk for volume, and one person should not hold both sides of
that trade.

### Log

| CR | Title | Raised by | Type | Decision | Net impact |
|---|---|---|---|---|---|
| **CR-001** | Extend ORIGIN to two-wheeler and gold loans | Head of Two-Wheeler Lending, via SH-01 | Scope | **❌ Rejected for release 1** | Deferred to Phase 2 roadmap; RSK-05 residual 6 → 3 |
| **CR-002** | Narrow the BRULE-04 auto-approve band | SH-02 CRO | Credit rule (tightening) | **✅ Approved** | BR-04 coverage 78.1% → 73.4%; FR-044 promoted to Must |
| **CR-003** | Cooling-off period and grievance redressal disclosure | SH-04 Compliance | Regulatory | **✅ Approved, split across a scope boundary** | +3 FRs, +1 story, +5 points; buffer 8 → 3 points; **new dependency DEP-05** |

---

## CR-001 · Extend ORIGIN to two-wheeler and gold loans ❌ Rejected

**Raised:** Sprint 1, day 4 · **Type:** Scope addition · **Decision authority:** SH-01

### Request

The Head of Two-Wheeler Lending observed that ORIGIN builds a digital KYC, income-verification,
e-Sign and e-NACH stack that his product also needs, and asked that two-wheeler and gold loans be
added to release 1 "since the plumbing is being built anyway."

This is RSK-05 from the risk register materialising exactly as predicted. It is also the most common
way a delivery-window project loses its delivery window, and the request is **reasonable on its
face** — which is what makes it dangerous. Rejecting it required numbers, not a reference to the
out-of-scope list.

### Impact assessment

The premise "the plumbing is being built anyway" is correct. The error is assuming the plumbing is
most of the work. Separating the reusable layer from the product-specific layer is the whole analysis.

| Layer | Reusable for two-wheeler / gold? | Why |
|---|---|---|
| Application capture, KYC, consent (FR-001 → FR-012) | ✅ Yes, unchanged | Applicant identity is product-independent |
| Audit trail, rule versioning (FR-023, FR-042, FR-043) | ✅ Yes, unchanged | Product-agnostic by design |
| e-Sign, e-NACH, disbursal (FR-029 → FR-032) | ✅ Mostly | Agreement template differs; mechanism identical |
| Income verification (FR-013 → FR-016) | ⚠️ Partly | Gold loans are collateral-assessed, not income-assessed |
| Decisioning rules (BRULE-01 → BRULE-08) | ❌ No | FOIR-based rules do not apply to a secured LTV product |
| Collateral valuation, hypothecation, RTO registration | ❌ Absent entirely | No equivalent exists in an unsecured product |
| Dealer channel: onboarding, subvention, delivery order | ❌ Absent entirely | ORIGIN has no third-party origination actor |

**Estimated additional scope:** 14 functional requirements, 6 business rules, 9 user stories,
**62 story points** — estimated jointly with SH-08 in a 90-minute sizing session rather than asserted.

| Constraint | Available | Required | Verdict |
|---|---|---|---|
| Sprint buffer (after CR-003) | 3 points | 62 points | ❌ |
| Should-item descope reserve | 12 points | — | ❌ Insufficient even if fully consumed |
| **Total headroom** | **15 points** | **62 points** | **❌ Short by 47 points** |
| Schedule | 3 sprints (CON-02) | 4.6 sprints | ❌ Breaches CON-02 by 1.6 sprints |

### Cost of accepting

| Item | Value | Basis |
|---|---|---|
| Personal-loan benefit deferred | **₹43,07,000 per month** | ₹5,16,84,000 annual benefit ÷ 12 |
| Delay if absorbed | 2 sprints (4 weeks) | 62 points ÷ 38 velocity, rounded up |
| Direct cost of delay | **≈ ₹43,07,000** | 1 month of forgone benefit |
| Festive season | **Missed** | Go-live would move past the Sep–Nov peak the conversion case was sized on |
| Credit risk | Not quantified | Secured-product rules would be drafted under schedule pressure, then approved by the same CRO who has just *tightened* the unsecured rules |

**The unquantified risk is the one that decided it.** The strongest argument against CR-001 is not the
₹43 lakh — it is that six new credit rules for an unfamiliar collateral class, written in the sprint
they are needed, is how a rule defect reaches production. CR-002 exists precisely because the CRO
wanted *more* conservatism on rules the team had already spent three weeks backtesting.

### Decision

**Rejected for release 1.** Recorded on the Phase 2 roadmap with an explicit note on why the request
is *cheaper later, not more expensive*:

> The reusable layer is being built product-agnostic on purpose. FR-023 versions rule sets rather than
> hard-coding them, and NFR-28 requires thresholds to be configurable without deployment. Re-estimated
> for Phase 2 with the ORIGIN platform in place: **41 points, not 62** — the 21-point difference is the
> KYC, consent, audit, e-Sign and e-NACH work that will already exist.

**The requester's concern was met, not dismissed.** The Head of Two-Wheeler Lending was given a
commitment that no ORIGIN design decision would preclude reuse, and was added as a **reviewer** on the
data model (07) and the rule-engine design. This converted an opponent of the schedule into a reviewer
of the architecture, and cost nothing.

**Register updated:** RSK-05 residual score revised from 6 to 3 — the mitigation was tested and held.
The CR process *was* the mitigation, and it worked.

---

## CR-002 · Narrow the BRULE-04 auto-approve band ✅ Approved

**Raised:** FRD review, day 2 · **Type:** Credit rule (tightening) · **Decision authority:** SH-02 CRO

### Request

BRULE-04 v1.1 auto-approved applicants with a bureau score of 700–749 at FOIR up to 0.50. During the
decision-table walkthrough the CRO asked that the **FOIR 0.46 – 0.50 × score 700 – 749** cell be moved
from `AUTO_APPROVE` to `REFER`.

| BRULE-04 · FOIR ↓ / Score → | 650–699 | 700–749 | ≥ 750 |
|---|---|---|---|
| ≤ 0.40 | `REFER` | `AUTO_APPROVE` | `AUTO_APPROVE` |
| 0.41 – 0.45 | `REFER` | `AUTO_APPROVE` | `AUTO_APPROVE` |
| **0.46 – 0.50** | `AUTO_DECLINE` | **`AUTO_APPROVE` → `REFER`** | `AUTO_APPROVE` |
| 0.51 – 0.55 | `AUTO_DECLINE` | `AUTO_DECLINE` | `REFER` |
| > 0.55 | `AUTO_DECLINE` | `AUTO_DECLINE` | `AUTO_DECLINE` |

The CRO's reasoning: a mid-band score combined with half of declared income already committed to
existing obligations is the cell where two weak signals compound, and it is the cell where underwriter
judgement adds the most value.

### Impact assessment — backtest against 4,612 historical applications

The affected cell is a single cell in one decision table, so the impact is directly **measurable**
rather than estimated.

| Measure | v1.1 | v1.2 (approved) | Change |
|---|---|---|---|
| Auto-approve share | 35.9% | 31.2% | **−4.7 pp** |
| Auto-decline share | 42.2% | 42.2% | — |
| **Auto-decisioned (BR-04)** | **78.1%** | **73.4%** | **−4.7 pp** |
| Referred share | 21.9% | 26.6% | +4.7 pp |
| Applications in the affected cell | — | **217 of 4,612** | 72 per month |

### Does it still meet BR-04?

| BR-04 target | v1.1 headroom | v1.2 headroom |
|---|---|---|
| ≥ 70% auto-decisioned | 8.1 pp | **3.4 pp** |

Yes — 73.4% clears the 70% target. **But the headroom more than halves, and that is the finding that
changed the release plan.** BR-04 is measured on live applicant mix, not on the backtest population. A
shift toward mid-band scores of the size seen in the last festive season would consume 3.4 pp of
headroom in weeks, and breach a baselined business requirement silently.

FR-044 (daily decision-band distribution report) is the only control that would detect this. It was
prioritised **Should** and sat at position 1 on the descope list — meaning the requirement protecting
BR-04 was the first thing scheduled to be cut under pressure.

> **Consequential change, approved with CR-002: FR-044 is promoted from Should to Must** and removed
> from the descope list. Cost: 3 points of descope reserve (15 → 12). This is the part of the
> assessment I would lead with in a review — the rule change itself was easy to assess, and its real
> cost was somewhere else entirely.

### Capacity impact — does CON-03 still hold?

CON-03 forbids any increase in underwriting headcount, so 72 extra referrals per month must be
absorbed by the existing 12 FTE.

| Measure | Value | Basis |
|---|---|---|
| Referred cases per month, v1.2 | 409 | 1,537 applications × 26.6% |
| Underwriter time per referred case | 15 min | TO-BE target (02 §4); AS-IS was 43 min |
| Monthly effort on referrals | **102 hours** | 409 × 15 min |
| Team capacity | 1,512 hours | 12 FTE × 21 days × 6 productive hours |
| **Utilisation on decisioning** | **6.8%** | Up from 5.6% at v1.1 |

**CON-03 holds with very large margin.** The AS-IS process consumed 43 minutes of underwriter time per
case on assessment and rework; the TO-BE target is 15 minutes on a quarter of the volume. The binding
constraint on referral volume in the TO-BE process is not underwriter hours — it is the 24-hour TAT
commitment in BR-01, and 409 cases per month across 12 underwriters is roughly 1.6 cases per
underwriter per day.

**Why the AS-IS process took 6.8 days at only ~50% average utilisation:** average utilisation is the
wrong statistic. Applications arrive in festive-season peaks at roughly twice the mean, and queueing
time rises non-linearly as utilisation approaches 1. A team at 50% on average is above 95% during the
peak, which is when the backlog forms and never clears. This is why the TO-BE design targets *referral
volume* rather than *underwriter speed*.

### Cost of accepting

| Item | Value | Basis |
|---|---|---|
| Applications moved to REFER | 124 per year | 72/month annualised on the affected cell |
| Of which underwriters actually declined in the baseline | **31 of 217 backtested (14.3%)** | Actual historical outcomes for the same cell |
| Disbursal v1.1 would have auto-approved and underwriters declined | ₹3,47,20,000 per year | 124 × ₹2,80,000 average ticket |
| Assumed marginal loss rate on the cell vs portfolio | 9.5% vs 2.8% | Credit team estimate — **the softest number here** |
| **Expected credit loss avoided** | **≈ ₹23,26,000 per year** | 6.7 pp excess × ₹3,47,20,000 |
| Revenue forgone | **₹0** | See below |

**CR-002 costs turnaround time, not revenue.** This is the point most easily got wrong. The 124
applications per year are not declined — they are **referred**. Roughly 93 of them will still be
approved, by an underwriter, within the same 24-hour window. The cost is that those 93 applicants wait
hours instead of seconds, and 409 cases a month need human review. The benefit is that the 31 the
underwriters would have declined are no longer auto-approved.

**Honest caveat on the 9.5% loss rate:** it is a credit-team judgement on a 217-application sample,
not an observed outcome, and the loss avoided is directly proportional to it. If the true marginal loss
rate is 4% rather than 9.5%, the benefit falls to ₹4,16,000 and the change is close to break-even on
pure economics. It would still be the right decision, because a 14.3% historical decline rate in a cell
proposed for *automatic approval* is on its own sufficient evidence that the cell needs judgement.

### Decision

**Approved by SH-02 on the day it was raised.** Documented as BRULE-04 **v1.2** with the version
history retained in the FRD — the superseded v1.1 is visible, not overwritten, because the audit trail
applies to requirements as much as to decisions.

### Downstream artefacts changed

| Artefact | Change |
|---|---|
| 02-Process models | Auto-decisioned figure restated 78.1% → 73.4% |
| 03-BRD | BR-04 note added: target subordinate to credit quality; approval status records the narrowing |
| 04-FRD | BRULE-04 → v1.2 with version note; **FR-044 priority Should → Must** |
| 05-User stories | US-18 priority Should → **Must** |
| 08-UAT | UAT-19 → UAT-21 expected results updated to the v1.2 matrix |
| 09-RTM | BRULE-04 version 1.2; FR-044 and US-18 priority updated |
| 10-Release plan | Must count 34 → 35; descope reserve 15 → 12 points; item 1 removed |

**Seven artefacts for a one-cell rule change.** That ratio is the argument for the traceability matrix
being machine-validated — a manual update of seven documents misses one, and the one it misses is
usually the matrix.

---

## CR-003 · Cooling-off period and grievance redressal disclosure ✅ Approved

**Raised:** Sprint 1, day 9 · **Type:** Regulatory · **Decision authority:** SH-04 Compliance

### Request

Compliance review of the baselined FRD against the RBI Digital Lending Guidelines found two
obligations with **no corresponding requirement anywhere in the package**:

1. **Cooling-off (look-up) period.** A digital-loan borrower must be able to exit the loan by paying
   the principal and the proportionate APR, without penalty, during an initial cooling-off window. For
   loan tenors of seven days or more the window is **not less than three days**. Project ORIGIN lends
   at 12–60 month tenors, so the three-day minimum applies.
   Sources: [Guidelines on Digital Lending, 2 September 2022](https://fintech.global/2022/09/07/rbi-unveils-new-guidelines-on-digital-lending/) ·
   [RBI Digital Lending Directions, 2025](https://www.axisbank.com/docs/default-source/default-document-library/reserve-bank-of-india-digital-lending-directions2025.pdf) ·
   [tenor-based duration](https://iibf.org.in/documents/Brochure/2025/Digital%20lending%20guidelines%202025.pdf)
2. **Grievance redressal disclosure.** Nodal grievance officer details for the lender and any lending
   service provider, plus the route to the RBI complaint portal, must be disclosed to the borrower.

*(Regulatory content above is paraphrased from the cited sources for licensing compliance.)*

This is a **gap in the requirements, not a change of mind.** BR-05 asserts that 100% of RBI Digital
Lending Guideline obligations are mapped to a control, so the package was in breach of its own
baselined business requirement. The Key Fact Statement itself was already covered by FR-026 — the
review found what FR-026 does *not* say.

### The interesting part: this obligation straddles the scope boundary

A cooling-off exit is exercised **after disbursal**. The BRD (03 §4) puts "collections and servicing"
explicitly out of scope and ends the ORIGIN value stream at the disbursal instruction. So a mandatory
obligation of the loan contract ORIGIN creates is *executed* by a system ORIGIN does not build.

The two tempting responses are both wrong:

| Wrong response | Why it fails |
|---|---|
| "It's servicing, therefore out of scope" | ORIGIN originates the contract that carries the obligation. Shipping a contract whose terms cannot be honoured is a compliance finding against ORIGIN |
| "It's regulatory, therefore absorb it" | Building loan closure, refund and proportionate-APR settlement inside an origination platform duplicates the LMS and breaches CON-01 |

**Decompose by obligation, not by system.** The obligation splits into four parts, and only three of
them are ORIGIN's:

| Obligation | Owner | Requirement |
|---|---|---|
| **Disclose** the cooling-off right, duration and exit amount before signing | **ORIGIN** | FR-045 |
| **Enable** it — compute the window expiry and hand it to the servicing platform | **ORIGIN** | FR-046 |
| **Execute** the penalty-free exit: settlement, closure, CIC reporting | **LMS / servicing** | Out of scope → **DEP-05** |
| Disclose grievance officer and RBI portal route | **ORIGIN** | FR-047 |

### Impact assessment

| Dimension | Assessment |
|---|---|
| Negotiable? | **No.** A regulatory obligation is absorbed by scope, not traded against it |
| New requirements | FR-045, FR-046, FR-047 — all **Must** (BR-05 requires 0 compliance findings) |
| New story | US-19 · 5 points, covering all three (static disclosure plus one data handoff) |
| New UAT cases | UAT-52, UAT-53 — both **S1-if-failed** |
| Data model impact | LOAN entity: `cooling_off_expires_at`; OFFER entity: `cooling_off_disclosed_at`. Both reproducible under FR-043 |
| State model impact | None. Deliberately — see below |
| New dependency | **DEP-05** — LMS must enforce penalty-free exit before the window expires |
| Cost | 5 story points; no new integration, no vendor, no licence |

**Why FR-046 is separate from FR-045, and why there is no new application state.** Disclosing a right
and making it operable are different obligations, and only the second is testable as a control. FR-046
requires the window expiry to be **computed at disbursal and transmitted in the disbursal instruction**
— a field on an existing message, not a new state in the ORIGIN state machine. Adding a `COOLING_OFF`
state to an origination workflow would model a servicing lifecycle in the wrong system. The application
reaches `DISBURSED` and ORIGIN's involvement ends; what it hands over is the deadline.

**DEP-05 is the honest output of this CR, and it is open at baseline.** ORIGIN can be fully compliant on
disclosure and the loan can still produce a compliance finding, because enforcement sits in the LMS. It
is recorded as a **go/no-go item for the pilot gate**, not as an assumption:

| ID | Dependency | Owner | Needed by | Status |
|---|---|---|---|---|
| DEP-05 | LMS enforces penalty-free exit within the cooling-off window, using the expiry supplied by FR-046 | LMS product owner (via SH-08) | **Pilot gate** | ⚠️ **Open — written confirmation requested, not yet received** |

**If DEP-05 is not confirmed, the recommendation is to hold go-live**, not to launch and remediate. That
is uncomfortable, because the sponsor's benefit case loses ₹43,07,000 for every month of delay. It is
still the right call: BR-05 targets zero compliance findings, and this one is knowable in advance.

### Schedule impact — this is the part that hurts

5 points does not sound like much. Against a plan with an 8-point buffer that had already lost 3 points
of descope reserve to CR-002, it matters.

| Measure | Before CR-003 | After CR-003 |
|---|---|---|
| Total committed | 106 points | **111 points** |
| Capacity (3 sprints × 38) | 114 points | 114 points |
| **Buffer** | **8 points (7.0%)** | **3 points (2.6%)** |
| Descope reserve (Should items) | 12 points | 12 points |

**Sequencing constraint:** FR-045 must be disclosed before the applicant signs, and e-Sign is delivered
by US-10 in sprint 2. Putting US-19 in sprint 3 would mean sprint 2 delivers a journey that cannot
legally go live, so the story has to land in sprint 2 — the sprint the release plan already identifies
as carrying the release risk, and which already runs 2 points above average velocity.

**Approved reallocation:** US-19 (5 points, Must) enters sprint 2; **US-07** (FR-018 bureau report cache,
3 points, Should) moves out to sprint 3. Sprint 2 goes to 42 points against a 38-point velocity —
**11% above average, flagged as accepted risk rather than hidden inside a total.**

| Sprint | Before | After |
|---|---|---|
| Sprint 1 — Capture and identity | 36 | 36 |
| Sprint 2 — Decisioning and offer | 40 | **42** |
| Sprint 3 — Workbench and hardening | 30 | **33** |
| **Total** | **106** | **111** |

**Pre-authorised trigger, agreed with SH-01 and SH-08 at approval time:** if sprint 2 burn-down is more
than 8 points behind at day 7, **US-09 (5 points, Should) is dropped from sprint 3 without a further
approval cycle.** Deciding this at approval time rather than at the point of pain is the entire purpose
of an agreed descope order.

### Decision

**Approved by SH-04, absorbed into scope, no schedule extension**, with the execution half assigned to
the LMS as DEP-05 and escalated as a pilot-gate condition. Recorded as a **requirements defect found by
compliance review**, not as a scope change — the distinction matters, because a defect prompts the
question of why a review was needed to find it.

**Root cause, recorded honestly:** the elicitation plan (01 §3) scoped the Compliance review gate to
"KYC, consent and disclosure requirements", and the BA read that as covering the *offer* disclosures.
Both missed obligations sit **outside the origination happy path** — one is post-disbursal, the other is
a support-channel disclosure — and the elicitation plan was organised around the happy path.

**Corrective action:** the compliance review was re-run against the RBI Digital Lending Guidelines
**clause by clause** rather than against the process flow, which is how the second gap (grievance
redressal) was found in the same pass. Re-review found no further gaps. The elicitation approach for
regulated requirements is now "walk the regulation", not "walk the process" — a process-driven
elicitation can only find obligations that fall inside the process you already drew.

### Downstream artefacts changed — all of them, in the same commit

| Artefact | Change |
|---|---|
| 01-Stakeholders | **DEP-05** added to the RAID log as an open, pilot-gating dependency |
| 04-FRD | §5.1 added: FR-045, FR-046, FR-047 (all Must, tracing to BR-05 / BR-06 / BR-08) |
| 05-User stories | US-19 added, 5 points, Gherkin including the negative case; summary 105 → 110 points |
| 07-Data model | `cooling_off_expires_at` on LOAN, `cooling_off_disclosed_at` on OFFER; no new state |
| 08-UAT | UAT-52, UAT-53 added, both S1-if-failed; coverage summary updated to 47 FRs |
| 09-RTM | FR-045 → FR-047 rows; forward trace BR-05, BR-06, BR-08 updated; counts updated |
| 10-Release plan | Must 35 → 38; sprints 2 and 3 reallocated; buffer 8 → 3 points |

**The validator is the reason this was applied completely.** The first attempt updated the FRD and the
user stories and stopped there, which is exactly what a tired BA does at the end of a sprint.
`make validate` failed:

```
  ✗ 5 error(s)
    3 functional requirement(s) defined in the FRD but absent from the matrix: FR-045, FR-046, FR-047
    Must-priority FR(s) with no user story: FR-046, FR-047
    Must-priority FR(s) with no UAT case: FR-045, FR-046, FR-047
    forward/full trace disagree: BR-05 claims FR-045, but the FR-045 row does not list BR-05
    release plan: sprint 2 declares 40 points but its rows sum to 45
```

That is the failure mode the matrix exists to prevent, reproduced on a real change. A hand-checked
matrix would have been signed off in the broken state, because the FRD and the stories — the two
documents anyone actually reads — were already correct.

---

## What the change log shows about the package

| CR | Type | Lesson it carries |
|---|---|---|
| CR-001 | Rejected scope | The reasonable-sounding request is the expensive one. Rejecting it needs a number, not a policy reference |
| CR-002 | Approved rule change | The direct impact was trivial to assess; the real cost was a Should-priority monitoring requirement two documents away |
| CR-003 | Approved regulatory | An obligation can straddle a scope boundary. Split it by obligation, keep what you own, and raise the rest as a dependency instead of silently dropping it |

**All three assessments answer the same four questions:** what does it cost, what does it displace, who
decides, and what breaks if we say yes. A change request that does not answer all four is a request,
not an assessment.
