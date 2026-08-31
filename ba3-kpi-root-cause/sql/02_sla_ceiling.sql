-- ============================================================================
-- Is the SLA target achievable at all?
-- ============================================================================
-- This is the question nobody in the business had asked, and it is the one that decides
-- the remedy.
--
-- SLA attainment has three obstacles: the ticket waits in a queue, the customer takes
-- time to respond, and the work itself takes time. Capacity can shrink the first.
-- Process can shrink the second. Neither touches the third.
--
-- So the WORK clock -- handling effort with no queueing and no customer delay -- is the
-- ceiling on what any level of staffing could ever deliver. If that ceiling sits below
-- the contractual threshold, the target is unachievable by construction and every rupee
-- spent on capacity is spent against a wall.
--
-- The candidate targets are evaluated on all three clocks so the remedy can be chosen on
-- evidence: what the target would have to become, and what performance would have to
-- become, to clear the threshold.

CREATE OR REPLACE VIEW atlas.sla_ceiling AS
WITH candidates AS (
    SELECT * FROM (VALUES (2.0), (3.0), (4.0), (5.0), (6.0), (8.0), (10.0), (12.0), (24.0))
        AS t(candidate_target_hours)
),
current_half AS (
    SELECT * FROM atlas.ticket_sla WHERE half = 'H2'
)
SELECT
    s.tier,
    MAX(s.sla_target_hours)                       AS current_target_hours,
    c.candidate_target_hours,
    c.candidate_target_hours = MAX(s.sla_target_hours) AS is_current_target,
    COUNT(*)                                      AS tickets,
    -- The ceiling: perfect operations, zero queue, zero customer delay.
    AVG(CASE WHEN s.work_hours   <= c.candidate_target_hours THEN 1.0 ELSE 0.0 END)
        AS attainment_work_ceiling,
    -- What the governed definition would report today at this target.
    AVG(CASE WHEN s.net_hours    <= c.candidate_target_hours THEN 1.0 ELSE 0.0 END)
        AS attainment_governed,
    -- What the migrated pipeline would report at this target.
    AVG(CASE WHEN s.strict_hours <= c.candidate_target_hours THEN 1.0 ELSE 0.0 END)
        AS attainment_strict,
    (SELECT service_credit_threshold FROM atlas.constants) AS threshold,
    AVG(CASE WHEN s.work_hours <= c.candidate_target_hours THEN 1.0 ELSE 0.0 END)
        >= (SELECT service_credit_threshold FROM atlas.constants) AS ceiling_clears_threshold,
    AVG(CASE WHEN s.net_hours  <= c.candidate_target_hours THEN 1.0 ELSE 0.0 END)
        >= (SELECT service_credit_threshold FROM atlas.constants) AS today_clears_threshold
FROM current_half s
CROSS JOIN candidates c
GROUP BY s.tier, c.candidate_target_hours
ORDER BY s.tier, c.candidate_target_hours;

-- ---------------------------------------------------------------------------
-- Where the time actually goes, by tier. This is the diagnostic that tells you
-- which of the three obstacles is binding.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW atlas.time_composition AS
SELECT
    s.half,
    s.tier,
    MAX(s.sla_target_hours)            AS sla_target_hours,
    COUNT(*)                           AS tickets,
    AVG(s.handle_hours)                AS mean_handle_hours,
    AVG(s.queue_wait_hours)            AS mean_queue_hours,
    AVG(s.pending_customer_hours)      AS mean_pending_hours,
    AVG(s.strict_hours)                AS mean_total_hours,
    -- Attainment lost to each obstacle, in percentage points.
    (AVG(CASE WHEN s.met_work THEN 1.0 ELSE 0.0 END)
       - AVG(CASE WHEN s.met_net THEN 1.0 ELSE 0.0 END)) * 100 AS pp_lost_to_queue,
    (AVG(CASE WHEN s.met_net THEN 1.0 ELSE 0.0 END)
       - AVG(CASE WHEN s.met_strict THEN 1.0 ELSE 0.0 END)) * 100 AS pp_lost_to_pending,
    (1 - AVG(CASE WHEN s.met_work THEN 1.0 ELSE 0.0 END)) * 100 AS pp_lost_to_work_itself
FROM atlas.ticket_sla s
GROUP BY s.half, s.tier
ORDER BY s.half, s.tier;
