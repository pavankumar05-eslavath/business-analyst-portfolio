# User Stories with Acceptance Criteria

**Project ORIGIN** · Version 1.5 · Baselined

Acceptance criteria are written in Gherkin, and **negative and edge cases are included**. A story
with only a happy path is not a specification — it is a wish. The edge cases below are where the
defects actually live.

---

## Epic 1 — Digital application capture

### US-01 · Start an application without visiting a branch
**As a** salaried applicant
**I want to** start a loan application from my phone
**So that** I do not have to travel to a branch
*Traces to: FR-001, FR-002, FR-004, FR-006 · Points: 5 · Priority: Must*

```gherkin
Scenario: Successful application start
  Given I am on the application landing page
  When I enter a valid 10-digit mobile number and a valid PAN
  And I submit the OTP sent to that mobile number
  Then an application is created with status "IN_PROGRESS"
  And I am taken to the personal details step

Scenario: Invalid PAN format is rejected before OTP is sent
  Given I am on the application landing page
  When I enter PAN "ABCD1234E"
  Then I see "PAN must be 5 letters, 4 digits, then 1 letter"
  And no OTP is sent

Scenario: OTP expires
  Given I requested an OTP more than 10 minutes ago
  When I submit that OTP
  Then I see "This OTP has expired. Request a new one."
  And no application is created

Scenario: Third consecutive incorrect OTP locks the attempt
  Given I have entered an incorrect OTP twice
  When I enter an incorrect OTP a third time
  Then I see "Too many incorrect attempts. Try again in 30 minutes."
  And the mobile number is blocked from new OTP requests for 30 minutes

Scenario: An application already exists for this PAN
  Given an application with status "IN_PROGRESS" exists for PAN "ABCDE1234F"
  When I start an application with the same PAN and the same mobile number
  Then I resume the existing application
  And no duplicate application is created

Scenario: Requested amount outside the product range is rejected at capture
  Given I am entering my loan requirement
  When I request ₹12,00,000 over 60 months
  Then I see "Amount must be between ₹50,000 and ₹10,00,000"
  And the application does not advance to KYC

Scenario: Requested tenure outside the product range is rejected at capture
  When I request ₹3,00,000 over 72 months
  Then I see "Tenure must be between 12 and 60 months"
  And the application does not advance to KYC
```

> **The last two scenarios were added after the traceability validator flagged a gap.** The matrix
> claimed US-01 covered FR-006 (product range rejection) and a UAT case existed for it, but the story
> had no acceptance criterion — so a developer building from this story would have shipped without the
> range check, and it would have been caught at UAT rather than in development. See
> [09-traceability-matrix.md](09-traceability-matrix.md) GAP-03.

### US-02 · Know what is needed before I start
**As an** applicant
**I want to** see the full list of required information up front
**So that** I do not abandon the application halfway
*Traces to: FR-005 · Points: 2 · Priority: Must*

```gherkin
Scenario: Requirements shown before data entry
  Given I have verified my mobile number
  When I select employment type "Salaried"
  Then I see the complete list of information required for a salaried applicant
  And I see which items can be retrieved automatically versus which I must provide
  And I must acknowledge the list before proceeding

Scenario: Requirement list changes with employment type
  Given I am viewing the requirement list for "Salaried"
  When I change employment type to "Salaried - contractual"
  Then the requirement list updates to include the contract document
```

### US-03 · Resume an interrupted application
**As an** applicant whose session was interrupted
**I want to** continue where I left off
**So that** I do not re-enter everything
*Traces to: FR-003 · Points: 3 · Priority: Must*

```gherkin
Scenario: Resume within the retention window
  Given I abandoned an application 3 days ago at the employment details step
  When I return and verify the same mobile number
  Then I resume at the employment details step
  And all previously entered data is present

Scenario: Application expires after 7 days
  Given I abandoned an application 8 days ago
  When I return and verify the same mobile number
  Then the previous application is marked "EXPIRED"
  And a new application is created

Scenario: Resume boundary at exactly 7 days
  Given I abandoned an application exactly 7 days and 0 hours ago
  When I return and verify the same mobile number
  Then I resume the existing application
```

