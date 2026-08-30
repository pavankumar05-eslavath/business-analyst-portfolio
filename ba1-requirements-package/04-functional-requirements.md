# Functional Requirements Document (FRD)

**Project ORIGIN** · Version 1.6 · Baselined

Every requirement is testable, traced to a business requirement, and written so a developer can
build it without a follow-up conversation. Where behaviour is conditional it is expressed as a
**decision table**, not prose — prose cannot be shown to cover every combination.

---

## 1. Application capture

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-001** | The system shall allow an applicant to start an application by entering mobile number and PAN, and shall verify the mobile number by OTP before any further data is captured. | BR-02 | Must |
| **FR-002** | The system shall capture: full name, date of birth, gender, PAN, current address, employment type, employer name, monthly net income, requested loan amount, requested tenure. | BR-02 | Must |
| **FR-003** | The system shall persist a partially completed application and allow the applicant to resume it from the same mobile number for **7 calendar days**. | BR-03 | Must |
| **FR-004** | The system shall validate each field at the point of entry and display the specific failure reason before the applicant can proceed. Validation rules are defined in [06-non-functional-requirements.md](06-non-functional-requirements.md) §5. | BR-03 | Must |
| **FR-005** | The system shall display the complete list of information and documents required for the selected employment type **before** the applicant begins data entry. | BR-03 | Must |
| **FR-006** | The system shall reject an application at capture where requested amount is outside ₹50,000–₹10,00,000 or requested tenure is outside 12–60 months, stating the permitted range. | BR-05 | Must |

**FR-005 is the direct fix for P-02.** 32% of applicants arrived with incomplete documents because
nothing told them what was needed up front. This requirement exists because of a measured
behaviour, not because it is good practice.

## 2. KYC and identity verification

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-007** | The system shall perform Aadhaar-based e-KYC using OTP authentication against the applicant's registered mobile number. | BR-02, BR-05 | Must |
| **FR-008** | The system shall capture explicit, purpose-limited applicant consent before initiating e-KYC, recording consent text version, timestamp and IP address. | BR-05 | Must |
| **FR-009** | The system shall verify that the name returned by e-KYC matches the name on the PAN record, applying the fuzzy-match tolerance in BRULE-07. | BR-05 | Must |
| **FR-010** | The system shall reject the application where e-KYC fails, display a plain-language reason, and record the failure reason code. | BR-05 | Must |
| **FR-011** | The system shall allow the applicant to revoke consent at any point before disbursal, and on revocation shall halt processing and mark the application as withdrawn. | BR-05 | Must |
| **FR-012** | The system shall not store Aadhaar numbers. Only the e-KYC reference identifier and the masked last-4 digits shall be retained. | BR-05 | Must |

**FR-012 is a hard regulatory constraint, not a design preference.** It is called out separately
from FR-007 because it is the requirement most likely to be violated by a developer taking the
convenient path of persisting the full response payload.

## 3. Income and bank statement verification

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-013** | The system shall retrieve the applicant's 6-month bank statement via Account Aggregator with applicant consent. | BR-01, BR-04 | Must |
| **FR-014** | The system shall derive from the statement: average monthly credit, salary credit identification, average monthly balance, count of returned/bounced debits, and existing EMI obligations. | BR-04 | Must |
| **FR-015** | Where Account Aggregator retrieval is unavailable or declined, the system shall allow PDF bank statement upload and shall parse it to derive the same fields as FR-014. | BR-03, BR-04 | Must |
| **FR-016** | The system shall flag for referral any case where derived monthly income deviates from the applicant-declared income by more than **20%**. | BR-04 | Must |

**FR-015 exists because of ASM-02.** Account Aggregator coverage is an assumption. Without a
fallback, a single external dependency can halt all applications.

