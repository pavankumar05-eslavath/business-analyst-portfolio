# Non-Functional Requirements

**Project ORIGIN** · Version 1.3 · Baselined
**Approvers:** SH-08 Engineering Manager (performance, availability) · SH-09 IT Security (security,
privacy) · SH-04 Compliance (retention, audit)

---

## Why this document exists separately

"The system should be fast and secure" is not a requirement. It cannot be built to, tested against,
or shown to be met.

Every NFR below states **a metric, a threshold, and the condition under which it is measured.**
Without the condition the threshold is meaningless: "decision in under 3 seconds" is a different
requirement at 5 concurrent users than at 40.

This is the document where most requirements packages are weakest, and it is where an interviewer
who has actually delivered software will look first.

---

## 1. Performance

| ID | Requirement | Threshold | Measured under | Traces to |
|---|---|---|---|---|
| **NFR-01** | Page response time for application capture steps | **P95 < 1.5 s**, P99 < 3.0 s | 40 concurrent sessions, 4G mobile network profile | BR-03 |
| **NFR-02** | Eligibility decision latency, from submission of the final input to decision band assignment | **P95 < 3.0 s** excluding third-party call time; **P95 < 12 s** including bureau and Account Aggregator calls | 40 concurrent applications | BR-01 |
| **NFR-03** | e-KYC round trip | **P95 < 45 s** | 20 concurrent | BR-01 |
| **NFR-04** | Account Aggregator statement retrieval and parsing | **P95 < 120 s** | 20 concurrent | BR-01 |
| **NFR-05** | Disbursal instruction raised after e-NACH success | **< 60 s at P99** | Normal load | BR-01 |

**NFR-02 is split deliberately.** Third-party latency is not controllable by the delivery team, but
it is entirely visible to the applicant. Stating only the combined figure makes the team accountable
for a vendor's performance; stating only the internal figure hides the applicant's actual
experience. Both are needed, and the combined figure is what drives the retry design in US-06.

## 2. Scalability and capacity

| ID | Requirement | Threshold | Traces to |
|---|---|---|---|
| **NFR-06** | Sustained throughput | **80 applications per hour** sustained; **250 per hour** peak for 2 hours without degradation beyond stated P95 targets | BR-01 |
| **NFR-07** | Concurrent underwriter sessions | 25 concurrent without workbench response exceeding P95 2.0 s | BR-07 |

Capacity basis: current volume is 1,537 applications/month, approximately 51/day. The **80/hour**
sustained figure carries roughly **12× headroom** on current daily volume, sized for the festive
season peak (CON-02) plus the expected conversion uplift.

## 3. Availability and reliability

| ID | Requirement | Threshold | Traces to |
|---|---|---|---|
| **NFR-08** | Platform availability during business hours (08:00–22:00 IST) | **99.5%** monthly, equating to a maximum of 42 minutes downtime per month within the window | BR-01 |
| **NFR-09** | Graceful degradation on third-party failure | No applicant-facing error page. Application is held in an explicit pending state with notification, and processing resumes automatically on recovery. | BR-03, BR-06 |
| **NFR-10** | Recovery point objective / recovery time objective | **RPO 15 min · RTO 4 h** | BR-08 |
| **NFR-11** | No application may be lost in a partial failure | Every state transition committed transactionally; zero orphaned applications tolerated | BR-08 |

**NFR-09 is derived from a business requirement, not from an engineering preference.** An error page
during income verification loses the applicant permanently, which directly defeats BR-03. That is
why the fallback in FR-015 and the pending states in US-06 exist.

## 4. Security

| ID | Requirement | Threshold / control | Traces to |
|---|---|---|---|
| **NFR-12** | Data in transit | TLS 1.2 minimum, TLS 1.3 preferred; no plaintext HTTP endpoints | BR-05 |
| **NFR-13** | Data at rest | AES-256 encryption for all personally identifiable and financial data | BR-05 |
| **NFR-14** | Aadhaar handling | Full Aadhaar number never persisted, never logged. Only e-KYC reference ID and masked last-4 retained. | BR-05 |
| **NFR-15** | Authentication for applicant status access | Mobile OTP; session expiry 15 min idle | BR-06 |
| **NFR-16** | Underwriter access control | Role-based; underwriters see only cases in their assigned queue; Credit Head override requires a distinct role | BR-08 |
| **NFR-17** | Audit log integrity | Append-only. Update and delete denied at database privilege level, not only in application code. | BR-08 |
| **NFR-18** | Sensitive data in logs | No PAN, Aadhaar, bank account number, full name or bureau score in application logs at any level | BR-05 |

**NFR-17 specifies enforcement at the database privilege level for a reason.** An append-only log
enforced only in application code is not append-only — any future code path, migration script, or
direct database access bypasses it. This is the difference between a control and an intention.

## 5. Data validation rules

Referenced by FR-004. Stated once here rather than repeated per field.