*The boundary scenario exists because "within 7 days" is ambiguous at the boundary, and ambiguity at
a boundary is where a defect gets written.*

---

## Epic 2 — Identity and income verification

### US-04 · Complete KYC digitally
**As an** applicant
**I want to** complete KYC using Aadhaar OTP
**So that** I avoid a branch visit and document photocopies
*Traces to: FR-007, FR-008, FR-009, FR-010, FR-011, FR-012 · Points: 8 · Priority: Must*

```gherkin
Scenario: Successful e-KYC
  Given I have entered my personal details
  When I consent to e-KYC and authenticate with the Aadhaar OTP
  Then my name, date of birth and address are populated from the e-KYC response
  And consent text version, timestamp and IP address are recorded
  And the application advances to income verification

Scenario: Name mismatch between Aadhaar and PAN triggers referral
  Given e-KYC returns name "Rajesh Kumar Sharma"
  And the PAN record shows name "Rajesh K Sharma"
  When the name match score is calculated as 0.78
  Then the application is flagged with referral reason "NAME_PARTIAL_MATCH"
  And processing continues to income verification

Scenario: Name mismatch below tolerance is declined
  Given the name match score is calculated as 0.55
  Then the application is declined with reason "NAME_MISMATCH"
  And I see a plain-language explanation

Scenario: Aadhaar not linked to the application mobile number
  Given my Aadhaar is linked to a different mobile number
  When I attempt e-KYC
  Then I see "Your Aadhaar is not linked to this mobile number"
  And I am offered the alternative verification route

Scenario: I withdraw consent before disbursal
  Given my application has status "OFFER_READY"
  When I revoke my consent
  Then the application status becomes "WITHDRAWN"
  And no further processing occurs
  And the withdrawal reason and timestamp are recorded

Scenario: e-KYC failure rejects the application with a stated reason
  Given the e-KYC service returns a biometric or demographic mismatch
  When I attempt e-KYC
  Then my application is rejected
  And I see a plain-language reason rather than a service error code
  And the failure reason code returned by the e-KYC service is recorded

Scenario: My Aadhaar number is never stored
  Given my e-KYC completed successfully
  When the application record and all audit entries are inspected
  Then no full Aadhaar number is present anywhere
  And only the e-KYC reference identifier and the masked last-4 digits are retained
```

> **The last two scenarios were added after the validator flagged a gap** — FR-010 and FR-012 were
> traced to this story in the matrix and had UAT cases, but no acceptance criterion. FR-012 is the more
> serious of the two: storing a full Aadhaar number is a regulatory breach, and the only thing standing
> between the requirement and a developer's data model was a UAT case that would have run weeks later.
> See [09-traceability-matrix.md](09-traceability-matrix.md) GAP-03.

### US-05 · Share bank statements without uploading files
**As an** applicant
**I want** my bank statement retrieved automatically
**So that** I do not have to find and upload PDFs
*Traces to: FR-013, FR-014, FR-015, FR-016 · Points: 8 · Priority: Must*

```gherkin
Scenario: Successful Account Aggregator retrieval
  Given I have completed KYC
  When I consent and select my bank through the Account Aggregator
  Then 6 months of statement data is retrieved
  And average monthly credit, salary credits, average balance, returned debits and existing EMIs are derived
  And the application advances to decisioning

Scenario: Account Aggregator unavailable falls back to upload
  Given the Account Aggregator service returns an error
  When I reach the income verification step
  Then I am offered PDF bank statement upload
  And the same derived fields are produced from the uploaded statement

Scenario: Statement covers less than 6 months
  Given the retrieved statement covers only 4 months
  Then the application is flagged with referral reason "INSUFFICIENT_STATEMENT_HISTORY"

Scenario: Derived income differs materially from declared income
  Given I declared monthly income of ₹80,000
  And the derived monthly income is ₹58,000
  When the deviation is calculated as 27.5%
  Then the application is flagged with referral reason "INCOME_MISMATCH"
```

