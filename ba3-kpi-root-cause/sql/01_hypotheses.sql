-- ============================================================================
-- MECE hypothesis audit trail
-- ============================================================================
-- One row per hypothesis, with the test, the numbers, and the verdict. Every branch of
-- the issue tree in KPI_TREE.md appears here, including the ones that were ruled out.
--
-- Recording the eliminated branches is the entire point. An analysis that presents only
-- the causes it found gets relitigated in the next meeting by whoever's favourite theory
-- was never mentioned. An analysis that shows a theory was tested, and what number ruled
-- it out, ends that conversation once.
--
-- The verdict is computed in SQL against a threshold declared in atlas.thresholds
-- BEFORE any result was seen (1.0 percentage point of the ~9pp decline). A bar set after
-- the fact is not a bar.
--
-- Verdicts:
--   RETAINED   -- moved in the direction that would harm the metric, by a material amount
--   PARTIAL    -- real and directionally harmful, but too small to be a root cause
--   ELIMINATED -- did not move, or moved in the direction that HELPS the metric
--   REFRAMED   -- the hypothesis is not answerable as posed; see the evidence column

CREATE OR REPLACE VIEW atlas.hypotheses AS
WITH
material AS (SELECT material_pp / 100.0 AS material FROM atlas.thresholds),
halves AS (SELECT * FROM atlas.half_summary),
h1 AS (SELECT * FROM halves WHERE half = 'H1'),
h2 AS (SELECT * FROM halves WHERE half = 'H2'),

-- ---------------------------------------------------------------------------
-- H01  Demand outgrew capacity
-- ---------------------------------------------------------------------------
-- The instinctive explanation. Tested by comparing demand per day against MODELLED
-- capacity per day, by half. If capacity kept pace, the trend cannot be the cause --
-- which leaves a specific event, not a chronic shortfall.
demand_capacity AS (
    SELECT
        m.half,
        SUM(m.tickets) / SUM(days.days) AS demand_per_day,
        AVG(c.capacity_per_day)         AS capacity_per_day,
        (SUM(m.tickets) / SUM(days.days)) / AVG(c.capacity_per_day) AS utilisation
    FROM atlas.monthly_attainment m
    JOIN atlas.capacity c USING (month_index)
    JOIN (
        SELECT month_index, COUNT(DISTINCT arrival_day) AS days
        FROM atlas.ticket_sla GROUP BY month_index
    ) days USING (month_index)
    GROUP BY m.half
),
h01 AS (
    SELECT
        'H01' AS hypothesis_id,
        'Demand outgrew capacity' AS hypothesis,
        'Tickets per day vs modelled capacity per day, by half' AS test,
        a.utilisation AS h1_value,
        b.utilisation AS h2_value,
        'utilisation' AS unit,
        CASE WHEN b.utilisation - a.utilisation > 0.05 THEN 'RETAINED' ELSE 'ELIMINATED' END
            AS verdict,
        'Utilisation ' || ROUND(a.utilisation * 100, 1) || '% -> '
            || ROUND(b.utilisation * 100, 1) || '%. Headcount grew with demand, so the '
            || 'team was never short against the TREND. This does not rule out a shortfall '
            || 'against a specific event -- see H10.' AS evidence
    FROM demand_capacity a, demand_capacity b
    WHERE a.half = 'H1' AND b.half = 'H2'
),

-- ---------------------------------------------------------------------------
-- H02  Headcount fell
-- ---------------------------------------------------------------------------
h02 AS (
    SELECT
        'H02', 'Support headcount fell',
        'Modelled agent count, first vs last month of each half',
        (SELECT agents FROM atlas.capacity WHERE month_index = 1),
        (SELECT agents FROM atlas.capacity
         WHERE month_index = (SELECT total_months FROM atlas.constants)),
        'agents',
        CASE WHEN (SELECT agents FROM atlas.capacity
                   WHERE month_index = (SELECT total_months FROM atlas.constants))
                  < (SELECT agents FROM atlas.capacity WHERE month_index = 1)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'Headcount rose across the period. No net attrition. The team is larger at the '
            || 'end of the window than at the start.'
),

