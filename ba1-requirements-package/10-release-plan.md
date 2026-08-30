# Prioritisation and Release Plan

**Project ORIGIN** · Version 1.5 · Baselined
**Accountable:** SH-01 Head of Retail Lending

---

## 1. MoSCoW prioritisation

MoSCoW only works if **"Must" means the release is worthless without it**. If everything is a Must,
nothing has been prioritised and the first schedule pressure produces an arbitrary cut made by
whoever is closest to the code.

### Must — 43 requirements

The release cannot go live without these. Each either delivers the core journey, or is a regulatory
or audit obligation.

| Group | Requirements |
|---|---|
| Application capture | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006 |
| KYC and consent | FR-007, FR-008, FR-009, FR-010, FR-011, FR-012 |
| Income verification | FR-013, FR-014, FR-015, FR-016 |
| Decisioning | FR-017, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024 |
| Offer and disbursal | FR-025, FR-026, FR-028, FR-029, FR-030, FR-031, FR-032 |
| Underwriter workbench | FR-033, FR-034, FR-035, FR-037 |
| Status and audit | FR-038, FR-039, FR-040, FR-042, FR-043 |
| Automation monitoring *(CR-002)* | FR-044 |
| Regulatory disclosure *(CR-003)* | FR-045, FR-046, FR-047 |

**This count moved twice after baselining, and the original figure was wrong.** The first version of
this section said "Must — 34 requirements" while the groups beneath it listed 39. Nobody re-added the
list after the FRD was revised, and nobody noticed, because the number and the table were three lines
apart and both looked plausible. It is now checked by `tools/validate_traceability.py` (rule 9)
against the FRD rather than maintained by hand: 39 at baseline, +1 from CR-002 (FR-044 promoted),
+3 from CR-003 = **43**.

### Should — 4 requirements

Materially valuable; the release is viable without them.

| Requirement | What is lost if dropped | Workaround |
|---|---|---|
| FR-018 bureau report cache | Duplicate bureau fees on reapplication | Accept the cost; volume is low at launch |
| FR-027 accept a revised amount | Some applicants decline rather than negotiate | Applicant reapplies at a lower amount |
| FR-036 queue ageing indicator | Underwriters self-manage queue order | Supervisor monitors the queue manually |
| FR-041 Customer Service read-only view | CS asks Operations for status | Operations answers ad hoc — sustainable only at launch volume |

**FR-044 was removed from this list by CR-002.** Narrowing the auto-approve band left BR-04 with
3.4 pp of headroom, and FR-044 is the only control that detects a breach. A monitoring requirement
sitting at Should priority, first on the descope list, while the thing it monitors is a baselined
business requirement, is a defect in the prioritisation rather than a judgement call.

### Could — deferred to a post-launch release

| Item | Reason for deferral |
|---|---|
| Applicant document vault / re-upload history | No launch-blocking need |
| Underwriter case notes and internal comment thread | Rationale field (FR-034) is sufficient at launch |
| Multi-language interface | Segment analysis first (BRD out-of-scope) |
| Offer comparison across tenures side by side | FR-027 covers the functional need |
| Automated employer verification API | Employer list check in BRULE-06 is adequate |

### Won't — explicitly out of this release

Restating the BRD exclusions here, because MoSCoW without a Won't list invites relitigation every
sprint.

Self-employed applicants · other loan products · native mobile apps · LMS replacement ·
collections · ML credit scoring · regional languages.

---

## 2. Sprint plan

Team velocity is **38 points per 2-week sprint**, measured over the preceding 4 sprints. Total
committed work is **111 points** — 110 story points plus 1 unstoried point for FR-041 (see GAP-01) —
which is 2.9 sprints against a 3-sprint constraint (CON-02). Feasible **only if the Should items are
genuinely allowed to slip.**

### Sprint 1 — Capture and identity (36 points)

| Story | Requirements | Points |
|---|---|---|
| US-01 Start an application | FR-001, FR-002, FR-004, FR-006 | 5 |
| US-02 Know what is needed up front | FR-005 | 2 |
| US-03 Resume an application | FR-003 | 3 |
| US-04 Complete KYC digitally | FR-007 → FR-012 | 8 |
| US-05 Share bank statements | FR-013 → FR-016 | 8 |
| US-17 Audit trail is immutable | FR-042 | 5 |
| US-14 Check status (capture stages only) | FR-038, FR-039 | 5 |

**Sprint goal:** an applicant can complete the digital journey up to income verification, and every
state transition is audited.

**Why the audit trail is built in sprint 1 and not last:** retrofitting an append-only log after the
state machine exists means revisiting every transition. Building it first makes every subsequent
story audited by default. This is also the sequencing that protects BR-08, which the BRD declared
non-negotiable.

**Dependency:** DEP-01 (bureau contract) is not needed until sprint 2, but must be signed during
sprint 1 or sprint 2 cannot start.

### Sprint 2 — Decisioning and offer (42 points)

| Story | Requirements | Points |
|---|---|---|
| US-06 Receive an immediate decision | FR-017, FR-019 → FR-023 | 13 |
| US-16 Reconstruct a past decision | FR-024, FR-043 | 8 |
| US-08 Understand the offer | FR-025, FR-026, FR-028 | 5 |
| US-10 Complete signing digitally | FR-029 → FR-032 | 8 |
| US-15 Understand why I was declined | FR-040 | 3 |
| US-19 Know my right to cancel | FR-045, FR-046, FR-047 | 5 *(CR-003)* |

**Sprint goal:** an applicant can receive an automated decision and complete a disbursal end to end,
with every disclosure required before signing in place.

