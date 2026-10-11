"""Tests that the same methods and reports behave differently per role."""

from decimal import Decimal

from employee import ContractEmployee, Employee, FullTimeEmployee, Intern
from main import format_payslip, format_role_summary
from payroll import process_payroll, summarize_by_role

EMPLOYEES: list[Employee] = [
    FullTimeEmployee("FT1", "Ama", annual_salary=60000, bonus=500),
    ContractEmployee("CT1", "Kwame", hourly_rate=20, hours_worked=170),
    Intern("IN1", "Esi", stipend=800),
]


def test_same_method_gives_role_specific_results() -> None:
    salaries = [employee.calculate_salary() for employee in EMPLOYEES]
    assert salaries == [
        Decimal("5500.00"),  # 60000 / 12 + 500 bonus
        Decimal("3400.00"),  # 170 hours * 20
        Decimal("800.00"),  # stipend
    ]


def test_report_shows_full_time_details() -> None:
    report = format_payslip(EMPLOYEES[0])
    assert "PAYSLIP - Full-time Employee" in report
    assert "Annual salary" in report and "60,000.00" in report
    assert "Bonus" in report
    assert "Tax (progressive bands)" in report
    assert "Hourly rate" not in report


def test_report_shows_contract_details() -> None:
    report = format_payslip(EMPLOYEES[1])
    assert "PAYSLIP - Contract Employee" in report
    assert "Hours worked" in report and "170" in report
    assert "Tax (flat 15%)" in report
    assert "Annual salary" not in report


def test_report_shows_intern_details() -> None:
    report = format_payslip(EMPLOYEES[2])
    assert "PAYSLIP - Intern" in report
    assert "Monthly stipend" in report
    assert "Bonus" not in report and "Hourly rate" not in report


def test_report_net_pay_matches_payslip() -> None:
    payroll = process_payroll(EMPLOYEES)
    for employee in EMPLOYEES:
        net = payroll[employee.employee_id]["net_pay"]
        net_line = format_payslip(employee).splitlines()[-2]
        assert net_line.startswith("NET PAY")
        assert net_line.endswith(f"{net:,}")


def test_role_summary_lists_each_role() -> None:
    summary = summarize_by_role(process_payroll(EMPLOYEES))
    report = format_role_summary(summary)
    lines = report.splitlines()
    assert lines[0] == "PAYROLL SUMMARY BY ROLE"
    assert lines[3].startswith("Full-time Employee")
    assert lines[4].startswith("Contract Employee")
    assert lines[5].startswith("Intern")