---

## Epic 3 — Decisioning

### US-06 · Receive an immediate decision
**As an** applicant
**I want** a decision within minutes
**So that** I know where I stand without waiting days
*Traces to: FR-017, FR-019, FR-020, FR-021, FR-022, FR-023 · Points: 13 · Priority: Must*

```gherkin
Scenario: Auto-approved
  Given my bureau score is 780
  And my calculated FOIR is 0.38
  And no adverse credit history exists
  When decisioning runs
  Then my decision band is "AUTO_APPROVE"
  And an offer is generated
  And I am notified within 2 minutes of submission

Scenario: Auto-declined for FOIR
  Given my bureau score is 720
  And my calculated FOIR is 0.58
  When decisioning runs
  Then my decision band is "AUTO_DECLINE"
  And the reason code is "FOIR_EXCEEDED"
  And I see a plain-language reason and reapplication guidance

Scenario: Referred to an underwriter
  Given my bureau score is 668
  When decisioning runs
  Then my decision band is "REFER"
  And the referral reason "SCORE_MARGINAL" is attached
  And the case enters the underwriter queue

Scenario: Decline overrides referral
  Given BRULE-03 returns "REFER" for a marginal score
  And BRULE-05 returns "AUTO_DECLINE" for a write-off in the last 36 months
  When decisioning runs
  Then my decision band is "AUTO_DECLINE"
  And both rule outcomes are recorded in the audit trail

Scenario: New-to-credit applicant with no bureau record
  Given no credit bureau record exists for my PAN
  When decisioning runs
  Then my decision band is "REFER"
  And the referral reason is "NTC_APPLICANT"

Scenario: Bureau service is unavailable
  Given the credit bureau API is not responding
  When decisioning is attempted
  Then the application status becomes "PENDING_BUREAU"
  And I am notified that a decision is in progress
  And retrieval is retried automatically every 15 minutes for up to 4 hours

Scenario: EMI is calculated on a reducing balance, not a flat rate
  Given I request ₹5,00,000 over 36 months at 14% per annum
  When the proposed EMI is calculated
  Then the EMI is ₹17,088.81 using reducing-balance amortisation
  And the same EMI value is used as the numerator input to the FOIR calculation
```

*The precedence scenario and the outage scenario are the two most valuable in this file. Both
describe situations that will certainly occur and that prose requirements routinely leave undefined.*

> **The EMI scenario was added after the validator flagged a gap.** FR-020 specifies reducing-balance
> amortisation and was traced to this story, but no acceptance criterion pinned the method. A flat-rate
> EMI on the same inputs is **₹19,722.22 against ₹17,088.81 — 15.4% higher** — which inflates FOIR by the
> same 15.4% and pushes applicants into worse decision bands. On BRULE-04 that is enough to move a
> borderline applicant from `AUTO_APPROVE` to `REFER`, or from `REFER` to `AUTO_DECLINE`. An unstated
> calculation method in a story that drives credit decisions is the most expensive kind of omission in
> this document. See
> [09-traceability-matrix.md](09-traceability-matrix.md) GAP-03.

### US-07 · Reuse a recent bureau report
**As the** business
**I want** bureau reports reused within 72 hours
**So that** we do not pay twice for the same data
*Traces to: FR-018 · Points: 3 · Priority: Should*

```gherkin
Scenario: Cached report is reused
  Given a bureau report was retrieved for my PAN 20 hours ago
  When decisioning runs
  Then the cached report is used
  And no new bureau request is issued
  And the audit trail records the report retrieval timestamp

Scenario: Stale report triggers a fresh pull
  Given a bureau report was retrieved for my PAN 80 hours ago
  When decisioning runs
  Then a new bureau request is issued
```

