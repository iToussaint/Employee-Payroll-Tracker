"""Command-line interface for the Employee Payroll Tracker.

Examples:
    python -m payroll_tracker
    python -m payroll_tracker --report summary
    python -m payroll_tracker --employee FT001
    python -m payroll_tracker --data data/employees.json --report table
"""

import argparse
import json
import sys
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from payroll_tracker.employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
    create_employee,
)
from payroll_tracker.payroll import (
    generate_report,
    payroll_table_report,
    process_payroll,
    role_summary_report,
)

REPORT_CHOICES = ("all", "payslips", "summary", "table")


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


def build_report(
    employees: Sequence[Employee],
    report: str,
    employee_id: str | None = None,
) -> str:
    """Return the requested report(s) as text.

    Args:
        employees: Everyone on the payroll.
        report: One of REPORT_CHOICES.
        employee_id: If given, limit the output to this employee.

    Raises:
        ValueError: If employee_id does not match anyone.
    """
    selected = list(employees)
    if employee_id is not None:
        selected = [e for e in employees if e.employee_id == employee_id]
        if not selected:
            raise ValueError(f"no employee with ID {employee_id!r}")

    sections: list[str] = []
    if report in ("all", "payslips"):
        sections += [generate_report(employee) for employee in selected]
    if report in ("all", "summary"):
        sections.append(role_summary_report(selected))
    if report in ("all", "table"):
        sections.append(payroll_table_report(selected))
    return "\n\n".join(sections)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="payroll_tracker",
        description=(
            "Compute monthly payslips for full-time, contract and intern "
            "employees."
        ),
    )
    parser.add_argument(
        "-r", "--report",
        choices=REPORT_CHOICES,
        default="all",
        help="which report to print (default: all)",
    )
    parser.add_argument(
        "-e", "--employee",
        metavar="ID",
        help="only include the employee with this ID",
    )
    parser.add_argument(
        "-d", "--data",
        type=Path,
        metavar="FILE",
        help="JSON file of employees (default: built-in sample data)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code (0 = success)."""
    args = build_parser().parse_args(argv)
    try:
        if args.data is None:
            employees = sample_employees()
        else:
            employees = load_employees(args.data)
        process_payroll(employees)  # fail early on duplicate IDs
        print(build_report(employees, args.report, args.employee))
    except FileNotFoundError:
        print(f"Error: data file not found: {args.data}", file=sys.stderr)
        return 1
    except OSError as error:
        print(
            f"Error: could not read {args.data}: {error.strerror}",
            file=sys.stderr,
        )
        return 1
    except json.JSONDecodeError as error:
        print(
            f"Error: {args.data} is not valid JSON "
            f"(line {error.lineno}, column {error.colno}: {error.msg})",
            file=sys.stderr,
        )
        return 1
    except (ValueError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