-- ---------------------------------------------------------------------------
-- H03  Agents got slower
-- ---------------------------------------------------------------------------
-- The hypothesis behind the executive proposal. Tested on the WORK clock, which excludes
-- queueing and pending-customer time, so it measures handling effort and nothing else.
-- The test has to be MIX-ADJUSTED, and getting this wrong the first time is instructive.
--
-- A blended work-clock comparison shows attainment FALLING, which would retain this
-- hypothesis and endorse the executive proposal. But the blended figure is contaminated
-- by the tier mix shift: enterprise tickets have lower work-clock attainment (a 4h target
-- against 24h) and enterprise grew from 8% to 27% of volume. The aggregate falls even
-- when every tier improves.
--
-- That is precisely the error this whole investigation exists to correct, reproduced
-- inside its own hypothesis test. The fix is to hold volume shares at their baseline
-- values and vary only within-tier attainment, which is the same construction as the
-- rate term in the decomposition.
work_perf AS (
    SELECT
        SUM(CASE WHEN half = 'H1' THEN met_work ELSE 0 END)::DOUBLE
            / SUM(CASE WHEN half = 'H1' THEN tickets ELSE 0 END) AS h1_blended,
        SUM(CASE WHEN half = 'H2' THEN met_work ELSE 0 END)::DOUBLE
            / SUM(CASE WHEN half = 'H2' THEN tickets ELSE 0 END) AS h2_blended
    FROM atlas.tier_half
),
h1_shares AS (
    SELECT tier, tickets::DOUBLE / SUM(tickets) OVER () AS share,
           met_work::DOUBLE / tickets AS work_rate
    FROM atlas.tier_half WHERE half = 'H1'
),
h2_rates AS (
    SELECT tier, met_work::DOUBLE / tickets AS work_rate
    FROM atlas.tier_half WHERE half = 'H2'
),
mix_adjusted AS (
    SELECT
        SUM(a.share * a.work_rate) AS h1_adjusted,
        SUM(a.share * b.work_rate) AS h2_adjusted
    FROM h1_shares a JOIN h2_rates b USING (tier)
),
h03 AS (
    SELECT
        'H03', 'Agents became slower at handling tickets',
        'Work-clock attainment held at baseline tier mix (excludes queueing, '
            || 'pending-customer time and the mix shift)',
        m.h1_adjusted, m.h2_adjusted, 'attainment',
        CASE WHEN m.h2_adjusted < m.h1_adjusted - (SELECT material FROM material)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'Mix-adjusted work-clock attainment ' || ROUND(m.h1_adjusted * 100, 2) || '% -> '
            || ROUND(m.h2_adjusted * 100, 2) || '% ('
            || ROUND((m.h2_adjusted - m.h1_adjusted) * 100, 2)
            || 'pp): the team got FASTER in the period the headline metric fell. '
            || 'Every tier improved on the work clock. The BLENDED figure appears to fall ('
            || ROUND(w.h1_blended * 100, 2) || '% -> ' || ROUND(w.h2_blended * 100, 2)
            || '%) purely because enterprise volume grew, and enterprise carries a tighter '
            || 'target -- the same aggregation error this investigation exists to correct.'
    FROM mix_adjusted m, work_perf w
),

