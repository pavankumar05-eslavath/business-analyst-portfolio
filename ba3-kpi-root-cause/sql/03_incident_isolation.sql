-- ============================================================================
-- Isolating the incident month
-- ============================================================================
-- A six-month average is a blunt instrument. If one month inside it was catastrophic and
-- the cause is already resolved, the average reports a problem the business no longer
-- has -- and invites a permanent remedy for a transient event.
--
-- These views answer three questions:
--   1. How much of the half-average decline is one month?
--   2. Had the backlog drained, or was it still there at the end of the window?
--   3. What does the trend look like with the incident month excluded?
--
-- Question 2 is the one that changes the remedy. A backlog that is still growing needs
-- capacity. A backlog that drained needs prevention.

CREATE OR REPLACE VIEW atlas.incident_isolation AS
WITH constants AS (SELECT * FROM atlas.constants),
half_all AS (
    SELECT
        half,
        COUNT(*) AS tickets,
        AVG(CASE WHEN met_net THEN 1.0 ELSE 0.0 END) AS attainment_governed
    FROM atlas.ticket_sla GROUP BY half
),
half_excl AS (
    SELECT
        half,
        COUNT(*) AS tickets_excl_incident,
        AVG(CASE WHEN met_net THEN 1.0 ELSE 0.0 END) AS attainment_excl_incident
    FROM atlas.ticket_sla
    WHERE month_index <> (SELECT incident_month FROM constants)
    GROUP BY half
),
incident AS (
    SELECT
        COUNT(*) AS incident_tickets,
        AVG(CASE WHEN met_net THEN 1.0 ELSE 0.0 END) AS incident_attainment,
        AVG(queue_wait_hours) AS incident_mean_queue_hours
    FROM atlas.ticket_sla
    WHERE month_index = (SELECT incident_month FROM constants)
)
SELECT
    a.half,
    a.tickets,
    a.attainment_governed,
    e.attainment_excl_incident,
    a.attainment_governed - e.attainment_excl_incident AS incident_drag,
    i.incident_tickets,
    i.incident_attainment,
    i.incident_mean_queue_hours,
    (SELECT incident_month FROM constants) AS incident_month
FROM half_all a
JOIN half_excl e USING (half)
CROSS JOIN incident i
ORDER BY a.half;

-- ---------------------------------------------------------------------------
-- Did the backlog drain? Peak open backlog by month, against the baseline norm.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW atlas.backlog_trace AS
WITH baseline AS (
    SELECT AVG(peak_backlog) AS baseline_peak
    FROM atlas.monthly_attainment WHERE half = 'H1'
)
SELECT
    m.month_index,
    m.half,
    m.tickets,
    m.peak_backlog,
    b.baseline_peak,
    m.peak_backlog / b.baseline_peak            AS vs_baseline_multiple,
    m.mean_queue_wait_hours,
    m.attainment_governed,
    m.month_index = (SELECT incident_month FROM atlas.constants) AS is_incident_month,
    -- A backlog is 'cleared' once it is back within 1.5x the baseline norm.
    m.peak_backlog <= b.baseline_peak * 1.5     AS backlog_within_normal
FROM atlas.monthly_attainment m
CROSS JOIN baseline b
ORDER BY m.month_index;
