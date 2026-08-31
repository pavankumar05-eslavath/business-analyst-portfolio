"""DuckDB warehouse: load the tickets, materialise capacity, run the SQL layer.

The analysis lives in SQL rather than in pandas on purpose. A root-cause investigation
is read by people who will want to re-run one step of it, disagree with a filter, or
check a definition. SQL is the medium where that conversation can happen -- an analyst
in the support team can open `sql/02_hypotheses.sql`, see exactly which rows were
counted, and argue with it. The same logic expressed as chained dataframe operations is
effectively unreviewable by anyone who is not the author.

Capacity is materialised as a table rather than hard-coded into the queries, because the
volume and headcount hypotheses both need to compare demand against capacity, and that
comparison has to be visible in the SQL rather than buried in Python.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
TICKETS_PATH = PROJECT_ROOT / "data" / "tickets.parquet"


@dataclass
class SqlStep:
    name: str
    path: Path

    @property
    def sql(self) -> str:
        return self.path.read_text(encoding="utf-8")


def sql_steps() -> list[SqlStep]:
    """Every .sql file, in filename order. Numbering is the execution contract."""
    return [SqlStep(name=path.stem, path=path) for path in sorted(SQL_DIR.glob("*.sql"))]


def capacity_frame(config: dict) -> pd.DataFrame:
    """Modelled daily capacity per month, from the scenario config.

    Mirrors the generator's calculation exactly: agents ramp linearly across the year,
    each handles a fixed number of tickets per day, and weekend cover is thinner. The
    weekday-weighted average is what a monthly demand figure should be compared against.
    """
    capacity = config["capacity"]
    months = int(config["meta"]["months"])
    agents_start = float(capacity["agents_first_month"])
    agents_final = float(capacity["agents_final_month"])
    per_agent = float(capacity["tickets_per_agent_per_day"])

    # (5 weekdays x 1.12 + 2 weekend days x 0.40) / 7
    shift_factor = (5 * 1.12 + 2 * 0.40) / 7

    rows = []
    for month_index in range(1, months + 1):
        progress = 0.0 if months == 1 else (month_index - 1) / (months - 1)
        agents = agents_start + (agents_final - agents_start) * progress
        rows.append({
            "month_index": month_index,
            "agents": agents,
            "tickets_per_agent_per_day": per_agent,
            "capacity_per_day": agents * per_agent * shift_factor,
        })
    return pd.DataFrame(rows)


def thresholds_frame(config: dict) -> pd.DataFrame:
    """Verdict thresholds, so the SQL audit trail states its own decision rules.

    A hypothesis is only genuinely eliminated if the bar it failed to clear was set
    before the result was seen. Putting the bar in a table -- and joining to it -- makes
    that auditable instead of a claim.
    """
    return pd.DataFrame([
        {
            "material_pp": 1.0,
            "note": (
                "A driver must move the headline metric by at least 1.0 percentage point "
                "to be treated as material. The observed decline is ~9pp, so a driver "
                "worth less than 1pp cannot be a root cause even if it moved in the "
                "expected direction."
            ),
        }
    ])


def build(config: dict, *, database: str | Path = ":memory:",
          tickets_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    """Create the warehouse and execute every SQL step in order."""
    tickets_path = tickets_path or TICKETS_PATH
    if not tickets_path.exists():
        raise FileNotFoundError(
            f"{tickets_path} not found -- run `python -m data.generate_tickets` first"
        )

    connection = duckdb.connect(str(database))
    connection.execute("CREATE SCHEMA IF NOT EXISTS atlas")

    connection.execute(
        "CREATE OR REPLACE TABLE atlas.tickets AS SELECT * FROM read_parquet(?)",
        [str(tickets_path)],
    )

    capacity = capacity_frame(config)
    thresholds = thresholds_frame(config)
    connection.register("capacity_src", capacity)
    connection.register("thresholds_src", thresholds)
    connection.execute("CREATE OR REPLACE TABLE atlas.capacity AS SELECT * FROM capacity_src")
    connection.execute(
        "CREATE OR REPLACE TABLE atlas.thresholds AS SELECT * FROM thresholds_src")

    # Scenario constants the SQL needs. Passed in rather than duplicated, so the config
    # remains the single source of truth.
    meta = config["meta"]
    spike = config["defect_spike"]
    start = meta["start_month"]
    start = start if isinstance(start, dt.date) else dt.date.fromisoformat(str(start))
    constants = pd.DataFrame([{
        "baseline_months": int(meta["baseline_months"]),
        "total_months": int(meta["months"]),
        "definition_change_month": int(config["definition_change"]["effective_month"]),
        "incident_month": int(spike["month"]),
        "incident_category": str(spike["category"]),
        "service_credit_threshold": float(config["commercial"]["service_credit_threshold"]),
        "start_month": start,
    }])
    connection.register("constants_src", constants)
    connection.execute("CREATE OR REPLACE TABLE atlas.constants AS SELECT * FROM constants_src")

    for step in sql_steps():
        try:
            connection.execute(step.sql)
        except duckdb.Error as error:
            raise RuntimeError(f"SQL step {step.name} failed: {error}") from error

    return connection


def query(connection: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return connection.execute(sql).fetchdf()
