# User Acceptance Test Cases

**Project ORIGIN** · Version 1.4 · Baselined
**Executed by:** SH-05 Operations (accountable) with SH-03 Underwriting and SH-04 Compliance
**Environment:** UAT with production-equivalent integrations in vendor sandbox mode

---

## Test approach

UAT verifies the system meets the **business** requirement, not that the code works — that is
covered by unit and integration tests. So each case below is written from the perspective of the
person who will use it, with data the business recognises.

**Defect severity, agreed before execution so it is not negotiated during it:**

| Severity | Definition | Go-live impact |
|---|---|---|
| **S1 Critical** | A regulatory obligation is breached, money moves incorrectly, or an audit trail is missing | **Blocks go-live** |
| **S2 Major** | A Must requirement fails; no workaround | **Blocks go-live** |
| **S3 Moderate** | A Must requirement fails but a workaround exists, or a Should requirement fails | Go-live with sponsor acceptance and a fix date |
| **S4 Minor** | Cosmetic or wording; no functional impact | Post-go-live backlog |

**Exit criteria:** zero open S1 or S2 defects; all S3 defects have an accepted fix date signed by
SH-01; ≥95% of Must-priority cases passed.

---

## 1. Application capture

| ID | Verifies | Precondition | Steps | Expected result | Pri |
|---|---|---|---|---|---|
| **UAT-01** | FR-001 | No existing application for PAN `ABCDE1234F` | Enter mobile `9876543210` and PAN; submit valid OTP | Application created with status `IN_PROGRESS`; personal details step shown | Must |
| **UAT-02** | FR-002, FR-004 | On the personal details step | Enter DOB making age 19; enter income `9000`; attempt to proceed | Both fields show specific messages; cannot proceed; no partial save of invalid values | Must |
| **UAT-03** | FR-005 | Mobile verified | Select employment type `Salaried` | Full requirement list shown before any data entry; items marked auto-retrieved vs applicant-provided; acknowledgement required | Must |
| **UAT-04** | FR-003 | Application abandoned 3 days ago at employment step | Return; verify same mobile | Resumes at employment step with all prior data present | Must |
| **UAT-05** | FR-003 | Application abandoned 8 days ago | Return; verify same mobile | Prior application marked `EXPIRED`; new application created | Must |
| **UAT-06** | FR-006 | On the loan details step | Enter amount `₹25,000`; then `₹12,00,000`; then tenure `72` | Each rejected stating the permitted range | Must |

## 2. KYC and consent

| ID | Verifies | Precondition | Steps | Expected result | Pri |
|---|---|---|---|---|---|
| **UAT-07** | FR-007, FR-008 | Details submitted | Grant consent; complete Aadhaar OTP | Name, DOB, address populated from e-KYC; consent text version, timestamp and IP recorded and visible in the audit view | Must |
| **UAT-08** | FR-009 | e-KYC name `Rajesh Kumar Sharma`, PAN name `Rajesh K Sharma` | Complete e-KYC | Match score 0.78 → referral reason `NAME_PARTIAL_MATCH`; processing continues | Must |
| **UAT-09** | FR-009 | e-KYC name differs substantially from PAN name | Complete e-KYC | Declined with reason `NAME_MISMATCH`; plain-language explanation shown | Must |
| **UAT-10** | FR-010 | Aadhaar not linked to the application mobile | Attempt e-KYC | Clear failure message; failure reason code recorded; no application data lost | Must |
| **UAT-11** | FR-011 | Application at `OFFER_READY` | Revoke consent | Status becomes `WITHDRAWN`; processing halts; revocation reason and timestamp recorded | Must |
| **UAT-12** | FR-012 | e-KYC completed | Inspect database and application logs for the application | No full Aadhaar number present in any table or log; only e-KYC reference ID and masked last-4 | **Must — S1 if failed** |

## 3. Income verification

| ID | Verifies | Precondition | Steps | Expected result | Pri |
|---|---|---|---|---|---|
| **UAT-13** | FR-013, FR-014 | KYC complete; AA sandbox available | Consent and select bank | 6 months retrieved; avg monthly credit, salary credit, avg balance, returned debits and existing EMIs all derived and displayed | Must |
| **UAT-14** | FR-015 | AA sandbox forced to error | Reach income step | PDF upload offered; uploaded statement parsed; same derived fields produced | Must |
| **UAT-15** | FR-014 | Statement covering 4 months only | Complete retrieval | Referral reason `INSUFFICIENT_STATEMENT_HISTORY` applied | Must |
| **UAT-16** | FR-016 | Declared income ₹80,000; statement shows ₹58,000 | Complete income step | Deviation 27.5% computed; referral reason `INCOME_MISMATCH` applied | Must |

## 4. Decisioning

