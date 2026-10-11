"""Tests for payroll.py: payslips, processing and summaries by role."""

from decimal import Decimal

import pytest

from employee import ContractEmployee, Employee, FullTimeEmployee, Intern
from payroll import generate_payslip, process_payroll, summarize_by_role

FULL_TIMER = FullTimeEmployee("FT1", "A", annual_salary=60000, bonus=500)
CONTRACTOR = ContractEmployee("CT1", "B", hourly_rate=20, hours_worked=100)
INTERN = Intern("IN1", "C", stipend=800)


@pytest.mark.parametrize(
    ("employee", "gross", "tax", "net"),
    [
        (FULL_TIMER, "5500.00", "700.00", "4800.00"),  # bands
        (CONTRACTOR, "2000.00", "300.00", "1700.00"),  # flat 15%
        (INTERN, "800.00", "0.00", "800.00"),  # below first band
    ],
)
def test_generate_payslip_for_each_role(
    employee: Employee, gross: str, tax: str, net: str
) -> None:
    slip = generate_payslip(employee)
    assert slip["gross_pay"] == Decimal(gross)
    assert slip["tax"] == Decimal(tax)
    assert slip["net_pay"] == Decimal(net)


def test_generate_payslip_fields() -> None:
    assert generate_payslip(FULL_TIMER) == {
        "employee_id": "FT1",
        "name": "A",
        "role": "Full-time Employee",
        "gross_pay": Decimal("5500.00"),
        "tax": Decimal("700.00"),
        "net_pay": Decimal("4800.00"),
    }


def test_process_payroll_maps_ids_to_payslips() -> None:
    payroll = process_payroll([INTERN, CONTRACTOR, FULL_TIMER])
    assert list(payroll) == ["IN1", "CT1", "FT1"]
    assert payroll["CT1"]["net_pay"] == Decimal("1700.00")


def test_duplicate_ids_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        process_payroll([INTERN, Intern("IN1", "Other", stipend=1)])


def test_summarize_by_role() -> None:
    other_intern = Intern("IN2", "D", stipend=1500)
    payroll = process_payroll([INTERN, FULL_TIMER, other_intern])
    summary = summarize_by_role(payroll)
    assert list(summary) == ["Intern", "Full-time Employee"]
    assert summary["Intern"] == {
        "headcount": 2,
        "gross_pay": Decimal("2300.00"),
        "tax": Decimal("50.00"),  # 0 on 800, 50 on 1500
        "net_pay": Decimal("2250.00"),
    }
