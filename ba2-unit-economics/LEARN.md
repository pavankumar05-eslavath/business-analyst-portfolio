# LEARN · BA-2 Unit Economics

How the model is put together, the three ideas worth taking from it, and the interview
questions it invites.

---

## 1. What a driver-based model is, and why it matters

A driver-based model separates **inputs** from **logic**. Every number lives in one place
(`config/drivers.yml`), and everything else is a calculation referencing it.

```
config/drivers.yml          38 drivers, each with value + unit + BASIS
        |
        v
src/model.py                CM ladder, basket distribution, cohorts, channels
        |
        +--> src/decisions.py     three proposals, break-evens, sensitivity
        |
        +--> src/workbook.py      the same logic as live Excel formulas
```

The test that matters most is not that the arithmetic is right. It is
`test_calculation_sheets_contain_no_hard_coded_numbers`, which fails if any value cell
outside the Drivers sheet is a constant.

**Why that test earns its place:** the promise of a driver-based model is "change one cell
and everything updates." One hard-coded number breaks that promise silently. A reviewer who
finds a constant buried in a calculation now has to check every other cell too, because
they can no longer trust that the Drivers sheet is the whole input surface. The property is
binary, so it deserves an automated check rather than a convention.

### Each driver carries a `basis`, and it is enforced

Validation fails if any driver has an empty basis. "Where did this number come from" is the
first question in any finance review, and the model should answer it without me in the
room. Drivers are also tagged:

- **ASSUMPTION** (4 of them) — judgement, not measured. These are what the sensitivity
  analysis is built around.
- **MEASURED** (2) — `incrementality` and `observed_volume_response`. Both recommendations
  turn on these, which is the point: the decisions rest on the two numbers we actually have
  evidence for.

---

## 2. The CM ladder, and the line that decides arguments

| Level | Stops before | Answers |
|---|---|---|
| **CM1** | variable fulfilment | Are our buying terms and ancillary income any good? |
| **CM2** | dark-store fixed cost | Is this store operating well? |
| **CM3** | central overhead + marketing | Does this store earn its keep? |
| **EBITDA** | — | Is the company viable? |

The split that matters is **CM2 → CM3**. Two acquisition channels in this model clear the
1.0x LTV:CAC hurdle on CM2 and fail on CM3 — same customers, same spend, opposite decision,
46% of the marketing budget riding on it.

**The lesson generalises past this model.** When a metric has more than one defensible
definition, the definition becomes a lever. Whoever picks it picks the answer. The fix is
not a better calculation, it is `METRIC_DEFINITIONS.md`: decide in writing, in advance,
which line the company makes decisions on.

The same trap appears a second time, in a completely different place:

| Lever | CM3/order | EBITDA/order |
|---|---|---|
| +1.0pp gross margin | **+₹4.49** | +₹4.49 |
| +40 orders/store/day | +₹3.17 | **+₹6.04** |

Margin wins on CM3; density wins on EBITDA. Density does double duty — it lifts CM3 *and*
dilutes fixed central overhead across more orders — while margin only does the first. **An
earlier draft of my own analysis claimed density beat margin outright.** That was false on
CM3, and it survived until I computed both instead of asserting one. There is now a test
pinning both directions.

---

## 3. The three ideas worth taking from this project

### 3.1 Per-unit metrics and aggregate outcomes can point in opposite directions

The store expansion raises orders 7.7% and revenue 7.7% while *reducing* monthly
contribution by ₹14.6 lakh. The threshold change reduces revenue 1.1% while *raising*
contribution by ₹35.6 lakh.

The mechanism is cost allocation. Dark-store fixed cost is incurred **per store**. Adding
stores to a city already covered splits existing demand across more stores, so orders per
store — the denominator the fixed cost is divided by — falls:

| | Now | After |
|---|---|---|
| Stores | 48 | 60 |
| Orders/store/day | 420 | **362** |
| Fixed cost per order | ₹36.51 | **₹42.38** |
| CM3 per order | ₹26.97 | **₹22.81** |

**This is why the "fixed costs stay fixed in rupees" convention is load-bearing.** State
overhead as a per-order rate and hold that rate constant while volume changes, and the
fixed cost silently follows the new order *count* instead of staying with the new store
*count*. The expansion flips from −₹14.6 lakh/month to apparently positive. The error is
easy to make, invisible in the output, and there is a test guarding against it.

### 3.2 Give the proposal you are rejecting its best case first

Adding stores in an already-covered city has a genuine benefit: smaller catchments mean
shorter rides. The model credits it — rider payout falls from ₹36.00 to ₹34.29 per order,
modelled as delivery distance scaling with the square root of area per store, with only the
distance-linked 45% of the payout able to move.

