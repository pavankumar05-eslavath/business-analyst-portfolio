# BA-2 · Quick-commerce unit economics and three investment decisions

A driver-based P&L model for a challenger quick-commerce operator (48 dark stores,
3 Indian cities), used to evaluate three real proposals — and to reject the most
exciting one.

```bash
make all     # print the analysis and build outputs/unit_economics.xlsx
make test    # 47 tests, including evaluating the delivered Excel file
```

Runs in about 4 seconds. No database, no API keys.

---

## The finding

**Revenue and contribution move in opposite directions on two of the three proposals.**
Judged on revenue growth — which is how both were pitched — the recommendations invert.

| Proposal | Orders | Revenue | Monthly CM3 | Verdict |
|---|---|---|---|---|
| Open 12 dark stores in existing cities | **+7.7%** | **+7.7%** | **−₹14.6 L** | ❌ REJECT |
| Raise free-delivery threshold ₹299 → ₹499 | −3.1% | −1.1% | **+₹35.6 L** | ✅ APPROVE |
| Raise retail media income ₹14 → ₹22/order | 0.0% | +1.7% | **+₹39.4 L** | ✅ APPROVE |

**Store count is not scale — order density is.** Dark-store fixed cost is incurred per
store (₹4.60 lakh/month). In a city already covered, most of a new store's volume moves
off a neighbour, so orders per store — the denominator the fixed cost is spread over —
falls from 420 to 362. Fixed cost per order rises from ₹36.51 to ₹42.38 and CM3 per order
drops from ₹26.97 to ₹22.81, on top of ₹4.20 Cr of capex that never pays back.

The two approved proposals together move annual EBITDA from **−₹4.37 Cr to +₹4.45 Cr with
no capital expenditure.**

Full reasoning: **[DECISION.md](DECISION.md)** — the one-page memo a director would
actually read.

## Every decision states the break-even value of the driver it turns on

This is the part that survives disagreement. Nobody has to accept my incrementality
estimate if I can tell them the threshold and what we measured against it.

| Proposal | Break-even | Observed | Margin |
|---|---|---|---|
| Store expansion | incrementality **63.7%** | pilot measured **43.0%** | ❌ misses by 20.7 pp |
| Threshold change | volume decline **11.3%** | last move produced **3.1%** | ✅ clears by 8.2 pp |
| Retail media | **18.6%** of the uplift must land | not yet measured | cost bounded at ₹9 L/month |

**Incrementality was measured against neighbouring store volume, not against forecast.**
Neighbours lost volume equal to 57% of the pilot stores' throughput. Measured against
forecast the pilot would have reported 100% incrementality, and a ₹4.2 crore capital
programme that *reduces* contribution would have been approved.

## The deliverable is a working model, not a screenshot of one

`outputs/unit_economics.xlsx` — 9 sheets, **every calculated cell is a formula**
referencing a named range that resolves back to the Drivers sheet. Change
`orders_per_store_per_day` and the basket distribution, the CM ladder, all three
decisions, six cohort curves, both sensitivity grids and the scenario block recalculate.

| Sheet | What it does |
|---|---|
| `Guide` | How to use it |
| `Drivers` | 38 inputs, each with its unit **and the basis for the number** |
| `Basket` | Lognormal basket distribution — resolves a threshold into fee-paying share and average basket, live, via `NORM.S.DIST` |
| `UnitEconomics` | CM1 / CM2 / CM3 ladder in four columns: base plus one per proposal |
| `Cohort` | 24-month retention and cumulative contribution, per channel |
| `Channels` | CAC, LTV, LTV:CAC — blended, paid-only and per channel |
| `Decisions` | The three proposals with impacts and break-evens |
| `Scenarios` | Base / bull / bear |
| `Sensitivity` | Two live two-way tables |

### How I know the spreadsheet is right

The test suite loads the generated `.xlsx` into **`formulas`, an independent Excel
formula engine**, evaluates it, and asserts it agrees with the Python model cell by named
cell — and that there are **zero error cells anywhere in the workbook**.

```
test_workbook_has_no_error_cells                 PASSED
test_workbook_basket_sheet_matches_python        PASSED
test_workbook_ladder_matches_python              PASSED
test_workbook_decision_columns_match_python      PASSED
test_workbook_reproduces_the_verdicts            PASSED
test_workbook_channel_ltv_and_ratios_match_python PASSED
test_calculation_sheets_contain_no_hard_coded_numbers PASSED
```

