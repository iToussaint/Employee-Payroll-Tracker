"""Text reports built from payroll data.

Reports depend only on the Reportable interface, never on concrete employee
classes, so a new role appears in every report without changes here. New
report types are added with @register_report, without editing existing code.
"""

from collections.abc import Callable, Sequence
from decimal import Decimal
from typing import Protocol

from payroll_tracker.employee import PayDetail
from payroll_tracker.payroll import (
    Payable,
    PayTotals,
    payroll_totals,
    process_payroll,
    summarize_by_role,
)
from payroll_tracker.utils import format_money, format_row


class Reportable(Payable, Protocol):
    """What a detailed payslip needs beyond the payroll figures."""

    @property
    def salary(self) -> Decimal:
        """Monthly gross pay."""
        ...

    @property
    def tax(self) -> Decimal:
        """Monthly tax."""
        ...

    @property
    def tax_basis(self) -> str:
        """Short description of how tax is calculated."""
        ...

    def pay_details(self) -> list[PayDetail]:
        """Return the figures that explain gross pay."""
        ...


ReportBuilder = Callable[[Sequence[Reportable]], str]

# Report name -> function, in the order "all" prints them.
REPORTS: dict[str, ReportBuilder] = {}


def register_report(name: str) -> Callable[[ReportBuilder], ReportBuilder]:
    """Register a report function under a name (used by the CLI)."""

    def decorator(builder: ReportBuilder) -> ReportBuilder:
        if name in REPORTS:
            raise ValueError(f"report {name!r} is already registered")
        REPORTS[name] = builder
        return builder

    return decorator


REPORT_WIDTH = 44
VALUE_WIDTH = 16

# Positive widths left-align, negative widths right-align.
TABLE_WIDTHS = [7, 15, 19, -11, -11, -11, -11]
SUMMARY_WIDTHS = [19, -6, -12, -11, -11, -12]


def format_detail(detail: PayDetail) -> str:
    """Format a pay detail's value according to its unit."""
    if detail.unit == "hours":
        return f"{detail.value:,}"
    return format_money(detail.value)


def _report_line(label: str, value: str) -> str:
    return f"{label:<{REPORT_WIDTH - VALUE_WIDTH}}{value:>{VALUE_WIDTH}}"


def _money_cells(totals: PayTotals) -> list[str]:
    fields = (
        totals["gross_pay"], totals["tax"],
        totals["pension"], totals["net_pay"],
    )
    return [format_money(amount) for amount in fields]


def generate_report(employee: Reportable) -> str:
    """Return a detailed payslip whose pay section depends on the role."""
    rule = "-" * REPORT_WIDTH
    double_rule = "=" * REPORT_WIDTH
    detail_lines = [
        _report_line(detail.label, format_detail(detail))
        for detail in employee.pay_details()
    ]
    tax_label = f"Tax ({employee.tax_basis})"
    return "\n".join([
        double_rule,
        f"PAYSLIP - {employee.role_title}".center(REPORT_WIDTH).rstrip(),
        double_rule,
        _report_line("Employee ID", employee.employee_id),
        _report_line("Name", employee.name),
        rule,
        *detail_lines,
        rule,
        _report_line("Gross pay", format_money(employee.salary)),
        _report_line("Pension", format_money(employee.pension)),
        _report_line(tax_label, format_money(employee.tax)),
        rule,
        _report_line("NET PAY", format_money(employee.net_pay)),
        double_rule,
    ])


@register_report("payslips")
def payslips_report(employees: Sequence[Reportable]) -> str:
    """Return a detailed payslip for each employee."""
    return "\n\n".join(generate_report(employee) for employee in employees)


@register_report("summary")
def role_summary_report(employees: Sequence[Reportable]) -> str:
    """Return a table of headcount and pay subtotals for each role."""
    header = format_row(
        ["Role", "Count", "Gross", "Tax", "Pension", "Net"], SUMMARY_WIDTHS
    )
    rows = [
        format_row(
            [title, str(group["headcount"]), *_money_cells(group)],
            SUMMARY_WIDTHS,
        )
        for title, group in summarize_by_role(employees).items()
    ]
    return "\n".join(
        ["PAYROLL SUMMARY BY ROLE", header, "-" * len(header), *rows]
    )


@register_report("table")
def payroll_table_report(employees: Sequence[Reportable]) -> str:
    """Return a one-line-per-employee payroll table with a totals row."""
    payroll = process_payroll(employees)
    header = format_row(
        ["ID", "Name", "Role", "Gross", "Tax", "Pension", "Net"],
        TABLE_WIDTHS,
    )
    rule = "-" * len(header)
    rows = [
        format_row(
            [slip["id"], slip["name"], slip["role_title"],
             *_money_cells(slip)],
            TABLE_WIDTHS,
        )
        for slip in payroll.values()
    ]
    total_row = format_row(
        ["TOTAL", "", "", *_money_cells(payroll_totals(payroll))],
        TABLE_WIDTHS,
    )
    return "\n".join(
        ["PAYROLL TABLE", header, rule, *rows, rule, total_row]
    )
