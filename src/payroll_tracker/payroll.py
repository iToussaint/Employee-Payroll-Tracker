"""Payslip calculations built on lists, dictionaries, conditionals and loops.

Employee records are plain dictionaries stored in a list. Processing a list
of records produces a dictionary that maps each employee ID to its payslip.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal, TypedDict

from payroll_tracker import rules

CENT = Decimal("0.01")


class FullTimeRecord(TypedDict):
    id: str
    name: str
    role: Literal["full_time"]
    annual_salary: Decimal
    bonus: Decimal


class ContractRecord(TypedDict):
    id: str
    name: str
    role: Literal["contract"]
    hourly_rate: Decimal
    hours_worked: Decimal


class InternRecord(TypedDict):
    id: str
    name: str
    role: Literal["intern"]
    stipend: Decimal


EmployeeRecord = FullTimeRecord | ContractRecord | InternRecord


class Payslip(TypedDict):
    name: str
    role: str
    gross_pay: Decimal
    tax: Decimal
    pension: Decimal
    net_pay: Decimal


def to_money(amount: Decimal) -> Decimal:
    """Round an amount to cents."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _require_non_negative(value: Decimal, field: str) -> None:
    if value < 0:
        raise ValueError(f"{field} cannot be negative (got {value})")


def progressive_tax(taxable: Decimal) -> Decimal:
    """Apply rules.TAX_BANDS to a monthly amount, band by band."""
    _require_non_negative(taxable, "taxable amount")
    tax = Decimal("0")
    remaining = taxable
    index = 0
    while remaining > 0 and index < len(rules.TAX_BANDS):
        width, rate = rules.TAX_BANDS[index]
        portion = remaining if width is None else min(remaining, width)
        tax += portion * rate
        remaining -= portion
        index += 1
    return to_money(tax)


def contract_gross(hourly_rate: Decimal, hours_worked: Decimal) -> Decimal:
    """Regular hours at the hourly rate, extra hours at the overtime rate."""
    _require_non_negative(hourly_rate, "hourly_rate")
    _require_non_negative(hours_worked, "hours_worked")
    if hours_worked <= rules.STANDARD_MONTHLY_HOURS:
        return to_money(hourly_rate * hours_worked)
    overtime_hours = hours_worked - rules.STANDARD_MONTHLY_HOURS
    regular_pay = hourly_rate * rules.STANDARD_MONTHLY_HOURS
    overtime_pay = hourly_rate * rules.OVERTIME_MULTIPLIER * overtime_hours
    return to_money(regular_pay + overtime_pay)


def calculate_payslip(record: EmployeeRecord) -> Payslip:
    """Compute one employee's payslip using the rules for their role."""
    pension = Decimal("0.00")
    if record["role"] == rules.FULL_TIME:
        _require_non_negative(record["annual_salary"], "annual_salary")
        _require_non_negative(record["bonus"], "bonus")
        base_monthly = record["annual_salary"] / rules.MONTHS_PER_YEAR
        gross = to_money(base_monthly + record["bonus"])
        pension = to_money(base_monthly * rules.PENSION_RATE)
        tax = progressive_tax(gross - pension)
    elif record["role"] == rules.CONTRACT:
        gross = contract_gross(record["hourly_rate"], record["hours_worked"])
        tax = to_money(gross * rules.CONTRACT_WITHHOLDING_RATE)
    elif record["role"] == rules.INTERN:
        _require_non_negative(record["stipend"], "stipend")
        gross = to_money(record["stipend"])
        tax = progressive_tax(gross)
    else:
        raise ValueError(f"Unknown role: {record['role']!r}")

    return {
        "name": record["name"],
        "role": record["role"],
        "gross_pay": gross,
        "tax": tax,
        "pension": pension,
        "net_pay": gross - tax - pension,
    }


def process_payroll(records: list[EmployeeRecord]) -> dict[str, Payslip]:
    """Calculate payslips for every record, keyed by employee ID."""
    payroll: dict[str, Payslip] = {}
    for record in records:
        if record["id"] in payroll:
            raise ValueError(f"Duplicate employee ID: {record['id']}")
        payroll[record["id"]] = calculate_payslip(record)
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