Verifying the Python that *wrote* the spreadsheet proves nothing about what a reader
opens. A model delivered as a spreadsheet has to be verified as a spreadsheet.

The last test is the one I would point at in a review: it fails if any value cell outside
the Drivers sheet is a constant rather than a formula. A single hard-coded number means
the Drivers sheet is no longer the whole input surface, and a reviewer can no longer trust
any of it.

## The base economics, checked against public disclosure

| Line | Per order | % of NOV | Benchmark |
|---|---|---|---|
| Net order value | ₹448.97 | 100.0% | Blinkit net AOV ~₹525 (we are a smaller-basket challenger) |
| **CM1** gross contribution | **₹115.62** | **25.75%** | Blinkit gross profit margin 26.6% |
| **CM2** store contribution | **₹63.48** | **14.14%** | ~13% for a mature dark store |
| **CM3** fully loaded store | **₹26.97** | **6.01%** | — |
| **EBITDA** | **−₹6.03** | **−1.34%** | Zepto −₹78.75/order FY26, −₹3.02 in Q1 FY26 |

Contribution-positive, EBITDA-negative — which is the actual position of the Indian
quick-commerce sector. Break-even sits at **460 orders/store/day**, 9.5% above today.

Sources: [Blinkit Q4 FY26 metrics](https://quashbugs.com/blog/blinkit-surpasses-zomato-in-quick-commerce) ·
[gross margin](https://www.livemint.com/market/mark-to-market/eternal-blinkit-q3-profit-turning-point-quick-commerce-zomato-11769066817033.html) ·
[dark store benchmarks](https://sacra.com/chat/h/536e9b12-72cb-4b5e-bc0c-372ea2aea43c/) ·
[Zepto per-order economics](https://moneyflowindia.substack.com/p/moneyflow-india-deep-dive-3-zepto).
*Content paraphrased from these sources for licensing compliance. Company, volumes and
cost base are constructed; the benchmarks they are calibrated against are real.*

## A second finding, larger than all three proposals

**Blended LTV:CAC 2.20x reads healthy. Paid-only LTV:CAC is 1.28x.**

Blended CAC divides total spend by *all* acquired customers, including the 42% who arrive
organically and cost nothing — overstating paid efficiency by **72%**, structurally rather
than by accident. The more organic demand a brand has, the better its paid marketing
looks.

At channel level, **`affiliate_coupon` (0.56x) and `offline_ooh` (0.57x) hold 46% of the
marketing budget — ₹1.07 Cr a month — and neither pays back within 24 months.**
Coupon-acquired customers place 11.2 orders over 24 months against 22.6 for organic.

> ⚠️ **Both clear 1.0x on CM2 (1.31x, 1.34x) and fail on CM3.** The same spend is
> defensible or not depending on which contribution margin the deck uses. That is why
> **[METRIC_DEFINITIONS.md](METRIC_DEFINITIONS.md)** exists and fixes CM3 as the company
> standard for funding decisions.

## Two modelling conventions that decide the answers

**1. Fixed costs are fixed in rupees, not per order.** Store rent, central overhead and
the marketing budget are stated per order in the driver file for readability, then
converted to absolute monthly amounts and held there whenever volume changes. Holding a
per-order overhead *rate* constant is what makes store expansion look free — the fixed
cost silently follows the new order count instead of staying with the new store count.
Under that error the expansion moves from −₹14.6 lakh/month to apparently positive.
There is a test that fails if anyone "simplifies" it.

**2. The basket distribution is modelled, not averaged.** A free-delivery threshold acts
on the distribution of basket values. You cannot evaluate a threshold change with an
average order value, because the whole mechanism is about which side of the threshold each
order falls on.

## Layout

```
config/drivers.yml         38 drivers, each with a stated basis. The only inputs.
src/drivers.py             Load and validate. A driver without a basis fails the build.
src/model.py               Basket distribution, CM ladder, cohorts, channels
src/decisions.py           The three proposals, break-evens, scenarios, sensitivity
src/workbook.py            Excel generation with live formulas
src/run.py                 CLI
tests/test_model.py        47 tests
METRIC_DEFINITIONS.md      Which CM to use for which question, and why
DECISION.md                The memo
LEARN.md                   How it fits together, plus interview questions
```

## What this is not

- Not a real company's P&L. Volumes and cost base are constructed to be internally
  consistent and calibrated to published benchmarks — not sampled from a live business.
- Not a forecast. It is a decision model: it exists to compare options and to state what
  would change the answer.
- Not a dashboard. No charts. Every claim here is a number with a break-even next to it.
