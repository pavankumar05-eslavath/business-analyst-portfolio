# Data & Business Analytics Portfolio — Complete Guide

**Author:** Pavan Kumar Eslavath · IIT Madras
**Purpose:** Nine end-to-end projects covering three job profiles — Data Engineer, Data Analyst, Business Analyst
**GitHub:** [`pavankumar05-eslavath`](https://github.com/pavankumar05-eslavath)

This single document explains everything: what each project is, what it found, how to run it, and
which files to read. If you are picking this up cold, read sections 1–3 and then jump to whichever
project interests you.

---

## Table of contents

1. [The short version](#1-the-short-version)
2. [The three repositories](#2-the-three-repositories)
3. [Setup — running any project in 5 minutes](#3-setup--running-any-project-in-5-minutes)
4. [What the three roles actually are](#4-what-the-three-roles-actually-are)
5. [The nine projects in detail](#5-the-nine-projects-in-detail)
   - [Data Engineering: DE-1, DE-2, DE-3](#data-engineering)
   - [Data Analytics: DA-1, DA-2, DA-3](#data-analytics)
   - [Business Analysis: BA-1, BA-2, BA-3](#business-analysis)
6. [Complete file inventory](#6-complete-file-inventory)
7. [Reading order — how to understand a project fast](#7-reading-order--how-to-understand-a-project-fast)
8. [The nine bugs found and documented](#8-the-nine-bugs-found-and-documented)
9. [Concepts glossary](#9-concepts-glossary)
10. [Verified numbers reference](#10-verified-numbers-reference)
11. [What is deliberately NOT here](#11-what-is-deliberately-not-here)

---

## 1. The short version

Nine projects. Three job profiles. Everything runs with one command and is verified by tests.

| | Count |
|---|---|
| Projects | **9** |
| Git commits | **80** |
| Files | **208** |
| Automated tests | **369 pytest + 98 dbt data tests = 467 checks** |
| CI pipelines | **9 GitHub Actions workflows** (one per project) |
| Real bugs found and documented | **9** |

**What makes these different from tutorial projects:**

1. **Every number is measured, not invented.** Where a project claims "65% of orders are updated
   late" or "conversion fell 0.396 percentage points," that figure comes from running the code.
2. **Tests pin the claims.** If a change breaks a number quoted in a README, the build fails rather
   than the document quietly becoming wrong.
3. **Each project contains a real bug, written up rather than hidden.** See
   [section 8](#8-the-nine-bugs-found-and-documented) — this is the most useful part of the whole
   portfolio.
4. **Every project reaches a decision**, and several of them say *no* to something expensive.

**The single idea that runs through the whole portfolio:**

> **Aggregate numbers lie when the mix underneath them changes.**
>
> Conversion fell while every device improved (DA-1). Revenue rose while profit fell (BA-2). A
> support metric fell while every tier improved (BA-3). Same phenomenon, three disguises, and in
> every case the obvious conclusion was backwards.

---

## 2. The three repositories

| Repository | Profile | Projects | Commits |
|---|---|---|---|
| **[data-engineering-portfolio](https://github.com/pavankumar05-eslavath/data-engineering-portfolio)** | Data Engineer | DE-1, DE-2, DE-3 | 33 |
| **[data-analyst-portfolio](https://github.com/pavankumar05-eslavath/data-analyst-portfolio)** | Data Analyst | DA-1, DA-2, DA-3 | 29 |
| **[business-analyst-portfolio](https://github.com/pavankumar05-eslavath/business-analyst-portfolio)** | Business Analyst | BA-1, BA-2, BA-3 | 18 |

Each repository has a root `README.md` explaining the set, and each project has its own folder.

---

## 3. Setup — running any project in 5 minutes

Every project is self-contained with its own `requirements.txt` and `Makefile`. No database server,
no cloud account, no API keys.

### One-time setup

```bash
# Python 3.11 or later required
git clone https://github.com/pavankumar05-eslavath/data-engineering-portfolio.git
cd data-engineering-portfolio

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### Running a project

```bash
cd de1-batch-elt-warehouse
pip install -r requirements.txt

make help      # see all available commands
make all       # run the whole thing end to end
make test      # run the test suite
make lint      # check code style
make clean     # remove generated files
```

**That's it.** Every one of the nine projects follows the same pattern.

### Runtimes

| Project | `make all` | `make test` |
|---|---|---|
| DE-1 | ~99s | ~5s |
| DE-2 | ~30s (calls a live API) | ~1.4s (offline) |
| DE-3 | ~10s | ~5.3s |
| DA-1 | ~13s | ~4s |
| DA-2 | ~4.4s | ~6.3s |
| DA-3 | ~5s | ~4s |
| BA-1 | <1s | <1s |
| BA-2 | ~0.5s | ~3.9s |
| BA-3 | ~1.8s | ~2s |

> **Note on data:** most projects generate their own dataset from a seeded configuration file, so
> results are reproducible byte-for-byte. DE-2 is the exception — it calls the live USGS earthquake
> API, so its numbers shift slightly with each run. Its tests are fully offline.

---

## 4. What the three roles actually are

Imagine a large retail business.

**The Data Engineer** builds the plumbing. Sales happen, customers sign up, deliveries go out — and
that information sits scattered across systems in messy formats. The engineer collects it reliably,
cleans it, and lands it somewhere queryable. Nobody thanks them when it works; everybody notices
when it breaks.

**The Data Analyst** uses that plumbing to answer questions. *Why did sales drop? Which customers
are about to leave? Did the new checkout page actually help?* They work in SQL, Python and
statistics.

**The Business Analyst** may not touch data at all. They sit between the business and the people who
build things: working out what the business actually needs, writing it down precisely enough that a
developer can build it without asking questions, and making the case for whether something is worth
doing at all.

Three genuinely different skill sets — which is why this is three separate sets of projects rather
than one set stretched to fit.

---

## 5. The nine projects in detail

## Data Engineering

### DE-1 · Batch ELT Warehouse

**Folder:** `de1-batch-elt-warehouse/`
**Stack:** Python · DuckDB · dbt · pytest

#### The problem

A business has raw records of orders, customers, products and sellers. The data is messy,
duplicated, and arrives late. Nobody can answer "what were sales by city last quarter?" because the
data isn't organised for questions — it's organised for transactions.

#### What it does

Takes raw messy source data and turns it into a clean **star schema** — the standard warehouse
design of central "fact" tables (things that happened) surrounded by "dimension" tables (the context
for those things).

The pipeline is **idempotent**: if it crashes halfway and you re-run it, you don't get duplicates.
That sounds simple and is one of the hardest properties to get right.

**Scale:** 5,000 customers · 800 products · 120 sellers · 60,000 orders · 91,135 line items
**Backfill:** 151,326 rows across 629 daily partitions in **71 seconds**, 3,150 loads, zero failures
**dbt layer:** 12 models validated by **98 data tests** — 110 nodes, all passing in 3 seconds

#### The key finding

When you load data incrementally, you only want the records that changed. So you ask "give me
everything newer than yesterday" — but **newer by which date?**

The intuitive answer is the order date. It's wrong. Orders get **modified** after creation: status
changes, addresses get corrected, refunds happen.

> **65% of orders were modified more than 7 days after being placed** — maximum lag 96 days.

Filter on order date and you load an order once, then never see it again. Its status silently
freezes. Your dashboard shows thousands of "pending" orders that were delivered weeks ago, and
nobody notices for months. The fix is to filter on the *last modified* timestamp.

**Second finding — why SCD Type 2 is worth the complexity.** A seller's commission rate changes over
time. If you just overwrite the old rate (Type 1), historical orders get recalculated at today's
rate. Keeping full history (Type 2) is more work. Is it worth it?

Measured: Type 1 would misstate total commission payable by **1.87% — ₹9.88 crore vs ₹9.69 crore.**
That's the business case for the complexity, in one number.

#### Files to read

| File | What's in it |
|---|---|
| `README.md` | Overview and headline results |
| `LEARN.md` | Concepts explained + interview questions |
| `docs/architecture.md` | How the pipeline is structured and why |
| `src/pipeline.py` | The orchestrator — start here for the code |
| `src/extract.py`, `src/load.py` | Extraction and the idempotent load logic |
| `src/quality.py` | Validation and record rejection |
| `dbt_project/models/marts/` | The star schema — `dim_*` and `fct_*` models |
| `dbt_project/models/marts/dim_seller.sql` | The SCD Type-2 implementation |
| `dbt_project/tests/` | 4 custom SQL tests, including SCD2 window contiguity |
| `config/pipeline.yml` | All configuration |

---

### DE-2 · Incremental API Ingestion

**Folder:** `de2-incremental-api-ingestion/`
**Stack:** Python · Pydantic · Tenacity · DuckDB · pytest

#### The problem

Your data lives in someone else's system and you can only reach it through an **API** — a web
endpoint you send requests to. APIs impose limits: don't ask too often, don't ask for too much at
once, and expect occasional failures.

#### What it does

Pulls real earthquake data from the **live USGS (US Geological Survey) public API**. It:

- Remembers where it left off (a **watermark**) so it only fetches new data
- Handles the API refusing oversized requests by **automatically splitting the time window in half**
  and retrying — 7 of 21 daily windows exceeded the 250-record cap and were bisected into 14
- Retries transient failures with exponential backoff
- Validates every record against a strict schema before it reaches the database
- **Archives every raw API response to disk**, gzipped and checksummed

**Initial load:** 4,889 events over a 21-day horizon in 24.8s · 63 API calls · p95 latency 514ms
**Archive:** 49 payloads · 470 KB · **7.33x gzip compression** · all checksums verify

#### The key finding

**Two things worth understanding here.**

**1. The archive enables replay.** Because every raw response is stored, the entire database can be
rebuilt from disk:

> **4,889 events reprocessed in 1.1 seconds with zero API calls — 22x faster than the 24.8s live
> run.**

Why this matters: if you find a bug in your parsing logic six months later, you can fix it and
reprocess all of history instantly. Without an archive you'd have to re-download everything, which
may be slow, rate-limited, or simply impossible if the API no longer serves old data.

**2. Real-world proof that data changes after you see it.**

> **81.6% of earthquake records were revised after publication.** Median revision lag: 11 hours.
> 34.3% revised more than 24 hours later. Maximum: 20 days.

An earthquake is detected automatically within seconds, then reviewed by a human seismologist hours
or days later who corrects the magnitude. Automatically-published events settle in ~25 minutes;
human-reviewed ones take a median of 980 minutes — **39x longer.**

This is the same lesson as DE-1, found in genuinely external data.

#### Files to read

| File | What's in it |
|---|---|
| `README.md` | Overview, the revision-rate finding |
| `LEARN.md` | API ingestion patterns + interview questions |
| `docs/architecture.md` | Design decisions |
| `src/client.py` | The HTTP client — retries, rate limits, adaptive chunking |
| `src/archive.py` | Raw payload archival, compression, checksums |
| `src/models.py` | Pydantic schema validation |
| `src/pipeline.py` | Orchestration, including `--rebuild` replay mode |
| `tests/conftest.py` | How the API is mocked so tests run offline |
| `config/ingestion.yml` | Configuration |

---

### DE-3 · Data Quality Framework

**Folder:** `de3-data-quality-framework/`
**Stack:** Python · DuckDB · YAML · pytest

#### The problem

Your pipeline runs perfectly. No errors, no crashes. But the data is *wrong* — a supplier started
sending prices in dollars instead of rupees, or a bug means half the rows have empty customer IDs.
Nothing fails. Your dashboards just quietly report nonsense.

#### What it does

A configuration-driven framework that runs **16 types of automatic check** every day and flags
problems, with an HTML report.

The checks fall into two families:

- **Static rules** — "this column must never be empty", "this value must be between 0 and 100".
  Simple, but you have to know the answer in advance.
- **Baseline comparison** — "compare today's value against the last 30 days; is it unusual?" Catches
  things you didn't anticipate. Includes z-score, modified z-score (MAD), and PSI distribution drift.

**Test:** 7 deliberate data incidents injected into 62,916 rows across 60 daily snapshots.
**Result:** **7/7 detected. Zero false positives. Across 1,080 check evaluations.**

#### The key finding

> **Static rules caught only 3 of the 7 incidents. Baseline comparison caught all four misses.**

The clearest example: a column normally 7.8% empty jumped to **43.2% empty (z = 43.7)**. A static
rule saying "must be under 50% empty" **passed it**. Comparison against history caught it instantly.

Others static rules missed: a 64% row-count drop (still above the static minimum), a distribution
drift of PSI 0.541 (all values still within the accepted range), and a brand-new category value
appearing.

**And the bug worth knowing about.** My baseline checks initially raised a false alarm on an
*ordinary Saturday* at z = 5.0. Cause: **weekend volume runs about 18% above weekdays.** Comparing
Saturday against a mixed baseline of weekdays and weekends makes every Saturday look abnormal —
every single week.

Fixed with day-of-week seasonal baselines (comparing Saturdays only against the 8 prior Saturdays)
plus a minimum relative-change floor. This is a real, common defect in production monitoring, and a
monitoring system that cries wolf gets switched off.

#### Files to read

| File | What's in it |
|---|---|
| `README.md` | The detection scorecard — which check type caught what |
| `LEARN.md` | Data quality concepts + the seasonality bug + interview questions |
| `docs/architecture.md` | How checks are registered and executed |
| `dq/checks/basic.py` | The static rule checks |
| `dq/checks/anomaly.py` | Baseline/statistical checks — read this one |
| `dq/engine.py` | Execution engine, suppression handling |
| `dq/types.py`, `dq/registry.py` | How new check types plug in |
| `config/checks.yml` | The 18 configured checks — readable without Python |
| `config/suppressions.yml` | Known-issue suppression with expiry |
| `demo/generate_demo_data.py` | The 7 injected incidents, with their definitions |
| `tests/test_demo_detection.py` | Asserts 7/7 detection and zero false positives |

---

## Data Analytics

### DA-1 · E-commerce Funnel & Cohort Analytics

**Folder:** `da1-ecommerce-analytics/`
**Stack:** SQL · DuckDB · Python · pytest

#### The problem

A website has hundreds of thousands of recorded actions — page views, add-to-carts, purchases.
Management wants to know where customers drop off, which channels are worth the money, and why
conversion is falling.

#### What it does

- Groups raw clicks into **sessions** (one visit by one person)
- Builds a 5-stage **conversion funnel**
- **Cohort retention** — do customers who joined in March behave like those who joined in June?
- **RFM segmentation** — Recency, Frequency, Monetary value scoring
- **Channel quality** analysis — revenue per acquired user by marketing channel

**Scale:** 318,840 events · 39,829 users · **169,867 sessions** · 5,371 purchases · ₹13.05M revenue

#### The key finding

**This is the most important thing in the entire portfolio.**

Overall conversion fell from **3.357% to 2.961%**. The obvious conclusion: the site got worse.

Split by device:

| Device | Before | After | |
|---|---|---|---|
| Desktop | 4.091% | **4.742%** | ↑ improved |
| Mobile | 2.091% | **2.428%** | ↑ improved |
| Tablet | 1.894% | **3.875%** | ↑ improved |

**Every single device improved. The total went down.**

The cause: mobile share of traffic grew from **31.3% to 75.1%**. Mobile converts worse than desktop
in absolute terms, so shifting traffic toward mobile drags the average down — even while mobile
itself improves.

This is **Simpson's paradox**. It's not a trick, it's arithmetic. And the business consequence is
severe: the intuitive conclusion is exactly backwards.

I then decomposed the −0.396pp change into its parts:

| Component | Effect |
|---|---|
| Rate (performance within segments) | **+0.617pp** |
| Mix (traffic composition shift) | **−0.877pp** |
| Interaction | −0.135pp |
| **Sum** | **−0.3956pp** ✓ reconciles with the observed −0.396pp |

**Why reconciliation matters:** a list of explanations that doesn't add up to the thing you're
explaining can't be checked. If your components sum to the observed change, your analysis is
falsifiable.

**Also verified:** sessionisation was validated against generated ground truth to an **exact match —
169,867 = 169,867, zero splits, zero merges.** Most analysts never check this; they trust the
30-minute timeout convention and move on.

#### Files to read

| File | What's in it |
|---|---|
| `README.md` | Overview and headline findings |
| `INSIGHTS.md` | The findings written up as an analyst would present them |
| `LEARN.md` | Simpson's paradox explained + interview questions |
| `sql/00_metric_definitions.md` | **Read this first** — how every metric is defined |
| `sql/01_sessionize.sql` | Turning clicks into sessions |
| `sql/02_funnel.sql` | The conversion funnel |
| `sql/03_cohort_retention.sql` | Cohort analysis |
| `sql/04_rfm.sql` | RFM segmentation |
| `sql/05_mix_effect_decomposition.sql` | **The Simpson's paradox analysis** |
| `sql/06_channel_quality.sql` | Marketing channel comparison |
| `dashboard/POWERBI_SPEC.md` | Dashboard specification (not yet built) |
| `data/generate_events.py` | The data generator with known ground truth |

---

### DA-2 · A/B Test Design & Analysis

**Folder:** `da2-ab-testing/`
**Stack:** Python · SciPy · statsmodels · matplotlib · pytest

#### The problem

You changed the checkout button. Did it actually help? You show the old version to half your users
and the new version to the other half, then compare. Simple in principle; full of traps in practice.

#### What it does

A complete experimentation framework:

- **Sample sizing before you start** — 18,872 users per arm, 12.6 days at 3,000 users/day
  (cross-checked against `statsmodels` to within 2%)
- **Sample ratio mismatch check** — was the split actually 50/50? (χ² = 0.81, p = 0.368 — passed)
- **Analysis** — proportions test, Welch's t-test, bootstrap confidence intervals
- **CUPED** — a variance reduction technique using pre-experiment data
- **Multiple testing correction** — Bonferroni and Benjamini-Hochberg
- **Peeking simulation** — quantifying the cost of stopping early

#### The key findings

**1. The winning test should not ship.**

| Metric | Control | Treatment | Change | |
|---|---|---|---|---|
| Conversion | 7.644% | 8.895% | **+1.251pp (+16.4%)** | p < 0.0001 ✓ |
| **Checkout errors** | 1.607% | 2.140% | **+0.533pp (+33.2%)** | p = 0.0001 ✗ |

Conversion improved significantly — but checkout errors rose 33%. The variant converted better
*partly because* it created errors users retried through.

**Verdict: do not ship.** The metric you're optimising is never the only metric that matters. You
define your **guardrails** — what you refuse to break — *before* you start.

**2. Peeking nearly quadruples your false positive rate.**

You plan a two-week test. On day 3 you peek — "it's significant!" — and stop early.

I ran **2,000 simulated experiments where the two versions were genuinely identical** (an A/A test,
so any "win" is pure noise):

| Approach | False positive rate |
|---|---|
| Check once at the planned end | **5.2%** (≈ the 5% you'd expect) |
| Check daily, stop when significant | **19.7%** |

**Nearly one in five "wins" is noise.** That's a 3.8x inflation, and it's why you fix your sample
size in advance and don't look until you get there.

**3. CUPED is powerful but conditional.** Using pre-period session counts as a covariate reduced
variance by **70.3% — equivalent to a 3.37x larger sample, for free.** But applied to revenue
(which is 91.7% zeros) it reduced variance by only 1.4%. CUPED's benefit is bounded by the
correlation between the pre-period and the metric; it isn't magic.

**4. Multiple testing is a real trap.** Across 19 segment tests, the probability of at least one
false positive reaches **62%**. Bonferroni reduced 6 raw significant results to 4; Benjamini-Hochberg
to 5.

#### Files to read

| File | What's in it |
|---|---|
| `README.md` | Overview and the ship/no-ship decision |
| `INSIGHTS.md` | The results as an analyst would present them |
| `LEARN.md` | Every statistical concept explained + interview questions |
| `src/design.py` | Power analysis and sample sizing |
| `src/checks.py` | Sample ratio mismatch, pre-period balance |
| `src/analysis.py` | The statistical tests, CUPED |
| `src/corrections.py` | Bonferroni and Benjamini-Hochberg |
| `src/simulate.py` | **The peeking simulation** — read this one |

---

### DA-3 · Churn Prediction & Retention Targeting

**Folder:** `da3-churn-analysis/`
**Stack:** Python · scikit-learn · DuckDB · pytest

#### The problem

Some customers will stop buying. If you knew who, you could try to keep them. But contacting people
costs money, and retention offers only work sometimes.

#### What it does

- Defines churn precisely, with a **disjoint observation window (months 0–8) and performance window
  (months 9–11)** so the model can't accidentally see the future
- Builds an explicit **eligibility funnel** reducing 60,000 users to a 9,566-user modelling
  population
- Trains and evaluates a model against multiple baselines
- Converts scores into a **profit-optimal contact policy**

**Scale:** 60,000 users · 269,849 user-months · 857,349 orders · ₹985.95M
**Model:** ROC-AUC **0.832** · PR-AUC 0.639 · Brier 0.105 · calibration error (ECE) **0.017**
**Lift:** top decile is 77.0% churn — **4.03x** the base rate. Top 3 deciles contain 72.5% of churners.

#### The key findings

**1. The decision matters more than the model.**

Contacting a customer costs ₹250. A saved customer is worth ₹4,000. Offers work 25% of the time.
So contacting is worth it above a churn probability of 250 ÷ (0.25 × 4,000) = **0.250**.

| Strategy | Users contacted | Precision | Net profit |
|---|---|---|---|
| Contact everyone at risk | 2,870 | — | **−₹169,500** (loses money) |
| Contact if p > 0.50 (the default) | 367 | 72.5% | ₹174,250 |
| **Contact if p > 0.203 (optimal)** | **694** | 51.7% | **₹185,500** |

**Contacting everyone loses money.** And the 0.50 threshold everyone reaches for by default is not
optimal — the right number comes from the *economics*, not from statistics.

**2. A simpler model won.** Gradient boosting scored **0.0017 worse** than logistic regression. When
the complex model doesn't win, interpretability is free — and being able to explain *why* a customer
was flagged is what makes the model usable by a retention team.

**3. Actionability beats predictive power.** The strongest predictor was recency of last order (odds
ratio 10.01) — but that's a *symptom*, not something you can fix. The strongest **actionable**
driver was late delivery rate (**OR 10.21, CI [4.11, 25.34]**). 66.4% of flagged users mapped to a
specific operational cause.

**4. The bug worth knowing about — and my favourite story in the portfolio.**

My first model showed that customers with **more payment failures were LESS likely to churn**
(12.6% vs 20.7%). Obvious nonsense.

The cause: I had only generated payment-failure records for customers who were *actively using the
service*. So "has a payment failure" secretly encoded "is an active customer" — and active customers
churn less. The variable was measuring the opposite of what I thought.

I found it by **cross-tabulating the raw relationship** instead of trusting the model output.

> **When a model tells you something absurd, check the data before you rationalise the model.**

#### Files to read

| File | What's in it |
|---|---|
| `README.md` | Overview and the targeting decision |
| `INSIGHTS.md` | Findings and the operational action plan |
| `LEARN.md` | Churn modelling concepts + the selection bias story + interview questions |
| `src/churn_definition.py` | **Read this first** — how churn is defined and the eligibility funnel |
| `src/features.py` | Feature engineering, and the leakage guards |
| `src/model.py` | Training, and the baseline comparisons |
| `src/evaluation.py` | Metrics, calibration, decile lift |
| `src/targeting.py` | **The profit-optimal threshold** — the important part |
| `data/generate_subscriptions.py` | The generator, including the fixed selection bias |

---

## Business Analysis

> These three have almost no code, and that's deliberate. BA interviews test whether you can think
> clearly and write precisely — not whether you can code.

### BA-1 · Loan Origination Requirements Package

**Folder:** `ba1-requirements-package/`
**Domain:** Digital personal loan origination for a mid-size Indian NBFC ("Project ORIGIN")

#### The problem

A lending company wants to let people apply for personal loans online. Today it takes **6.8 days**
and **59% of applicants give up**. Someone has to write down exactly what to build — precisely
enough that developers can build it without guessing, and that the business can verify it later.

#### What it does

A complete **12-document requirements package**:

| # | Document | Contents |
|---|---|---|
| 01 | Stakeholder analysis & RACI | 12 stakeholders, power/interest map, elicitation method per stakeholder, RAID log |
| 02 | Process models | AS-IS and TO-BE flows, 9 quantified pain points, gap analysis |
| 03 | Business requirements | 8 BRs with measurable success criteria, scope with reasons, business case |
| 04 | Functional requirements | **47 FRs**, 8 versioned business rules as decision tables, rule precedence |
| 05 | User stories | **19 stories, 110 points**, Gherkin acceptance criteria |
| 06 | Non-functional requirements | **30 NFRs** with numeric thresholds and measurement conditions |
| 07 | Data model | ERD, 4 justified modelling decisions, data dictionary, state diagram |
| 08 | UAT test cases | **53 cases**, severity definitions, exit criteria |
| 09 | Traceability matrix | Forward trace, full trace, rule trace, 3 documented gaps |
| 10 | Release plan | MoSCoW, 3-sprint plan, descope order agreed in advance, rollback triggers |
| 11 | Change requests | **3 worked impact assessments** — one rejected, two approved |

**Baseline:** 4,612 applications · 1,893 disbursals (41.0% completion) · median 6.8 days · **2,690
manual hours/month ≈ 16 FTE**
**Business case:** ₹71 lakh cost against **₹5.17 crore annual benefit — 1.6 month payback**

#### The key finding

I wrote a program (`tools/validate_traceability.py`) that reads all 12 documents and checks they
agree with each other: does every requirement trace to a business need, does every requirement have
a test, do the numbers in the plan add up? **13 rules, 25 tests.**

> **It found 12 real defects in documents I had already finished and proofread.**

The worst class — and this is the finding worth remembering:

**Four Must-priority requirements were fully "traced."** They had a business justification, appeared
in the tracking matrix, were assigned to a sprint, and had UAT test cases. But **none had any
acceptance criteria.** The user story that supposedly covered them said nothing about them.

One was FR-020: *"calculate EMI using reducing-balance amortisation."* No story pinned the method, so
a developer could reasonably have used flat-rate interest. On a ₹5,00,000 loan over 36 months at 14%:

| Method | Monthly EMI |
|---|---|
| Reducing balance (correct) | **₹17,088.81** |
| Flat rate | **₹19,722.22** — **15.4% higher** |

That 15.4% error flows into the affordability ratio and pushes borderline applicants into worse
credit decision bands. **The system would have been confidently wrong about who gets a loan — and
every traceability check would have passed.**

> **A traceability matrix can be 100% complete and completely hollow.**

Other defects found: 5 places where the forward trace and full trace contradicted each other, a
MoSCoW count that said 34 when the table listed 39, a sprint total declaring 39 points when its rows
summed to 40, and an NFR count of 10 against a table of 8.

#### Files to read

| File | What's in it |
|---|---|
| `README.md` | Overview and the 12 defects found |
| `LEARN.md` | How the artefacts fit together + BA interview questions |
| `03-business-requirements.md` | **Start here** — the *why* |
| `02-process-models.md` | Then the current state |
| `04-functional-requirements.md` | Then the *what* — including the decision tables |
| `09-traceability-matrix.md` | The proof it all connects, and the 3 documented gaps |
| `11-change-request.md` | The 3 impact assessments — the best BA material here |
| `tools/validate_traceability.py` | The validator |

**Run it:** `make validate` and `make test`

---

### BA-2 · Quick-Commerce Unit Economics

**Folder:** `ba2-unit-economics/`
**Domain:** A 10-minute grocery delivery company with 48 "dark stores" across 3 Indian cities

#### The problem

Three teams each have a proposal. Which are worth doing?

1. **Growth** wants 12 more dark stores in the cities already covered
2. **Pricing** wants to raise the free-delivery minimum from ₹299 to ₹499
3. **Category** wants to raise brand-funded advertising income from ₹14 to ₹22 per order

#### What it does

A **38-driver financial model** delivered as a **9-sheet Excel workbook where every calculated cell
is a live formula** — change one input and the whole thing recalculates.

| Sheet | What it does |
|---|---|
| `Guide` | How to use it |
| `Drivers` | All 38 inputs, each with its unit **and the basis for the number** |
| `Basket` | Lognormal basket-value distribution, live via `NORM.S.DIST` |
| `UnitEconomics` | The CM1/CM2/CM3 profit ladder, four columns (base + one per proposal) |
| `Cohort` | 24-month retention and cumulative contribution per channel |
| `Channels` | CAC, LTV, LTV:CAC — blended, paid-only, and per channel |
| `Decisions` | The three proposals with impacts and break-evens |
| `Scenarios` | Base / bull / bear |
| `Sensitivity` | Two live two-way tables |

**The profit ladder, per order:**

| Line | Amount | % of revenue |
|---|---|---|
| Net order value | ₹448.97 | 100% |
| **CM1** (after cost of goods, payment fees, packaging) | **₹115.62** | 25.75% |
| **CM2** (after delivery rider, picking labour, spoilage) | **₹63.48** | 14.14% |
| **CM3** (after allocated store rent/staff/utilities) | **₹26.97** | 6.01% |
| **EBITDA** (after central overhead and marketing) | **−₹6.03** | −1.34% |

Calibrated against published figures: CM1 of 25.75% against Blinkit's reported 26.6% gross margin;
CM2 of 14.14% against an industry benchmark of ~13% for a mature dark store.

#### The key finding

| Proposal | Orders | **Revenue** | **Monthly profit (CM3)** | Verdict |
|---|---|---|---|---|
| 12 new dark stores | +7.7% | **+7.7%** | **−₹14.6 lakh** | ❌ REJECT |
| Threshold ₹299 → ₹499 | −3.1% | **−1.1%** | **+₹35.6 lakh** | ✅ APPROVE |
| Retail media ₹14 → ₹22 | 0.0% | +1.7% | **+₹39.4 lakh** | ✅ APPROVE |

**Revenue and profit move in opposite directions on two of three proposals.** Judged on revenue
growth — which is how both were pitched — you would approve the bad one and reject the good one.

**Why the store expansion fails.** Each store costs ~₹4.6 lakh/month in rent, utilities and staff
regardless of volume. The new stores go into cities **already covered**, so most of their orders
aren't new customers — they're existing customers now served by a nearer store:

| | Now | After |
|---|---|---|
| Stores | 48 | 60 |
| Orders per store per day | 420 | **362** |
| Fixed cost per order | ₹36.51 | **₹42.38** |
| Profit per order | ₹26.97 | **₹22.81** |

Plus ₹4.20 crore of build cost that never pays back. **Store count is not scale — order density is.**

**Break-even framing.** Every decision states the break-even value of the driver it turns on, because
that survives disagreement better than a point estimate:

| Proposal | Needs | Actually measured |
|---|---|---|
| Store expansion | 63.7% incrementality | **43.0%** in a 2-store pilot |
| Threshold change | survives an 11.3% volume drop | **3.1%** observed last time |

**Second finding — marketing.** Blended LTV:CAC reads a healthy **2.20x**. Paid-only is **1.28x** —
because blended divides total spend by *all* customers including the 42% who arrive organically and
cost nothing, overstating paid efficiency by **72%**. At channel level, two channels sit at **0.56x
and 0.57x** and hold **46% of the marketing budget.**

#### How the workbook is verified

The tests load the generated `.xlsx` into **`formulas`, an independent Excel formula engine**,
evaluate it, and assert it agrees with the Python model cell by cell — with **zero error cells
anywhere.** There's also a test that fails if any value cell outside the Drivers sheet is a
hard-coded number rather than a formula.

> Verifying the Python that *wrote* the spreadsheet proves nothing about what a reader opens.

#### Files to read

| File | What's in it |
|---|---|
| `DECISION.md` | **Start here** — the one-page memo a director would read |
| `README.md` | Overview and how the workbook is verified |
| `METRIC_DEFINITIONS.md` | Which contribution margin to use for which question, and why |
| `LEARN.md` | Unit economics concepts + interview questions |
| `config/drivers.yml` | All 38 drivers with their basis |
| `src/model.py` | The CM ladder, basket distribution, cohorts, channels |
| `src/decisions.py` | The three proposals and their break-evens |
| `src/workbook.py` | Excel generation with live formulas |
| `outputs/unit_economics.xlsx` | **The deliverable** (generated by `make build`) |

---

### BA-3 · KPI Framework & Root-Cause Diagnosis

**Folder:** `ba3-kpi-root-cause/`
**Domain:** A B2B software company's customer support organisation ("Project ATLAS")

#### The problem

Support promises to resolve tickets within a time limit. The success rate fell from **95% to 86%**
over six months. The VP of Support wants **8 more engineers — ₹96 lakh a year.**

#### What it does

- Builds a **KPI tree** (what arithmetically determines the metric) and a **MECE issue tree** (what
  might have moved it)
- Tests **12 hypotheses in SQL**, each with its query, its numbers, and a verdict
- Decomposes the decline into components that **sum exactly to the observed gap**
- Costs the remedies on **cost and on capability**

**Scale:** 46,941 tickets over 12 months, generated with a **day-by-day priority queue simulation**

#### The key findings

**1. Four things were happening, and the VP's theory wasn't one of them.**

| Cause | Effect | Fixable by hiring? |
|---|---|---|
| A software upgrade quietly changed how the metric was calculated | **−2.71pp** | No — not a real decline |
| Customer mix shifted toward clients with stricter deadlines | **−4.11pp** | No — structural |
| One bad month from a release defect | **−5.36pp** | Already resolved itself |
| **The team's actual speed** | **+0.99pp** | They got **faster** |
| Interaction between mix and rate | +2.15pp | — |
| **Total** | **−9.06pp** | **residual: −2.78e-17** |

**75% of the decline (6.82pp) cannot be moved by hiring anyone.**

That residual — 0.0000000000000000278 — is the point. A decomposition that reconciles to machine
precision is falsifiable. A list of causes can always absorb one more item.

**2. The finding that ended the discussion.**

Top-tier customers have a **4-hour** resolution deadline. Nobody had asked: *is 4 hours even
possible?*

I measured only the hands-on work time — no queue wait, no waiting on the customer, a perfectly
staffed team responding instantly:

| Enterprise target | Ceiling (perfect operations) | Today | Clears 95%? |
|---|---|---|---|
| **4h (current)** | **85.60%** | 80.85% | ✗ |
| 6h | 95.34% | 92.67% | ✗ |
| **8h** | 98.36% | **97.20%** | **✓** |

> **14.40% of enterprise tickets take longer than 4 hours of actual work.** The contract penalty
> triggers below 95%. **The target has never been achievable at any staffing level** — extra capacity
> closes at most **4.75pp of a 14.15pp gap.**

The 4-hour commitment was agreed by Sales during contract negotiation **without a capacity model.**
Six months of pressure on that team was spent chasing a number that doesn't exist. At an 8-hour
target they're already at 97.20% today.

**3. The business case.**

Enterprise book: 34 accounts, ₹14.28 crore ARR, with a 5% monthly service credit below 95%
attainment. **Exposure: ₹71.4 lakh a year.**

Service credits are a **step function, not a gradient** — an option that closes most of the gap saves
nothing.

| Option | One-off | Recurring/yr | Achievable | Clears? | Steady-state |
|---|---|---|---|---|---|
| Add 8 permanent engineers | — | **₹96,00,000** | 85.60% | ✗ | **−₹96,00,000** |
| **Restate + re-baseline to 8h + prevent** | **₹12,50,000** | — | **97.20%** | **✓** | **+₹71,40,000** |
| Change nothing | — | — | 80.85% | ✗ | ₹0 |

A contractor burst to clear the backlog was costed at ₹17.6 lakh and **deliberately not
recommended** — the backlog was back to normal one month after the incident. It's the kind of remedy
that gets approved *because* it sounds proportionate.

**4. The bug worth knowing about.** My own test of "did the team get slower?" was **wrong the first
time.** I used the blended company-wide figure, which *fell* from 96.39% to 94.89% — so the test said
yes, the team got slower, approve the hiring. But that blended figure falls for exactly the same
mix-shift reason as the headline metric. Holding customer mix constant, **every tier had improved.**

> The aggregation trap the whole investigation existed to expose was sitting inside its own
> hypothesis test.

#### Files to read

| File | What's in it |
|---|---|
| `FINDINGS.md` | **Start here** — the memo, with what would change the recommendation |
| `README.md` | Overview and the ceiling finding |
| `METRIC_DICTIONARY.md` | Why "SLA attainment" was never one number, and the governance decision |
| `KPI_TREE.md` | KPI tree vs MECE issue tree — two diagrams people constantly confuse |
| `LEARN.md` | Root cause methodology + interview questions |
| `sql/00_definitions.sql` | The three clocks, defined once |
| `sql/01_hypotheses.sql` | **The audit trail** — 12 hypotheses with verdicts in SQL |
| `sql/02_sla_ceiling.sql` | The ceiling analysis — the decisive query |
| `src/decomposition.py` | The five-component identity |
| `src/business_case.py` | Options scored on cost **and capability** |
| `data/generate_tickets.py` | The queue simulation |

---

## 6. Complete file inventory

### data-engineering-portfolio (95 files)

```
README.md
.gitignore
.github/workflows/          de1-ci.yml, de2-ci.yml, de3-ci.yml

de1-batch-elt-warehouse/
├── README.md, LEARN.md, Makefile, pyproject.toml, requirements.txt
├── docs/architecture.md
├── config/                 pipeline.yml, pipeline.ci.yml
├── src/                    utils.py, generate_source.py, warehouse.py,
│                           extract.py, load.py, quality.py, pipeline.py
├── dbt_project/
│   ├── dbt_project.yml, profiles.yml
│   ├── macros/             generate_schema_name.sql, generic_tests.sql, string_utils.sql
│   ├── models/staging/     _sources.yml, _staging.yml, stg_customers.sql,
│   │                       stg_orders.sql, stg_order_items.sql,
│   │                       stg_products.sql, stg_sellers.sql
│   ├── models/intermediate/ int_order_totals.sql
│   ├── models/marts/       _marts.yml, dim_customer.sql, dim_date.sql,
│   │                       dim_product.sql, dim_seller.sql (SCD2),
│   │                       fct_orders.sql, fct_order_items.sql
│   ├── models/audit/       _audit.yml, rejected_records.sql
│   └── tests/              assert_order_totals_reconcile.sql,
│                           assert_scd2_windows_contiguous.sql,
│                           assert_no_fanout_from_scd2_join.sql,
│                           assert_delivery_timeline_sane.sql
└── tests/test_pipeline.py

de2-incremental-api-ingestion/
├── README.md, LEARN.md, Makefile, pyproject.toml, requirements.txt
├── docs/architecture.md
├── config/ingestion.yml
├── src/                    utils.py, models.py, client.py, archive.py,
│                           extract.py, load.py, warehouse.py, pipeline.py
└── tests/                  conftest.py, test_validation.py, test_load.py,
                            test_client.py, test_archive_and_extract.py

de3-data-quality-framework/
├── README.md, LEARN.md, Makefile, pyproject.toml, requirements.txt
├── docs/architecture.md
├── config/                 checks.yml, suppressions.yml
├── dq/                     types.py, registry.py, config.py, engine.py,
│                           store.py, profiler.py, report.py, cli.py
├── dq/checks/              basic.py, anomaly.py
├── demo/generate_demo_data.py
└── tests/                  conftest.py, test_basic_checks.py,
                            test_anomaly_checks.py, test_engine_and_config.py,
                            test_demo_detection.py
```

### data-analyst-portfolio (54 files)

```
README.md
.gitignore
.github/workflows/          da1-ci.yml, da2-ci.yml, da3-ci.yml

da1-ecommerce-analytics/
├── README.md, INSIGHTS.md, LEARN.md, Makefile, pyproject.toml, requirements.txt
├── sql/                    00_metric_definitions.md, 01_sessionize.sql,
│                           02_funnel.sql, 03_cohort_retention.sql, 04_rfm.sql,
│                           05_mix_effect_decomposition.sql, 06_channel_quality.sql
├── data/generate_events.py
├── dashboard/POWERBI_SPEC.md
├── src/run.py
└── tests/test_analytics.py

da2-ab-testing/
├── README.md, INSIGHTS.md, LEARN.md, Makefile, pyproject.toml, requirements.txt
├── src/                    design.py, checks.py, analysis.py,
│                           corrections.py, simulate.py, run.py
└── tests/test_ab.py

da3-churn-analysis/
├── README.md, INSIGHTS.md, LEARN.md, Makefile, pyproject.toml, requirements.txt
├── data/generate_subscriptions.py
├── src/                    churn_definition.py, features.py, model.py,
│                           evaluation.py, targeting.py, run.py
└── tests/test_churn.py
```

### business-analyst-portfolio (59 files)

```
README.md
.gitignore
.github/workflows/          ba1-ci.yml, ba2-ci.yml, ba3-ci.yml

ba1-requirements-package/
├── 01-stakeholder-analysis-and-raci.md
├── 02-process-models.md
├── 03-business-requirements.md
├── 04-functional-requirements.md
├── 05-user-stories.md
├── 06-non-functional-requirements.md
├── 07-data-model.md
├── 08-uat-test-cases.md
├── 09-traceability-matrix.md
├── 10-release-plan.md
├── 11-change-request.md
├── README.md, LEARN.md, Makefile, pyproject.toml, requirements.txt
├── tools/validate_traceability.py
└── tests/test_package.py

ba2-unit-economics/
├── README.md, DECISION.md, METRIC_DEFINITIONS.md, LEARN.md
├── Makefile, pyproject.toml, requirements.txt
├── config/drivers.yml
├── src/                    drivers.py, model.py, decisions.py, workbook.py, run.py
└── tests/test_model.py

ba3-kpi-root-cause/
├── README.md, FINDINGS.md, METRIC_DICTIONARY.md, KPI_TREE.md, LEARN.md
├── Makefile, pyproject.toml, requirements.txt
├── config/scenario.yml
├── data/generate_tickets.py
├── sql/                    00_definitions.sql, 01_hypotheses.sql,
│                           02_sla_ceiling.sql, 03_incident_isolation.sql
├── src/                    warehouse.py, decomposition.py, business_case.py, run.py
└── tests/test_analysis.py
```

### What each document type contains

Every project has the same document set, so once you know the pattern you can navigate any of them:

| File | Purpose | Read it when |
|---|---|---|
| `README.md` | What the project is, the headline finding, how to run it | Always first |
| `LEARN.md` | Concepts explained from scratch + interview Q&A | You want to *understand*, not just run |
| `INSIGHTS.md` (DA only) | The findings written up as an analyst would present them | You want the business story |
| `DECISION.md` / `FINDINGS.md` (BA) | The one-page memo a director would read | You want the recommendation |
| `METRIC_DEFINITIONS.md` / `METRIC_DICTIONARY.md` | How every metric is defined and why it matters | Before disputing any number |
| `docs/architecture.md` (DE only) | Structure and design decisions | Before reading the code |
| `Makefile` | Every runnable command | To run anything |
| `config/*.yml` | All inputs, each with a stated basis | To change assumptions |

---

## 7. Reading order — how to understand a project fast

**If you have 5 minutes:** read the project's `README.md`. The headline finding is in the first
screen.

**If you have 30 minutes:** `README.md` → `LEARN.md` → run `make all` and read the output.

**If you have 2 hours and want to genuinely understand it:**

1. `README.md` — what and why
2. `LEARN.md` — the concepts, explained from scratch
3. `config/*.yml` — the inputs, so you know what's assumed
4. Run `make all`, read the printed output alongside the README
5. The one or two source files the README points at as "the important part"
6. `tests/` — the tests state what the project *claims*, in executable form
7. Change a config value, re-run, watch what moves

**Step 7 is the one people skip and it's the most instructive.** Change
`orders_per_store_per_day` in BA-2 or `incrementality` in BA-3 and watch the recommendation flip.

**If you only read three files in the whole portfolio:**

1. `da1-ecommerce-analytics/sql/05_mix_effect_decomposition.sql` — Simpson's paradox
2. `da2-ab-testing/src/simulate.py` — the peeking simulation
3. `ba3-kpi-root-cause/sql/02_sla_ceiling.sql` — the unachievable-target finding

---

## 8. The nine bugs found and documented

This section is the most useful part of the portfolio, and it's deliberate. An interviewer who sees
only successes assumes you got lucky or hid the mess. One who sees *"here's what I got wrong and how
I caught it"* concludes you actually did the work.

| # | Project | The bug | How it was caught |
|---|---|---|---|
| 1 | DE-1 | Cache eviction defect made backfill 5.2x slower than necessary (31.2s → 6.0s for 61 days) | Profiling the backfill loop |
| 2 | DE-3 | **Every Saturday** flagged as an anomaly (z = 5.0) because weekend volume runs ~18% above weekdays and the baseline mixed both | The false positive recurred weekly — too regular to be real |
| 3 | DA-1 | `NTILE` ranking was **non-deterministic** — tied values were assigned to different quartiles on each run, so RFM segments changed between runs | md5-hashing the output and finding it differed run to run |
| 4 | DA-1 | A planted trend of +0.55pp/year was **below the monthly sampling noise floor** (SE ≈ 0.5pp), so it was statistically undetectable | Comparing the effect size against the standard error |
| 5 | DA-3 | **Selection bias inverted a coefficient.** Payment failures were only generated for active users, so the variable secretly encoded "is active" and appeared to *reduce* churn (12.6% vs 20.7%) | Cross-tabulating the raw relationship instead of trusting the model |
| 6 | BA-1 | **Four Must-priority requirements had full traceability and UAT coverage but zero acceptance criteria.** One would have shipped a 15.4% EMI calculation error | Writing a validator that compared each story's declared coverage against the matrix |
| 7 | BA-2 | `days_per_month` was never registered as a named range, causing a **`#REF!` cascade** through every volume-dependent cell — while CM1 and CM2 stayed correct because they're volume-independent | Scanning the entire workbook for error cells |
| 8 | BA-3 | A strict priority queue **starved the lowest tier** — standard tickets lost 35pp of attainment to queue wait alone. A pathology, not a backlog | The magnitude was implausible; real queues have fairness mechanisms |
| 9 | BA-3 | **My own hypothesis test returned the wrong verdict**, because it used a blended figure contaminated by the exact mix effect the investigation existed to expose | Cross-checking the test result against the decomposition |

**A pattern worth noticing:** bugs 5, 7, 8 and 9 all produced *plausible-looking output.* Nothing
crashed. The numbers looked reasonable. That's the dangerous category, and the only defence is
checking claims independently rather than trusting the pipeline.

---

## 9. Concepts glossary

Everything you'd need to look up, in plain language.

### Data engineering

| Term | Meaning |
|---|---|
| **ETL / ELT** | Extract-Transform-Load vs Extract-Load-Transform. ELT loads raw data first and transforms it in the warehouse — it won because compute got cheap |
| **Star schema** | Warehouse design: central "fact" tables (events) surrounded by "dimension" tables (context) |
| **Fact / dimension** | A fact is something that happened (an order). A dimension is context (the customer, the date, the product) |
| **Grain** | What one row of a table represents. "One row per order line" is a grain |
| **Idempotency** | Running the same operation twice gives the same result as running it once. Critical for pipelines that might crash mid-run |
| **SCD Type 1 / Type 2** | Slowly Changing Dimension. Type 1 overwrites old values; Type 2 keeps full history with valid-from/valid-to dates |
| **Watermark / high-water mark** | The bookmark of "how far did I get last time," so you only fetch new data |
| **Late-arriving data** | Records that show up or get modified after you first processed their time period |
| **Backfill** | Processing historical data, usually one period at a time |
| **Partition** | A slice of data processed independently, usually by date |
| **dbt** | A tool for transforming data in a warehouse using SQL, with built-in testing and dependency management |
| **Quarantine / rejected records** | Rows that fail validation, kept in a separate table rather than dropped silently |
| **PSI (Population Stability Index)** | A measure of how much a distribution has shifted between two periods |
| **Modified z-score / MAD** | An outlier measure using the median instead of the mean, so it isn't distorted by the outlier it's trying to detect |

### Data analytics

| Term | Meaning |
|---|---|
| **Sessionisation** | Grouping a stream of individual actions into "visits," usually by a 30-minute inactivity gap |
| **Funnel** | The sequence of steps toward a goal, and the drop-off at each step |
| **Cohort analysis** | Grouping users by when they joined and tracking each group over time |
| **RFM** | Recency, Frequency, Monetary — a simple, durable customer segmentation |
| **Simpson's paradox** | A trend appears in every subgroup but reverses when the groups are combined, because the group sizes changed |
| **Mix vs rate effect** | Splitting a change into "the composition shifted" (mix) and "performance changed within each group" (rate) |
| **p-value** | The probability of seeing a result this extreme if there were genuinely no effect. **Not** the probability that your hypothesis is true |
| **Confidence interval** | A range of plausible values for the true effect. More informative than a p-value |
| **Statistical power** | The probability of detecting an effect that genuinely exists |
| **MDE** | Minimum Detectable Effect — the smallest effect your sample size can reliably find |
| **Type I / Type II error** | False positive (seeing an effect that isn't there) / false negative (missing one that is) |
| **Sample ratio mismatch (SRM)** | Your 50/50 split didn't come out 50/50 — a sign the experiment infrastructure is broken |
| **Guardrail metric** | A metric you refuse to damage, even in exchange for a win on your primary metric |
| **CUPED** | Using pre-experiment data to reduce variance, making the test more sensitive at the same sample size |
| **Peeking / optional stopping** | Checking results repeatedly and stopping when they look good. Inflates false positives dramatically |
| **Bonferroni / Benjamini-Hochberg** | Corrections for testing many hypotheses at once. Bonferroni is strict; BH is less conservative |
| **Bootstrap** | Estimating uncertainty by resampling your data thousands of times, without assuming a distribution |
| **ROC-AUC** | How well a model *ranks* — 0.5 is random, 1.0 is perfect |
| **PR-AUC** | Precision-Recall AUC. More informative than ROC-AUC when the positive class is rare |
| **Brier score / ECE** | Whether predicted probabilities are *accurate* (calibration), not just well-ordered |
| **Calibration** | If the model says 70%, does it happen 70% of the time? |
| **Lift** | How much better than random your top-scored group is |
| **Data leakage** | Information from the future accidentally available to the model at training time |
| **Selection bias** | Your sample isn't representative, so a variable measures something other than what you think |

### Business analysis

| Term | Meaning |
|---|---|
| **BRD / FRD / SRS** | Business Requirements Document (what the business needs), Functional Requirements Document / Software Requirements Specification (what the system must do) |
| **Functional vs non-functional** | What the system does vs how well it does it (speed, security, availability) |
| **Business rule** | A policy that exists independently of any system. The functional requirement is what the system does about it |
| **Decision table** | A grid resolving every combination of conditions. Forces you to define the cases prose would skip |
| **Gherkin** | The Given/When/Then format for writing testable acceptance criteria |
| **RACI** | Responsible, Accountable, Consulted, Informed. Exactly one Accountable per activity |
| **RAID log** | Risks, Assumptions, Issues, Dependencies |
| **AS-IS / TO-BE** | Current process vs proposed process |
| **Traceability matrix (RTM)** | Proof that every business need maps to a requirement, a story, and a test |
| **MoSCoW** | Must / Should / Could / Won't. Only works if "Must" means the release is worthless without it |
| **Elicitation** | The techniques for discovering requirements: interviews, workshops, job shadowing, document analysis |
| **UAT** | User Acceptance Testing — the business confirming the system does what they asked |
| **Change control** | The process for assessing a change's cost and impact before absorbing it |
| **KPI tree** | Decomposition of what arithmetically determines a metric |
| **Issue tree** | The space of candidate explanations for a movement. Must be MECE |
| **MECE** | Mutually Exclusive, Collectively Exhaustive — no overlaps, no gaps |
| **Contribution margin (CM1/CM2/CM3)** | Profit after progressively more cost layers. Which one you use changes the decision |
| **Unit economics** | The profit and loss of a single transaction |
| **LTV : CAC** | Lifetime Value vs Customer Acquisition Cost. Above 1.0x means the customer pays for themselves |
| **Blended vs paid CAC** | Blended divides spend by *all* customers including organic ones you didn't pay for — so it flatters paid performance |
| **Break-even analysis** | The value at which a decision flips. More robust than a point estimate |
| **Sensitivity analysis** | How the answer changes as assumptions change |
| **Payback period** | How long until an investment repays itself |
| **Capex vs opex** | One-off capital spend vs recurring operating cost. A recurring cost is much worse than the same amount once |
| **Stock vs flow** | A level (backlog) vs a rate (throughput). They need different remedies |
| **Step function** | A benefit that only arrives past a threshold. Closing 90% of the gap saves nothing |

---

## 10. Verified numbers reference

Every figure below is reproducible by running the project. Useful for a quick check.

### Data Engineering

| Metric | Value |
|---|---|
| DE-1 backfill | 151,326 rows · 629 partitions · 71.1s · 3,150 loads · 0 failures |
| DE-1 dbt | 12 models + 98 tests = 110 nodes, pass in 3.0s |
| DE-1 idempotency | 453 duplicates injected → exactly 453 rows superseded |
| DE-1 late arrivals | 65% of orders updated >7 days after purchase (max 96 days) |
| DE-1 SCD2 justification | Type 1 misstates commission 1.87% (₹9.88Cr vs ₹9.69Cr) |
| DE-1 performance fix | Backfill 31.2s → 6.0s for 61 days (5.2x) |
| DE-2 initial load | 4,889 events · 24.8s · 63 API calls · p95 514ms |
| DE-2 adaptive chunking | 7 of 21 windows bisected → 28 windows total |
| DE-2 archive | 49 payloads · 470 KB · 7.33x gzip · checksums verify |
| DE-2 replay | 4,889 events in 1.1s · zero API calls · 22x faster |
| DE-2 revision rate | **81.6% revised >1h after event**; 34.3% >24h; median 660 min |
| DE-2 review lag | Reviewed 980 min vs automatic 25 min (39x) |
| DE-3 backtest | 1,080 evaluations · 7/7 incidents detected · 0 false positives |
| DE-3 scorecard | Static rules caught 3/7; baseline caught the 4 misses |
| DE-3 example miss | Null rate 43.20% vs 7.78% baseline (z = 43.7), static max 0.50 passed |
| DE-3 seasonality bug | Weekend volume ~18% above weekdays caused weekly false positives |

### Data Analytics

| Metric | Value |
|---|---|
| DA-1 scale | 318,840 events · 39,829 users · 169,867 sessions · ₹13.05M |
| DA-1 sessionisation | Ground truth 169,867 = derived 169,867 · 0 splits · 0 merges |
| DA-1 funnel | 169,867 → 97,450 (57.37%) → 31,448 (32.27%) → 14,704 (46.76%) → 5,371 (36.53%) |
| DA-1 overall conversion | 3.162% |
| DA-1 Simpson's paradox | Aggregate 3.357% → 2.961%; desktop 4.091→4.742, mobile 2.091→2.428, tablet 1.894→3.875 |
| DA-1 mobile share | 31.3% → 75.1% |
| DA-1 decomposition | Rate +0.617 · Mix −0.877 · Interaction −0.135 = **−0.3956pp** |
| DA-1 device gap | Cart→checkout: desktop 54.83% vs mobile 41.36% (13.47pp) |
| DA-1 opportunity | ₹1.88M = 14.4% of revenue (stated as upper bound) |
| DA-1 RFM | Champions 677 users (15.2%) → 31.5% of revenue |
| DA-2 sample size | 18,872/arm · 37,744 total · 12.6 days |
| DA-2 SRM check | 19,910 / 20,090 = 0.5022 · χ² = 0.81 · p = 0.368 (pass) |
| DA-2 primary metric | 7.644% → 8.895% = **+1.251pp (+16.4%)** · CI [+0.711, +1.790] · p < 0.0001 |
| DA-2 guardrail | Checkout errors 1.607% → 2.140% = **+33.2%** · p = 0.0001 → **do not ship** |
| DA-2 CUPED | ρ = 0.838 → variance −70.3% = **3.37x sample size** |
| DA-2 CUPED contrast | Revenue ρ = 0.118 → only −1.4% |
| DA-2 multiple testing | 19 tests · FWER 62% · 6 raw → Bonferroni 4, BH 5 |
| DA-2 peeking | 2,000 A/A tests: **5.2% fixed-horizon vs 19.7% peeking (3.8x)** |
| DA-3 scale | 60,000 users · 269,849 user-months · 857,349 orders · ₹985.95M |
| DA-3 eligibility funnel | 60,000 → 27,009 → 22,930 → **9,566** |
| DA-3 churn rate | 19.08% (1,825 / 9,566) |
| DA-3 model | ROC-AUC **0.8317** · PR-AUC 0.6393 · Brier 0.1053 · ECE **0.0165** |
| DA-3 vs baselines | Constant 0.500 · hand-rule 0.726 · **GBM 0.8300 (0.0017 worse)** |
| DA-3 lift | Top decile 77.0% churn = **4.03x**; top 3 deciles = 72.5% of churners |
| DA-3 key driver | Late delivery rate OR **10.21** [4.11, 25.34] |
| DA-3 break-even | p = 250 / (0.25 × 4,000) = **0.250**; optimal **0.203** |
| DA-3 policy comparison | All: **−₹169,500** · p>0.50: ₹174,250 · **p>0.203: ₹185,500** |
| DA-3 actionability | 66.4% of flagged users map to a specific operational cause |

### Business Analysis

| Metric | Value |
|---|---|
| BA-1 package | 12 docs · 8 BRs · 47 FRs · 8 business rules · 30 NFRs · 19 stories · 53 UAT cases · 3 CRs |
| BA-1 validation | 13 rules · 25 tests · **12 real defects found** |
| BA-1 worst defect | 4 Must FRs fully traced with **zero acceptance criteria** |
| BA-1 EMI error | Flat rate ₹19,722.22 vs reducing balance ₹17,088.81 = **15.4% higher** |
| BA-1 baseline | 4,612 applications · 41.0% completion · 6.8-day TAT · 2,690 hrs/month ≈ 16 FTE |
| BA-1 business case | ₹71,00,000 cost · **₹5,16,84,000 annual benefit** · 1.6-month payback |
| BA-1 automation backtest | **73.4%** auto-decisioned (78.1% before CR-002) · variance −1.2pp |
| BA-1 rejected CR | 62 points vs 15 available · ₹43,07,000/month cost of delay |
| BA-2 model | 38 drivers · 9 sheets · all live formulas · 47 tests · zero error cells |
| BA-2 ladder | NOV ₹448.97 · CM1 ₹115.62 (25.75%) · CM2 ₹63.48 (14.14%) · CM3 ₹26.97 (6.01%) · EBITDA −₹6.03 |
| BA-2 store expansion | Revenue **+7.7%** · CM3 **−₹14.6L/month** · capex ₹4.20Cr · **REJECT** |
| BA-2 break-even | Needs 63.7% incrementality; pilot measured **43.0%** |
| BA-2 density effect | Orders/store/day 420 → 362; fixed cost/order ₹36.51 → ₹42.38 |
| BA-2 threshold change | Revenue **−1.1%** · CM3 **+₹35.6L/month** · **APPROVE** |
| BA-2 retail media | CM3 **+₹39.4L/month** · only 18.6% of uplift needed · **APPROVE** |
| BA-2 non-additivity | Sum of parts ₹9.00Cr vs modelled together ₹8.82Cr (interaction −₹0.18Cr) |
| BA-2 EBITDA impact | −₹4.37Cr → **+₹4.45Cr** |
| BA-2 channel finding | Blended 2.20x vs paid-only 1.28x (**72% overstatement**) |
| BA-2 bad channels | affiliate 0.56x · OOH 0.57x · **46% of spend** · both flip >1.0x on CM2 |
| BA-3 scale | 46,941 tickets · 12 months · day-by-day queue simulation |
| BA-3 three clocks | Strict 85.96% · Governed 88.67% · Work 94.90% |
| BA-3 decomposition | Definition −2.71 · Mix −4.11 · Backlog −5.36 · Performance **+0.99** · Interaction +2.15 = **−9.06pp** |
| BA-3 residual | **−2.78e-17** |
| BA-3 not fixable by hiring | **6.82pp of 9.06pp = 75%** |
| BA-3 ceiling finding | 4h target ceiling **85.60%** vs 95% threshold; capacity closes 4.75pp of 14.15pp |
| BA-3 viable target | 8h → **97.20%** today, 2.20pp headroom |
| BA-3 incident month | Backlog 146 (4.6x baseline) · attainment 73.39% · drags half-average 3.50pp |
| BA-3 exposure | 34 accounts · ₹14.28Cr ARR · 5% credit → **₹71.4L/year** |
| BA-3 business case | Executive ₹96L/yr (cannot clear) vs recommended **₹12.5L one-off** |
| BA-3 hypotheses | 12 tested: 5 eliminated · 2 partial · 4 retained · 1 reframed |

---

## 11. What is deliberately NOT here

Being straight about the gaps, because a portfolio that claims completeness invites someone to find
the hole themselves.

### Not included, and why

| Missing | Note |
|---|---|
| **Airflow / orchestration** | The pipelines run via `Makefile` and CLI. Production would use Airflow, Dagster or Prefect. DE-1's stages (`extract`, `load`, `quality`, `dbt`) are already separable into tasks |
| **Spark / distributed compute** | Data volumes here are thousands to hundreds of thousands of rows. DuckDB handles this comfortably; Spark would be pure overhead |
| **Cloud infrastructure** | No AWS/GCP/Azure. Everything runs locally so that anyone can reproduce it without an account or a bill |
| **A built Power BI dashboard** | DA-1 ships a `POWERBI_SPEC.md` specifying the dashboard, but the dashboard itself is not built |
| **Streaming / Kafka** | All batch. Streaming is a different architecture and a different set of problems |
| **Real production data** | All datasets are generated from seeded configs. This is a deliberate trade-off — see below |
| **JIRA / Confluence** | The BA artefacts are Markdown files rather than JIRA tickets |

### On synthetic data

Every dataset except DE-2's earthquakes is generated from a seeded configuration file. This is a
genuine limitation and also a deliberate choice:

**The cost:** these are not real business volumes, and real data is messier in ways no generator
reproduces.

**The benefit:** because each effect is planted with a known size, the analysis can be **verified**
rather than merely believed. When DA-1 claims sessionisation is correct, it's compared against
ground truth — 169,867 = 169,867 exactly. When BA-3 claims a four-way decomposition is right, the
components are checked against the planted sizes *and* required to sum to the observed gap within
1e-12. With real data neither check is possible; you'd have to take the analysis on trust.

**Where the numbers are anchored to reality:** BA-2's unit economics are calibrated against published
Blinkit and Zepto figures. BA-3's regulatory context and BA-1's RBI Digital Lending Guidelines
obligations are cited to real sources. DE-2 uses a genuinely live external API.

---

## Contact

**Pavan Kumar Eslavath** · IIT Madras
GitHub: [pavankumar05-eslavath](https://github.com/pavankumar05-eslavath)

- [data-engineering-portfolio](https://github.com/pavankumar05-eslavath/data-engineering-portfolio)
- [data-analyst-portfolio](https://github.com/pavankumar05-eslavath/data-analyst-portfolio)
- [business-analyst-portfolio](https://github.com/pavankumar05-eslavath/business-analyst-portfolio)

*Every figure in this document is reproducible by cloning the relevant repository and running
`make all`.*