## 4. Eligibility and credit decisioning

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-017** | The system shall retrieve a credit bureau report for the applicant using PAN. | BR-04 | Must |
| **FR-018** | The system shall reuse a bureau report retrieved within the previous **72 hours** for the same PAN rather than issuing a new request. | BR-01 | Should |
| **FR-019** | The system shall calculate FOIR as (existing monthly EMI obligations + proposed EMI) ÷ derived monthly net income, expressed to 4 decimal places. | BR-04 | Must |
| **FR-020** | The system shall calculate proposed EMI using reducing-balance amortisation at the applicable product interest rate for the requested amount and tenure. | BR-04 | Must |
| **FR-021** | The system shall evaluate all eligibility rules BRULE-01 through BRULE-08 and assign exactly one decision band: `AUTO_APPROVE`, `REFER`, or `AUTO_DECLINE`. | BR-04 | Must |
| **FR-022** | The system shall route every `REFER` application to the underwriter work queue together with the specific rule identifier(s) that triggered referral. | BR-04, BR-07 | Must |
| **FR-023** | The system shall record the decision outcome directly against the application in the system of record, with no manual re-entry step. | BR-08 | Must |
| **FR-024** | The system shall persist, for every decision: each rule identifier evaluated, the rule version, the input values used, the individual rule outcome, and the final band. | BR-08 | Must |

**FR-024 is what makes BR-08 real.** Storing only the final decision is not an audit trail — an
auditor asks *why* a decision was reached, which requires the inputs and the rule version in force
at that moment. Rules change; decisions must remain reconstructable against the version that
actually applied.

### 4.1 Business rules — decision tables

Every rule is versioned and CRO-approved. A decision table is used wherever more than two
conditions interact, because prose cannot be shown to be exhaustive.

#### BRULE-01 · Age eligibility (v1.0)

| Condition | Outcome |
|---|---|
| Age < 21 | `AUTO_DECLINE` (reason `AGE_BELOW_MIN`) |
| Age 21–57 | Pass |
| Age = 58 **and** tenure would end after age 60 | `REFER` (reason `AGE_TENURE_MISMATCH`) |
| Age > 58 | `AUTO_DECLINE` (reason `AGE_ABOVE_MAX`) |

#### BRULE-02 · Minimum income (v1.0)

| Condition | Outcome |
|---|---|
| Derived monthly net income < ₹25,000 | `AUTO_DECLINE` (reason `INCOME_BELOW_MIN`) |
| ₹25,000 – ₹34,999 **and** requested amount > ₹3,00,000 | `REFER` (reason `INCOME_AMOUNT_MISMATCH`) |
| ≥ ₹35,000 | Pass |

#### BRULE-03 · Bureau score band (v1.1)

| Bureau score | Outcome |
|---|---|
| No bureau record ("new to credit") | `REFER` (reason `NTC_APPLICANT`) |
| < 650 | `AUTO_DECLINE` (reason `SCORE_BELOW_MIN`) |
| 650 – 699 | `REFER` (reason `SCORE_MARGINAL`) |
| 700 – 749 | Pass with FOIR cap 0.45 (see BRULE-04) |
| ≥ 750 | Pass with FOIR cap 0.55 |

#### BRULE-04 · FOIR against bureau score (v1.2 — narrowed by CR-002)

Two conditions interacting, so a full matrix. Every combination is resolved.

| FOIR ↓ / Score → | 650–699 | 700–749 | ≥ 750 |
|---|---|---|---|
| ≤ 0.40 | `REFER` | **`AUTO_APPROVE`** | **`AUTO_APPROVE`** |
| 0.41 – 0.45 | `REFER` | **`AUTO_APPROVE`** | **`AUTO_APPROVE`** |
| 0.46 – 0.50 | `AUTO_DECLINE` | `REFER` | **`AUTO_APPROVE`** |
| 0.51 – 0.55 | `AUTO_DECLINE` | `AUTO_DECLINE` | `REFER` |
| > 0.55 | `AUTO_DECLINE` | `AUTO_DECLINE` | `AUTO_DECLINE` |

> **Version note:** v1.1 auto-approved FOIR 0.46–0.50 at score 700–749. The CRO narrowed this to
> `REFER` during review (CR-002). Backtesting showed the change reduces auto-decision coverage from
> 78.1% to **73.4%** while remaining above the BR-04 target of 70%. This is exactly the trade the
> BRD anticipated when it stated that BR-04 yields to credit quality.

#### BRULE-05 · Adverse credit history (v1.0)

Evaluated in order; the first match wins.

| Condition | Outcome |
|---|---|
| Any account written off or settled in the last 36 months | `AUTO_DECLINE` (reason `WRITEOFF_SETTLED`) |
| Any account 90+ days past due in the last 12 months | `AUTO_DECLINE` (reason `DPD_90_RECENT`) |
| Any account 60–89 days past due in the last 12 months | `REFER` (reason `DPD_60_RECENT`) |
| More than 3 unsecured enquiries in the last 30 days | `REFER` (reason `ENQUIRY_VELOCITY`) |
| None of the above | Pass |

