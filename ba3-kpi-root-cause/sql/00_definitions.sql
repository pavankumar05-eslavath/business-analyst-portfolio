-- ============================================================================
-- Governed metric definitions
-- ============================================================================
-- Every figure in this analysis is computed from the views below, and nowhere else.
-- The point is that "SLA attainment" is not one number: it depends on which clock you
-- measure, and the whole investigation turns on that. Defining all three clocks in one
-- place, once, is what stops the rest of the analysis from quietly mixing them.
--
-- See METRIC_DICTIONARY.md for the prose version and the governance decision about
-- which clock the business reports on.

-- ---------------------------------------------------------------------------
-- The three clocks, and the SLA outcome on each.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW atlas.ticket_sla AS
SELECT
    t.ticket_id,
    t.created_at,
    t.resolved_at,
    t.month_index,
    t.half,
    t.arrival_day,
    t.tier,
    t.category,
    t.sla_target_hours,
    t.agent_tenure_months,
    t.agent_is_new_hire,
    t.reopened,
    t.escalated,
    t.misrouted,
    t.backlog_open_at_close,

    -- work: the handling effort itself. A counterfactual in which the ticket is picked
    -- up the instant it arrives and the customer never has to be chased. This is the
    -- ceiling on what any level of staffing could achieve.
    t.work_hours,
    -- net: the GOVERNED clock. Queue wait plus handling, excluding approved
    -- pending-customer time. This is the definition the SLA policy specifies.
    t.net_hours,
    -- strict: what the migrated reporting pipeline computes -- resolved_at minus
    -- created_at, with no clock pause at all.
    t.elapsed_hours AS strict_hours,

    t.queue_wait_hours,
    t.handle_hours,
    t.pending_customer_hours,

    t.work_hours   <= t.sla_target_hours AS met_work,
    t.net_hours    <= t.sla_target_hours AS met_net,
    t.elapsed_hours <= t.sla_target_hours AS met_strict,

    -- Which clock the business ACTUALLY reported for this ticket's period. Before the
    -- migration the pipeline paused the clock; afterwards it did not. This column is the
    -- measurement discontinuity, made explicit.
    CASE WHEN t.month_index >= (SELECT definition_change_month FROM atlas.constants)
         THEN 'strict' ELSE 'net' END AS reported_clock,
    CASE WHEN t.month_index >= (SELECT definition_change_month FROM atlas.constants)
         THEN t.elapsed_hours <= t.sla_target_hours
         ELSE t.net_hours <= t.sla_target_hours END AS met_as_reported
FROM atlas.tickets t;

-- ---------------------------------------------------------------------------
-- Monthly series: what was reported, versus what the governed definition says.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW atlas.monthly_attainment AS
SELECT
    s.month_index,
    s.half,
    MAX(s.reported_clock)                       AS reported_clock,
    COUNT(*)                                    AS tickets,
    AVG(CASE WHEN s.met_as_reported THEN 1.0 ELSE 0.0 END) AS attainment_as_reported,
    AVG(CASE WHEN s.met_net         THEN 1.0 ELSE 0.0 END) AS attainment_governed,
    AVG(CASE WHEN s.met_work        THEN 1.0 ELSE 0.0 END) AS attainment_work,
    AVG(CASE WHEN s.met_strict      THEN 1.0 ELSE 0.0 END) AS attainment_strict,
    AVG(s.queue_wait_hours)                     AS mean_queue_wait_hours,
    MEDIAN(s.handle_hours)                      AS median_handle_hours,
    MAX(s.backlog_open_at_close)                AS peak_backlog,
    AVG(CASE WHEN s.tier = 'enterprise' THEN 1.0 ELSE 0.0 END) AS enterprise_share
FROM atlas.ticket_sla s
GROUP BY s.month_index, s.half;

-- ---------------------------------------------------------------------------
-- Tier x half aggregates. This is the input to the decomposition, and the grain
-- matters: the mix effect is only visible if volume share and attainment are
-- carried separately for every tier.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW atlas.tier_half AS
SELECT
    s.half,
    s.tier,
    COUNT(*)                                          AS tickets,
    SUM(CASE WHEN s.met_work   THEN 1 ELSE 0 END)     AS met_work,
    SUM(CASE WHEN s.met_net    THEN 1 ELSE 0 END)     AS met_net,
    SUM(CASE WHEN s.met_strict THEN 1 ELSE 0 END)     AS met_strict,
    AVG(s.queue_wait_hours)                           AS mean_queue_wait_hours,
    AVG(s.pending_customer_hours)                     AS mean_pending_hours,
    MEDIAN(s.handle_hours)                            AS median_handle_hours,
    MAX(s.sla_target_hours)                           AS sla_target_hours
FROM atlas.ticket_sla s
GROUP BY s.half, s.tier;

-- ---------------------------------------------------------------------------
-- Half-level summary on every clock.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW atlas.half_summary AS
SELECT
    s.half,
    COUNT(*)                                              AS tickets,
    AVG(CASE WHEN s.met_as_reported THEN 1.0 ELSE 0.0 END) AS attainment_as_reported,
    AVG(CASE WHEN s.met_net    THEN 1.0 ELSE 0.0 END)     AS attainment_governed,
    AVG(CASE WHEN s.met_work   THEN 1.0 ELSE 0.0 END)     AS attainment_work,
    AVG(CASE WHEN s.met_strict THEN 1.0 ELSE 0.0 END)     AS attainment_strict
FROM atlas.ticket_sla s
GROUP BY s.half;