**It still does not clear.** That is a much stronger position than rejecting it on a
comparison that ignored the benefit, because the first question in the room is "did you
account for shorter delivery distances?" — and the answer is a row in the model rather than
a promise to look into it.

Three further effects were left out, and I say so explicitly: thinner inventory pooling
raises spoilage, lower per-store volume worsens picking efficiency, and new stores ramp
slowly. All three run *against* the proposal, so the rejection is conservative.

### 3.3 Lead with the break-even, not with the answer

Every recommendation states the break-even value of the driver it depends on:

| Proposal | Break-even | Observed |
|---|---|---|
| Store expansion | incrementality 63.7% | pilot: **43.0%** |
| Threshold change | volume decline 11.3% | last move: **3.1%** |
| Retail media | 18.6% of uplift lands | not yet measured |

**Why this beats a point estimate.** A point estimate invites an argument about the
estimate. A break-even converts the discussion into a factual question with a known answer:
nobody has to accept my 43% if I can say the proposal needs 63.7% and show how 43% was
measured. It also tells you what evidence to go and get — which is why the sensitivity grid
is an argument for a bigger pilot rather than for a better guess.

**Direction matters and is easy to get wrong.** Higher incrementality is favourable; a
higher volume decline is not. The `Decision` dataclass carries an explicit
`higher_is_better` flag because without it the safety margin renders backwards on exactly
one of the three proposals — the kind of sign error that reads fine and is wrong.

---

## 4. Two supporting techniques

### Model the distribution when the mechanism acts on the distribution

A free-delivery threshold does not act on the average basket; it acts on **which side of
the threshold each order falls**. So basket value is a lognormal calibrated so its mean
equals the ₹465 AOV the business reports (median falls out at ₹383.69, which is the right
shape for grocery).

| Threshold | Below | Up-size | Fee-paying | Avg basket | Fee income |
|---|---|---|---|---|---|
| ₹299 | 34.4% | 5.3% | 29.1% | ₹466.97 | ₹7.28 |
| ₹499 | 66.4% | 6.3% | 60.1% | ₹469.18 | ₹15.03 |

Only baskets within 25% below the threshold are treated as capable of up-sizing. Letting
every sub-threshold order up-size is the single easiest way to overstate this proposal — a
customer with a ₹120 basket will not add ₹380 of groceries to dodge a ₹25 fee.

All of this is live in the workbook via `NORM.S.DIST`, so changing the threshold on the
Drivers sheet moves the whole model.

### Do not add business cases together

| | Annual |
|---|---|
| Sum of the two approved cases | +₹9.00 Cr |
| **Modelled together** | **+₹8.82 Cr** |
| Interaction | **−₹0.18 Cr** |

Retail media income is earned per order; the threshold change removes 3.1% of orders.
Adding the cases claims income on orders that will not exist. The error is 2% here — small
enough to be worth showing precisely because it demonstrates the general point: anything
measured *per unit* is overstated by any lever that reduces unit count, and an operating
plan assembled by stapling business cases together accumulates these silently.

---

## 5. Interview questions this project invites

### On the model

**Q: Walk me through CM1, CM2 and CM3.**
CM1 is revenue less COGS, payment gateway and packaging — commercial performance. CM2
subtracts variable fulfilment: rider payout, picking labour, spoilage — store operating
performance, and deliberately excludes anything a store manager cannot influence in a week.
CM3 subtracts allocated dark-store fixed cost — whether the store earns its rent. The split
that matters is CM2 → CM3, because a store-opening decision must clear CM3 while a store
manager should be measured on CM2. Two of my acquisition channels flip verdict across that
line, which is why I wrote a metric dictionary rather than picking one per analysis.

**Q: Why lognormal for basket value?**
Positive, right-skewed, median below mean — that is what grocery baskets look like. I
calibrated on the mean rather than the median so the distribution reproduces the AOV the
business actually reports. The test asserts the partial expectation integrates back to the
mean, so the calibration is checked rather than assumed.

**Q: How did you set the retention curve?**
It climbs from a month-1 shock (58%) toward a 90% asymptote, because in quick commerce most
loss is immediate and survivors are habitual. A flat monthly retention rate — the usual
shortcut — understates LTV early and overstates it late. Channel quality moves **month-1
retention only**, and that is a deliberate change I made after seeing the first version:
scaling every month's retention by a channel multiplier compounds over 24 months and
produced a 6x LTV spread between best and worst channel. That is not a finding, it is a
multiplier applied 24 times. Behaviourally it is also wrong — a coupon-acquired customer
still ordering in month 6 behaves like any other month-6 customer.

**Q: Why is the LTV horizon 24 months?**
Because it is the longest period we have real cohort data for. Extending the horizon raises
every LTV:CAC ratio without any change in performance, so an unconstrained horizon is a
dial for making a channel look fundable. I fixed it in the metric dictionary so it cannot
be chosen per analysis.

