"""Tests for utils.py: validation, money, tax rules and formatting."""

from decimal import Decimal

import pytest

from utils import (
    CONTRACT,
    FULL_TIME,
    INTERN,
    TAX_BANDS,
    apply_tax,
    format_money,
    format_row,
    progressive_tax,
    tax_basis,
    to_amount,
    to_money,
    to_text,
)


def test_to_money_rounds_half_up_to_cents() -> None:
    assert to_money(Decimal("10.005")) == Decimal("10.01")
    assert to_money(Decimal("10")) == Decimal("10.00")


def test_format_money_adds_separators_and_cents() -> None:
    assert format_money(Decimal("60000")) == "60,000.00"
    assert format_money(Decimal("1234.565")) == "1,234.57"


def test_to_amount_converts_numbers_and_strings() -> None:
    assert to_amount(5, "x") == Decimal("5")
    assert to_amount("2.50", "x") == Decimal("2.50")
    assert to_amount(0.1, "x") == Decimal("0.1")  # exact, not 0.1000000...


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("abc", "not a valid number"),
        ("NaN", "finite"),
        (-1, "cannot be negative"),
    ],
)
def test_to_amount_rejects_bad_values(value: str | int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        to_amount(value, "x")


def test_to_amount_ranges() -> None:
    assert to_amount(0, "x") == 0
    with pytest.raises(ValueError, match="greater than 0"):
        to_amount(0, "x", positive=True)
    with pytest.raises(ValueError, match="cannot exceed 10"):
        to_amount(11, "x", maximum=Decimal("10"))


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


def test_format_row_alignment() -> None:
    assert format_row(["ab", "7"], [(4, "<"), (3, ">")]) == "ab    7"


def test_format_row_rejects_mismatched_cells() -> None:
    with pytest.raises(ValueError):
        format_row(["only one"], [(4, "<"), (3, ">")])


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (CONTRACT, "300.00"),  # flat 15% of 2000
        (FULL_TIME, "100.00"),  # bands: 0 + 100
        (INTERN, "100.00"),  # bands: 0 + 100
    ],
)
def test_apply_tax_picks_rule_by_role(role: str, expected: str) -> None:
    assert apply_tax(Decimal("2000"), role) == Decimal(expected)


def test_apply_tax_rejects_unknown_role() -> None:
    with pytest.raises(ValueError, match="No tax rule for role 'Manager'"):
        apply_tax(Decimal("2000"), "Manager")


def test_tax_basis_describes_each_rule() -> None:
    assert tax_basis(CONTRACT) == "flat 15%"
    assert tax_basis(FULL_TIME) == "progressive bands"
    assert tax_basis(INTERN) == "progressive bands"


def test_tax_bands_cannot_be_modified() -> None:
    assert isinstance(TAX_BANDS, tuple)
    with pytest.raises(TypeError):
        TAX_BANDS[0] = (None, Decimal("0"))  # type: ignore[index]


def test_to_text_strips_and_rejects_empty() -> None:
    assert to_text("  Ama Mensah ", "name") == "Ama Mensah"
    with pytest.raises(ValueError, match="name cannot be empty"):
        to_text("   ", "name")
