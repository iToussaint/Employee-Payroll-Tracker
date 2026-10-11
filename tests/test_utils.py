from decimal import Decimal

import pytest

from payroll_tracker.utils import (
    format_money,
    format_row,
    require_non_negative,
    to_amount,
    to_money,
)


def test_to_money_rounds_half_up_to_cents() -> None:
    assert to_money(Decimal("10.005")) == Decimal("10.01")
    assert to_money(Decimal("10")) == Decimal("10.00")


def test_format_money_adds_separators_and_cents() -> None:
    assert format_money(Decimal("60000")) == "60,000.00"
    assert format_money(Decimal("1234.565")) == "1,234.57"


def test_require_non_negative() -> None:
    require_non_negative(Decimal("0"), "x")
    with pytest.raises(ValueError, match="x cannot be negative"):
        require_non_negative(Decimal("-0.01"), "x")


def test_to_amount_converts_int_and_str() -> None:
    assert to_amount(5, "x") == Decimal("5")
    assert to_amount("2.50", "x") == Decimal("2.50")


@pytest.mark.parametrize("bad", [True, 1.5, None, [1]])
def test_to_amount_rejects_wrong_types(bad: object) -> None:
    with pytest.raises(TypeError, match="x must be"):
        to_amount(bad, "x")


def test_to_amount_ranges() -> None:
    assert to_amount(0, "x") == 0
    with pytest.raises(ValueError, match="greater than 0"):
        to_amount(0, "x", positive=True)
    with pytest.raises(ValueError, match="cannot exceed 10"):
        to_amount(11, "x", maximum=Decimal("10"))


def test_format_row_alignment() -> None:
    assert format_row(["ab", "7"], [4, -3]) == "ab    7"
