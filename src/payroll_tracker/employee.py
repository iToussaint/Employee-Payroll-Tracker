"""Employee record types and validation.

Each employee is a dictionary whose "role" decides which pay fields it has.
"""

from decimal import Decimal
from typing import Literal, TypedDict

from payroll_tracker.utils import CONTRACT, FULL_TIME, INTERN, require_non_negative


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


def validate_employee(record: EmployeeRecord) -> None:
    """Check a record has an ID, a known role and no negative pay values."""
    if not record["id"].strip():
        raise ValueError("Employee ID cannot be empty")
    if record["role"] == FULL_TIME:
        require_non_negative(record["annual_salary"], "annual_salary")
        require_non_negative(record["bonus"], "bonus")
    elif record["role"] == CONTRACT:
        require_non_negative(record["hourly_rate"], "hourly_rate")
        require_non_negative(record["hours_worked"], "hours_worked")
    elif record["role"] == INTERN:
        require_non_negative(record["stipend"], "stipend")
    else:
        raise ValueError(f"Unknown role: {record['role']!r}")
