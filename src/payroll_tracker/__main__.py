"""Run a sample payroll: python -m payroll_tracker"""

from decimal import Decimal

from payroll_tracker.payroll import EmployeeRecord, payroll_totals, process_payroll

SAMPLE_EMPLOYEES: list[EmployeeRecord] = [
    {
        "id": "FT001",
        "name": "Ama Mensah",
        "role": "full_time",
        "annual_salary": Decimal("60000"),
        "bonus": Decimal("500"),
    },
    {
        "id": "CT001",
        "name": "Kwame Boateng",
        "role": "contract",
        "hourly_rate": Decimal("25"),
        "hours_worked": Decimal("172"),
    },
    {
        "id": "IN001",
        "name": "Esi Owusu",
        "role": "intern",
        "stipend": Decimal("1200"),
    },
]


def main() -> None:
    payroll = process_payroll(SAMPLE_EMPLOYEES)
    header = f"{'ID':<7}{'Name':<16}{'Role':<11}{'Gross':>10}{'Tax':>10}{'Pension':>10}{'Net':>10}"
    print(header)
    print("-" * len(header))
    for emp_id, slip in payroll.items():
        print(
            f"{emp_id:<7}{slip['name']:<16}{slip['role']:<11}"
            f"{slip['gross_pay']:>10}{slip['tax']:>10}{slip['pension']:>10}{slip['net_pay']:>10}"
        )
    totals = payroll_totals(payroll)
    print("-" * len(header))
    print(
        f"{'TOTAL':<34}{totals['gross_pay']:>10}{totals['tax']:>10}"
        f"{totals['pension']:>10}{totals['net_pay']:>10}"
    )


if __name__ == "__main__":
    main()
