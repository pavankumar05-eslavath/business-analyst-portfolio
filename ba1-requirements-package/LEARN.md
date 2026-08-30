# LEARN · BA-1 Requirements Package

How the twelve artefacts fit together, why each one exists, and the interview questions this package
invites. Read this after skimming the documents themselves.

---

## 1. The chain, and why order matters

A requirements package is not twelve documents. It is **one argument, told in twelve parts**, and each
part is only defensible because of the one before it.

```
Stakeholders (01)   who decides, who is affected, and how you elicited from each
        ↓
Process models (02) what happens today, measured -- and where the cost sits
        ↓
BRD (03)            what the business needs, with success criteria and a business case
        ↓
FRD (04)            what the system must do, plus business rules as decision tables
        ↓
Stories (05)        how each requirement will be accepted, in the developer's language
NFRs (06)           the qualities, with numbers and measurement conditions
Data model (07)     the entities the requirements imply
        ↓
UAT (08)            how the business confirms it works
        ↓
RTM (09)            proof that the chain is unbroken
        ↓
Release plan (10)   what ships first, and what gets cut when it slips
        ↓
Change log (11)     what happened when reality arrived
```

**The direction of the arrows is the discipline.** You cannot write a functional requirement without a
business requirement to trace it to, and you cannot write a business requirement without a measurement
that proves the problem exists. Every FR in this package traces upward to a BR; every BR traces to a
number in the AS-IS analysis. When someone asks "why does the system need FR-035?", the answer is a
chain, not an opinion.

### The single most common failure this structure prevents

Starting at 04. Most requirements documents begin as a feature list because that is the fun part.
Then, when the sponsor asks whether the project is worth doing, the business case is reverse-engineered
from the features — which produces benefits that were chosen to justify decisions already made.

Here the business case in 03 is built from the pain points in 02, which are measured: 9 quantified
pain points totalling **2,690 hours/month ≈ 16 FTE**. The ₹5,16,84,000 annual benefit is what removing
those costs is worth. The features come after.

---

## 2. What each artefact is actually for

Not what the textbook says — what it does that nothing else does.

| Artefact | Its unique job | The failure it prevents |
|---|---|---|
| **Stakeholder register + RACI** | Establishes **who can say no** | Building for six weeks, then discovering the CRO holds a veto nobody consulted |
| **Elicitation plan** | States *method per stakeholder, with a reason* | Interviewing everyone identically and missing what only shadowing reveals |
| **AS-IS model** | Quantifies the current cost | A business case built on adjectives |
| **TO-BE model + gap analysis** | Shows what changes and what deliberately does not | Redesigning things that were never broken |
| **BRD** | Ties every objective to a measurement and an owner | "Improve customer experience" as a requirement |
| **FRD** | Specifies behaviour precisely enough to build | Ambiguity resolved by whoever writes the code |
| **Decision tables** | Forces **every combination** to be resolved | Rules that are individually correct and collectively contradictory |
| **Rule precedence** | Defines what wins when two rules fire | The most expensive undefined case in any rules engine |
| **User stories** | Convert requirements into acceptance criteria | A requirement that is "done" by someone else's definition |
| **NFRs** | Make quality testable | "The system should be fast" |
| **Data model** | Exposes entities the prose implied but never named | Discovering in sprint 3 that rule versions were never stored |
| **UAT cases** | Let the business accept or reject on evidence | Sign-off by demo |
| **RTM** | Proves nothing was dropped between layers | A requirement that exists in the FRD and nowhere else |
| **Release plan** | Decides the descope order **before** it is needed | Cuts made under pressure by whoever is closest to the code |
| **Change log** | Makes change cost something visible | Absorbed scope creep with no decision to point at |

### The two artefacts most candidates skip, and shouldn't

