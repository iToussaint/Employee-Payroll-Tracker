"""Shared payroll rules and helper functions.

All amounts are per monthly pay period. Change the rule values here to adjust
how every payslip is calculated.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Final

# Roles
FULL_TIME: Final = "full_time"
CONTRACT: Final = "contract"
INTERN: Final = "intern"
VALID_ROLES = (FULL_TIME, CONTRACT, INTERN)

MONTHS_PER_YEAR = Decimal("12")

# Full-time: pension contribution taken from base monthly salary.
PENSION_RATE = Decimal("0.05")

# Contract: hours beyond the standard month are paid at the overtime multiplier.
STANDARD_MONTHLY_HOURS = Decimal("160")
OVERTIME_MULTIPLIER = Decimal("1.5")
CONTRACT_WITHHOLDING_RATE = Decimal("0.15")

# Progressive monthly income tax bands as (band width, rate).
# A width of None means "everything above the previous bands".
TAX_BANDS: list[tuple[Decimal | None, Decimal]] = [
    (Decimal("1000"), Decimal("0.00")),
    (Decimal("2000"), Decimal("0.10")),
    (Decimal("3000"), Decimal("0.20")),
    (None, Decimal("0.30")),
]

CENT = Decimal("0.01")


def to_money(amount: Decimal) -> Decimal:
    """Round an amount to cents."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def require_non_negative(value: Decimal, field: str) -> None:
    """Raise ValueError if a numeric field is negative."""
    if value < 0:
        raise ValueError(f"{field} cannot be negative (got {value})")


def format_row(cells: list[str], widths: list[int]) -> str:
    """Join cells into one table row; positive widths left-align, negative right-align."""
    parts = []
    for cell, width in zip(cells, widths):
        parts.append(f"{cell:<{width}}" if width > 0 else f"{cell:>{-width}}")
    return "".join(parts)