---

## Epic 4 — Offer and disbursal

### US-08 · Understand the offer before accepting
**As an** applicant
**I want** all costs stated clearly
**So that** I can decide with full information
*Traces to: FR-025, FR-026, FR-028 · Points: 5 · Priority: Must*

```gherkin
Scenario: Offer displays all mandatory terms
  Given my application is approved
  When I view my offer
  Then I see approved amount, interest rate, tenure, EMI, processing fee, APR and total repayable
  And I see the Key Fact Statement
  And I must acknowledge the Key Fact Statement before I can accept

Scenario: Offer expires
  Given my offer was generated 7 days and 1 hour ago
  When I attempt to accept it
  Then I see "This offer has expired"
  And I am offered the option to submit a new application

Scenario: I am warned before expiry
  Given my offer expires in 24 hours
  Then I receive an SMS and email reminder
```

### US-09 · Accept a smaller loan than offered
**As an** applicant
**I want to** accept a lower amount or different tenure
**So that** the EMI fits my budget
*Traces to: FR-027 · Points: 5 · Priority: Should*

```gherkin
Scenario: Lower amount is recalculated and re-checked
  Given I am offered ₹5,00,000 over 48 months
  When I select ₹3,00,000 over 48 months
  Then the EMI is recalculated
  And BRULE-04 is re-evaluated on the revised FOIR
  And the revised offer is presented

Scenario: A shorter tenure raises FOIR beyond the permitted band
  Given I am offered ₹5,00,000 over 60 months at FOIR 0.44
  When I select ₹5,00,000 over 12 months
  And the recalculated FOIR is 0.71
  Then I see "This tenure results in an EMI above your permitted limit"
  And the original offer remains available
```

*The second scenario is the one that catches a real credit defect: treating "the applicant asked for
less" as automatically safe. A shorter tenure increases the EMI and can push FOIR out of band.*

### US-10 · Complete signing digitally
**As an** applicant
**I want to** sign the agreement online
**So that** I avoid a second branch visit
*Traces to: FR-029, FR-030, FR-031, FR-032 · Points: 8 · Priority: Must*

```gherkin
Scenario: e-Sign and e-NACH complete, disbursal is instructed immediately
  Given I have accepted my offer
  When I complete e-Sign with Aadhaar OTP
  And the e-NACH mandate is registered successfully
  Then a disbursal instruction is raised to the LMS within 1 minute
  And I am notified of the amount and first EMI date

Scenario: e-NACH registration fails
  Given I have completed e-Sign
  When e-NACH registration fails
  Then the application status becomes "MANDATE_FAILED"
  And no disbursal instruction is raised
  And I am prompted to select a different bank account

Scenario: e-Sign abandoned midway
  Given I opened the e-Sign flow and did not complete it
  When 24 hours pass
  Then I receive a reminder notification
  And my offer remains valid until its original expiry
```

---

## Epic 5 — Underwriter workbench

### US-11 · Assess a referred case in one place
**As an** underwriter
**I want** all case information in a single view
**So that** I do not rebuild the assessment in a spreadsheet
*Traces to: FR-033, FR-034, FR-037 · Points: 13 · Priority: Must*

```gherkin
Scenario: Complete case context is presented
  Given a case is referred to me
  When I open it
  Then I see applicant details, derived income figures, bureau summary, every rule outcome, and the referral reason
  And I do not need to open any other system

Scenario: Decision requires a rationale
  Given I am reviewing a referred case
  When I select "APPROVE" and enter a rationale of 12 characters
  Then I see "Rationale must be at least 20 characters"
  And the decision is not saved

Scenario: Approve with a revised amount
  Given a case referred with reason "INCOME_MISMATCH"
  When I select "APPROVE_WITH_CHANGES" and reduce the amount to ₹2,00,000
  And I enter a rationale of at least 20 characters
  Then the revised offer is generated
  And my identity, decision, rationale and timestamp are recorded
```

