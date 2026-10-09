from decimal import Decimal

import pytest

from payroll_tracker.employee import ContractRecord, EmployeeRecord, FullTimeRecord, InternRecord
from payroll_tracker.payroll import (
    apply_tax,
    calculate_pension,
    calculate_salary,
    contract_gross,
    generate_payslip,
    payroll_totals,
    process_payroll,
    progressive_tax,
)

FULL_TIMER: FullTimeRecord = {
    "id": "FT1",
    "name": "A",
    "role": "full_time",
    "annual_salary": Decimal("60000"),
    "bonus": Decimal("500"),
}
CONTRACTOR: ContractRecord = {
    "id": "CT1",
    "name": "B",
    "role": "contract",
    "hourly_rate": Decimal("20"),
    "hours_worked": Decimal("100"),
}
INTERN: InternRecord = {"id": "IN1", "name": "C", "role": "intern", "stipend": Decimal("800")}


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


def test_contract_gross_without_overtime() -> None:
    assert contract_gross(Decimal("20"), Decimal("160")) == Decimal("3200.00")


def test_contract_gross_with_overtime() -> None:
    # 160h * 20 + 10h * 20 * 1.5
    assert contract_gross(Decimal("20"), Decimal("170")) == Decimal("3500.00")


@pytest.mark.parametrize(
    ("record", "expected"),
    [(FULL_TIMER, "5500.00"), (CONTRACTOR, "2000.00"), (INTERN, "800.00")],
)
def test_calculate_salary_per_role(record: EmployeeRecord, expected: str) -> None:
    assert calculate_salary(record) == Decimal(expected)


def test_only_full_time_pays_pension() -> None:
    assert calculate_pension(FULL_TIMER) == Decimal("250.00")
    assert calculate_pension(CONTRACTOR) == Decimal("0.00")
    assert calculate_pension(INTERN) == Decimal("0.00")


def test_apply_tax_flat_for_contract_progressive_otherwise() -> None:
    assert apply_tax(Decimal("2000"), "contract") == Decimal("300.00")
    assert apply_tax(Decimal("2000"), "full_time") == Decimal("100.00")
    assert apply_tax(Decimal("2000"), "intern") == Decimal("100.00")


def test_apply_tax_rejects_unknown_role_and_negative_amount() -> None:
    with pytest.raises(ValueError, match="Unknown role"):
        apply_tax(Decimal("2000"), "manager")
    with pytest.raises(ValueError, match="negative"):
        apply_tax(Decimal("-1"), "contract")


def test_generate_payslip_full_time() -> None:
    slip = generate_payslip(FULL_TIMER)
    # gross 5000 + 500; pension 5% of 5000 = 250; taxable 5250 -> tax 650
    assert slip == {
        "id": "FT1",
        "name": "A",
        "role": "full_time",
        "gross_pay": Decimal("5500.00"),
        "tax": Decimal("650.00"),
        "pension": Decimal("250.00"),
        "net_pay": Decimal("4600.00"),
    }


def test_generate_payslip_contract_and_intern() -> None:
    contract_slip = generate_payslip(CONTRACTOR)
    assert contract_slip["tax"] == Decimal("300.00")
    assert contract_slip["net_pay"] == Decimal("1700.00")

    intern_slip = generate_payslip(INTERN)
    assert intern_slip["tax"] == Decimal("0.00")
    assert intern_slip["net_pay"] == Decimal("800.00")


def test_process_payroll_maps_ids_and_totals() -> None:
    payroll = process_payroll([INTERN, CONTRACTOR])
    assert list(payroll) == ["IN1", "CT1"]
    totals = payroll_totals(payroll)
    assert totals["gross_pay"] == Decimal("2800.00")
    assert totals["net_pay"] == Decimal("2500.00")


def test_duplicate_ids_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        process_payroll([INTERN, INTERN])
