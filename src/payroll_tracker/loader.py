"""Build employees from plain data: dictionaries, JSON files, sample data.

Each role has a builder function registered with @register_builder. A new
role is supported by registering one more builder, without editing
create_employee() or any existing builder.
"""

import json
from collections.abc import Callable, Mapping
from decimal import Decimal
from pathlib import Path

from payroll_tracker import config
from payroll_tracker.employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
)
from payroll_tracker.utils import to_amount

Record = Mapping[str, object]
Builder = Callable[[Record], Employee]

# Role key -> function that builds that role from a record.
BUILDERS: dict[str, Builder] = {}


def register_builder(role: str) -> Callable[[Builder], Builder]:
    """Register the function that builds employees of a role."""

    def decorator(builder: Builder) -> Builder:
        if role in BUILDERS:
            raise ValueError(f"role {role!r} is already registered")
        BUILDERS[role] = builder
        return builder

    return decorator


# Field helpers


def _check_fields(
    data: Record,
    required: set[str],
    optional: frozenset[str] = frozenset(),
) -> None:
    """Raise ValueError if fields are missing or unrecognised."""
    missing = sorted(required - data.keys())
    unknown = sorted(data.keys() - required - optional - {"role"})
    if missing:
        raise ValueError(f"missing field(s): {', '.join(missing)}")
    if unknown:
        raise ValueError(f"unknown field(s): {', '.join(unknown)}")


def _text(data: Record, key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be text (got {value!r})")
    return value


def _amount(data: Record, key: str) -> Decimal:
    return to_amount(data[key], key)


# Builders for the built-in roles


@register_builder(config.FULL_TIME)
def build_full_time(data: Record) -> FullTimeEmployee:
    """Build from keys id, name, annual_salary and optional bonus."""
    _check_fields(data, {"id", "name", "annual_salary"}, frozenset({"bonus"}))
    return FullTimeEmployee(
        _text(data, "id"),
        _text(data, "name"),
        annual_salary=_amount(data, "annual_salary"),
        bonus=_amount(data, "bonus") if "bonus" in data else 0,
    )


@register_builder(config.CONTRACT)
def build_contract(data: Record) -> ContractEmployee:
    """Build from keys id, name, hourly_rate and hours_worked."""
    _check_fields(data, {"id", "name", "hourly_rate", "hours_worked"})
    return ContractEmployee(
        _text(data, "id"),
        _text(data, "name"),
        hourly_rate=_amount(data, "hourly_rate"),
        hours_worked=_amount(data, "hours_worked"),
    )


@register_builder(config.INTERN)
def build_intern(data: Record) -> Intern:
    """Build from keys id, name and stipend."""
    _check_fields(data, {"id", "name", "stipend"})
    return Intern(
        _text(data, "id"),
        _text(data, "name"),
        stipend=_amount(data, "stipend"),
    )


def create_employee(data: Record) -> Employee:
    """Build the right Employee subclass from a record with a 'role' key.

    Raises:
        ValueError: If the role is unknown or any field is missing/invalid.
    """
    role = data.get("role")
    if not isinstance(role, str) or role not in BUILDERS:
        valid = ", ".join(BUILDERS)
        raise ValueError(f"unknown role {role!r} (expected one of: {valid})")
    return BUILDERS[role](data)


def load_employees(path: Path) -> list[Employee]:
    """Load employees from a JSON file containing a list of records.

    Each record is an object with a "role" key plus that role's fields,
    for example {"id": "IN001", "name": "Esi", "role": "intern",
    "stipend": 1200}. Decimal numbers are read exactly, never as floats.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the JSON is malformed or a record is invalid.
    """
    with path.open(encoding="utf-8") as file:
        raw = json.load(file, parse_float=Decimal)
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a JSON list of employees")
    if not raw:
        raise ValueError(f"{path} contains no employees")

    employees: list[Employee] = []
    for number, record in enumerate(raw, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"record {number}: expected a JSON object")
        try:
            employees.append(create_employee(record))
        except (ValueError, TypeError) as error:
            raise ValueError(f"record {number}: {error}") from error
    return employees


def sample_employees() -> list[Employee]:
    """Return a fresh list of demo employees covering every role."""
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
