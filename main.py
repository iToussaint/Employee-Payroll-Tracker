"""Entry point: an interactive menu to enter employees and print payslips.

This module handles the command line and presentation: it reads input,
formats the results produced by payroll.py and prints them. Run with:
    python main.py
"""

import sys
from collections.abc import Callable

from employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
    PayDetail,
)
from payroll import RoleSummary, process_payroll, summarize_by_role
from utils import Column, format_money, format_row

# A function that shows a prompt and returns what the user typed. main()
# uses the built-in input(); tests pass in scripted answers instead.
InputFn = Callable[[str], str]

REPORT_WIDTH = 44
VALUE_WIDTH = 16

# Summary table columns: Role, Count, Gross, Tax, Net.
SUMMARY_COLUMNS: list[Column] = [
    (19, "<"), (6, ">"), (12, ">"), (11, ">"), (12, ">"),
]

# Menu options as (key, description), in display order.
MENU: tuple[tuple[str, str], ...] = (
    ("1", "Add a full-time employee"),
    ("2", "Add a contract employee"),
    ("3", "Add an intern"),
    ("4", "Load the sample employees"),
    ("5", "Show payslips and summary"),
    ("6", "Exit"),
)


def sample_employees() -> list[Employee]:
    """Return demo employee records covering every role."""
    # A list keeps the records in the order the payslips are printed.
    return [
        FullTimeEmployee(
            "FT001", "Ama Mensah", annual_salary=60000, bonus=500
        ),
        ContractEmployee(
            "CT001", "Kwame Boateng", hourly_rate=25, hours_worked=172
        ),
        Intern("IN001", "Esi Owusu", stipend=1200),
        FullTimeEmployee("FT002", "Yaw Asante", annual_salary=84000),
        Intern("IN002", "Abena Darko", stipend=900),
    ]


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def _report_line(label: str, value: str) -> str:
    return f"{label:<{REPORT_WIDTH - VALUE_WIDTH}}{value:>{VALUE_WIDTH}}"


def format_detail(detail: PayDetail) -> str:
    """Format a pay detail's value for display, based on its unit."""
    if detail.unit == "hours":
        return f"{detail.value:,}"
    return format_money(detail.value)


def format_payslip(employee: Employee) -> str:
    """Return a payslip report whose pay section depends on the role.

    The function never checks the employee's type: each role supplies its
    own pay details and tax basis.
    """
    rule = "-" * REPORT_WIDTH
    double_rule = "=" * REPORT_WIDTH
    detail_lines = [
        _report_line(detail.label, format_detail(detail))
        for detail in employee.pay_details()
    ]
    tax_label = f"Tax ({employee.tax_basis})"
    return "\n".join([
        double_rule,
        f"PAYSLIP - {employee.role}".center(REPORT_WIDTH).rstrip(),
        double_rule,
        _report_line("Employee ID", employee.employee_id),
        _report_line("Name", employee.name),
        rule,
        *detail_lines,
        rule,
        _report_line("Gross pay", format_money(employee.salary)),
        _report_line(tax_label, format_money(employee.tax)),
        rule,
        _report_line("NET PAY", format_money(employee.net_pay)),
        double_rule,
    ])


def format_role_summary(summary: dict[str, RoleSummary]) -> str:
    """Return a table of headcount and pay subtotals for each role."""
    header = format_row(
        ["Role", "Count", "Gross", "Tax", "Net"], SUMMARY_COLUMNS
    )
    rows = [
        format_row(
            [
                role,
                str(group["headcount"]),
                format_money(group["gross_pay"]),
                format_money(group["tax"]),
                format_money(group["net_pay"]),
            ],
            SUMMARY_COLUMNS,
        )
        for role, group in summary.items()
    ]
    return "\n".join(
        ["PAYROLL SUMMARY BY ROLE", header, "-" * len(header), *rows]
    )


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------


def print_menu() -> None:
    """Print the numbered menu options."""
    print()
    for key, description in MENU:
        print(f"  {key}. {description}")


def ask(prompt: str, read: InputFn) -> str:
    """Show a prompt and return the answer without surrounding spaces."""
    return read(prompt).strip()


def add_employee(
    choice: str, employees: list[Employee], read: InputFn
) -> None:
    """Ask for one employee's details and add them to the list.

    Invalid details (an empty name, a salary of 0, a duplicate ID, ...) are
    reported and nothing is added, so the user can simply try again.
    """
    existing_ids = {employee.employee_id for employee in employees}
    employee_id = ask("Employee ID: ", read)
    if employee_id in existing_ids:
        print(f"Error: employee ID {employee_id} is already in use.")
        return
    name = ask("Name: ", read)

    # The role decides which pay details to ask for.
    employee: Employee
    try:
        if choice == "1":
            annual_salary = ask("Annual salary: ", read)
            bonus = ask("Bonus (press Enter for none): ", read) or "0"
            employee = FullTimeEmployee(
                employee_id, name, annual_salary, bonus
            )
        elif choice == "2":
            hourly_rate = ask("Hourly rate: ", read)
            hours_worked = ask("Hours worked this month: ", read)
            employee = ContractEmployee(
                employee_id, name, hourly_rate, hours_worked
            )
        else:
            stipend = ask("Monthly stipend: ", read)
            employee = Intern(employee_id, name, stipend)
    except ValueError as error:
        print(f"Error: {error}. Employee not added.")
        return

    employees.append(employee)
    print(f"Added {employee.role} {employee.name} ({employee.employee_id}).")


def load_samples(employees: list[Employee]) -> None:
    """Add the sample employees whose IDs are not already in the list."""
    existing_ids = {employee.employee_id for employee in employees}
    new = [e for e in sample_employees() if e.employee_id not in existing_ids]
    employees.extend(new)
    print(f"Loaded {len(new)} sample employee(s).")


def show_payroll(employees: list[Employee]) -> None:
    """Print every payslip, then the summary by role."""
    if not employees:
        print("No employees yet. Add one, or load the samples (option 4).")
        return
    payroll = process_payroll(employees)
    for employee in employees:
        print()
        print(format_payslip(employee))
    print()
    print(format_role_summary(summarize_by_role(payroll)))


def main(read: InputFn = input) -> int:
    """Run the menu until the user exits; return an exit code (0 = ok)."""
    employees: list[Employee] = []
    print("EMPLOYEE PAYROLL TRACKER")

    # Ctrl+C, or the end of piped input, ends the program cleanly instead
    # of printing a traceback.
    try:
        while True:
            print_menu()
            choice = ask(f"Choose an option (1-{len(MENU)}): ", read)
            if choice in ("1", "2", "3"):
                add_employee(choice, employees, read)
            elif choice == "4":
                load_samples(employees)
            elif choice == "5":
                show_payroll(employees)
            elif choice == "6":
                break
            else:
                print(f"'{choice}' is not an option. Enter a number from "
                      f"1 to {len(MENU)}.")
    except (EOFError, KeyboardInterrupt):
        print()

    print("Goodbye.")
    return 0


if __name__ == "__main__":
    # Pass main()'s exit code back to the shell.
    sys.exit(main())