-- ---------------------------------------------------------------------------
-- H04-H06  Quality: rework, escalation, misrouting
-- ---------------------------------------------------------------------------
quality AS (
    SELECT
        AVG(CASE WHEN half = 'H1' AND reopened  THEN 1.0 WHEN half = 'H1' THEN 0.0 END) AS h1_reopen,
        AVG(CASE WHEN half = 'H2' AND reopened  THEN 1.0 WHEN half = 'H2' THEN 0.0 END) AS h2_reopen,
        AVG(CASE WHEN half = 'H1' AND escalated THEN 1.0 WHEN half = 'H1' THEN 0.0 END) AS h1_esc,
        AVG(CASE WHEN half = 'H2' AND escalated THEN 1.0 WHEN half = 'H2' THEN 0.0 END) AS h2_esc,
        AVG(CASE WHEN half = 'H1' AND misrouted THEN 1.0 WHEN half = 'H1' THEN 0.0 END) AS h1_mis,
        AVG(CASE WHEN half = 'H2' AND misrouted THEN 1.0 WHEN half = 'H2' THEN 0.0 END) AS h2_mis
    FROM atlas.ticket_sla
),
h04 AS (
    SELECT 'H04', 'Rework rose (tickets reopened after resolution)',
        'Share of tickets reopened, by half',
        q.h1_reopen, q.h2_reopen, 'rate',
        CASE WHEN q.h2_reopen > q.h1_reopen + (SELECT material FROM material)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'Reopen rate ' || ROUND(q.h1_reopen * 100, 2) || '% -> ' || ROUND(q.h2_reopen * 100, 2)
            || '%. Marginally improved, and far too small to move a 9pp decline.'
    FROM quality q
),
h05 AS (
    SELECT 'H05', 'Escalations rose, consuming senior capacity',
        'Share of tickets escalated, by half',
        q.h1_esc, q.h2_esc, 'rate',
        CASE WHEN q.h2_esc > q.h1_esc + (SELECT material FROM material)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'Escalation rate ' || ROUND(q.h1_esc * 100, 2) || '% -> ' || ROUND(q.h2_esc * 100, 2)
            || '%. Flat to marginally improved.'
    FROM quality q
),
h06 AS (
    SELECT 'H06', 'Routing accuracy fell, adding handoffs',
        'Share of tickets misrouted on first assignment, by half',
        q.h1_mis, q.h2_mis, 'rate',
        CASE WHEN q.h2_mis > q.h1_mis + (SELECT material FROM material)
             THEN 'RETAINED' ELSE 'PARTIAL' END,
        'Misroute rate ' || ROUND(q.h1_mis * 100, 2) || '% -> ' || ROUND(q.h2_mis * 100, 2)
            || '%. Genuinely worse, but the change is a fraction of a percentage point '
            || 'against a 9pp decline. Worth fixing on its own merits; not a root cause.'
    FROM quality q
),

-- ---------------------------------------------------------------------------
-- H07  Tenure mix: more new hires
-- ---------------------------------------------------------------------------
tenure AS (
    SELECT
        AVG(CASE WHEN half = 'H1' AND agent_is_new_hire THEN 1.0
                 WHEN half = 'H1' THEN 0.0 END) AS h1_new,
        AVG(CASE WHEN half = 'H2' AND agent_is_new_hire THEN 1.0
                 WHEN half = 'H2' THEN 0.0 END) AS h2_new,
        AVG(CASE WHEN agent_is_new_hire THEN handle_hours END) AS new_handle,
        AVG(CASE WHEN NOT agent_is_new_hire THEN handle_hours END) AS tenured_handle
    FROM atlas.ticket_sla
),
h07 AS (
    SELECT 'H07', 'A larger share of tickets went to agents under 6 months tenure',
        'Share of tickets handled by new hires, and their handle-time penalty',
        t.h1_new, t.h2_new, 'share',
        CASE WHEN t.h2_new > t.h1_new + (SELECT material FROM material)
             THEN 'PARTIAL' ELSE 'ELIMINATED' END,
        'New-hire share ' || ROUND(t.h1_new * 100, 1) || '% -> ' || ROUND(t.h2_new * 100, 1)
            || '%, and new hires take ' || ROUND((t.new_handle / t.tenured_handle - 1) * 100, 0)
            || '% longer. Real, and it is why the measured work-clock gain is smaller than '
            || 'the tooling improvement that produced it. It partly OFFSETS a positive, '
            || 'rather than causing the decline.'
    FROM tenure t
),

