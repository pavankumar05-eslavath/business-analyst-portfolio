# LEARN · BA-3 KPI framework and root-cause diagnosis

How the analysis is built, the four ideas worth taking from it, and the interview questions it
invites.

---

## 1. The shape of a root-cause investigation

Most root-cause analyses go: *notice the metric moved → guess at causes → find evidence for the
guess*. The failure mode is not that the guess is wrong. It is that you cannot tell whether it
is right, because nothing constrains the answer.

This one has a different shape, and the order matters:

```
1. Define the metric           METRIC_DICTIONARY.md
   |                           Three clocks give three answers. Pick one, in writing.
   v
2. Build the KPI tree          KPI_TREE.md
   |                           What ARITHMETICALLY determines the metric.
   v
3. Build the issue tree        MECE hypotheses, derived FROM the KPI tree
   |
   v
4. Test every branch           sql/01_hypotheses.sql -- including the ones ruled out
   |
   v
5. Quantify what survived      src/decomposition.py -- must sum to the observed gap
   |
   v
6. Cost the remedies           src/business_case.py -- on cost AND on capability
```

**Step 1 before step 2 is not pedantry.** The investigation started because attainment "fell
9.06pp". Three defensible clocks give three different answers for the same six months, and the
spread between them (85.96% / 88.67% / 94.90%) is *larger than the decline being investigated*.
Any analysis that starts at step 3 is arguing about a number nobody has defined.

**Step 5 is what makes the whole thing falsifiable.** Steps 3 and 4 produce a list of causes.
A list can always absorb one more item. A decomposition that sums to the gap cannot — if you
add a cause, something else has to shrink.

### KPI tree vs issue tree

Constantly confused, and they do different jobs.

| | KPI tree | Issue tree |
|---|---|---|
| Contains | Arithmetic drivers of the metric | Candidate explanations for a movement |
| Changes when | The metric definition changes | Every investigation |
| Test | Does it multiply/sum to the metric? | Is it MECE? |
| Built | Once | Fresh each time |

You need the first to build the second. A KPI tree is also **an audit of what you have assumed
is fixed** — and in this project the node nobody questioned (`SLA target per tier`) turned out
to be the answer.

---

## 2. Four ideas worth taking

### 2.1 Ask whether the target is achievable before asking why it was missed

Six months of escalation, a headcount request, and pressure on a support team — all directed at
a target with a **hard ceiling of 85.60% against a 95% threshold.**

The test is simple once you think to run it. Strip out everything capacity or process could
influence — queueing, waiting on the customer — and measure the work alone:

| Enterprise target | Ceiling (perfect ops) | Governed (today) |
|---|---|---|
| **4h (current)** | **85.60%** | 80.85% |
| 8h | 98.36% | **97.20%** |

**14.40% of enterprise tickets take longer than 4h of actual work.** No staffing level changes
that. Capacity closes 4.75pp of a 14.15pp gap.

**The generalisable move:** for any threshold metric, compute the ceiling under perfect
execution of everything you control. If the ceiling is below the target, you are not looking at
a performance problem, and every rupee spent on performance is spent against a wall. This is a
five-line query and almost nobody runs it.

### 2.2 Per-unit and aggregate metrics can point in opposite directions — including inside your own analysis

Every tier improved on the work clock. The blended figure fell.

| | H1 → H2 |
|---|---|
| standard work-clock attainment | 99.4% → 99.5% |
| business | 93.0% → 95.2% |
| enterprise | 81.0% → 85.6% |
| **Blended** | **96.39% → 94.89%** ⚠️ |
| **Mix-adjusted** | **96.39% → 97.38%** |

Enterprise volume grew 8.1% → 26.9% and carries a tighter target, so the mix drags the
aggregate down while every component rises.

**The part worth remembering:** my first version of hypothesis H03 used the blended figure and
returned **RETAINED** — endorsing the headcount request the analysis exists to reject. The trap
was inside the test built to detect it.

There is now a test (`test_the_blended_version_of_h03_would_have_returned_the_wrong_answer`)
asserting the blended version gives the wrong answer, because that property is the finding.

### 2.3 Distinguish a stock from a flow

The KPI tree puts demand, capacity, throughput and *backlog* on the same branch. Three are
rates. One is an accumulated level.