**This sprint carries the release risk.** It contains the two highest-point stories and depends on
three external integrations (bureau, e-Sign, e-NACH). If anything slips, it slips here.

**It also now runs 4 points above average velocity, and that is a deliberate, recorded choice.**
CR-003 added US-19, and FR-045 must be disclosed before e-Sign — which sprint 2 delivers. Scheduling
US-19 in sprint 3 would mean sprint 2 ends with a journey that cannot legally go live, so US-07
(Should) was moved out to sprint 3 to partially offset it. The residual 4-point overrun is accepted
rather than hidden, and it is why the day-7 trigger below exists.

### Sprint 3 — Underwriter workbench and hardening (33 points)

| Story | Requirements | Points |
|---|---|---|
| US-11 Assess a referred case | FR-033, FR-034, FR-037 | 13 |
| US-12 Prevent unilateral override | FR-035 | 5 |
| US-18 Monitor the automation rate | FR-044 | 3 |
| US-13 Work the oldest cases first | FR-036 | 3 *(Should)* |
| US-09 Accept a smaller loan | FR-027 | 5 *(Should)* |
| US-07 Reuse a recent bureau report | FR-018 | 3 *(Should — moved from sprint 2 by CR-003)* |
| FR-041 CS read-only view | FR-041 | 1 *(Should — story to be written in sprint 2 refinement, see GAP-01)* |

**Sprint goal:** referred cases can be processed, and the release is ready for UAT.

**Total: 111 points across 3 sprints (36 + 42 + 33) against 114 points of capacity.** The buffer is
**3 points — 2.6%**, down from 8% at baseline. CR-002 cost 3 points of descope reserve and CR-003 cost
5 points of buffer. The mitigation is that **12 of the 33 points in sprint 3 are Should items**, so if
sprint 2 overruns, sprint 3 absorbs it by dropping Should work rather than by cutting Must work or
extending the timeline.

**Pre-authorised trigger:** if sprint 2 burn-down is more than 8 points behind at day 7, **US-09
(5 points) is dropped from sprint 3 without a further approval cycle.** Agreed with SH-01 and SH-08
when CR-003 was approved, not at the point of pain.

### Descope order, agreed in advance

Deciding this now rather than under pressure is the point.

| Order | Drop | Points recovered | Consequence accepted |
|---|---|---|---|
| 1 | FR-036 queue ageing (US-13) | 3 | Supervisor manages the queue manually |
| 2 | FR-018 bureau cache (US-07) | 3 | Duplicate bureau fees accepted at launch volume |
| 3 | FR-027 revised amount (US-09) | 5 | Applicant reapplies at a lower amount |
| 4 | FR-041 CS view | 1 | Operations answers status queries ad hoc |

**12 points of descope available without touching a single Must requirement.** No Must requirement is
on this list, and none will be added to it — a Must that can be dropped was never a Must.

**The reserve shrank from 15 points to 12 when CR-002 promoted FR-044 to Must**, which is the real
cost of that change request. The rule change itself was free; losing the ability to cut 3 points under
pressure was not.

---

## 3. Go-live plan

### Phased rollout, not a full switch

| Phase | Duration | Scope | Exit gate |
|---|---|---|---|
| **Pilot** | 1 week | 2 branches, ~40 applications, manual shadow review of **every** decision | Zero credit decisions the underwriting team disagrees with |
| **Limited** | 2 weeks | 20% of applicant traffic, 10% shadow-reviewed | TAT < 24 h on ≥ 90% of auto-decisioned cases; no S1/S2 defects |
| **Full** | — | 100% of salaried applicants | Sustained for 30 days |

**Shadow review of every decision during pilot is the control that makes the automation acceptable
to the CRO.** It converts "we believe the rules are right" into evidence, and it is the only way to
detect a rule that is individually correct but wrong in combination.

### Rollback

| Trigger | Action |
|---|---|
| S1 defect in production | Route all new applications to the manual process; complete in-flight applications digitally |
| Auto-approval rate exceeds 85% | Suspend auto-approve band; route everything to REFER pending CRO review |
| Any auto-approved case later found to breach credit policy | Suspend auto-approve immediately; full rule audit |

The second trigger is a **safety limit in the opposite direction from the target**. BR-04 asks for
≥70% automation; an unexpected jump above 85% more likely indicates a rule defect than a genuine
improvement in applicant quality, and it should stop the system rather than be celebrated.

---

## 4. Post-launch measurement

Because [09-traceability-matrix.md](09-traceability-matrix.md) GAP-02 established that several
business requirements cannot be verified at UAT, they are verified here.

| BR | Metric | Target | Review point | Owner |
|---|---|---|---|---|
| BR-01 | Median TAT, auto-decisioned | < 24 h | Weekly from pilot | SH-01 |
| BR-02 | Journeys completed without a branch event | 100% | Day 30 | SH-01 |
| BR-03 | Document-stage drop-off | < 12% | Day 30 and day 90 | SH-05 |
| BR-04 | Auto-decisioned share | ≥ 70% | Daily from pilot | SH-02 |
| BR-05 | Compliance findings | 0 | Go-live review + quarterly | SH-04 |
| BR-06 | Status-related support contacts | < 15% of volume | Day 30 | SH-07 |
| BR-07 | Median underwriter handling time | < 15 min | Day 30 | SH-03 |
| BR-08 | Decisions with a complete audit trail | 100% | Sample audit of 50 cases at day 30 | SH-04 |

**The day-30 review of BR-03 replaces an assumption with a measurement.** The BRD business case
rests on recovering 60% of the friction-driven loss, and that number is a judgement. Day 30 is when
it becomes a fact — and the point at which the benefit case should be restated honestly rather than
left as approved.
