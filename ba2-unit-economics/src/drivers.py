"""Load and validate the driver set.

Every number the model uses comes from config/drivers.yml. Nothing is hard-coded
here, for one reason: a driver-based model is only useful if a reviewer can find
and change any assumption in one place. The moment a constant is typed into the
calculation layer, the model stops being auditable and becomes someone's opinion
expressed in Python.

Each driver carries a `basis` string as well as a value. That is enforced, not
optional -- a driver without a stated basis fails validation, because "where did
this number come from" is the first question in any finance review and the model
should be able to answer it without the author present.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "drivers.yml"

# Keys that hold structure rather than drivers.
RESERVED = {"meta", "channels", "scenarios"}


@dataclass(frozen=True)
class Driver:
    name: str
    value: float
    unit: str
    basis: str
    group: str

    @property
    def is_assumption(self) -> bool:
        """Drivers whose basis is flagged ASSUMPTION are the ones to stress first."""
        return self.basis.strip().upper().startswith("ASSUMPTION")

    @property
    def is_measured(self) -> bool:
        return self.basis.strip().upper().startswith("MEASURED")


@dataclass(frozen=True)
class Channel:
    name: str
    new_customers: int
    spend: float
    retention_multiplier: float
    basis: str

    @property
    def cac(self) -> float:
        """Organic acquisition has no spend, so it has no CAC -- not a CAC of zero.

        Returning 0.0 here would be arithmetically true and analytically wrong: it
        makes organic look infinitely efficient and drags the blended figure down
        for reasons that have nothing to do with marketing performance.
        """
        if self.new_customers == 0:
            return 0.0
        return self.spend / self.new_customers

    @property
    def is_paid(self) -> bool:
        return self.spend > 0


class Drivers:
    """Flat, validated access to every driver plus the channel and meta blocks."""

    def __init__(self, raw: dict[str, Any]):
        self.meta: dict[str, Any] = raw.get("meta", {})
        self.scenarios: dict[str, dict[str, Any]] = raw.get("scenarios", {})
        self._drivers: dict[str, Driver] = {}
        self.channels: list[Channel] = []
        self._load(raw)
        self._validate()

    # -- loading ----------------------------------------------------------- #
    def _load(self, raw: dict[str, Any]) -> None:
        for group, block in raw.items():
            if group in RESERVED:
                continue
            self._walk(group, block)

        for entry in raw.get("channels", []):
            self.channels.append(Channel(
                name=entry["name"],
                new_customers=int(entry["new_customers"]),
                spend=float(entry["spend"]),
                retention_multiplier=float(entry["retention_multiplier"]),
                basis=str(entry.get("basis", "")),
            ))

    def _walk(self, group: str, block: Any) -> None:
        if not isinstance(block, dict):
            return
        if "value" in block and "unit" in block:
            name = group.rsplit(".", 1)[-1]
            self._add(Driver(
                name=name,
                value=float(block["value"]),
                unit=str(block["unit"]),
                basis=str(block.get("basis", "")).strip(),
                group=group,
            ))
            return
        for key, value in block.items():
            self._walk(f"{group}.{key}", value)

    def _add(self, driver: Driver) -> None:
        if driver.name in self._drivers:
            raise ValueError(
                f"duplicate driver name {driver.name!r} at {driver.group!r}; driver "
                f"names must be unique because the Excel workbook turns them into "
                f"named ranges"
            )
        self._drivers[driver.name] = driver

    # -- validation -------------------------------------------------------- #
    def _validate(self) -> None:
        problems: list[str] = []

        missing_basis = [d.name for d in self._drivers.values() if not d.basis]
        if missing_basis:
            problems.append(f"drivers with no stated basis: {', '.join(sorted(missing_basis))}")

        problems.extend(
            f"{name} is a fraction but reads {self[name]}"
            for name in ("product_gross_margin_pct", "payment_gateway_pct", "spoilage_pct",
                         "month_1_retention", "asymptotic_retention", "retention_decay",
                         "tenure_frequency_uplift", "incrementality", "upsize_propensity",
                         "upsize_band_width", "observed_volume_response",
                         "rider_payout_distance_share")
            if not 0.0 <= self[name] <= 1.0
        )
        problems.extend(
            f"{name} must be positive, reads {self[name]}"
            for name in ("dark_stores", "orders_per_store_per_day", "gross_order_value",
                         "basket_log_sigma", "horizon_months",
                         "orders_per_customer_per_month")
            if self[name] <= 0
        )

        if self["month_1_retention"] >= self["asymptotic_retention"]:
            problems.append(
                "month_1_retention should be below asymptotic_retention -- the curve is "
                "meant to climb from an initial shock toward a floor"
            )

        if self["platform_funded_discount"] >= self["gross_order_value"]:
            problems.append("platform_funded_discount exceeds gross_order_value")

        if self["proposed_threshold"] <= self["free_delivery_threshold"]:
            problems.append(
                "proposed_threshold is not above the current threshold, so the "
                "threshold decision has nothing to evaluate"
            )

        if not self.channels:
            problems.append("no acquisition channels defined")

        duplicate_channels = {c.name for c in self.channels}
        if len(duplicate_channels) != len(self.channels):
            problems.append("duplicate channel names")

        if problems:
            raise ValueError("driver validation failed:\n  - " + "\n  - ".join(problems))

    # -- access ------------------------------------------------------------ #
    def __getitem__(self, name: str) -> float:
        try:
            return self._drivers[name].value
        except KeyError:
            raise KeyError(f"unknown driver {name!r}") from None

    def driver(self, name: str) -> Driver:
        return self._drivers[name]

    def all(self) -> list[Driver]:
        return list(self._drivers.values())

    @property
    def days_per_month(self) -> int:
        return int(self.meta.get("days_per_month", 30))

    @property
    def assumptions(self) -> list[Driver]:
        return [d for d in self._drivers.values() if d.is_assumption]

    @property
    def measured(self) -> list[Driver]:
        return [d for d in self._drivers.values() if d.is_measured]


def load(path: Path | str | None = None) -> Drivers:
    path = Path(path) if path else CONFIG_PATH
    with path.open(encoding="utf-8") as handle:
        return Drivers(yaml.safe_load(handle))
