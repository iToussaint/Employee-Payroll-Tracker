from decimal import Decimal

import pytest

from payroll_tracker.utils import format_row, require_non_negative, to_money


def test_to_money_rounds_half_up_to_cents() -> None:
    assert to_money(Decimal("10.005")) == Decimal("10.01")
    assert to_money(Decimal("10")) == Decimal("10.00")


def test_require_non_negative() -> None:
    require_non_negative(Decimal("0"), "x")
    with pytest.raises(ValueError, match="x cannot be negative"):
        require_non_negative(Decimal("-0.01"), "x")


def test_format_row_alignment() -> None:
    assert format_row(["ab", "7"], [4, -3]) == "ab    7"
