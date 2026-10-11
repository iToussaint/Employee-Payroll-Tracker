from decimal import Decimal

import pytest

from payroll_tracker.utils import (
    format_money,
    format_row,
    progressive_tax,
    require_non_negative,
    to_amount,
    to_money,
)


def test_to_money_rounds_half_up_to_cents() -> None:
    assert to_money(Decimal("10.005")) == Decimal("10.01")
    assert to_money(Decimal("10")) == Decimal("10.00")


def test_require_non_negative() -> None:
    require_non_negative(Decimal("0"), "x")
    with pytest.raises(ValueError, match="x cannot be negative"):
        require_non_negative(Decimal("-0.01"), "x")


def test_format_row_alignment() -> None:
    assert format_row(["ab", "7"], [4, -3]) == "ab    7"


@pytest.mark.parametrize(
    ("taxable", "expected"),
    [
        ("0", "0.00"),
        ("1000", "0.00"),  # entirely in the 0% band
        ("1500", "50.00"),  # 500 at 10%
        ("3000", "200.00"),  # 2000 at 10%
        ("6000", "800.00"),  # 200 + 3000 at 20%
        ("7000", "1100.00"),  # 800 + 1000 at 30%
    ],
)
def test_progressive_tax_bands(taxable: str, expected: str) -> None:
    assert progressive_tax(Decimal(taxable)) == Decimal(expected)


def test_to_amount_converts_int_and_str() -> None:
    assert to_amount(5, "x") == Decimal("5")
    assert to_amount("2.50", "x") == Decimal("2.50")
    with pytest.raises(TypeError):
        to_amount(True, "x")


def test_format_money_adds_separators_and_cents() -> None:
    assert format_money(Decimal("60000")) == "60,000.00"
    assert format_money(Decimal("1234.565")) == "1,234.57"