### US-12 · Prevent unilateral override of a hard decline
**As the** Chief Risk Officer
**I want** auto-declines to require dual approval to overturn
**So that** credit policy is binding rather than advisory
*Traces to: FR-035 · Points: 5 · Priority: Must*

```gherkin
Scenario: Underwriter cannot approve a hard-declined case alone
  Given a case triggered BRULE-05 "WRITEOFF_SETTLED"
  When I attempt to record "APPROVE"
  Then I see "This case triggered an automatic decline and requires Credit Head approval"
  And the decision is not saved

Scenario: Credit Head second approval is recorded
  Given an underwriter has requested override on a hard-declined case
  When the Credit Head approves the override with a rationale
  Then the approval is recorded with both identities
  And the audit trail shows the override and both approvers
```

### US-13 · Work the oldest cases first
**As an** underwriter
**I want** the queue ordered by application age
**So that** no applicant is left waiting
*Traces to: FR-036 · Points: 3 · Priority: Should*

```gherkin
Scenario: Queue is ordered oldest first
  Given three referred cases submitted 6, 2 and 4 hours ago
  When I view my queue
  Then they appear in the order 6 hours, 4 hours, 2 hours

Scenario: Ageing cases are flagged
  Given a referred case was submitted 5 hours ago
  When I view my queue
  Then that case shows an ageing indicator
```

---

## Epic 6 — Status visibility

### US-14 · Check my application status myself
**As an** applicant
**I want to** see my status without calling support
**So that** I am not left guessing
*Traces to: FR-038, FR-039 · Points: 5 · Priority: Must*

```gherkin
Scenario: Status is visible after OTP authentication
  Given I have an application in progress
  When I open my status link and authenticate with mobile OTP
  Then I see the current stage and what happens next

Scenario: Status link cannot be accessed without authentication
  Given I have an application in progress
  When I open the status link without completing OTP
  Then I see the authentication prompt
  And no application information is shown

Scenario: Notifications are sent at each milestone
  Given my application progresses to "OFFER_READY"
  Then I receive an SMS and an email within 5 minutes
```

### US-15 · Understand why I was declined
**As a** declined applicant
**I want** a clear reason and reapplication guidance
**So that** I know what to do next
*Traces to: FR-040 · Points: 3 · Priority: Must*

```gherkin
Scenario: Plain-language decline reason
  Given my application was declined with reason code "FOIR_EXCEEDED"
  When I view my status
  Then I see "Your existing loan commitments are high relative to your income"
  And I see when I may reapply
  And I do not see internal rule identifiers or bureau scores
```

*The last line is deliberate. A decline reason must be honest and comprehensible without disclosing
the internal decisioning model or third-party bureau data the applicant should obtain from the
bureau directly.*

---

## Epic 7 — Audit and compliance

### US-16 · Reconstruct any past decision
**As a** compliance officer
**I want to** see exactly how a decision was reached
**So that** I can answer a regulatory query
*Traces to: FR-024, FR-043 · Points: 8 · Priority: Must*

```gherkin
Scenario: Full decision reconstruction
  Given an application was decided 4 months ago
  When I request the decision reconstruction
  Then I see every rule evaluated, its version at that time, the input values used, each outcome, and the final band

Scenario: Reconstruction reflects the rule version in force at the time
  Given BRULE-04 was version 1.1 when the application was decided
  And BRULE-04 is now version 1.2
  When I request the reconstruction
  Then the outcome is shown against version 1.1
  And the report states the rule version used
```

*The second scenario is the entire point of FR-024. Rules change; reconstructing an old decision
against today's rules would produce a different answer and would be worthless as evidence.*

### US-17 · Audit trail cannot be altered
**As a** compliance officer
**I want** the audit log to be append-only
**So that** it is trustworthy
*Traces to: FR-042 · Points: 5 · Priority: Must*

