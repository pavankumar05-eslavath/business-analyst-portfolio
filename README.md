# Business Analyst Portfolio

Three projects covering three different BA archetypes, so they demonstrate different skills
rather than the same one three times.

| Project | Archetype | What it demonstrates |
|---|---|---|
| **[BA-1 — Loan Origination Requirements Package](./ba1-requirements-package)** ✅ | Product / SDLC BA | 12 documents: stakeholder analysis and RACI, AS-IS→TO-BE process models, BRD with business case, 47 functional requirements, 8 versioned decision tables, 19 Gherkin stories, 30 NFRs, data model, 53 UAT cases, release plan, and 3 worked change-request impact assessments. **The traceability matrix is executable — and it found 12 real defects in my own documents, including 4 Must requirements with no acceptance criteria.** |
| **[BA-2 — Unit Economics & Pricing Decision](./ba2-unit-economics)** | Commercial / finance BA | Driver-based P&L model with live formulas, CM1–CM3 per order, channel LTV:CAC, cohort payback, break-even, two-way sensitivity, and a recommendation with second-order effects modelled. |
| **[BA-3 — KPI Framework & Root-Cause Diagnosis](./ba3-kpi-root-cause)** | Operations / MI BA | KPI tree, governed metric dictionary, MECE hypothesis testing in SQL with an audit trail of eliminated branches, mix-vs-rate decomposition, and a business case with ROI. |

## Why documents, not code

BA interviews test elicitation, process modelling, precision of specification, and the ability
to make a decision under ambiguity. They do not test whether you can write a for-loop.

Very few candidates build proper requirements artefacts, which is exactly why these land well.
The output of a BA is a document that a developer can build from without asking questions, and a
recommendation a director can approve without a second meeting.

## What makes these different from a template dump

Anyone can download a BRD template and fill in headings. Three things here are not that:

1. **Every requirement has an ID and is traced end to end** — business need → functional
   requirement → user story → UAT case. BA-1 ships a script that *validates* the chain and fails
   the build if anything is orphaned, miscounted, or inconsistent between documents.
2. **Non-functional requirements carry real numbers.** "The system should be fast" is not a
   requirement. "P95 eligibility decision under 3 seconds at 40 concurrent applications" is.
3. **Each project commits to a decision** and states what would change its mind. "It depends"
   is the answer that loses BA interviews.
4. **The defects found are documented, not hidden.** BA-1's validator caught 12 inconsistencies in
   documents I had already finished and reviewed — four of them Must-priority requirements that were
   fully traced but had no acceptance criteria at all. Those findings are the most persuasive part of
   the project, so they are written up rather than quietly fixed.

## Reading order

Each project has a `README.md` (what it is and the headline finding) and a `LEARN.md` (how the
artefacts fit together, plus the interview questions the project invites).
