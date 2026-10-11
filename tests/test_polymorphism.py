from decimal import Decimal

from payroll_tracker.employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
    PayDetail,
)
from payroll_tracker.payroll import process_payroll, summarize_by_role
from payroll_tracker.reports import (
    generate_report,
    payroll_table_report,
    role_summary_report,
)

EMPLOYEES: list[Employee] = [
    FullTimeEmployee("FT1", "Ama", annual_salary=60000, bonus=500),
    ContractEmployee("CT1", "Kwame", hourly_rate=20, hours_worked=170),
    Intern("IN1", "Esi", stipend=800),
    FullTimeEmployee("FT2", "Yaw", annual_salary=84000),
]


class Consultant(Employee):
    """A role defined only in this test: reports must handle it unchanged."""

    ROLE = "consultant"
    ROLE_TITLE = "Consultant"

    def calculate_salary(self) -> Decimal:
        return Decimal("3000.00")

    def pay_details(self) -> list[PayDetail]:
        return [
            PayDetail("Day rate", Decimal("300")),
            PayDetail("Days worked", Decimal("10"), "hours"),
        ]


def test_same_method_gives_role_specific_results() -> None:
    salaries = [employee.calculate_salary() for employee in EMPLOYEES]
    assert salaries == [
        Decimal("5500.00"),  # 60000 / 12 + 500 bonus
        Decimal("3500.00"),  # 160h * 20 + 10h overtime * 30
        Decimal("800.00"),  # stipend
        Decimal("7000.00"),  # 84000 / 12
    ]


def test_report_shows_full_time_details() -> None:
    report = generate_report(EMPLOYEES[0])
    assert "PAYSLIP - Full-time Employee" in report
    assert "Annual salary" in report and "60,000.00" in report
    assert "Bonus" in report
    assert "Tax (progressive bands)" in report
    assert "Hourly rate" not in report


def test_report_shows_contract_details() -> None:
    report = generate_report(EMPLOYEES[1])
    assert "PAYSLIP - Contract Employee" in report
    assert "Overtime hours (x1.5)" in report
    assert "Overtime pay" in report and "300.00" in report
    assert "Tax (flat 15% withholding)" in report
    assert "Annual salary" not in report


def test_report_shows_intern_details() -> None:
    report = generate_report(EMPLOYEES[2])
    assert "PAYSLIP - Intern" in report
    assert "Monthly stipend" in report
    assert "Bonus" not in report and "Overtime" not in report


def test_report_net_pay_matches_payslip() -> None:
    payroll = process_payroll(EMPLOYEES)
    for employee in EMPLOYEES:
        net = payroll[employee.employee_id]["net_pay"]
        net_line = generate_report(employee).splitlines()[-2]
        assert net_line.startswith("NET PAY")
        assert net_line.endswith(f"{net:,}")


def test_report_lines_have_no_trailing_spaces() -> None:
    for employee in EMPLOYEES:
        for line in generate_report(employee).splitlines():
            assert line == line.rstrip()


def test_summarize_by_role_groups_and_totals() -> None:
    summary = summarize_by_role(EMPLOYEES)
    assert list(summary) == [
        "Full-time Employee",
        "Contract Employee",
        "Intern",
    ]
    full_time = summary["Full-time Employee"]
    assert full_time["headcount"] == 2
    assert full_time["gross_pay"] == Decimal("12500.00")
    assert full_time["pension"] == Decimal("600.00")
    assert summary["Intern"]["net_pay"] == Decimal("800.00")


def test_role_summary_report_lists_only_roles_present() -> None:
    report = role_summary_report([EMPLOYEES[2]])
    assert "Intern" in report
    assert "Full-time Employee" not in report


def test_new_role_works_without_changing_report_code() -> None:
    consultant = Consultant("CO1", "Kofi")
    report = generate_report(consultant)
    assert "PAYSLIP - Consultant" in report
    assert "Day rate" in report and "300.00" in report
    assert "Tax (progressive bands)" in report  # inherited default
    everyone = [consultant, *EMPLOYEES]
    assert "Consultant" in role_summary_report(everyone)
    assert "Consultant" in payroll_table_report(everyone)
