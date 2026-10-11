"""Payroll rules and helper functions shared by the other modules.

The module has two parts:

* Rules: roles, rates, tax bands and valid ranges. All amounts are per
  monthly pay period; change a value here to change every payslip.
* Helpers: validating input, working with money, calculating tax and
  formatting table rows.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Literal

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

# Employee roles.
FULL_TIME = "Full-time Employee"
CONTRACT = "Contract Employee"
INTERN = "Intern"

# Roles taxed on the progressive bands. A frozenset gives fast,
# read-only membership checks.
PROGRESSIVE_TAX_ROLES = frozenset({FULL_TIME, INTERN})

MONTHS_PER_YEAR = Decimal("12")

# Contract employees pay a flat rate on their whole gross pay.
CONTRACT_TAX_RATE = Decimal("0.15")

# Progressive monthly income tax bands as (band width, rate).
# A width of None means "everything above the previous bands".
# Stored as a tuple so the bands cannot be changed by accident.
TAX_BANDS: tuple[tuple[Decimal | None, Decimal], ...] = (
    (Decimal("1000"), Decimal("0.00")),
    (Decimal("2000"), Decimal("0.10")),
    (Decimal("3000"), Decimal("0.20")),
    (None, Decimal("0.30")),
)

# Valid ranges for pay inputs.
MAX_ANNUAL_SALARY = Decimal("1000000")
MAX_BONUS = Decimal("50000")
MAX_HOURLY_RATE = Decimal("1000")
MAX_MONTHLY_HOURS = Decimal("744")  # 31 days * 24 hours
MAX_STIPEND = Decimal("5000")

# ---------------------------------------------------------------------------
# Types and constants used by the helpers
# ---------------------------------------------------------------------------

# Accepted input types for money and hours.
Amount = Decimal | int | float | str

# A table column: its width and alignment ("<" left, ">" right).
Column = tuple[int, Literal["<", ">"]]

CENT = Decimal("0.01")
ZERO = Decimal("0.00")

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def to_text(value: str, field: str) -> str:
    """Return the value with surrounding spaces removed.

    Raises:
        ValueError: If nothing is left after removing the spaces.
    """
    text = value.strip()
    if not text:
        raise ValueError(f"{field} cannot be empty")
    return text


def to_amount(
    value: Amount,
    field: str,
    *,
    positive: bool = False,
    maximum: Decimal | None = None,
) -> Decimal:
    """Convert a number or numeric string to a Decimal within a valid range.

    Args:
        value: The raw input.
        field: Field name used in error messages.
        positive: If True, the amount must be greater than 0.
        maximum: If given, the amount must not exceed it.

    Returns:
        The amount as a non-negative Decimal within range.

    Raises:
        ValueError: If value is not a number or is out of range.
    """
    try:
        # str() first so floats such as 0.1 convert exactly as written.
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(
            f"{field} is not a valid number (got {value!r})"
        ) from None
    if not amount.is_finite():
        raise ValueError(f"{field} must be a finite number (got {value!r})")
    if positive and amount <= 0:
        raise ValueError(f"{field} must be greater than 0 (got {amount})")
    if amount < 0:
        raise ValueError(f"{field} cannot be negative (got {amount})")
    if maximum is not None and amount > maximum:
        raise ValueError(f"{field} cannot exceed {maximum} (got {amount})")
    return amount


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------


def to_money(amount: Decimal) -> Decimal:
    """Round an amount to cents, rounding halves up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def format_money(amount: Decimal) -> str:
    """Round to cents and add thousands separators (60000 -> '60,000.00')."""
    return f"{to_money(amount):,}"


# ---------------------------------------------------------------------------
# Tax
# ---------------------------------------------------------------------------


def progressive_tax(taxable: Decimal) -> Decimal:
    """Apply TAX_BANDS to a monthly amount, one band at a time."""
    tax = Decimal(0)
    remaining = taxable
    index = 0
    while remaining > 0 and index < len(TAX_BANDS):
        width, rate = TAX_BANDS[index]
        # The last band has no width and takes whatever is left.
        portion = remaining if width is None else min(remaining, width)
        tax += portion * rate
        remaining -= portion
        index += 1
    return to_money(tax)


def apply_tax(taxable: Decimal, role: str) -> Decimal:
    """Return the tax owed on an amount, using the rule for the role.

    Contract employees pay a flat rate; full-time employees and interns
    are taxed on the progressive bands.

    Raises:
        ValueError: If the role has no tax rule.
    """
    if role == CONTRACT:
        return to_money(taxable * CONTRACT_TAX_RATE)
    elif role in PROGRESSIVE_TAX_ROLES:
        return progressive_tax(taxable)
    else:
        raise ValueError(f"No tax rule for role {role!r}")


def tax_basis(role: str) -> str:
    """Return a short description of the role's tax rule, for reports."""
    if role == CONTRACT:
        return f"flat {CONTRACT_TAX_RATE:.0%}"
    return "progressive bands"


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_row(cells: list[str], columns: list[Column]) -> str:
    """Join cells into one fixed-width table row.

    Each cell is padded to its column's width and aligned left ("<") or
    right (">").

    Raises:
        ValueError: If there are more or fewer cells than columns.
    """
    return "".join(
        f"{cell:{align}{width}}"
        for cell, (width, align) in zip(cells, columns, strict=True)
    )
