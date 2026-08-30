# Requirements Traceability Matrix

**Project ORIGIN** · Version 1.8 · Baselined
**Validated by:** `tools/validate_traceability.py` — run `make validate`

---

## Why this matrix is machine-checked

A traceability matrix maintained by hand goes stale within two sprints. Someone adds a requirement
and forgets the matrix; someone renumbers a story; a test case is deleted. The matrix then becomes a
document that *claims* coverage without providing it, which is worse than not having one, because it
is trusted.

So this matrix is **parsed and validated by a script** that reads every other document in the package
and asserts:

**Traceability (rules 1–6)**

1. Every ID referenced here exists in its source document
2. Every requirement in the source documents appears here — nothing is silently dropped
3. Every **Must** functional requirement traces to at least one user story **and** one UAT case
4. Every business requirement is satisfied by at least one functional requirement
5. No orphans: no functional requirement exists without a parent business requirement
6. Priorities here match the priorities stated in the FRD

**Consistency of the plan (rules 7–10, added after CR-003)**

7. Each story's declared "Traces to" list matches the matrix rows naming that story
8. A story delivering any Must requirement is itself prioritised Must
9. The MoSCoW groups in the release plan match the FRD priorities exactly, and the declared counts
   match the number of requirements actually listed
10. Sprint arithmetic reconciles: declared sprint totals equal the sum of their rows, every story is
    allocated to exactly one sprint at the points the stories document gives it, and the committed
    total is within velocity × sprint count

The script **fails the build** on any of these. It found three genuine gaps, documented at the end.

**Rules 7–10 were added late, and they immediately found five more defects that rules 1–6 could not
see.** Traceability being intact says nothing about the numbers in the plan being right, or about
whether the artefacts a requirement traces *to* actually contain anything:

| Found by rules 7–10 | Why rules 1–6 were blind to it |
|---|---|
| 4 Must requirements (FR-006, FR-010, FR-012, FR-020) had a matrix row and a UAT case but **no acceptance criterion** in any story | Rules 3–4 check that a story *is named*, not that the story *says anything about that requirement* |
| 7 stories under-declared their own "Traces to" lists | The matrix was right; the stories document was stale, and nothing compared them |
| Release plan declared "Must — 34 requirements" while listing 39 | The count was prose, not a traced ID |
| Sprint 2 declared 39 points while its rows summed to 40 | Arithmetic is not traceability |
| UAT coverage summary claimed 10 gated NFRs against a table listing 8 | Same |

The first row is the one that matters. **A matrix can be 100% complete and still hollow** — every
requirement traced, every box ticked, and four Must requirements with nothing a developer could build
from. FR-012 ("never store an Aadhaar number") is the clearest case: a regulatory obligation whose only
defence was a UAT case that would have run weeks after the data model was set.

---

## Forward trace: business requirement → functional requirement

| BR | Objective | Satisfied by |
|---|---|---|
| **BR-01** | TAT < 24 h | FR-013, FR-018, FR-025, FR-030, FR-031, FR-036 |
| **BR-02** | No branch visit | FR-001, FR-002, FR-007, FR-029 |
| **BR-03** | Document drop-off < 12% | FR-003, FR-004, FR-005, FR-015, FR-027 |
| **BR-04** | ≥ 70% auto-decisioned | FR-013, FR-014, FR-015, FR-016, FR-017, FR-019, FR-020, FR-021, FR-022, FR-044 |
| **BR-05** | Regulatory compliance | FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-025, FR-026, FR-035, FR-040, FR-045, FR-046, FR-047 |
| **BR-06** | Applicant status visibility | FR-028, FR-032, FR-038, FR-039, FR-040, FR-041, FR-045, FR-047 |
| **BR-07** | Underwriter efficiency | FR-022, FR-033, FR-034, FR-036 |
| **BR-08** | Auditable decision trail | FR-023, FR-024, FR-034, FR-035, FR-037, FR-042, FR-043, FR-046 |

> **This table was corrected by the validator.** The first draft listed FR-019, FR-020, FR-021 and
> FR-023 under BR-01, and FR-037 under BR-07, on the reasoning that faster decisioning serves the
> TAT objective. But the FRD traces those requirements to BR-04 and BR-08, and the FRD is the source
> of truth. The validator's forward/full consistency check caught all five, which is the single most
> useful rule it enforces — a matrix that disagrees with itself looks correct when either half is
> read in isolation.

## Full trace: functional requirement → story → test

