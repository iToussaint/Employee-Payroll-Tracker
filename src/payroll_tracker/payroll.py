"""Payroll processing for any mix of employee types.

These functions only call methods defined on the Employee base class, so they
work the same way for every subclass (polymorphism). Processing a list of
employees produces a dictionary that maps each employee ID to its payslip.
"""

from decimal import Decimal
from typing import TypedDict

from payroll_tracker.employee import Employee


class Payslip(TypedDict):
    id: str
    name: str
    role: str
    gross_pay: Decimal
    tax: Decimal
    pension: Decimal
    net_pay: Decimal


def calculate_salary(employee: Employee) -> Decimal:
    """Monthly gross pay, using the employee's own role rule."""
    return employee.calculate_salary()


def apply_tax(employee: Employee, taxable: Decimal) -> Decimal:
    """Tax owed on a taxable amount, using the employee's own tax rule."""
    return employee.calculate_tax(taxable)


def generate_payslip(employee: Employee) -> Payslip:
    """Build a full payslip: gross pay, pension, tax and net pay."""
    gross = calculate_salary(employee)
    pension = employee.calculate_pension()
    tax = apply_tax(employee, gross - pension)
    return {
        "id": employee.employee_id,
        "name": employee.name,
        "role": employee.role,
        "gross_pay": gross,
        "tax": tax,
        "pension": pension,
        "net_pay": gross - tax - pension,
    }


def process_payroll(employees: list[Employee]) -> dict[str, Payslip]:
    """Generate payslips for every employee, keyed by employee ID."""
    payroll: dict[str, Payslip] = {}
    for employee in employees:
        if employee.employee_id in payroll:
            raise ValueError(f"Duplicate employee ID: {employee.employee_id}")
        payroll[employee.employee_id] = generate_payslip(employee)
    return payroll


def payroll_totals(payroll: dict[str, Payslip]) -> dict[str, Decimal]:
    """Sum gross, tax, pension and net pay across all payslips."""
    totals = {
        "gross_pay": Decimal("0"),
        "tax": Decimal("0"),
        "pension": Decimal("0"),
        "net_pay": Decimal("0"),
    }
    for payslip in payroll.values():
        totals["gross_pay"] += payslip["gross_pay"]
        totals["tax"] += payslip["tax"]
        totals["pension"] += payslip["pension"]
        totals["net_pay"] += payslip["net_pay"]
    return totals
