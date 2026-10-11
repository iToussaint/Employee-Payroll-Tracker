"""Shared payroll rules and helper functions.

All amounts are per monthly pay period. Change the rule values here to adjust
how every payslip is calculated.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Final

# Accepted input types for money and hours. Floats are excluded on purpose:
# they cannot represent most decimal amounts exactly.
Amount = Decimal | int | str

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

# Upper limits on pay inputs, to catch data-entry mistakes (e.g. an extra zero).
MAX_ANNUAL_SALARY = Decimal("1000000")
MAX_BONUS = Decimal("50000")
MAX_HOURLY_RATE = Decimal("1000")
MAX_MONTHLY_HOURS = Decimal("744")  # 31 days * 24 hours
MAX_STIPEND = Decimal("5000")

CENT = Decimal("0.01")


def to_money(amount: Decimal) -> Decimal:
    """Round an amount to cents."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def require_non_negative(value: Decimal, field: str) -> None:
    """Raise ValueError if a numeric field is negative."""
    if value < 0:
        raise ValueError(f"{field} cannot be negative (got {value})")


def to_amount(
    value: Amount,
    field: str,
    *,
    positive: bool = False,
    maximum: Decimal | None = None,
) -> Decimal:
    """Convert an int, numeric string or Decimal to a finite Decimal within range.

    The result is always >= 0. With positive=True it must be > 0, and with a
    maximum it must not exceed that limit.
    """
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise TypeError(f"{field} must be a Decimal, int or numeric string (got {value!r})")
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"{field} is not a valid number (got {value!r})") from None
    if not amount.is_finite():
        raise ValueError(f"{field} must be a finite number (got {value!r})")
    if positive and amount <= 0:
        raise ValueError(f"{field} must be greater than 0 (got {amount})")
    require_non_negative(amount, field)
    if maximum is not None and amount > maximum:
        raise ValueError(f"{field} cannot exceed {maximum} (got {amount})")
    return amount


def progressive_tax(taxable: Decimal) -> Decimal:
    """Apply TAX_BANDS to a monthly amount, band by band."""
    require_non_negative(taxable, "taxable amount")
    tax = Decimal("0")
    remaining = taxable
    index = 0
    while remaining > 0 and index < len(TAX_BANDS):
        width, rate = TAX_BANDS[index]
        portion = remaining if width is None else min(remaining, width)
        tax += portion * rate
        remaining -= portion
        index += 1
    return to_money(tax)


def format_row(cells: list[str], widths: list[int]) -> str:
    """Join cells into one table row; positive widths left-align, negative right-align."""
    parts = []
    for cell, width in zip(cells, widths):
        parts.append(f"{cell:<{width}}" if width > 0 else f"{cell:>{-width}}")
    return "".join(parts)
