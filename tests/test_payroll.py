from decimal import Decimal

import pytest

from payroll_tracker.employee import ContractEmployee, Employee, FullTimeEmployee, Intern
from payroll_tracker.payroll import (
    apply_tax,
    calculate_salary,
    generate_payslip,
    payroll_totals,
    process_payroll,
)

FULL_TIMER = FullTimeEmployee("FT1", "A", annual_salary=Decimal("60000"), bonus=Decimal("500"))
CONTRACTOR = ContractEmployee("CT1", "B", hourly_rate=Decimal("20"), hours_worked=Decimal("100"))
INTERN = Intern("IN1", "C", stipend=Decimal("800"))


@pytest.mark.parametrize(
    ("employee", "expected"),
    [(FULL_TIMER, "5500.00"), (CONTRACTOR, "2000.00"), (INTERN, "800.00")],
)
def test_calculate_salary_dispatches_by_type(employee: Employee, expected: str) -> None:
    assert calculate_salary(employee) == Decimal(expected)


def test_apply_tax_uses_each_role_rule() -> None:
    assert apply_tax(CONTRACTOR, Decimal("2000")) == Decimal("300.00")  # flat 15%
    assert apply_tax(FULL_TIMER, Decimal("2000")) == Decimal("100.00")  # bands
    assert apply_tax(INTERN, Decimal("2000")) == Decimal("100.00")  # bands


def test_apply_tax_rejects_negative_amount() -> None:
    with pytest.raises(ValueError, match="negative"):
        apply_tax(CONTRACTOR, Decimal("-1"))
    with pytest.raises(ValueError, match="negative"):
        apply_tax(INTERN, Decimal("-1"))


def test_generate_payslip_full_time() -> None:
    # gross 5000 + 500; pension 5% of 5000 = 250; taxable 5250 -> tax 650
    assert generate_payslip(FULL_TIMER) == {
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
    assert contract_slip["pension"] == Decimal("0.00")
    assert contract_slip["net_pay"] == Decimal("1700.00")

    intern_slip = generate_payslip(INTERN)
    assert intern_slip["tax"] == Decimal("0.00")
    assert intern_slip["net_pay"] == Decimal("800.00")


def test_process_payroll_handles_mixed_employee_types() -> None:
    payroll = process_payroll([INTERN, CONTRACTOR, FULL_TIMER])
    assert list(payroll) == ["IN1", "CT1", "FT1"]
    totals = payroll_totals(payroll)
    assert totals == {
        "gross_pay": Decimal("8300.00"),
        "tax": Decimal("950.00"),
        "pension": Decimal("250.00"),
        "net_pay": Decimal("7100.00"),
    }


def test_duplicate_ids_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        process_payroll([INTERN, Intern("IN1", "Other", stipend=1)])
