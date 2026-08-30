# BA-1 · Loan Origination Requirements Package

A complete, internally consistent requirements package for **Project ORIGIN** — a digital personal
loan origination journey for a mid-size Indian NBFC (₹50,000 – ₹10,00,000, salaried applicants).

Twelve documents, 8 business requirements, 47 functional requirements, 8 business rules, 30 NFRs,
19 user stories, 53 UAT cases, 3 change requests — **and a script that proves they agree with each
other.**

```bash
make validate   # parse all 12 documents and enforce 13 consistency rules
make test       # 25 tests: 9 assert the package is consistent, 16 assert the validator catches breakage
```

---

## The headline: the traceability matrix is executable

Every requirements package claims traceability. Almost none of them can prove it, because the matrix
is a table maintained by hand and it goes stale within two sprints — someone adds a requirement and
forgets the matrix, someone renumbers a story, someone deletes a test case. The matrix then *claims*
coverage without providing it, which is worse than having no matrix at all, because it is trusted.

`tools/validate_traceability.py` parses all twelve documents and enforces thirteen rules. It exits
non-zero on any violation.

```
Traceability validation — Project ORIGIN
────────────────────────────────────────────
  business requirements     8 found,  8 traced
  functional requirements  47 found, 47 traced
  business rules            8 found,  8 traced
  user stories             19 found, 19 traced
  UAT cases                53 found, 53 traced
  NFR gates                 8 found,  8 traced
  story points             110 found, 111 traced

  ✓ every FR in the FRD appears in the matrix, and vice versa
  ✓ every referenced ID exists in its source document
  ✓ priorities in the matrix match the FRD
  ✓ every Must FR has >= 1 user story
  ✓ every Must FR has >= 1 UAT case
  ✓ every BR is satisfied by >= 1 FR
  ✓ every FR has a parent BR (no orphans)
  ✓ forward trace and full trace are mutually consistent
  ✓ every business rule is traced to a UAT case
  ✓ each story's declared FRs match the matrix rows naming that story
  ✓ story priorities are consistent with the FRs they deliver
  ✓ MoSCoW groups in the release plan match the FRD priorities
  ✓ sprint plan reconciles: 111 points allocated, every story in exactly one sprint, within capacity

  ⚠ 1 warning(s)
    FR-041 (Should) has no user story -- acceptable for non-Must, but must be documented as a gap

PASS — 0 errors, 1 accepted warning(s)
```

## What it caught in my own documents

This is the part worth reading. The validator was not a formality — **it found twelve real defects in
work I had already written and believed was finished.**

| # | Defect | Rule | Why I could not see it by reading |
|---|---|---|---|
| 1–5 | Five forward/full trace disagreements: BR-01 claimed FR-019, FR-020, FR-021, FR-023 and BR-07 claimed FR-037, but the FRD traces those to BR-04 and BR-08 | 6, 8 | Each half of the matrix looked correct in isolation. Only comparing the two directions exposes it |
| 6–9 | **Four Must requirements had a matrix row and a UAT case but no acceptance criterion in any story** — FR-006, FR-010, FR-012, FR-020 | 7 | "Every Must FR traces to a story" was *true*. The story existed and was named. It just said nothing about that requirement |
| 10 | Release plan declared "Must — 34 requirements" while the table beneath it listed 39 | 9 | A number and a table three lines apart, both plausible |
| 11 | Sprint 2 declared 39 points; its rows summed to 40 | 10 | Arithmetic is not traceability |
| 12 | UAT coverage summary claimed 10 gated NFRs against a table listing 8 | — | Found while fixing the others |