### On the recommendations

**Q: Your rejection kills a growth programme. How confident are you?**
The proposal needs 63.7% incrementality and the pilot measured 43%. It is negative across
**every cell** of a sensitivity grid spanning 200–400 orders per new store at that
incrementality, and I credited it the densification saving on rider payout while leaving
out three effects that all run against it. I would also say what I am *not* claiming: this
is an argument against infill, not against expansion. Break-even needs about 59 stores at
today's density, which means new catchments where incrementality approaches 100%. Bring me
that proposal and I expect it clears.

**Q: How would you measure incrementality properly?**
By what happens to **neighbouring store volume**, not by comparing the new store to its
forecast. The pilot's neighbours lost volume equal to 57% of the pilot stores' throughput,
which is where 43% comes from. Measured against forecast the pilot reports 100%
incrementality and the ₹4.2 crore programme gets approved — same data, opposite answer,
purely from the choice of comparison.

**Q: Blended LTV:CAC is 2.20x. Isn't that fine?**
It is arithmetically true and useless for the decision, because it divides total spend by
*all* acquired customers including the 42% who came organically and cost nothing. Paid-only
is 1.28x — blended overstates by 72%, and it does so structurally: the more organic demand
you have, the better your paid marketing looks. At channel level, two channels holding 46%
of the budget sit at 0.56x and 0.57x and never pay back inside 24 months.

**Q: What if the CFO says the rent is sunk, so use CM2 for channel funding?**
Two answers. At the margin they are right — one more customer contributes CM2. As a funding
rule they are wrong, for two reasons. First, the estate is not fixed over a 24-month LTV
horizon; leases and store count both change inside it, so treating them as sunk for the
whole period asserts something we do not believe about our own plan. Second, **every
channel clears 1.0x on CM2 in this model** — a hurdle nothing fails is not a hurdle. I would
also point out that the two channels in question never reach payback on the CM2 curve
either; they only clear the ratio because the horizon is truncated at 24 months.

**Q: What would change your mind?**
Listed in DECISION.md with the effect of each: up-size propensity is a judgement (at 0% the
threshold gain is still positive, so the decision holds), the 3.1% volume response was
measured on a smaller step (which is why I recommend staging ₹299 → ₹399 → ₹499 rather than
one move), and retail media at ₹22 is a target with no signed commitments (but break-even
needs only 18.6% of it).

### On the harder challenges

**Q: This is a made-up company. What does it demonstrate?**
Not domain access — the volumes and cost base are constructed. What is real and checkable:
CM1 at 25.75% of NOV against Blinkit's reported 26.6% gross margin, CM2 at 14.14% against a
~13% mature-dark-store benchmark, EBITDA of −₹6.03 per order between Zepto's reported FY26
and Q1 FY26 figures. The skill is holding a 38-driver model internally consistent, reaching
three defensible decisions with different verdicts, and being able to state the break-even
for each.

**Q: Why build the Excel file at all if the Python already computes it?**
Because the audience uses Excel, and a model that a CFO cannot open and poke is not a model
they will act on. The pointed version of the question is: how do you know the spreadsheet is
right? I load the generated `.xlsx` into an independent formula engine, evaluate it, and
assert it matches the Python cell by named cell with zero error cells anywhere. Verifying
the code that *wrote* the spreadsheet proves nothing about what a reader opens.

**Q: Where is this model weakest?**
Three places. **New-store ramp is not modelled** — I assume steady-state volume immediately,
which flatters the proposal I am rejecting, so it is conservative but imprecise.
**Competitive response is absent** — raising a delivery threshold when a competitor does not
is not the same experiment, and nothing here captures that. **Rider cost is modelled per
order rather than per rider-hour**, so it does not capture the utilisation effects a real
operations team would care about. The first two are the ones I would fix before taking this
to a board.

---

## 6. If you rebuild this yourself

1. **Pick a business with a cost that is fixed per *something* other than per unit** —
   dark stores, restaurants, clinics, delivery hubs. That is where per-unit and aggregate
   metrics come apart, and it is where the interesting findings live.
2. **Put every number in one file with a stated basis.** Then add the test that fails if a
   constant appears anywhere else. It will catch you.
3. **Build three decisions, not one, and make sure they do not all say yes.** A model that
   approves everything demonstrates arithmetic. A model that rejects the most exciting
   proposal for a reason you can defend demonstrates judgement.
4. **Give the rejected proposal its genuine upside before rejecting it.**
5. **Lead every recommendation with a break-even.** It is the difference between an opinion
   and an analysis.
6. **Verify the artefact you ship**, not the code that produced it.