| ID | Verifies | Precondition | Steps | Expected result | Pri |
|---|---|---|---|---|---|
| **UAT-17** | FR-017 | Income assessed | Trigger decisioning | Bureau report retrieved using PAN; retrieval recorded | Must |
| **UAT-18** | FR-018 | Bureau report for this PAN retrieved 20 h ago | Trigger decisioning | Cached report reused; no new bureau request issued; retrieval timestamp shown in audit | Should |
| **UAT-19** | FR-019, FR-020 | Income ₹80,000; existing EMI ₹12,000; requested ₹4,00,000 over 48 months | Trigger decisioning | EMI computed on reducing balance; FOIR computed to 4 dp; both values visible in the rule evaluation record | Must |
| **UAT-20** | FR-021 | Bureau 780; FOIR 0.38; no adverse history | Trigger decisioning | Band `AUTO_APPROVE`; offer generated; applicant notified within 2 min | Must |
| **UAT-21** | FR-021 | Bureau 720; FOIR 0.58 | Trigger decisioning | Band `AUTO_DECLINE`; reason `FOIR_EXCEEDED`; applicant sees plain-language reason and reapplication guidance | Must |
| **UAT-22** | FR-021, FR-022 | Bureau 668 | Trigger decisioning | Band `REFER`; reason `SCORE_MARGINAL`; case appears in underwriter queue with the triggering rule identifier | Must |
| **UAT-23** | FR-021 | BRULE-03 returns `REFER`; BRULE-05 returns `AUTO_DECLINE` | Trigger decisioning | Final band `AUTO_DECLINE`; **both** rule outcomes present in the audit trail | **Must — precedence** |
| **UAT-24** | FR-021 | No bureau record exists for the PAN | Trigger decisioning | Band `REFER`; reason `NTC_APPLICANT` | Must |
| **UAT-25** | FR-023 | Decision made | Inspect the system of record | Decision present against the application with no manual entry step in the process; no intermediate spreadsheet exists | Must |
| **UAT-26** | FR-024 | Decision made | Open the decision reconstruction | Every rule evaluated is listed with rule version, input values used, individual outcome, and final band | **Must — S1 if failed** |

## 5. Offer and disbursal

| ID | Verifies | Precondition | Steps | Expected result | Pri |
|---|---|---|---|---|---|
| **UAT-27** | FR-025, FR-026 | Application approved | View offer | Amount, rate, tenure, EMI, processing fee, APR and total repayable all shown; Key Fact Statement presented; acknowledgement required before acceptance | Must |
| **UAT-28** | FR-027 | Offered ₹5,00,000 over 60 months at FOIR 0.44 | Select ₹5,00,000 over 12 months | Recalculated FOIR 0.71 exceeds band; change rejected with explanation; original offer remains available | Should |
| **UAT-29** | FR-028 | Offer generated 7 days and 1 hour ago | Attempt acceptance | Offer expired; new application offered. Separately confirm a reminder was sent 24 h before expiry | Must |
| **UAT-30** | FR-029, FR-030, FR-031 | Offer accepted | Complete e-Sign with Aadhaar OTP; e-NACH registers | Disbursal instruction raised to LMS within 1 minute, not held for a batch window | Must |
| **UAT-31** | FR-030 | e-Sign complete; e-NACH forced to fail | Observe | Status `MANDATE_FAILED`; **no disbursal instruction raised**; applicant prompted for a different account | **Must — S1 if disbursal proceeds** |
| **UAT-32** | FR-032 | Disbursal complete | Check notifications | Applicant notified with amount credited, first EMI date and repayment schedule | Must |

## 6. Underwriter workbench

| ID | Verifies | Precondition | Steps | Expected result | Pri |
|---|---|---|---|---|---|
| **UAT-33** | FR-033 | Case referred with reason `INCOME_MISMATCH` | Open the case | Applicant details, derived income, bureau summary, all rule outcomes and referral reason visible in one view; no other system needed | Must |
| **UAT-34** | FR-034 | Reviewing a referred case | Select `APPROVE` with a 12-character rationale | Rejected requiring ≥20 characters; decision not saved | Must |
| **UAT-35** | FR-034, FR-037 | Reviewing a referred case | Select `APPROVE_WITH_CHANGES`, reduce amount, enter valid rationale | Revised offer generated; underwriter identity, decision, rationale and timestamp recorded | Must |
| **UAT-36** | FR-035 | Case triggered BRULE-05 `WRITEOFF_SETTLED` | Attempt `APPROVE` as an underwriter | Blocked with a message requiring Credit Head approval; decision not saved | **Must — S1 if override succeeds** |
| **UAT-37** | FR-035 | Override requested on a hard-declined case | Credit Head approves with rationale | Override recorded with both identities in the audit trail | Must |
| **UAT-38** | FR-036 | Three referred cases aged 6 h, 2 h, 4 h | View queue | Ordered 6 h, 4 h, 2 h; cases over 4 h show an ageing indicator | Should |

## 7. Status, notifications and audit