| FR | Priority | BR | User story | UAT case |
|---|---|---|---|---|
| FR-001 | Must | BR-02 | US-01 | UAT-01 |
| FR-002 | Must | BR-02 | US-01 | UAT-02 |
| FR-003 | Must | BR-03 | US-03 | UAT-04, UAT-05 |
| FR-004 | Must | BR-03 | US-01 | UAT-02 |
| FR-005 | Must | BR-03 | US-02 | UAT-03 |
| FR-006 | Must | BR-05 | US-01 | UAT-06 |
| FR-007 | Must | BR-02, BR-05 | US-04 | UAT-07 |
| FR-008 | Must | BR-05 | US-04 | UAT-07 |
| FR-009 | Must | BR-05 | US-04 | UAT-08, UAT-09 |
| FR-010 | Must | BR-05 | US-04 | UAT-10 |
| FR-011 | Must | BR-05 | US-04 | UAT-11 |
| FR-012 | Must | BR-05 | US-04 | UAT-12 |
| FR-013 | Must | BR-01, BR-04 | US-05 | UAT-13 |
| FR-014 | Must | BR-04 | US-05 | UAT-13, UAT-15 |
| FR-015 | Must | BR-03, BR-04 | US-05 | UAT-14 |
| FR-016 | Must | BR-04 | US-05 | UAT-16 |
| FR-017 | Must | BR-04 | US-06 | UAT-17 |
| FR-018 | Should | BR-01 | US-07 | UAT-18 |
| FR-019 | Must | BR-04 | US-06 | UAT-19 |
| FR-020 | Must | BR-04 | US-06 | UAT-19 |
| FR-021 | Must | BR-04 | US-06 | UAT-20, UAT-21, UAT-22, UAT-23, UAT-24 |
| FR-022 | Must | BR-04, BR-07 | US-06 | UAT-22 |
| FR-023 | Must | BR-08 | US-06 | UAT-25 |
| FR-024 | Must | BR-08 | US-16 | UAT-26 |
| FR-025 | Must | BR-01, BR-05 | US-08 | UAT-27 |
| FR-026 | Must | BR-05 | US-08 | UAT-27 |
| FR-027 | Should | BR-03 | US-09 | UAT-28 |
| FR-028 | Must | BR-06 | US-08 | UAT-29 |
| FR-029 | Must | BR-02 | US-10 | UAT-30 |
| FR-030 | Must | BR-01 | US-10 | UAT-30, UAT-31 |
| FR-031 | Must | BR-01 | US-10 | UAT-30 |
| FR-032 | Must | BR-06 | US-10 | UAT-32 |
| FR-033 | Must | BR-07 | US-11 | UAT-33 |
| FR-034 | Must | BR-07, BR-08 | US-11 | UAT-34, UAT-35 |
| FR-035 | Must | BR-05, BR-08 | US-12 | UAT-36, UAT-37 |
| FR-036 | Should | BR-01, BR-07 | US-13 | UAT-38 |
| FR-037 | Must | BR-08 | US-11 | UAT-35 |
| FR-038 | Must | BR-06 | US-14 | UAT-39, UAT-40 |
| FR-039 | Must | BR-06 | US-14 | UAT-39 |
| FR-040 | Must | BR-05, BR-06 | US-15 | UAT-41 |
| FR-041 | Should | BR-06 | — ⚠️ | UAT-42 |
| FR-042 | Must | BR-08 | US-17 | UAT-43 |
| FR-043 | Must | BR-08 | US-16 | UAT-44 |
| FR-044 | Must | BR-04 | US-18 | UAT-45 |
| FR-045 | Must | BR-05, BR-06 | US-19 | UAT-52 |
| FR-046 | Must | BR-05, BR-08 | US-19 | UAT-53 |
| FR-047 | Must | BR-05, BR-06 | US-19 | UAT-52 |

> **The last three rows and the FR-044 priority arrived by change request, not by the original
> baseline.** FR-044 was promoted Should → Must by CR-002; FR-045 → FR-047 were added by CR-003.
> Both are recorded in [11-change-request.md](11-change-request.md), and the validator is what forced
> the matrix to be updated in the same commit as the FRD.

## Business rule trace

| Business rule | Version | Implements | Tested by |
|---|---|---|---|
| BRULE-01 Age eligibility | 1.0 | FR-021 | UAT-20, UAT-21 |
| BRULE-02 Minimum income | 1.0 | FR-021 | UAT-21 |
| BRULE-03 Bureau score band | 1.1 | FR-021 | UAT-22, UAT-24 |
| BRULE-04 FOIR against score | **1.2** | FR-019, FR-021 | UAT-19, UAT-20, UAT-21, UAT-44 |
| BRULE-05 Adverse credit history | 1.0 | FR-021 | UAT-23, UAT-36 |
| BRULE-06 Referral band | 1.0 | FR-021, FR-022 | UAT-22 |
| BRULE-07 Name matching | 1.0 | FR-009 | UAT-08, UAT-09 |
| BRULE-08 Existing exposure | 1.0 | FR-021 | UAT-21 |

## Non-functional gate trace

Only the NFRs verified through UAT appear here; the remainder are verified by code review,
penetration test or architecture sign-off as stated in [06-non-functional-requirements.md](06-non-functional-requirements.md) §Verification.