#### BRULE-06 · Referral band definition (v1.0)

This rule exists because of gap **P-08** — escalation criteria had never been written down.

| Condition | Outcome |
|---|---|
| Any rule above returned `REFER` | `REFER` |
| Derived income deviates > 20% from declared (FR-016) | `REFER` (reason `INCOME_MISMATCH`) |
| ≥ 3 returned debits in the 6-month statement | `REFER` (reason `BOUNCE_HISTORY`) |
| Employer not on the approved employer list **and** requested amount > ₹5,00,000 | `REFER` (reason `EMPLOYER_UNLISTED_HIGH_VALUE`) |
| All rules pass and no referral trigger | `AUTO_APPROVE` |

#### BRULE-07 · Name matching tolerance (v1.0)

| Condition | Outcome |
|---|---|
| Exact match after case and whitespace normalisation | Pass |
| Match score ≥ 0.85 (token-based similarity) | Pass |
| Match score 0.70 – 0.84 | `REFER` (reason `NAME_PARTIAL_MATCH`) |
| Match score < 0.70 | `AUTO_DECLINE` (reason `NAME_MISMATCH`) |

#### BRULE-08 · Existing exposure limit (v1.0)

| Condition | Outcome |
|---|---|
| Existing unsecured exposure + requested amount > 15 × derived monthly income | `AUTO_DECLINE` (reason `EXPOSURE_LIMIT`) |
| Existing exposure with this NBFC and any current DPD > 0 | `AUTO_DECLINE` (reason `INTERNAL_DPD`) |
| Two or more live personal loans with any lender | `REFER` (reason `MULTIPLE_PL`) |
| Otherwise | Pass |

### 4.2 Rule precedence

Because rules can return conflicting outcomes, precedence must be defined. Leaving this to
implementation order is how the same applicant gets different decisions on different days.

> **Any `AUTO_DECLINE` overrides any `REFER`, and any `REFER` overrides `AUTO_APPROVE`.**
> All rules are evaluated regardless, so the audit trail records every outcome rather than stopping
> at the first decline.

## 5. Offer generation and acceptance

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-025** | The system shall generate an offer stating approved amount, interest rate, tenure, EMI, processing fee, APR, and total repayable amount. | BR-01, BR-05 | Must |
| **FR-026** | The system shall present the Key Fact Statement to the applicant before acceptance and record acknowledgement. | BR-05 | Must |
| **FR-027** | The system shall allow the applicant to accept a lower amount or a different tenure within the approved limits, recalculating EMI and re-running BRULE-04 on the revised figures. | BR-03 | Should |
| **FR-028** | The system shall expire an unaccepted offer **7 calendar days** after generation and notify the applicant 24 hours before expiry. | BR-06 | Must |
| **FR-029** | The system shall capture the applicant's e-Sign on the loan agreement using Aadhaar OTP authentication. | BR-02 | Must |

**FR-027 re-runs BRULE-04 rather than assuming a lower amount is always safe.** A shorter tenure
raises the EMI and therefore raises FOIR, which can move an application into a worse band. Treating
a "smaller loan" as automatically acceptable is a real credit defect.

### 5.1 Regulatory disclosures — added by CR-003

Added after the baseline. Compliance review found that FR-026 requires the Key Fact Statement to be
presented, but the package contained no requirement covering the **cooling-off period** or
**grievance redressal disclosure**, both of which are RBI Digital Lending Guideline obligations. See
[11-change-request.md](11-change-request.md) CR-003 for the impact assessment and root cause.

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-045** | The system shall disclose in the Key Fact Statement and the loan agreement, before e-Sign, the cooling-off period duration of **3 calendar days from disbursal**, the applicant's right to exit within it by paying principal plus proportionate APR with no penalty or exit charge, and the method of exercising that right. | BR-05, BR-06 | Must |
| **FR-046** | The system shall compute `cooling_off_expires_at` as disbursal timestamp + 3 calendar days, persist it against the loan, and transmit it in the disbursal instruction to the LMS (FR-031). | BR-05, BR-08 | Must |
| **FR-047** | The system shall display the nodal grievance officer name, designation, contact number, email and postal address, together with the escalation route to the RBI complaint portal, in the Key Fact Statement and on the applicant status page. | BR-05, BR-06 | Must |

