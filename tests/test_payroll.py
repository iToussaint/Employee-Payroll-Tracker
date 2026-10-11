from decimal import Decimal

import pytest

from payroll_tracker.employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
)
from payroll_tracker.payroll import (
    apply_tax,
    calculate_salary,
    generate_payslip,
    payroll_table_report,
    payroll_totals,
    process_payroll,
    sum_payslips,
)

FULL_TIMER = FullTimeEmployee("FT1", "A", annual_salary=60000, bonus=500)
CONTRACTOR = ContractEmployee("CT1", "B", hourly_rate=20, hours_worked=100)
INTERN = Intern("IN1", "C", stipend=800)


@pytest.mark.parametrize(
    ("employee", "expected"),
    [(FULL_TIMER, "5500.00"), (CONTRACTOR, "2000.00"), (INTERN, "800.00")],
)
def test_calculate_salary_dispatches_by_type(
    employee: Employee, expected: str
) -> None:
    assert calculate_salary(employee) == Decimal(expected)


def test_apply_tax_uses_each_role_rule() -> None:
    amount = Decimal("2000")
    assert apply_tax(CONTRACTOR, amount) == Decimal("300.00")  # flat 15%
    assert apply_tax(FULL_TIMER, amount) == Decimal("100.00")  # bands
    assert apply_tax(INTERN, amount) == Decimal("100.00")  # bands


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
        "role_title": "Full-time Employee",
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
    assert payroll_totals(payroll) == {
        "gross_pay": Decimal("8300.00"),
        "tax": Decimal("950.00"),
        "pension": Decimal("250.00"),
        "net_pay": Decimal("7100.00"),
    }


def test_sum_payslips_of_nothing_is_zero() -> None:
    assert sum_payslips([]) == {
        "gross_pay": Decimal("0.00"),
        "tax": Decimal("0.00"),
        "pension": Decimal("0.00"),
        "net_pay": Decimal("0.00"),
    }


def test_duplicate_ids_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        process_payroll([INTERN, Intern("IN1", "Other", stipend=1)])


def test_payroll_table_report() -> None:
    lines = payroll_table_report([FULL_TIMER, INTERN]).splitlines()
    assert lines[0] == "PAYROLL TABLE"
    assert "Full-time Employee" in lines[3] and "5,500.00" in lines[3]
    assert "Intern" in lines[4]
    assert lines[-1].startswith("TOTAL") and "6,300.00" in lines[-1]