```gherkin
Scenario: Audit entries cannot be modified
  Given an audit entry exists for a state transition
  When any user or process attempts to update or delete it
  Then the attempt is rejected
  And the attempt itself is logged

Scenario: Every state transition is captured
  Given an application moves from "OFFER_READY" to "ACCEPTED"
  Then an audit entry records actor, timestamp, previous state and new state
```

### US-18 · Monitor the automation rate
**As the** Head of Retail Lending
**I want** a daily decision-band distribution
**So that** I know if the 70% automation target is holding
*Traces to: FR-044 · Points: 3 · Priority: Must (raised from Should by CR-002)*

```gherkin
Scenario: Daily distribution report
  Given decisions were made yesterday
  When I open the daily report
  Then I see counts and percentages for AUTO_APPROVE, REFER and AUTO_DECLINE
  And REFER cases are broken down by referral reason

Scenario: Automation rate falls below target
  Given yesterday's AUTO_APPROVE plus AUTO_DECLINE share was 64%
  Then the report highlights the breach against the 70% target
```

### US-19 · Know my right to cancel, and who to complain to
**As a** loan applicant
**I want** to be told before I sign that I can exit the loan within a short window, and how to raise a complaint
**So that** I am not committed to a decision I cannot reverse
*Traces to: FR-045, FR-046, FR-047 · Points: 5 · Priority: Must (added by CR-003)*

```gherkin
Scenario: Cooling-off right is disclosed before signing
  Given I have an offer ready to sign
  When I open the Key Fact Statement
  Then I see that I may exit within 3 calendar days of disbursal
  And I see that I would pay only principal plus proportionate APR
  And I see that no penalty or exit charge applies
  And I see how to exercise the right

Scenario: Grievance route is disclosed
  Given I am viewing the Key Fact Statement or my application status page
  Then I see the nodal grievance officer's name, designation, phone, email and postal address
  And I see the escalation route to the RBI complaint portal

Scenario: Cooling-off deadline is handed to the servicing platform
  Given my loan is disbursed at 2026-03-10 14:20 IST
  Then "cooling_off_expires_at" is recorded as 2026-03-13 14:20 IST
  And the disbursal instruction sent to the LMS carries that value

Scenario: Signing is blocked if the disclosure was not presented
  Given the Key Fact Statement failed to render the cooling-off disclosure
  When I attempt to e-Sign
  Then the attempt is rejected
  And the failure is logged as a compliance-blocking event

Scenario: Disclosed terms are reproducible after the fact
  Given a loan was disbursed 8 months ago
  When compliance reconstructs the application under FR-043
  Then the exact cooling-off text and APR shown to me at signing are retrievable
```

**The last two scenarios are why this story is 5 points and not 2.** Displaying text is trivial;
*proving* that the text was displayed, and reproducing what it said months later, is the part a
compliance auditor actually tests. A story that stopped at "applicant sees the disclosure" would have
been accepted at UAT and failed the first audit.

---

## Story summary

| Epic | Stories | Points |
|---|---|---|
| 1 · Application capture | US-01 → US-03 | 10 |
| 2 · Identity and income | US-04 → US-05 | 16 |
| 3 · Decisioning | US-06 → US-07 | 16 |
| 4 · Offer and disbursal | US-08 → US-10 | 18 |
| 5 · Underwriter workbench | US-11 → US-13 | 21 |
| 6 · Status visibility | US-14 → US-15 | 8 |
| 7 · Audit and compliance | US-16 → US-19 | 21 |
| **Total** | **19 stories** | **110 points** |

At an observed team velocity of 38 points per 2-week sprint, 110 points is **2.9 sprints** against a
3-sprint constraint (CON-02) — feasible only if the Should items are genuinely allowed to slip. The
5 points came from CR-003 and consumed most of the remaining buffer. See
[10-release-plan.md](10-release-plan.md).