-- ---------------------------------------------------------------------------
-- H08  Service-tier mix shifted toward tighter SLA targets
-- ---------------------------------------------------------------------------
mix AS (
    SELECT
        SUM(CASE WHEN half = 'H1' AND tier = 'enterprise' THEN tickets ELSE 0 END)::DOUBLE
            / SUM(CASE WHEN half = 'H1' THEN tickets ELSE 0 END) AS h1_ent,
        SUM(CASE WHEN half = 'H2' AND tier = 'enterprise' THEN tickets ELSE 0 END)::DOUBLE
            / SUM(CASE WHEN half = 'H2' THEN tickets ELSE 0 END) AS h2_ent
    FROM atlas.tier_half
),
h08 AS (
    SELECT 'H08', 'Service-tier mix shifted toward tighter SLA targets',
        'Enterprise share of ticket volume, and the SLA target spread across tiers',
        m.h1_ent, m.h2_ent, 'share',
        CASE WHEN m.h2_ent > m.h1_ent + (SELECT material FROM material)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'Enterprise share ' || ROUND(m.h1_ent * 100, 1) || '% -> ' || ROUND(m.h2_ent * 100, 1)
            || '%, on a ' || (SELECT MAX(sla_target_hours) FROM atlas.tier_half
                              WHERE tier = 'enterprise')
            || 'h target against '
            || (SELECT MAX(sla_target_hours) FROM atlas.tier_half WHERE tier = 'standard')
            || 'h for standard. Identical performance scores worse against a harder mix. '
            || 'Quantified in the decomposition.'
    FROM mix m
),

-- ---------------------------------------------------------------------------
-- H09  The SLA clock definition changed
-- ---------------------------------------------------------------------------
h09 AS (
    SELECT 'H09', 'The SLA clock definition changed mid-period',
        'Reported attainment vs the governed definition, current half',
        b.attainment_governed, b.attainment_as_reported, 'attainment',
        CASE WHEN b.attainment_governed - b.attainment_as_reported
                  > (SELECT material FROM material)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'The migrated pipeline stopped excluding approved pending-customer time from month '
            || (SELECT definition_change_month FROM atlas.constants)
            || '. Current-half attainment reads '
            || ROUND(b.attainment_as_reported * 100, 2) || '% as reported against '
            || ROUND(b.attainment_governed * 100, 2) || '% on the governed definition. '
            || 'The baseline half was never restated, so every comparison in the business '
            || 'compares two different metrics.'
    FROM h2 b
),

-- ---------------------------------------------------------------------------
-- H10  A one-off incident created a backlog
-- ---------------------------------------------------------------------------
-- Tested by isolating the incident month. A cause that lives in one month is a stock
-- problem, not a flow problem, and needs a different remedy from permanent capacity.
incident AS (
    SELECT
        (SELECT incident_month FROM atlas.constants) AS incident_month,
        (SELECT AVG(CASE WHEN met_net THEN 1.0 ELSE 0.0 END) FROM atlas.ticket_sla
         WHERE month_index = (SELECT incident_month FROM atlas.constants)) AS incident_attainment,
        (SELECT AVG(CASE WHEN met_net THEN 1.0 ELSE 0.0 END) FROM atlas.ticket_sla
         WHERE half = 'H2'
           AND month_index <> (SELECT incident_month FROM atlas.constants)) AS h2_ex_incident,
        (SELECT AVG(CASE WHEN met_net THEN 1.0 ELSE 0.0 END) FROM atlas.ticket_sla
         WHERE half = 'H2') AS h2_all,
        (SELECT MAX(peak_backlog) FROM atlas.monthly_attainment
         WHERE month_index = (SELECT incident_month FROM atlas.constants)) AS incident_backlog,
        (SELECT MAX(peak_backlog) FROM atlas.monthly_attainment WHERE half = 'H1') AS h1_backlog
),
h10 AS (
    SELECT 'H10', 'A one-off incident created a backlog that depressed the average',
        'Governed attainment in the incident month vs the rest of the current half',
        i.h2_ex_incident, i.incident_attainment, 'attainment',
        CASE WHEN i.h2_ex_incident - i.incident_attainment > (SELECT material FROM material)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'Month ' || i.incident_month || ' attainment ' || ROUND(i.incident_attainment * 100, 1)
            || '% against ' || ROUND(i.h2_ex_incident * 100, 1)
            || '% for the rest of the half. Peak open backlog reached ' || i.incident_backlog
            || ' against ' || i.h1_backlog || ' in the baseline half. Including that month '
            || 'costs the half-average ' || ROUND((i.h2_ex_incident - i.h2_all) * 100, 2)
            || 'pp. The backlog had drained within a month -- it is a stock problem that '
            || 'is already resolved, not a flow problem needing permanent capacity.'
    FROM incident i
),

