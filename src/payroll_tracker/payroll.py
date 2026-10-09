"""Salary, tax and payslip calculations.

Processing a list of employee records produces a dictionary that maps each
employee ID to its payslip.
"""

from decimal import Decimal
from typing import TypedDict

from payroll_tracker import utils
from payroll_tracker.employee import EmployeeRecord, validate_employee


class Payslip(TypedDict):
    id: str
    name: str
    role: str
    gross_pay: Decimal
    tax: Decimal
    pension: Decimal
    net_pay: Decimal


def contract_gross(hourly_rate: Decimal, hours_worked: Decimal) -> Decimal:
    """Regular hours at the hourly rate, extra hours at the overtime rate."""
    utils.require_non_negative(hourly_rate, "hourly_rate")
    utils.require_non_negative(hours_worked, "hours_worked")
    if hours_worked <= utils.STANDARD_MONTHLY_HOURS:
        return utils.to_money(hourly_rate * hours_worked)
    overtime_hours = hours_worked - utils.STANDARD_MONTHLY_HOURS
    regular_pay = hourly_rate * utils.STANDARD_MONTHLY_HOURS
    overtime_pay = hourly_rate * utils.OVERTIME_MULTIPLIER * overtime_hours
    return utils.to_money(regular_pay + overtime_pay)


def calculate_salary(record: EmployeeRecord) -> Decimal:
    """Monthly gross pay for an employee, using the rules for their role."""
    validate_employee(record)
    if record["role"] == utils.FULL_TIME:
        base_monthly = record["annual_salary"] / utils.MONTHS_PER_YEAR
        return utils.to_money(base_monthly + record["bonus"])
    elif record["role"] == utils.CONTRACT:
        return contract_gross(record["hourly_rate"], record["hours_worked"])
    else:
        return utils.to_money(record["stipend"])


def calculate_pension(record: EmployeeRecord) -> Decimal:
    """Pension contribution; only full-time employees contribute."""
    if record["role"] == utils.FULL_TIME:
        base_monthly = record["annual_salary"] / utils.MONTHS_PER_YEAR
        return utils.to_money(base_monthly * utils.PENSION_RATE)
    return Decimal("0.00")


def progressive_tax(taxable: Decimal) -> Decimal:
    """Apply utils.TAX_BANDS to a monthly amount, band by band."""
    utils.require_non_negative(taxable, "taxable amount")
    tax = Decimal("0")
    remaining = taxable
    index = 0
    while remaining > 0 and index < len(utils.TAX_BANDS):
        width, rate = utils.TAX_BANDS[index]
        portion = remaining if width is None else min(remaining, width)
        tax += portion * rate
        remaining -= portion
        index += 1
    return utils.to_money(tax)


def apply_tax(taxable: Decimal, role: str) -> Decimal:
    """Tax owed on a taxable amount: flat withholding for contractors, bands otherwise."""
    if role == utils.CONTRACT:
        utils.require_non_negative(taxable, "taxable amount")
        return utils.to_money(taxable * utils.CONTRACT_WITHHOLDING_RATE)
    elif role in utils.VALID_ROLES:
        return progressive_tax(taxable)
    else:
        raise ValueError(f"Unknown role: {role!r}")


def generate_payslip(record: EmployeeRecord) -> Payslip:
    """Build a full payslip: gross pay, pension, tax and net pay."""
    gross = calculate_salary(record)
    pension = calculate_pension(record)
    tax = apply_tax(gross - pension, record["role"])
    return {
        "id": record["id"],
        "name": record["name"],
        "role": record["role"],
        "gross_pay": gross,
        "tax": tax,
        "pension": pension,
        "net_pay": gross - tax - pension,
    }


def process_payroll(records: list[EmployeeRecord]) -> dict[str, Payslip]:
    """Generate payslips for every record, keyed by employee ID."""
    payroll: dict[str, Payslip] = {}
    for record in records:
        if record["id"] in payroll:
            raise ValueError(f"Duplicate employee ID: {record['id']}")
        payroll[record["id"]] = generate_payslip(record)
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