**Defects 6–9 are the ones I would talk about in an interview.** A matrix can be 100% complete and
still hollow. FR-020 specifies reducing-balance EMI amortisation; no story pinned the method. A
developer choosing flat-rate interest on ₹5,00,000 / 36 months / 14% produces an EMI of **₹19,722.22
instead of ₹17,088.81 — 15.4% higher**, which inflates FOIR by 15.4% and moves applicants across
BRULE-04 decision-band boundaries. The system would have been *confidently wrong* about credit
decisions, and every traceability check would still have passed. FR-012 ("never store an Aadhaar
number") is the same shape with a regulatory consequence.

Rules 7–10 were written *after* a change request, to catch drift. They found four defects that
predated any change request. All twelve are documented in
[09-traceability-matrix.md](09-traceability-matrix.md) (GAP-01 → GAP-03) rather than quietly patched.

## The documents

| # | Document | What it contains |
|---|---|---|
| 01 | [Stakeholder analysis and RACI](01-stakeholder-analysis-and-raci.md) | 12 stakeholders, power/interest map, elicitation method **per stakeholder with a reason**, RACI with exactly one Accountable per activity, RAID log |
| 02 | [Process models](02-process-models.md) | AS-IS and TO-BE flows, 9 quantified pain points, gap analysis, expected impact |
| 03 | [Business requirements](03-business-requirements.md) | BR-01 → BR-08 with measurable success criteria, scope with **reasons for every exclusion**, business case with sensitivity analysis |
| 04 | [Functional requirements](04-functional-requirements.md) | FR-001 → FR-047, 8 versioned business rules as decision tables, rule precedence |
| 05 | [User stories](05-user-stories.md) | US-01 → US-19, 110 points, Gherkin covering negative and edge cases |
| 06 | [Non-functional requirements](06-non-functional-requirements.md) | NFR-01 → NFR-30 with numeric thresholds **and the conditions they are measured under** |
| 07 | [Data model](07-data-model.md) | ERD, 4 justified modelling decisions, data dictionary, state model, volumetrics |
| 08 | [UAT test cases](08-uat-test-cases.md) | UAT-01 → UAT-53, severity definitions, exit criteria, 11 S1-if-failed cases |
| 09 | [Traceability matrix](09-traceability-matrix.md) | Forward trace, full trace, rule trace, NFR gates, 3 documented gaps |
| 10 | [Release plan](10-release-plan.md) | MoSCoW, 3-sprint plan, **descope order agreed in advance**, phased go-live, rollback triggers |
| 11 | [Change requests](11-change-request.md) | 3 worked impact assessments — one rejected, two approved |
| — | [LEARN.md](LEARN.md) | How the artefacts fit together, and the interview questions this package invites |

## The numbers the package is built on

Everything traces back to a measured baseline rather than an assumption:

| Measure | AS-IS | TO-BE target |
|---|---|---|
| Applications / disbursals over 3 months | 4,612 / 1,893 | — |
| Completion rate | **41.0%** | > 62% |
| Median turnaround | **6.8 days** | < 24 hours |
| Manual handling per application | **1 h 45 min** | < 20 min |
| Monthly manual effort | **2,690 hours ≈ 16 FTE** | — |
| Auto-decisioned share | 0% | ≥ 70% (**backtested 73.4%**) |

**The ≥70% automation target was backtested before it was committed.** The drafted decision tables
were applied to all 4,612 historical applications: 73.4% would have fallen in an auto-decision band,
with approval-rate variance of −1.2pp against actual underwriter outcomes. Committing to a number
first and hoping the rules reach it is how automation targets get quietly restated at go-live.

Business case: **₹71,00,000 cost against ₹5,16,84,000 annual benefit — payback in 1.6 months**, with
the benefit sensitivity-tested against the one soft assumption it depends on (that 60% of
friction-driven drop-off is recoverable — modelled at 30% / 60% / 80%).

## Three change requests, three different lessons

| CR | Decision | The lesson |
|---|---|---|
| **CR-001** Extend to two-wheeler and gold loans | ❌ **Rejected** | The reasonable-sounding request is the expensive one. 62 points against 15 points of headroom; ₹43,07,000/month cost of delay. Rejecting it needed a number, not a policy reference |
| **CR-002** Narrow the BRULE-04 auto-approve band | ✅ Approved | The rule change was trivial to assess (78.1% → 73.4%). Its **real cost was two documents away**: BR-04 headroom fell to 3.4pp, so FR-044 — the only control that detects a breach — had to be promoted from Should to Must, costing 3 points of descope reserve |
| **CR-003** Cooling-off period and grievance disclosure | ✅ Approved, **split** | A regulatory obligation that **straddles the scope boundary**. Cooling-off exit happens after disbursal, in a system the BRD excludes. Split by obligation: ORIGIN discloses and computes the deadline; the LMS enforces it, raised as **DEP-05** — an open dependency that gates go-live |

**DEP-05 is the most honest thing in this package.** Every ORIGIN requirement can pass UAT and the
loan can still produce a compliance finding, because enforcement lives outside this scope. The
recommendation is to hold go-live if it is unconfirmed — which costs the sponsor ₹43,07,000 per month
of delay. Recording that, rather than launching and remediating, is the recommendation I would defend.

## Reading order

Skim in this order to see the chain rather than the documents: **03** (why) → **02** (current state)
→ **04** (what) → **05** (how it will be accepted) → **09** (proof it all connects) → **11** (what
happened when it changed).

## What this is not

- Not a real NBFC's requirements. The domain is realistic and the regulatory obligations are real and
  cited; the volumes, baseline metrics and backtest results are constructed to be internally
  consistent, not sampled from a live portfolio.
- Not a delivered system. There is no application here — the deliverable is the specification, and
  the code that exists is the validator that checks it.
- Not a template. Every ID resolves, every number reconciles, and `make validate` fails if that stops
  being true.