| ID | Verifies | Precondition | Steps | Expected result | Pri |
|---|---|---|---|---|---|
| **UAT-39** | FR-038, FR-039 | Application in progress | Open status link and authenticate by OTP | Current stage and next step shown. Then confirm SMS and email received within 5 min of reaching `OFFER_READY` | Must |
| **UAT-40** | FR-038 | Application in progress | Open status link **without** completing OTP | Authentication prompt shown; no application information disclosed | **Must — S1 if data leaks** |
| **UAT-41** | FR-040 | Application declined with `FOIR_EXCEEDED` | View status | Plain-language reason and reapplication guidance shown; **no** internal rule identifiers or bureau score displayed | Must |
| **UAT-42** | FR-041 | Application in progress | Log in as Customer Service | Read-only status and history visible; no ability to edit or decide | Should |
| **UAT-43** | FR-042 | Audit entry exists | Attempt to update and then delete the entry via application and via direct database access | Both rejected; the attempt itself is logged | **Must — S1 if mutable** |
| **UAT-44** | FR-043 | Application decided under BRULE-04 v1.1; BRULE-04 now v1.2 | Request reconstruction | Outcome shown against **v1.1** with the version stated, not re-evaluated under v1.2 | **Must — S1 if version drifts** |
| **UAT-45** | FR-044 | Decisions made yesterday | Open the daily report | Counts and percentages by band; REFER broken down by reason; breach against the 70% target highlighted if applicable | Should |

## 8. Non-functional verification

Not conventional UAT cases, but recorded here because they are exit-criteria gates.

| ID | Verifies | Method | Threshold | Pri |
|---|---|---|---|---|
| **UAT-46** | NFR-01, NFR-02 | Load test at 40 concurrent applications | Capture P95 < 1.5 s; decision P95 < 3.0 s internal, < 12 s including third parties | Must |
| **UAT-47** | NFR-06 | 2-hour soak at 250 applications/hour | No degradation beyond stated P95 targets | Must |
| **UAT-48** | NFR-09 | Chaos test: fail bureau, then AA, then e-Sign in turn | Pending state and notification in every case; **no error page**; automatic resumption on recovery | Must |
| **UAT-49** | NFR-18 | Log inspection across all levels during a full journey | No PAN, Aadhaar, account number, full name or bureau score present in any log | **Must — S1 if present** |
| **UAT-50** | NFR-24, NFR-25 | Purge job dry-run against records seeded at each retention boundary | Declined purged at 24 months, abandoned at 90 days; anonymised record retained for declined | Must |
| **UAT-51** | NFR-28 | Change the BRULE-04 FOIR threshold via configuration | Takes effect without a code deployment; new rule version created | Should |

## 9. Regulatory disclosures — added by CR-003

| ID | Verifies | Setup | Expected result | Priority |
|---|---|---|---|---|
| **UAT-52** | FR-045, FR-047 | Reach an offer ready to sign and open the Key Fact Statement | Cooling-off duration of 3 calendar days, the exit basis (principal + proportionate APR), an explicit statement that no penalty applies, the method of exercising it, and the nodal grievance officer details with the RBI portal escalation route are all present before e-Sign is offered | **Must — S1 if absent** |
| **UAT-53** | FR-046 | Disburse a loan at a known timestamp, then inspect the loan record and the disbursal instruction sent to the LMS | `cooling_off_expires_at` = disbursal + 3 calendar days on both the loan record and the LMS instruction payload; value is retrievable in a FR-043 decision reconstruction 8 months later | **Must — S1 if incorrect** |

**UAT-53 tests a handoff, which is the case most likely to be skipped.** It is tempting to test that
ORIGIN stores the expiry and stop there. The obligation is only met if the LMS *receives* it, so the
assertion is on the outbound payload, not on ORIGIN's database.

**What these cases do not verify: DEP-05.** No UAT case here proves the LMS enforces a penalty-free
exit, because that behaviour lives in a system outside this scope. That verification is a
**pilot-gate condition** owned by SH-08, and it is the reason DEP-05 is recorded as an open
dependency rather than an assumption. UAT passing in full is *not* sufficient to declare CR-003
compliant.

---

## Coverage summary

| Requirement group | Requirements | UAT cases | Coverage |
|---|---|---|---|
| Functional (FR-001 → FR-044) | 44 | UAT-01 → UAT-45 | 44/44 |
| Functional (FR-045 → FR-047, CR-003) | 3 | UAT-52 → UAT-53 | 3/3 |
| Non-functional (selected gates) | 8 of 30 | UAT-46 → UAT-51 | Gated NFRs only |

**Eleven cases are marked S1-if-failed.** Every one of them is either a regulatory obligation
(UAT-12, UAT-49, **UAT-52**, **UAT-53**), an audit-trail guarantee (UAT-26, UAT-43, UAT-44), a
money-movement control (UAT-31), a credit-policy control (UAT-36), or a data-disclosure control
(UAT-40). These are the cases where a workaround does not exist and go-live cannot proceed.

**Not every NFR has a UAT case, and that is deliberate.** The 20 NFRs without one are verified
through code review, penetration testing or architecture sign-off rather than through business
acceptance testing. Listing all 30 here would imply Operations can meaningfully accept a TLS
version, which they cannot.
