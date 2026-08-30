# Business Requirements Document (BRD)

**Project ORIGIN** — Digital Personal Loan Origination
**Version:** 1.4 · **Status:** Baselined · **Approved by:** SH-01 Head of Retail Lending

---

## 1. Business context

The NBFC originates personal loans through a branch-dependent, paper-first process. Over the
3-month baseline period it received **4,612 applications** and disbursed **1,893** — a **41.0%
completion rate** with a **median 6.8-day turnaround**.

Competitors offering same-day digital disbursal are winning the salaried segment. Every day of
turnaround is a day in which the applicant can be approved elsewhere, and **28% of applicants are
lost purely to the requirement to visit a branch twice**.

Separately, credit assessments are performed in offline spreadsheets outside the system of record,
meaning **no auditable decision trail exists for any lending decision**. This was discovered during
process shadowing and is a regulatory exposure independent of the commercial case.

## 2. Problem statement

> The current origination process loses 59% of applicants before disbursal, takes 6.8 days, consumes
> approximately 16 FTE in manual processing, and produces no auditable record of how credit
> decisions were reached.

## 3. Objectives and success criteria

| ID | Business requirement | Success criterion | Measured by | Owner |
|---|---|---|---|---|
| **BR-01** | Reduce application turnaround time | Median TAT **< 24 hours** for auto-decisioned applications | LMS timestamp: application submit → disbursal instruction | SH-01 |
| **BR-02** | Remove the mandatory branch visit for salaried applicants | **0** mandatory branch visits in the standard journey | Process audit; journey completion without branch event | SH-01 |
| **BR-03** | Reduce abandonment at the document stage | Document-stage drop-off **< 12%** (from 32%) | Funnel analytics, stage-level exit rate | SH-05 |
| **BR-04** | Automate credit decisioning for the majority of applications | **≥ 70%** of applications decided without human review | Decision-band distribution report | SH-02 |
| **BR-05** | Maintain full regulatory compliance | **100%** of RBI Digital Lending Guideline obligations mapped to a control; **0** compliance findings at go-live review | Compliance sign-off checklist | SH-04 |
| **BR-06** | Give applicants real-time application visibility | Status-related support contacts **< 15%** of call volume (from 41%) | Call-centre tagging report | SH-07 |
| **BR-07** | Equip underwriters to process referred cases efficiently | Median handling time **< 15 min** per referred case (from 43 min including rework) | Workbench timing instrumentation | SH-03 |
| **BR-08** | Produce an auditable trail for every credit decision | **100%** of decisions reconstructable: inputs, rule versions, outcome, actor | Audit log completeness test; sample audit of 50 cases | SH-04 |

### Prioritisation of objectives against each other

Stated explicitly because objectives conflict and someone must decide in advance which yields.

**BR-05 (compliance) and BR-08 (auditability) are absolute.** They are not traded against TAT or
conversion under any circumstances. If a control slows the journey, the journey is slower.

**BR-04 (automation rate) yields to credit quality.** The 70% target is subordinate to maintaining
the current approval-quality profile. The CRO holds the authority to narrow the auto-approve band
at any point, and doing so is an accepted outcome rather than a project failure.

**BR-01, BR-02, BR-03 (speed and conversion) are the commercial core** and drive sequencing.

**BR-06, BR-07 (experience and efficiency) are valuable and deferrable.** These are the candidates
if the 3-sprint window (CON-02) comes under pressure — reflected in the MoSCoW allocation in
[10-release-plan.md](10-release-plan.md).

## 4. Scope

### In scope

| Area | Included |
|---|---|
| Product | Personal loans, ₹50,000 – ₹10,00,000, tenure 12–60 months |
| Segment | Salaried applicants, age 21–58, Indian resident |
| Journey | Application capture → KYC → income verification → decisioning → offer → e-sign → disbursal instruction |
| Channels | Web and mobile web |
| Decisioning | Rules-based auto-approve / refer / auto-decline with underwriter workbench for referrals |
| Integrations | Aadhaar e-KYC, Account Aggregator, credit bureau, e-Sign, e-NACH, existing LMS |

