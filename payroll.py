"""Payroll processing for any mix of employee types.

These functions only use members defined on the Employee base class, so they
work the same way for every subclass (polymorphism). Processing a list of
employees produces a dictionary that maps each employee ID to its payslip.
Formatting the results for display is done in main.py.
"""

from collections.abc import Iterable
from decimal import Decimal
from typing import TypedDict

import utils
from employee import Employee


class Payslip(TypedDict):
    """One employee's pay for the month."""

    employee_id: str
    name: str
    role: str
    gross_pay: Decimal
    tax: Decimal
    net_pay: Decimal


class RoleSummary(TypedDict):
    """Headcount and pay subtotals for one role."""

    headcount: int
    gross_pay: Decimal
    tax: Decimal
    net_pay: Decimal


def generate_payslip(employee: Employee) -> Payslip:
    """Build a payslip from the employee's gross pay, tax and net pay."""
    return {
        "employee_id": employee.employee_id,
        "name": employee.name,
        "role": employee.role,
        "gross_pay": employee.salary,
        "tax": employee.tax,
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


def summarize_by_role(payroll: dict[str, Payslip]) -> dict[str, RoleSummary]:
    """Group payslips by role, in order of first appearance, with subtotals."""
    # One pass over the payroll: collect each role's payslips.
    groups: dict[str, list[Payslip]] = {}
    for slip in payroll.values():
        groups.setdefault(slip["role"], []).append(slip)

    return {
        role: {
            "headcount": len(slips),
            "gross_pay": sum((s["gross_pay"] for s in slips), utils.ZERO),
            "tax": sum((s["tax"] for s in slips), utils.ZERO),
            "net_pay": sum((s["net_pay"] for s in slips), utils.ZERO),
        }
        for role, slips in groups.items()
    }
