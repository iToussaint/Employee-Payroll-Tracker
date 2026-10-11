"""Payroll calculations for any mix of employee types.

These functions depend only on the small Payable interface below, not on the
Employee classes themselves. Any object with those members can be paid, so
new roles need no changes here (polymorphism + dependency inversion).
"""

from collections.abc import Iterable
from decimal import Decimal
from typing import Protocol, TypedDict

from payroll_tracker.utils import ZERO


class Payable(Protocol):
    """What payroll needs from an employee: identity and pay figures."""

    @property
    def employee_id(self) -> str:
        """Unique employee ID."""
        ...

    @property
    def name(self) -> str:
        """Employee's full name."""
        ...

    @property
    def role(self) -> str:
        """Machine-readable role key."""
        ...

    @property
    def role_title(self) -> str:
        """Human-readable role name."""
        ...

    @property
    def pension(self) -> Decimal:
        """Monthly pension contribution."""
        ...

    @property
    def taxable_income(self) -> Decimal:
        """Monthly amount tax is charged on."""
        ...

    @property
    def net_pay(self) -> Decimal:
        """Monthly take-home pay."""
        ...

    def calculate_salary(self) -> Decimal:
        """Return monthly gross pay."""
        ...

    def calculate_tax(self, taxable: Decimal) -> Decimal:
        """Return tax on a taxable amount."""
        ...


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


def calculate_salary(employee: Payable) -> Decimal:
    """Return monthly gross pay, using the employee's own role rule."""
    return employee.calculate_salary()


def apply_tax(employee: Payable, taxable: Decimal) -> Decimal:
    """Return tax on a taxable amount, using the employee's own tax rule."""
    return employee.calculate_tax(taxable)


def generate_payslip(employee: Payable) -> Payslip:
    """Build a full payslip: gross pay, pension, tax and net pay."""
    return {
        "id": employee.employee_id,
        "name": employee.name,
        "role": employee.role,
        "role_title": employee.role_title,
        "gross_pay": calculate_salary(employee),
        "tax": apply_tax(employee, employee.taxable_income),
        "pension": employee.pension,
        "net_pay": employee.net_pay,
    }


def process_payroll(employees: Iterable[Payable]) -> dict[str, Payslip]:
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
        "gross_pay": sum((s["gross_pay"] for s in slips), ZERO),
        "tax": sum((s["tax"] for s in slips), ZERO),
        "pension": sum((s["pension"] for s in slips), ZERO),
        "net_pay": sum((s["net_pay"] for s in slips), ZERO),
    }


def payroll_totals(payroll: dict[str, Payslip]) -> PayTotals:
    """Sum gross, tax, pension and net pay across a processed payroll."""
    return sum_payslips(payroll.values())


def summarize_by_role(
    employees: Iterable[Payable],
) -> dict[str, RoleSummary]:
    """Group payslips by role title, in order of first appearance."""
    groups: dict[str, list[Payslip]] = {}
    for slip in process_payroll(employees).values():
        groups.setdefault(slip["role_title"], []).append(slip)
    return {
        title: {"headcount": len(slips), **sum_payslips(slips)}
        for title, slips in groups.items()
    }