### Explicitly out of scope

Listed with reasons, because an out-of-scope list without reasons gets relitigated every sprint.

| Excluded | Reason |
|---|---|
| Self-employed / business income applicants | Requires ITR and GST assessment logic — a materially different credit model. Separate initiative. |
| Two-wheeler, gold, and consumer durable loans | Different collateral and regulatory treatment. Reusing this platform is a future roadmap item. |
| Native mobile applications | Mobile web meets CON-02. Native is a separate delivery. |
| Replacement of the core LMS | CON-01. Integration only. |
| Collections and servicing | Downstream of origination. Out of the value stream in scope. |
| Machine-learning credit scoring | Rules-based decisioning is required first to establish auditability (BR-08) and a labelled dataset. ML without either is not approvable. |
| Regional language support | Deferred to post-launch based on segment analysis. |

**The ML exclusion is a deliberate sequencing argument, not a technology objection.** An ML
underwriting model needs (a) an auditable decision baseline to be compared against and (b) a
labelled outcome dataset generated under consistent rules. This project creates both. Attempting ML
first would fail BR-08 and would not be approvable by SH-02 or SH-04.

## 5. Business case

### Costs

| Item | Amount |
|---|---|
| Delivery (3 sprints, 6 FTE) | ₹42,00,000 |
| Integration and vendor onboarding (AA, e-Sign, e-NACH) | ₹11,00,000 |
| Annual licence and per-transaction fees | ₹18,00,000 / year |
| **Year 1 total** | **₹71,00,000** |

### Benefits

| Benefit | Basis | Annual value |
|---|---|---|
| Additional disbursals from conversion 41.0% → 62% | +21pp × 18,448 applications/year × ₹2,80,000 avg ticket × 4.2% net margin | **₹4,55,55,000** |
| Operations cost avoided | 16 FTE → 4 FTE; 12 FTE × ₹4,80,000 fully loaded | **₹57,60,000** |
| Support cost avoided | 26pp reduction in status calls × 16,720 calls/year × ₹85 | **₹3,69,000** |
| **Total annual benefit** | | **₹5,16,84,000** |

### Return

| Measure | Value |
|---|---|
| Year 1 net benefit | ₹4,45,84,000 |
| Payback period | **≈ 1.6 months** |
| 3-year NPV @ 12% | ₹11,42,00,000 |

### Why this case should be treated with suspicion

The benefit is dominated by one number — the conversion improvement — and that number rests on an
assumption, not a measurement: **that 60% of the loss currently caused by branch visits and document
friction is recoverable.**

Sensitivity on that single assumption:

| Share of friction loss recovered | Conversion | Annual benefit | Payback |
|---|---|---|---|
| 30% | 51.5% | ₹2,89,00,000 | 2.9 months |
| **60% (base)** | **62.0%** | **₹5,16,84,000** | **1.6 months** |
| 80% | 69.0% | ₹6,68,00,000 | 1.3 months |

The project remains strongly positive across the range, so the *decision* is robust even though the
*number* is uncertain. That is the honest way to present it — and the reason the go-live plan in
[10-release-plan.md](10-release-plan.md) instruments stage-level conversion from day one, so the
assumption gets replaced by a measurement within the first month.

## 6. Approvals

| Role | Stakeholder | Approval scope | Status |
|---|---|---|---|
| Sponsor | SH-01 | Business case, scope, objectives | ✅ Baselined v1.4 |
| Chief Risk Officer | SH-02 | BR-04 target and all decisioning rules | ✅ Approved with narrowed FOIR band (see [11-change-request.md](11-change-request.md) CR-002) |
| Compliance | SH-04 | BR-05, BR-08 | ✅ Approved |
| Engineering | SH-08 | Feasibility within CON-02 | ✅ Confirmed, contingent on DEP-01 |