| NFR | BR | UAT gate |
|---|---|---|
| NFR-01 | BR-03 | UAT-46 |
| NFR-02 | BR-01 | UAT-46 |
| NFR-06 | BR-01 | UAT-47 |
| NFR-09 | BR-03, BR-06 | UAT-48 |
| NFR-18 | BR-05 | UAT-49 |
| NFR-24 | BR-05 | UAT-50 |
| NFR-25 | BR-05 | UAT-50 |
| NFR-28 | BR-04 | UAT-51 |

---

## Gaps the validator found

The value of a checked matrix is that it surfaces gaps rather than concealing them. Three were found
and all three are recorded rather than quietly patched.

### GAP-01 · FR-041 has no user story ⚠️ *accepted*

**Finding:** FR-041 (read-only application view for Customer Service) has a UAT case but no user
story.

**Cause:** Customer Service (SH-07) was **consulted** in the elicitation plan, not represented as a
persona. The requirement came from call-log analysis rather than from a user conversation, so no
story was written for it.

**Decision:** Accepted for the baseline. FR-041 is a Should-priority requirement allocated to Sprint
3, and a story will be written during Sprint 2 refinement with two Customer Service representatives.
The validator reports this as a **warning, not an error**, because the priority is Should. Had it
been Must, this would block baselining.

**Why it is recorded rather than fixed immediately:** writing a story without talking to the users
would produce acceptance criteria invented by the BA, which is worse than an acknowledged gap.

### GAP-02 · BR-03 is only partially verifiable at UAT ⚠️ *accepted with monitoring*

**Finding:** BR-03 targets document-stage drop-off below 12%. Every functional requirement
supporting it (FR-003, FR-004, FR-005, FR-015, FR-027) has UAT coverage, but **no UAT case can
verify the business outcome** — drop-off is a behavioural metric that only exists once real
applicants use the system.

**Decision:** Accepted. UAT verifies the *mechanism*; the *outcome* is verified post-go-live. The
release plan therefore instruments stage-level funnel analytics from day one, with a 30-day review
against the 12% target as a formal gate.

**Why this matters generally:** several business requirements are like this. Confusing "the feature
works" with "the business outcome was achieved" is how projects are declared successful while the
benefit case never materialises. Stating which BRs are outcome-measured rather than
acceptance-tested is part of an honest matrix.

### GAP-03 · Four Must requirements were traced but had no acceptance criteria ✅ *fixed*

**Finding:** rule 7 compared each story's declared "Traces to" list against the matrix rows naming
that story. Seven stories disagreed with the matrix. In four cases the matrix was right and the story
was simply missing the requirement from its metadata line — but in four cases the requirement had **no
acceptance criterion at all**:

| Requirement | Priority | Story it was traced to | What was missing |
|---|---|---|---|
| **FR-006** product amount / tenure range rejection | Must | US-01 | No scenario for an out-of-range request |
| **FR-010** reject on e-KYC failure with a reason code | Must | US-04 | No scenario for e-KYC failing outright |
| **FR-012** never store an Aadhaar number | Must | US-04 | No scenario asserting the number is absent from storage |
| **FR-020** reducing-balance EMI calculation | Must | US-06 | No scenario pinning the calculation method |

**Why rules 1–6 could not see this.** Rule 3 asserts that every Must requirement traces to at least one
user story. All four did. The story existed, was named in the matrix, and was allocated to a sprint.
What the matrix could not tell was whether the story *said anything* about the requirement it was
credited with delivering — and a matrix that reports 100% coverage over hollow stories is worse than no
matrix, because it stops anyone looking.

**Consequence if it had shipped.** Each would have been caught at UAT, which is the expensive place to
catch a requirement rather than a defect:

- **FR-020 is the worst.** A developer choosing flat-rate interest instead of reducing-balance produces
  an EMI of ₹19,722.22 instead of ₹17,088.81 on a ₹5,00,000 / 36-month / 14% loan — **15.4% higher**.
  FOIR inflates by the same 15.4%, which is enough to move applicants across BRULE-04 band boundaries.
  The system would have been *confidently wrong* about credit decisions.
- **FR-012 is the most serious.** Storing a full Aadhaar number is a regulatory breach, and the data
  model is set in sprint 1 — weeks before UAT would have found it.

**Decision:** fixed, not accepted. Six scenarios were added across US-01, US-04 and US-06, and all
seven "Traces to" lines were completed. The additions did not change any story's points, because the
requirements were always inside those stories' scope — what was missing was the *specification*, not
the work.

**What I would change in the process:** rule 7 should have existed before the FRD was baselined. It was
written to catch drift *after* a change request, and it found four defects that predated any change
request. The lesson is that a traceability matrix verifies the *shape* of the requirements set, and
something else has to verify the *substance*.

---

## Validation status

Actual output, reproducible with `make validate`:

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

**"110 found, 111 traced" on story points is correct, not a discrepancy.** 110 points are attached to
the 19 user stories; the extra point is FR-041, allocated to sprint 3 without a story because GAP-01
is still open. The validator reconciles the two figures explicitly rather than reporting a single
number that hides one of them.
