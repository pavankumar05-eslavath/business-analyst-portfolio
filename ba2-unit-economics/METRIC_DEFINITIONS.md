# Metric definitions

This document exists because of one finding in the model.

Two acquisition channels — `affiliate_coupon` and `offline_ooh` — clear the 1.0x
LTV:CAC hurdle when lifetime value is calculated on **CM2** and fail it when the
same lifetime value is calculated on **CM3**. Same customers, same spend, same
retention curve, opposite decision:

| Channel | CAC | LTV on CM2 | LTV:CAC | LTV on CM3 | LTV:CAC | Verdict |
|---|---|---|---|---|---|---|
| `affiliate_coupon` | ₹545 | ₹712 | **1.31x** ✅ | ₹303 | **0.56x** ❌ | flips |
| `offline_ooh` | ₹690 | ₹927 | **1.34x** ✅ | ₹394 | **0.57x** ❌ | flips |

Between them they hold **46.0% of the marketing budget**. Whether that spend is
defensible depends entirely on which contribution margin the deck happens to use —
and "contribution margin" is used loosely enough across quick commerce that both
numbers can be quoted honestly by people who disagree.

**That is a governance problem, not an arithmetic one.** The fix is not a better
calculation. It is deciding, in writing and in advance, which definition the company
makes decisions on. Everything below is that decision.

---

## The contribution margin ladder

| Metric | Definition | What it is for |
|---|---|---|
| **GOV** | Gross order value — basket value before platform-funded discount | Basket-size analysis, threshold decisions |
| **NOV** | GOV less platform-funded discount. The revenue line | Denominator for every margin percentage in this model |
| **CM1** | NOV + delivery fee + handling fee + retail media, less COGS, payment gateway and packaging | Commercial performance: buying terms, pricing, ancillary income |
| **CM2** | CM1 less rider payout, picking labour and spoilage | **Store-level operating performance.** Excludes anything a store manager cannot influence in a week |
| **CM3** | CM2 less allocated dark-store fixed cost (rent, utilities, store staff, security) | **Whether a store earns its keep.** The number a store-opening decision must clear |
| **EBITDA** | CM3 less central overhead and marketing | Company profitability |

### Which one to use, and when

| Question | Use | Why |
|---|---|---|
| Is this store operating well? | **CM2** | Rent is not the store manager's decision |
| Should we open this store? | **CM3** | Rent is exactly the decision being made |
| Should we fund this marketing channel? | **CM3** | A customer acquired into a store estate that does not cover its rent has not been acquired profitably |
| Is the company viable? | **EBITDA** | Central overhead is real |
| Should we change price or fees? | **CM3** contribution, in rupees | Per-order margin can improve while total contribution falls |

**The company-standard LTV definition for funding decisions is CM3.** Stated once,
here, so that it is not chosen per deck.

### Why CM3 and not CM2 for channel funding

The argument for CM2 is that dark-store fixed cost is sunk — the rent is paid whether
or not one more customer is acquired, so the marginal contribution of that customer is
CM2. That is correct at the margin and wrong as a funding rule, for two reasons.

1. **The estate is not fixed over an LTV horizon.** This model values a customer over
   24 months. Store count, leases and staffing all change inside 24 months, so
   treating them as sunk for the whole period asserts something the business does not
   believe about its own plan.
2. **It makes the hurdle unfalsifiable.** Every channel clears 1.0x on CM2 in this
   model. A hurdle that nothing fails is not a hurdle; it is a formality that makes
   spend look approved.

Using CM2 would keep ₹1.07 crore a month of spend in channels that do not pay back
within 24 months on any definition. `affiliate_coupon` and `offline_ooh` never reach
payback even on the CM2 curve — the ratio clears 1.0x only because the horizon is
truncated at 24 months, which is the second definitional trap below.

---

## Definitions that decide arguments before they start

### Contribution margin excludes marketing. Always.

Marketing is an acquisition cost, not a cost of fulfilling an order. Including it in
"contribution" makes the metric move when the marketing budget moves, which destroys
its use as an operating measure. It sits below CM3, next to central overhead.

### Fixed costs are fixed in rupees, not per order.

Dark-store rent, central overhead and the marketing budget are stated per order in the
driver file for readability, and they are **converted to absolute monthly amounts and
held there** whenever a scenario changes volume.

This is the single most important convention in the model. Holding a per-order overhead
*rate* constant while volume changes is what makes store expansion look free: add
stores, and the fixed cost per order silently follows the new order count instead of
staying with the new store count. The store-expansion proposal moves from
**−₹14.6 lakh a month to apparently positive** under that error.

### LTV horizon is 24 months, and it is not negotiable per analysis.

24 months is the longest period the company has actual cohort data for. Extending the
horizon raises every LTV:CAC ratio without any change in performance, so an
unconstrained horizon is a dial for making a channel look fundable. Any analysis
quoting a different horizon must say so in the same sentence as the ratio.

### CAC is channel spend divided by customers that channel acquired.

**Blended CAC is not a decision metric.** It divides total spend by *all* acquired
customers, including the 42% who came organically and cost nothing. In this model that
produces:

| Measure | Value | LTV:CAC |
|---|---|---|
| Blended CAC | ₹233.12 | **2.20x** — reads healthy |
| Paid-only CAC | ₹401.94 | **1.28x** — reads marginal |

Blended overstates paid efficiency by **72%**, and it does so structurally rather than
by accident: the more organic demand a brand has, the more efficient its paid marketing
appears. Decisions about incremental spend use channel-level or paid-only figures.

### Retail media income carries no payment gateway fee.

Brand-funded placement income is invoiced to the brand, not collected through the
consumer payment rail, so no MDR applies. Charging gateway fees against it would
understate the highest-margin line in the model by roughly 0.9%.

### Incrementality is measured against neighbouring stores, not against plan.

A new store's "incrementality" is the share of its orders that are genuinely new
demand. It is measured by what happened to **neighbouring store volume**, not by
comparing the new store to its own forecast. The pilot measured 43%: neighbouring
stores lost volume equal to 57% of the pilot stores' throughput.

Measuring against forecast would have reported 100% incrementality and approved a
₹4.2 crore capital programme that reduces contribution.

---

## Metrics deliberately absent

| Not used | Why |
|---|---|
| GMV / gross merchandise value | Ambiguous across the industry — sometimes gross of discount, sometimes of returns, sometimes of taxes. GOV and NOV are defined above and used instead |
| Revenue growth | Two of the three proposals move revenue and contribution in opposite directions. Revenue is reported in the analysis for context and is never a decision criterion |
| CAC payback on blended CAC | Combines both errors above in one number |
| Orders per rider per hour | A real operating metric, but not a driver of any decision here. Rider cost enters as payout per order |

**The absent list matters as much as the present one.** A metric dictionary that only
defines what you use leaves every excluded metric available to whoever wants to argue
with the conclusion.