**Rule precedence (04 §4.2).** Eight decision tables can all fire on one application. BRULE-03 might
return `REFER` while BRULE-05 returns `AUTO_DECLINE`. Without a stated precedence — `AUTO_DECLINE` >
`REFER` > `AUTO_APPROVE` — the outcome depends on evaluation order, which is an implementation
accident. This is three lines of document that prevent a class of production defect, and it is almost
always missing.

**Descope order agreed in advance (10).** Everyone writes MoSCoW. Almost nobody writes down, before
the sprint starts, *which* Should items get dropped in *which* order and what consequence is accepted
for each. The value is entirely in the timing: the same decision made under schedule pressure is made
badly, by the wrong person, without the sponsor.

---

## 3. The three findings that carry this project

If you remember three things, remember these.

### 3.1 A traceability matrix can be 100% complete and completely hollow

Rule 3 of the validator asserts every Must requirement traces to at least one user story. Four Must
requirements passed that check while having **no acceptance criterion at all** — the story existed,
was named in the matrix, was allocated to a sprint, and said nothing about the requirement it was
credited with delivering.

| Requirement | What was missing | Consequence if shipped |
|---|---|---|
| FR-020 reducing-balance EMI | No scenario pinning the calculation method | Flat-rate EMI on ₹5,00,000 / 36mo / 14% is **₹19,722.22 vs ₹17,088.81 — 15.4% higher**. FOIR inflates 15.4%, moving applicants across BRULE-04 band boundaries. Confidently wrong credit decisions |
| FR-012 never store Aadhaar | No scenario asserting absence from storage | Regulatory breach. The data model is set in sprint 1; UAT runs weeks later |
| FR-006 amount/tenure range | No out-of-range scenario | Out-of-policy applications enter the funnel |
| FR-010 e-KYC failure handling | No scenario for outright failure | Undefined behaviour on a path that will certainly occur |