**FR-046 is the requirement that makes FR-045 more than a paragraph of text.** A disclosed right that
no downstream system can honour is a compliance finding waiting to happen. ORIGIN cannot *execute* a
cooling-off exit — settlement and loan closure sit in the LMS, which the BRD places out of scope — so
the obligation is split: ORIGIN discloses and computes the deadline, the LMS enforces it. The
enforcement half is tracked as **DEP-05** and gates the pilot.

**There is deliberately no `COOLING_OFF` application state.** The cooling-off window belongs to the
loan servicing lifecycle, not the origination lifecycle. The application reaches `DISBURSED` and
ORIGIN's involvement ends; what crosses the boundary is a timestamp, not a workflow.

## 6. Disbursal

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-030** | The system shall register an e-NACH mandate on the applicant's bank account before disbursal. | BR-01 | Must |
| **FR-031** | The system shall raise a disbursal instruction to the LMS immediately on completion of e-Sign and e-NACH, without waiting for a batch window. | BR-01 | Must |
| **FR-032** | The system shall notify the applicant on disbursal with the amount credited, the first EMI date, and the repayment schedule. | BR-06 | Must |

## 7. Underwriter workbench

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-033** | The system shall present the underwriter with a single case view containing applicant details, derived income figures, bureau summary, all rule outcomes, and the specific referral reason(s). | BR-07 | Must |
| **FR-034** | The system shall allow the underwriter to record a decision of `APPROVE`, `DECLINE`, or `APPROVE_WITH_CHANGES` (revised amount or tenure), with a mandatory free-text rationale of at least 20 characters. | BR-07, BR-08 | Must |
| **FR-035** | The system shall prevent an underwriter from approving a case that triggered any `AUTO_DECLINE` rule. Overriding a decline requires a second approver at Credit Head level. | BR-05, BR-08 | Must |
| **FR-036** | The system shall prioritise the work queue by application age, oldest first, and shall display an ageing indicator for cases older than 4 working hours. | BR-01, BR-07 | Should |
| **FR-037** | The system shall record the underwriter identity, decision, rationale and timestamp against the application. | BR-08 | Must |

**FR-035 is the most important control in this section.** Without it, the referral queue becomes a
route to override credit policy — a single underwriter could approve anything the rules declined,
and the rules would be advisory rather than binding.

## 8. Status visibility and notifications

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-038** | The system shall display current application status to the applicant from a link authenticated by mobile OTP. | BR-06 | Must |
| **FR-039** | The system shall notify the applicant by SMS and email on: application received, KYC complete, decision made, offer ready, offer expiring, disbursal complete. | BR-06 | Must |
| **FR-040** | The system shall display, for a declined application, a plain-language reason and guidance on when reapplication is permitted. | BR-05, BR-06 | Must |
| **FR-041** | The system shall provide the customer service team a read-only view of application status and history. | BR-06 | Should |

## 9. Audit and reporting

| ID | Requirement | Traces to | Priority |
|---|---|---|---|
| **FR-042** | The system shall maintain an immutable, append-only audit log of every state transition, recording actor, timestamp, previous state and new state. | BR-08 | Must |
| **FR-043** | The system shall allow retrieval of a complete decision reconstruction for any application, showing all inputs, rule versions and outcomes as at the decision moment. | BR-08 | Must |
| **FR-044** | The system shall produce a daily decision-band distribution report showing counts and percentages by band and referral reason. | BR-04 | Must |

**FR-044 is how BR-04 is monitored rather than assumed.** The 70% target degrades silently as the
applicant mix shifts; a daily distribution makes that visible within days instead of at the next
quarterly review.

> **Priority raised from Should to Must by CR-002.** Narrowing BRULE-04 cut BR-04's headroom from
> 8.1 pp to 3.4 pp. FR-044 is the only control that detects the target being breached by a shift in
> applicant mix, and at Should priority it was position 1 on the descope list — the requirement
> protecting BR-04 was the first thing scheduled to be cut under schedule pressure. A monitoring
> requirement should carry the priority of the thing it monitors.