| Month | Peak backlog | vs baseline | Attainment |
|---|---|---|---|
| 7 | 28 | 0.9x | 94.70% |
| **8** | **146** | **4.6x** | **73.39%** |
| 9 | 36 | 1.1x | 92.25% |

A three-week defect built a backlog; it drained within a month. **Month 8 alone drags the
six-month average down 3.50pp.**

The remedies are completely different:
- Backlog **still growing** → capacity problem → more people
- Backlog **drained** → prevention problem → fix release testing

I costed a contractor burst at ₹17.6 lakh and **did not recommend it**, because the thing it
would clear had already cleared. Recommending it would have been treating a resolved symptom —
and it is the kind of remedy that gets approved precisely because it sounds proportionate.

**A counter-intuitive detail worth checking for:** the damage landed on the **standard** tier
(−5.26pp of the −5.36pp), not enterprise. Priority ordering protected the tightest SLA and
pushed the queue onto the loosest one. If you had looked only at the tier under contractual
pressure, you would have missed the entire component.

### 2.4 Score options on capability, not just on cost

A business case that only prices options is half a business case.

| Option | Recurring/yr | Achievable | **Clears 95%?** |
|---|---|---|---|
| 8 permanent engineers | ₹96,00,000 | 85.60% | **✗** |
| Restate + re-baseline to 8h | ₹0 | 97.20% | **✓** |

Service credits are a **step function**. An option that gets 90% of the way to the threshold
saves exactly nothing. So the third column is not a nuance — it is the decision, and it turns
an argument about cost into a question of fact.

---

## 3. Two techniques worth copying

### Declare the materiality bar before looking at results

`atlas.thresholds` holds a single number — 1.0 percentage point — joined into every verdict in
the SQL. Against a ~9pp decline, a driver worth less than 1pp cannot be a root cause even if it
moved in the expected direction.

A bar set after seeing the results is not a bar. Putting it in a table and joining to it makes
that auditable rather than a claim.

It is also what lets H06 (routing accuracy) be recorded honestly: genuinely worse, +0.17pp,
**worth fixing on its own merits and not a root cause.** Without a declared bar, that finding
has to be either inflated or dropped.

### Record the eliminated hypotheses

Five of twelve were ruled out. It would be shorter to present only the four that survived.

They stay because **an analysis that omits them gets relitigated by whoever's theory went
unmentioned.** "Did you check whether escalations went up?" is a fair question, and the
difference between a five-minute answer and a reopened investigation is whether the query and
the number are already written down.

H11 (seasonality) is recorded as **REFRAMED — untestable** rather than eliminated. There is no
prior-year comparison in twelve months of data. Marking it eliminated would be a false claim;
dropping it would leave the tree not collectively exhaustive. It is *bounded* instead:
seasonality cannot explain a measurement change or a deliberate commercial mix shift.

---

## 4. Interview questions this project invites

### On method

**Q: Walk me through how you'd investigate a KPI that dropped.**
Define the metric first — I found three defensible clocks giving answers spanning 9 percentage
points, which is wider than the decline. Then build the KPI tree so the hypothesis space comes
from arithmetic rather than from whoever is loudest. Then test every branch and record the
eliminations. Then quantify what survived in a decomposition that **sums to the observed gap** —
without that constraint a list of causes can always absorb one more. Then cost the remedies on
capability as well as price.

**Q: What is a MECE issue tree and why does it matter?**
Mutually exclusive so you do not double-count a cause across branches, collectively exhaustive
so the answer is definitely somewhere in the tree. It matters because it converts "here are
some theories" into "here is the complete space, and here is where in it the answer lies." Mine
has six branches — demand, capacity, performance, mix, measurement, external — and the
measurement branch is the one people leave off, which is where 2.71pp of this decline was.

**Q: How do you know your decomposition is right?**
It reconciles to zero residual — the five components sum to the observed −9.06pp to
floating-point precision, and there is a test asserting `abs(residual) < 1e-12`. Beyond the
real data, I test the identity on synthetic cases: a no-change case must produce zero for every
component, and a pure mix shift must put the entire gap in the mix term. And because the data
is generated from a config that plants each effect with a known size, I can check the
decomposition *recovers* what was planted rather than merely adding up.