**Why this is the interesting finding:** the fix is not "add more rules to the matrix". It is
recognising that a matrix verifies the **shape** of a requirements set — that every box has something
in it — and something else has to verify the **substance**. Rules 1–6 check shape. Rule 7 (compare
each story's declared coverage against the matrix rows naming it) was the first rule that could see
inside the box, and it found four defects that had survived every review.

### 3.2 The cost of a change request is rarely where the change is

CR-002 moved one cell of one decision table from `AUTO_APPROVE` to `REFER`. Direct impact, measured by
backtesting 4,612 applications: auto-decision coverage 78.1% → 73.4%. Still above the 70% target, so
apparently a clean approval.

The actual cost was two documents away. BR-04's headroom fell from 8.1pp to **3.4pp** — and BR-04 is
measured on live applicant mix, not on the backtest population. The only control that detects a
mix-driven breach is FR-044, the daily decision-band distribution report, which was prioritised
**Should** and sat at **position 1 on the descope list**. The requirement protecting a baselined
business requirement was the first thing scheduled to be cut under pressure.

So the assessment's real output was: **promote FR-044 to Must**, costing 3 points of descope reserve.
The rule change was free; losing the ability to cut 3 points was not.

**Generalisable principle: a monitoring requirement should carry the priority of the thing it
monitors.** That sentence is worth more in an interview than the whole decision table.

### 3.3 An obligation can straddle a scope boundary, and both easy answers are wrong

CR-003 found that the RBI Digital Lending Guidelines require a cooling-off period during which a
borrower can exit by paying principal plus proportionate APR without penalty
([source](https://fintech.global/2022/09/07/rbi-unveils-new-guidelines-on-digital-lending/), minimum
3 days for tenors ≥ 7 days per the [2025 Directions](https://www.axisbank.com/docs/default-source/default-document-library/reserve-bank-of-india-digital-lending-directions2025.pdf)).
The exit is exercised **after disbursal** — and the BRD explicitly excludes collections and servicing.

| Easy answer | Why it fails |
|---|---|
| "It's servicing, out of scope" | ORIGIN originates the contract carrying the obligation. Shipping terms that cannot be honoured is a finding against ORIGIN |
| "It's regulatory, absorb it" | Building settlement and closure inside an origination platform duplicates the LMS and breaches CON-01 |

The resolution is to **decompose by obligation rather than by system**: ORIGIN discloses the right
(FR-045), computes the deadline and hands it over (FR-046), discloses the grievance route (FR-047) —
and the *execution* is assigned to the LMS as **DEP-05**, an open dependency that gates the pilot.

**The uncomfortable part is the recommendation.** Every ORIGIN requirement can pass UAT and the loan
can still produce a compliance finding, because enforcement is outside this scope. So the
recommendation is to **hold go-live** if DEP-05 is unconfirmed — at ₹43,07,000 per month of forgone
benefit. Naming that trade-off is the job; hoping it resolves itself is not.

---

## 4. Interview questions this package invites

Prepared honestly — including the ones that expose its weaknesses.

### On requirements practice

**Q: How do you know when a requirement is well-written?**
It is testable, unambiguous, traceable to a business need, and free of solution detail. The practical
test I use: could two developers read it and build different things? FR-019 says FOIR is
"(existing monthly EMI obligations + proposed EMI) ÷ derived monthly net income, expressed to 4 decimal
places" — the precision is not pedantry, it is the difference between two implementations agreeing.
And FR-020 in this package is the counter-example: it *was* precise, but no story pinned it, and
precision in the FRD does not survive if the acceptance criteria are silent.

**Q: Why decision tables instead of prose for the credit rules?**
Prose lets you describe rules one at a time, which is how you miss interactions. BRULE-04 has 5 FOIR
bands × 3 score bands = 15 combinations, and a table forces all 15 to be resolved. When the CRO
narrowed one cell in review, the change was a single cell — visible, versioned, and backtestable.
Prose would have hidden it in a paragraph.

**Q: What's the difference between a business rule and a functional requirement?**
A business rule is a policy that exists independently of any system — the NBFC would apply the FOIR
cap on paper. A functional requirement is what the system does about it. Separating them matters
because rules change on a different cycle and with a different approver: the CRO owns BRULE-04, the
project owns FR-021 which evaluates it. That is why the rules are versioned separately and why
NFR-28 requires thresholds to be configurable without a deployment.

**Q: How do you handle a stakeholder who won't engage?**
SH-11 (applicants) cannot be consulted at all, so they are represented by call-centre complaint data
and drop-off analytics. SH-07 (Customer Service) was consulted rather than treated as a persona — and
GAP-01 is the honest consequence: FR-041 has no user story, because writing one without talking to
them would have produced acceptance criteria I invented. I recorded the gap and scheduled the
conversation rather than filling it in.

### On this specific package

**Q: Walk me through a requirement from business need to test.**
BR-08 (auditable decision trail, non-negotiable) → FR-023 (persist every rule evaluation with its
rule version) and FR-043 (reconstruct any past decision) → the data model turns this into
RULE_EVALUATION as a separate entity with `rule_version` as a foreign key, not a copied string
(07 §2.1, §2.2) → US-16 gives the Gherkin → UAT-26 and UAT-44 verify it, both S1-if-failed → RTM row
FR-023 proves the chain. The design decision worth defending is `rule_version` as an FK: copying the
version string at write time looks simpler and destroys your ability to answer "what did v1.1
actually say?" — which is the only question an auditor asks.

**Q: You have 47 requirements and 3 sprints. What do you cut?**
Nothing that is Must, and I decided the order before the sprint started: FR-036 queue ageing (3) →
FR-018 bureau cache (3) → FR-027 revised amount (5) → FR-041 CS view (1). Twelve points, no Musts, each
with a stated consequence and workaround. There is also a pre-authorised trigger: if sprint 2 is more
than 8 points behind at day 7, US-09 drops without another approval cycle. The value is the timing —
the same decision made under pressure gets made badly.

**Q: Your buffer is 2.6%. Is this plan credible?**
Marginally, and I would say so to the sponsor. It is 111 points against 114 of capacity, and sprint 2
runs 4 points above average velocity because CR-003 landed there — FR-045 must be disclosed before
e-Sign, and e-Sign is a sprint 2 story, so it could not be deferred. What makes it survivable is that
12 of sprint 3's 33 points are Should items, so the overrun has somewhere to go that is not a Must and
is not the timeline. What I would not do is restate the buffer as adequate because the total still fits.

**Q: What would you do differently?**
Write rule 7 of the validator before baselining the FRD. It was added to catch drift after a change
request, and it immediately found four Must requirements with no acceptance criteria that predated any
change. Those four had survived a full review cycle. The lesson is that I was reviewing for
completeness of the *matrix* when I should have been reviewing for substance of the *stories* — and I
only learned it because I automated the check.

**Q: The 9.5% loss rate in CR-002 — where did that come from?**
A credit-team judgement on a 217-application sample, not an observed outcome, and I flagged it as the
softest number in the assessment. The benefit is directly proportional to it: at 4% instead of 9.5%,
the loss avoided falls from ₹23,26,000 to ₹4,16,000 and the change is near break-even on pure
economics. I still recommended approval, on a different argument — underwriters historically declined
14.3% of applications in a cell proposed for *automatic approval*, and that alone is sufficient
evidence the cell needs judgement. Making the recommendation robust to the weak number is the point.

### On the harder challenges

**Q: This is synthetic. Why should I believe any of it?**
You shouldn't believe the volumes — 4,612 applications and 41.0% completion are constructed. What is
real and checkable is everything downstream: the regulatory obligations are cited to RBI sources, the
EMI arithmetic is computed not asserted, the business case reconciles to its inputs, and the twelve
documents are provably consistent with each other because a script fails the build otherwise. The
skill on display is not "I have access to an NBFC's data" — it is whether I can hold a 47-requirement
specification internally consistent across three change requests.

**Q: Isn't a validation script overkill for twelve documents?**
It found twelve defects in twelve documents, four of them Must-priority requirements with no
acceptance criteria, and one of those would have shipped a 15.4% error into credit decisioning. At
this scale it is arguably overkill for the *checking* and clearly not overkill for the *finding*. The
real argument is different though: a check that runs in 0.07 seconds gets run on every change, and a
review meeting does not.

**Q: Where is this package weakest?**
Three places. **GAP-01** — FR-041 has no user story, and I chose to record that rather than invent
acceptance criteria. **GAP-02** — BR-03's outcome (document-stage drop-off below 12%) cannot be
verified at UAT at all; it is a behavioural metric, so it moves to a day-30 post-launch gate, which
means the package cannot prove that business requirement is met before go-live. **DEP-05** — the
cooling-off enforcement sits in a system I do not control, and no amount of specification here fixes
that. All three are stated in the documents rather than left to be discovered.

---

## 5. If you rebuild this yourself

The order that works, and the two places to spend disproportionate time:

1. Pick a domain with **real rules** — lending, insurance claims, KYC. Rules give you decision tables,
   versioning, precedence and audit requirements for free. A CRUD app gives you none of that.
2. Write **02 before 03**. Measure the current state first, then let the business case fall out of it.
   Doing it the other way round produces benefits reverse-engineered from features.
3. **Spend the most time on the decision tables.** They are where a BA visibly adds value over a
   product owner, and they are what makes the change request in 11 assessable.
4. Write the **validator early** — before baselining, not after. Then let it tell you what you got
   wrong, and *document what it found* rather than silently fixing it. The gaps are more persuasive
   than the passes.
5. Include **one rejected change request**. Anyone can say yes. The rejection is where judgement shows,
   and it needs a number: 62 points against 15 points of headroom, ₹43,07,000 per month of delay.

**The thing that makes this package different from a template dump** is not the number of documents.
It is that every ID resolves, every number reconciles to its inputs, three change requests propagated
through all of it, and a script fails the build if any of that stops being true.
