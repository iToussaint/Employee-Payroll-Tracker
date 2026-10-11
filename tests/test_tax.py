from decimal import Decimal

import pytest

from payroll_tracker.tax import (
    CONTRACT_WITHHOLDING,
    STANDARD_TAX,
    FlatTax,
    ProgressiveTax,
    TaxPolicy,
)


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
def test_standard_progressive_bands(taxable: str, expected: str) -> None:
    assert STANDARD_TAX.calculate(Decimal(taxable)) == Decimal(expected)


def test_custom_progressive_bands() -> None:
    policy = ProgressiveTax([(Decimal("100"), Decimal("0")),
                             (None, Decimal("0.5"))])
    assert policy.calculate(Decimal("300")) == Decimal("100.00")


@pytest.mark.parametrize(
    "bands",
    [
        [],
        [(None, Decimal("0.1")), (Decimal("100"), Decimal("0.2"))],
    ],
)
def test_invalid_bands_rejected(
    bands: list[tuple[Decimal | None, Decimal]],
) -> None:
    with pytest.raises(ValueError, match="band"):
        ProgressiveTax(bands)


def test_flat_tax() -> None:
    assert CONTRACT_WITHHOLDING.calculate(Decimal("2000")) == Decimal("300.00")
    assert CONTRACT_WITHHOLDING.description == "flat 15% withholding"


@pytest.mark.parametrize("rate", ["-0.1", "1.1"])
def test_flat_tax_rate_must_be_a_fraction(rate: str) -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        FlatTax(Decimal(rate))


@pytest.mark.parametrize("policy", [STANDARD_TAX, CONTRACT_WITHHOLDING])
def test_policies_reject_negative_amounts(policy: TaxPolicy) -> None:
    with pytest.raises(ValueError, match="negative"):
        policy.calculate(Decimal("-1"))


def test_tax_policy_is_abstract() -> None:
    with pytest.raises(TypeError):
        TaxPolicy()  # type: ignore[abstract]