**Q: Why SQL rather than pandas?**
Because a root-cause investigation gets re-run by people who want to disagree with a filter. An
analyst in the support team can open `01_hypotheses.sql`, see exactly which rows were counted,
and argue with it. The same logic as chained dataframe operations is effectively unreviewable
by anyone who is not the author.

### On the findings

**Q: The VP Support wants 8 engineers. Talk me out of it.**
Three points. The premise is that the team got slower — mix-adjusted work-clock attainment
improved 0.99pp, and every tier improved. Second, 75% of the decline is a measurement change
and a structural mix shift, neither of which responds to hiring. Third and decisive: the
enterprise target has a ceiling of 85.60% against a 95% threshold, so capacity closes 4.75pp of
a 14.15pp gap and the service credits continue in full. That is ₹96 lakh a year, recurring, for
an objective that is never met.

**Q: How would you present this to the VP who made the proposal?**
Lead with the thing that is not their fault and not their team's — the metric changed
underneath them, and their team's actual performance improved. That reframes the conversation
from defending a request to fixing a measurement. Then the ceiling finding, which moves the
problem to Sales and the contract, where it belongs. I would not open with "your proposal is
wrong"; I would open with "your team is being measured on a target that has never been
achievable."

**Q: You're telling Sales they sold something undeliverable. How do you handle that?**
With the arithmetic, not the blame. The 4-hour target was agreed without a capacity model — that
is a process gap, not a person. The constructive output is the control: any future SLA
commitment gets signed off against the work-clock distribution before it is offered. And I would
bring the 8-hour option with the number attached, so the conversation is about a specific
renegotiation worth ₹71.4 lakh a year rather than about fault.

**Q: What if customers refuse to renegotiate the 4h target?**
Then recommendation 2 fails and the only route to 95% is cutting enterprise handle time by
roughly 35% through specialist tooling or a dedicated pod. That is a larger investment and it
has to be costed against the same ₹71.4 lakh a year. It is still not a blanket headcount case —
it is a targeted one. This is in FINDINGS.md under what would change my recommendation, because
a memo that only describes the world where it is right is not much use.

### On the harder challenges

**Q: This data is synthetic. What does it demonstrate?**
Not domain access. What is real and checkable: the decomposition identity holds to 1e-12, the
backlog emerges from an actual queue simulation rather than a parameter, the twelve hypotheses
are tested against a materiality bar declared in advance, and 36 tests pin every number quoted
in the documents. It also demonstrates something a real dataset would hide — because I planted
the effects with known sizes, I can prove the method *recovers* them.

**Q: Where is this analysis weakest?**
Three places, in order. **All three clocks run on calendar hours**, which is right for the 24/7
tiers and too harsh for standard, whose customers do not expect weekend service — so standard
attainment is understated and the mix effect is if anything larger than reported. **The
pending-customer flag is trusted as logged** and is not audited, so the governed clock is
gameable; I recommend sampling it. **Queue wait is modelled at daily granularity**, so
within-day prioritisation is invisible. The first is the one I would fix next, and it needs a
per-region business-hours calendar.

**Q: The interaction term is +2.15pp. Isn't that just a fudge?**
It is the arithmetic residual of mix and rate moving simultaneously, and it is reported
separately rather than folded into either — because assigning it to one would overstate that
component by exactly its size. It is positive here because volume shifted toward enterprise *and*
enterprise improved, so the two effects reinforce. If it were large relative to the components
I would treat that as a signal the two-factor split is too coarse and go to a finer grain.

---

## 5. If you rebuild this yourself

1. **Pick a metric with a threshold, not an average.** SLA attainment, on-time-in-full,
   first-pass yield. Thresholds make the ceiling question meaningful and make step-function
   remedies visible.
2. **Give the metric more than one defensible definition.** That is where the real finding
   usually is, and it forces you to write a dictionary rather than assume one.
3. **Simulate the queue.** Do not parameterise backlog. A stock that emerges from a mechanism
   behaves differently from a number you chose, and the difference between a stock and a flow is
   the most useful distinction in operations analysis.
4. **Plant every effect with a known size in a config file.** Then you can prove the
   decomposition recovers them rather than asking to be believed.
5. **Write down the hypotheses you eliminate, and declare the materiality bar first.**
6. **Make at least one recommendation a rejection**, and make the rejection quantitative:
   not "this is misdirected" but "this closes 4.75pp of a 14.15pp gap."
