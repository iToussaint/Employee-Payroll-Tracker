"""Entry point: runs a sample payroll and prints payslips and payroll reports."""

from decimal import Decimal

from payroll_tracker.employee import ContractEmployee, Employee, FullTimeEmployee, Intern
from payroll_tracker.payroll import (
    generate_report,
    payroll_totals,
    process_payroll,
    role_summary_report,
)
from payroll_tracker.utils import format_row

SAMPLE_EMPLOYEES: list[Employee] = [
    FullTimeEmployee("FT001", "Ama Mensah", annual_salary=Decimal("60000"), bonus=Decimal("500")),
    ContractEmployee("CT001", "Kwame Boateng", hourly_rate=Decimal("25"), hours_worked=Decimal("172")),
    Intern("IN001", "Esi Owusu", stipend=Decimal("1200")),
    FullTimeEmployee("FT002", "Yaw Asante", annual_salary=Decimal("84000")),
    Intern("IN002", "Abena Darko", stipend=Decimal("900")),
]

# Positive widths left-align, negative widths right-align.
COLUMN_WIDTHS = [7, 16, 11, -10, -10, -10, -10]


def print_payroll_table(employees: list[Employee]) -> None:
    payroll = process_payroll(employees)
    header = format_row(["ID", "Name", "Role", "Gross", "Tax", "Pension", "Net"], COLUMN_WIDTHS)
    print(header)
    print("-" * len(header))
    for slip in payroll.values():
        cells = [
            slip["id"],
            slip["name"],
            slip["role"],
            str(slip["gross_pay"]),
            str(slip["tax"]),
            str(slip["pension"]),
            str(slip["net_pay"]),
        ]
        print(format_row(cells, COLUMN_WIDTHS))
    totals = payroll_totals(payroll)
    print("-" * len(header))
    total_cells = ["TOTAL", "", ""] + [str(amount) for amount in totals.values()]
    print(format_row(total_cells, COLUMN_WIDTHS))


def main() -> None:
    for employee in SAMPLE_EMPLOYEES:
        print(generate_report(employee))
        print()
    print(role_summary_report(SAMPLE_EMPLOYEES))
    print()
    print_payroll_table(SAMPLE_EMPLOYEES)


if __name__ == "__main__":
    main()
