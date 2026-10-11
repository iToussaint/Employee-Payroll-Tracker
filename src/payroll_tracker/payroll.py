"""Payroll processing and reports for any mix of employee types.

These functions only call methods defined on the Employee base class, so they
work the same way for every subclass (polymorphism). Processing a list of
employees produces a dictionary that maps each employee ID to its payslip.
"""

from collections.abc import Iterable, Sequence
from decimal import Decimal
from typing import TypedDict

from payroll_tracker import utils
from payroll_tracker.employee import Employee


class PayTotals(TypedDict):
    """Money columns shared by payslips and summaries."""

    gross_pay: Decimal
    tax: Decimal
    pension: Decimal
    net_pay: Decimal


class Payslip(PayTotals):
    """One employee's pay for the month."""

    id: str
    name: str
    role: str
    role_title: str


class RoleSummary(PayTotals):
    """Headcount and pay subtotals for one role."""

    headcount: int


# Calculations


def calculate_salary(employee: Employee) -> Decimal:
    """Return monthly gross pay, using the employee's own role rule."""
    return employee.calculate_salary()


def apply_tax(employee: Employee, taxable: Decimal) -> Decimal:
    """Return tax on a taxable amount, using the employee's own tax rule."""
    return employee.calculate_tax(taxable)


def generate_payslip(employee: Employee) -> Payslip:
    """Build a full payslip: gross pay, pension, tax and net pay."""
    return {
        "id": employee.employee_id,
        "name": employee.name,
        "role": employee.role,
        "role_title": employee.ROLE_TITLE,
        "gross_pay": calculate_salary(employee),
        "tax": apply_tax(employee, employee.taxable_income),
        "pension": employee.pension,
        "net_pay": employee.net_pay,
    }


def process_payroll(employees: Iterable[Employee]) -> dict[str, Payslip]:
    """Generate payslips for every employee, keyed by employee ID.

    Raises:
        ValueError: If two employees share an ID.
    """
    payroll: dict[str, Payslip] = {}
    for employee in employees:
        if employee.employee_id in payroll:
            raise ValueError(
                f"Duplicate employee ID: {employee.employee_id}"
            )
        payroll[employee.employee_id] = generate_payslip(employee)
    return payroll


def sum_payslips(payslips: Iterable[Payslip]) -> PayTotals:
    """Add up the money columns of any number of payslips."""
    slips = list(payslips)
    return {
        "gross_pay": sum((s["gross_pay"] for s in slips), utils.ZERO),
        "tax": sum((s["tax"] for s in slips), utils.ZERO),
        "pension": sum((s["pension"] for s in slips), utils.ZERO),
        "net_pay": sum((s["net_pay"] for s in slips), utils.ZERO),
    }


def payroll_totals(payroll: dict[str, Payslip]) -> PayTotals:
    """Sum gross, tax, pension and net pay across a processed payroll."""
    return sum_payslips(payroll.values())


def summarize_by_role(
    employees: Sequence[Employee],
) -> dict[str, RoleSummary]:
    """Group payslips by role title, in order of first appearance."""
    groups: dict[str, list[Payslip]] = {}
    for slip in process_payroll(employees).values():
        groups.setdefault(slip["role_title"], []).append(slip)
    return {
        title: {"headcount": len(slips), **sum_payslips(slips)}
        for title, slips in groups.items()
    }


# Reports. These never check an employee's type: each employee supplies its
# own role title, pay details and tax basis, so new roles need no changes here.

REPORT_WIDTH = 44
VALUE_WIDTH = 16

# Positive widths left-align, negative widths right-align.
TABLE_WIDTHS = [7, 15, 19, -11, -11, -11, -11]
SUMMARY_WIDTHS = [19, -6, -12, -11, -11, -12]


def _report_line(label: str, value: str) -> str:
    return f"{label:<{REPORT_WIDTH - VALUE_WIDTH}}{value:>{VALUE_WIDTH}}"


def _money_cells(totals: PayTotals) -> list[str]:
    fields = (
        totals["gross_pay"], totals["tax"],
        totals["pension"], totals["net_pay"],
    )
    return [utils.format_money(amount) for amount in fields]


def generate_report(employee: Employee) -> str:
    """Return a detailed payslip whose pay section depends on the role."""
    rule = "-" * REPORT_WIDTH
    double_rule = "=" * REPORT_WIDTH
    detail_lines = [
        _report_line(label, value)
        for label, value in employee.pay_details()
    ]
    tax_label = f"Tax ({employee.tax_basis})"
    return "\n".join([
        double_rule,
        f"PAYSLIP - {employee.ROLE_TITLE}".center(REPORT_WIDTH).rstrip(),
        double_rule,
        _report_line("Employee ID", employee.employee_id),
        _report_line("Name", employee.name),
        rule,
        *detail_lines,
        rule,
        _report_line("Gross pay", utils.format_money(employee.salary)),
        _report_line("Pension", utils.format_money(employee.pension)),
        _report_line(tax_label, utils.format_money(employee.tax)),
        rule,
        _report_line("NET PAY", utils.format_money(employee.net_pay)),
        double_rule,
    ])


def role_summary_report(employees: Sequence[Employee]) -> str:
    """Return a table of headcount and pay subtotals for each role."""
    header = utils.format_row(
        ["Role", "Count", "Gross", "Tax", "Pension", "Net"], SUMMARY_WIDTHS
    )
    rows = [
        utils.format_row(
            [title, str(group["headcount"]), *_money_cells(group)],
            SUMMARY_WIDTHS,
        )
        for title, group in summarize_by_role(employees).items()
    ]
    return "\n".join(
        ["PAYROLL SUMMARY BY ROLE", header, "-" * len(header), *rows]
    )


def payroll_table_report(employees: Sequence[Employee]) -> str:
    """Return a one-line-per-employee payroll table with a totals row."""
    payroll = process_payroll(employees)
    header = utils.format_row(
        ["ID", "Name", "Role", "Gross", "Tax", "Pension", "Net"],
        TABLE_WIDTHS,
    )
    rule = "-" * len(header)
    rows = [
        utils.format_row(
            [slip["id"], slip["name"], slip["role_title"],
             *_money_cells(slip)],
            TABLE_WIDTHS,
        )
        for slip in payroll.values()
    ]
    total_row = utils.format_row(
        ["TOTAL", "", "", *_money_cells(payroll_totals(payroll))],
        TABLE_WIDTHS,
    )
    return "\n".join(
        ["PAYROLL TABLE", header, rule, *rows, rule, total_row]
    )