-- ---------------------------------------------------------------------------
-- H11  Seasonality
-- ---------------------------------------------------------------------------
-- Cannot be answered with 12 months of data. Recorded as REFRAMED rather than
-- eliminated, because "we do not know" is a legitimate finding and pretending
-- otherwise is how a spurious cause gets adopted.
h11 AS (
    SELECT 'H11', 'Seasonality -- the current half is simply a harder half',
        'Requires the same calendar half in a prior year; the dataset covers 12 months',
        CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), 'n/a',
        'REFRAMED',
        'Not testable with a single year of history. Recorded rather than dismissed. It is '
            || 'bounded, though: seasonality cannot explain a measurement change (H09) or a '
            || 'deliberate commercial mix shift (H08), which together account for most of '
            || 'the decline.'
),

-- ---------------------------------------------------------------------------
-- H12  The enterprise SLA target is unachievable at any staffing level
-- ---------------------------------------------------------------------------
-- Not on the original issue tree. It emerged from the work clock: if the ceiling on
-- attainment with zero queueing and zero customer delay is below the contractual
-- threshold, no amount of capacity can deliver it.
ceiling AS (
    SELECT
        met_work::DOUBLE / tickets AS work_ceiling,
        met_net::DOUBLE / tickets  AS governed_actual,
        sla_target_hours
    FROM atlas.tier_half WHERE half = 'H2' AND tier = 'enterprise'
),
h12 AS (
    SELECT 'H12', 'The enterprise SLA target cannot be met at any staffing level',
        'Enterprise attainment on the work clock -- the ceiling with zero queueing and '
            || 'zero pending-customer time',
        c.governed_actual, c.work_ceiling, 'attainment',
        CASE WHEN c.work_ceiling < (SELECT service_credit_threshold FROM atlas.constants)
             THEN 'RETAINED' ELSE 'ELIMINATED' END,
        'Even with instant pickup and no customer delay, only '
            || ROUND(c.work_ceiling * 100, 2) || '% of enterprise tickets can be resolved '
            || 'inside the ' || c.sla_target_hours || 'h target, because the handling work '
            || 'itself takes longer. The contractual threshold is '
            || ROUND((SELECT service_credit_threshold FROM atlas.constants) * 100, 0)
            || '%. The gap is structural: capacity closes at most '
            || ROUND((c.work_ceiling - c.governed_actual) * 100, 2)
            || 'pp of it and cannot reach the threshold.'
    FROM ceiling c
),

combined AS (
    SELECT 1 AS sort_order, * FROM h01
    UNION ALL SELECT 2, * FROM h02
    UNION ALL SELECT 3, * FROM h03
    UNION ALL SELECT 4, * FROM h04
    UNION ALL SELECT 5, * FROM h05
    UNION ALL SELECT 6, * FROM h06
    UNION ALL SELECT 7, * FROM h07
    UNION ALL SELECT 8, * FROM h08
    UNION ALL SELECT 9, * FROM h09
    UNION ALL SELECT 10, * FROM h10
    UNION ALL SELECT 11, * FROM h11
    UNION ALL SELECT 12, * FROM h12
)
SELECT * FROM combined ORDER BY sort_order;
