"""General-purpose helpers for money, input validation and text tables.

Nothing here knows about employees or payroll rules, so these functions can
be reused anywhere in the project.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# Accepted input types for money and hours. Floats are excluded on purpose:
# they cannot represent most decimal amounts exactly.
Amount = Decimal | int | str

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def to_money(amount: Decimal) -> Decimal:
    """Round an amount to cents, rounding halves up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def format_money(amount: Decimal) -> str:
    """Round to cents and add thousands separators (60000 -> '60,000.00')."""
    return f"{to_money(amount):,}"


def require_non_negative(value: Decimal, field: str) -> None:
    """Raise ValueError if a numeric field is negative."""
    if value < 0:
        raise ValueError(f"{field} cannot be negative (got {value})")


def to_amount(
    value: object,
    field: str,
    *,
    positive: bool = False,
    maximum: Decimal | None = None,
) -> Decimal:
    """Convert an int, numeric string or Decimal to a validated Decimal.

    Args:
        value: The raw input. Floats and bools are rejected.
        field: Field name used in error messages.
        positive: If True, the amount must be greater than 0.
        maximum: If given, the amount must not exceed it.

    Returns:
        The amount as a finite, non-negative Decimal within range.

    Raises:
        TypeError: If value is not a Decimal, int or str.
        ValueError: If value is not a number or is out of range.
    """
    # bool is a subclass of int, so it has to be excluded explicitly.
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise TypeError(
            f"{field} must be a Decimal, int or numeric string "
            f"(got {value!r})"
        )
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise ValueError(
            f"{field} is not a valid number (got {value!r})"
        ) from None
    if not amount.is_finite():
        raise ValueError(f"{field} must be a finite number (got {value!r})")
    if positive and amount <= 0:
        raise ValueError(f"{field} must be greater than 0 (got {amount})")
    require_non_negative(amount, field)
    if maximum is not None and amount > maximum:
        raise ValueError(f"{field} cannot exceed {maximum} (got {amount})")
    return amount


def format_row(cells: list[str], widths: list[int]) -> str:
    """Join cells into one fixed-width table row.

    A positive width left-aligns its cell; a negative width right-aligns it.
    """
    return "".join(
        f"{cell:<{width}}" if width > 0 else f"{cell:>{-width}}"
        for cell, width in zip(cells, widths)
    )
