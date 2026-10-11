"""Command-line interface for the Employee Payroll Tracker.

This module only handles the command line: parsing options, choosing where
employees come from, and turning errors into messages and exit codes. The
payroll work itself is delegated to loader, payroll and reports.

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
from pathlib import Path
from typing import TextIO

from payroll_tracker.employee import Employee
from payroll_tracker.loader import load_employees, sample_employees
from payroll_tracker.payroll import process_payroll
from payroll_tracker.reports import REPORTS

ALL_REPORTS = "all"


def report_choices() -> list[str]:
    """Return the valid --report values: 'all' plus every registered one."""
    return [ALL_REPORTS, *REPORTS]


def build_report(
    employees: Sequence[Employee],
    report: str,
    employee_id: str | None = None,
) -> str:
    """Return the requested report(s) as text.

    Args:
        employees: Everyone on the payroll.
        report: 'all' or the name of a registered report.
        employee_id: If given, limit the output to this employee.

    Raises:
        ValueError: If the report is unknown or employee_id matches nobody.
    """
    if report != ALL_REPORTS and report not in REPORTS:
        raise ValueError(f"unknown report {report!r}")
    selected = list(employees)
    if employee_id is not None:
        selected = [e for e in employees if e.employee_id == employee_id]
        if not selected:
            raise ValueError(f"no employee with ID {employee_id!r}")

    names = list(REPORTS) if report == ALL_REPORTS else [report]
    return "\n\n".join(REPORTS[name](selected) for name in names)


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
        choices=report_choices(),
        default=ALL_REPORTS,
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


def main(
    argv: Sequence[str] | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    """Run the CLI and return a process exit code (0 = success).

    Args:
        argv: Command-line arguments (default: sys.argv[1:]).
        out: Stream for reports (default: sys.stdout).
        err: Stream for error messages (default: sys.stderr).
    """
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    try:
        if args.data is None:
            employees = sample_employees()
        else:
            employees = load_employees(args.data)
        process_payroll(employees)  # fail early on duplicate IDs
        print(build_report(employees, args.report, args.employee), file=out)
    except FileNotFoundError:
        print(f"Error: data file not found: {args.data}", file=err)
        return 1
    except OSError as error:
        print(f"Error: could not read {args.data}: {error.strerror}", file=err)
        return 1
    except json.JSONDecodeError as error:
        print(
            f"Error: {args.data} is not valid JSON "
            f"(line {error.lineno}, column {error.colno}: {error.msg})",
            file=err,
        )
        return 1
    except (ValueError, TypeError) as error:
        print(f"Error: {error}", file=err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