| Field | Rule | Error message |
|---|---|---|
| Mobile number | Exactly 10 digits, first digit 6–9 | "Enter a valid 10-digit Indian mobile number" |
| PAN | `[A-Z]{5}[0-9]{4}[A-Z]{1}` | "PAN must be 5 letters, 4 digits, then 1 letter" |
| Date of birth | Valid date; age 21–58 inclusive at application date | "Applicant must be between 21 and 58 years old" |
| Monthly net income | Numeric, ₹15,000 – ₹50,00,000 | "Enter your monthly take-home income" |
| Requested amount | Numeric, ₹50,000 – ₹10,00,000, multiples of ₹10,000 | "Amount must be between ₹50,000 and ₹10,00,000 in multiples of ₹10,000" |
| Requested tenure | Integer, 12–60 months | "Tenure must be between 12 and 60 months" |
| Employer name | 2–100 characters, letters, digits, spaces, `& . -` | "Enter your employer's name as it appears on your salary slip" |
| Email | RFC 5322 basic form | "Enter a valid email address" |

**Income lower bound differs between validation and credit policy on purpose.** Field validation
accepts from ₹15,000 while BRULE-02 declines below ₹25,000. The field rule catches typing errors;
the credit rule makes a lending decision. Conflating them would present a credit decline as a form
error, which is both confusing and, for a lending decision, arguably improper.

## 6. Usability and accessibility

| ID | Requirement | Threshold | Traces to |
|---|---|---|---|
| **NFR-19** | Mobile-first responsive layout | Fully usable at 360 px viewport width without horizontal scroll | BR-02 |
| **NFR-20** | Accessibility | WCAG 2.1 Level AA for all applicant-facing screens | BR-02 |
| **NFR-21** | Application completion effort | Median **≤ 9 minutes** from start to submission, excluding third-party wait time | BR-03 |
| **NFR-22** | Error messages | Every validation and decline message states what is wrong and what to do next; no error codes shown to applicants | BR-03, BR-06 |

## 7. Data retention and privacy

| ID | Requirement | Threshold | Traces to |
|---|---|---|---|
| **NFR-23** | Retention of disbursed loan records | 8 years after closure, per statutory requirement | BR-05 |
| **NFR-24** | Retention of declined and withdrawn applications | **24 months**, then purge of personal data with a retained anonymised record for portfolio analysis | BR-05 |
| **NFR-25** | Retention of abandoned incomplete applications | **90 days**, then full purge | BR-05 |
| **NFR-26** | Consent records | Retained for the full life of the relationship plus 8 years, including consent text version | BR-05 |
| **NFR-27** | Data localisation | All storage and processing within India | BR-05 (CON-04) |

**NFR-24 and NFR-25 are the requirements most often missing entirely from a requirements package.**
Under the DPDP Act, keeping personal data indefinitely without a purpose is itself a violation. A
retention schedule is a requirement, not an operations detail, because it determines database design
and purge tooling — both of which must be built, not retrofitted.

## 8. Maintainability

| ID | Requirement | Threshold | Traces to |
|---|---|---|---|
| **NFR-28** | Credit rule changes | A threshold change within an existing rule shall be deployable via configuration without a code release | BR-04 |
| **NFR-29** | Rule versioning | Every rule change increments a version; historical versions retained indefinitely for decision reconstruction | BR-08 |
| **NFR-30** | Observability | Decision-band distribution, third-party latency and error rates emitted as metrics with alerting on the BR-04 target breach | BR-04 |

**NFR-28 is directly justified by risk RSK-01 and by what happened in CR-002.** The CRO narrowed a
FOIR band during requirements review. Credit policy changes regularly, and if every change requires
a code release, the rules engine becomes a bottleneck on risk management rather than an enabler of
it.

---

## Verification approach

An NFR without a verification method is an aspiration. How each will be proven:

| Group | Verification |
|---|---|
| Performance (NFR-01→05) | Load test at stated concurrency in a production-equivalent environment; third-party calls stubbed at measured vendor P95 for the internal-only figures |
| Scalability (NFR-06→07) | Sustained 2-hour soak test at peak rate |
| Availability (NFR-08→11) | Chaos test: each third-party dependency failed in turn; assert pending state and automatic resumption, not an error page |
| Security (NFR-12→18) | Penetration test plus static analysis; log inspection for the NFR-18 prohibited-field list |
| Retention (NFR-23→27) | Purge job dry-run against seeded records at each retention boundary |
| Maintainability (NFR-28→30) | Change a FOIR threshold via configuration in a test environment and confirm no deployment is required |

**DEP-04 is a dependency for this section.** Performance and scalability targets cannot be verified
without production-equivalent infrastructure sizing signed off by IT Infrastructure. If DEP-04 slips
past sprint 2, these NFRs go to go-live unverified — which is a risk the sponsor must accept
explicitly rather than discover later.
