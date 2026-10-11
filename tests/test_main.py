"""Tests for main.py: the interactive menu, report formatting and exit."""

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from employee import PayDetail
from main import InputFn, format_detail, main, sample_employees

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def scripted(*answers: str) -> InputFn:
    """Return an input function that replies with the given answers.

    When the answers run out it raises EOFError, like input() does at the
    end of piped input.
    """
    remaining = list(answers)

    def read(prompt: str) -> str:
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    return read


def run(capsys: pytest.CaptureFixture[str], *answers: str) -> str:
    """Run the menu with scripted answers; return everything printed."""
    assert main(scripted(*answers)) == 0
    return capsys.readouterr().out


# Sample data


def test_sample_employees_cover_every_role() -> None:
    roles = {employee.role for employee in sample_employees()}
    assert roles == {"Full-time Employee", "Contract Employee", "Intern"}


def test_load_samples_then_show(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, "4", "5", "6")
    assert "Loaded 5 sample employee(s)." in out
    assert out.count("PAYSLIP - ") == 5
    assert "PAYROLL SUMMARY BY ROLE" in out
    assert out.rstrip().endswith("Goodbye.")


def test_loading_samples_twice_adds_no_duplicates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run(capsys, "4", "4", "5", "6")
    assert "Loaded 0 sample employee(s)." in out
    assert out.count("PAYSLIP - ") == 5


# Adding employees


def test_add_one_employee_of_each_role(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run(
        capsys,
        "1", "FT1", "Ama", "60000", "500",
        "2", "CT1", "Kwame", "20", "100",
        "3", "IN1", "Esi", "800",
        "5", "6",
    )
    assert "Added Full-time Employee Ama (FT1)." in out
    assert "Added Contract Employee Kwame (CT1)." in out
    assert "Added Intern Esi (IN1)." in out
    assert out.count("PAYSLIP - ") == 3
    assert "4,800.00" in out  # full-time net pay: 5,500 - 700
    assert "1,700.00" in out  # contract net pay: 2,000 - 300


def test_blank_bonus_means_no_bonus(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run(capsys, "1", "FT1", "Ama", "60000", "", "5", "6")
    assert "Added Full-time Employee Ama (FT1)." in out
    assert "Bonus                                   0.00" in out


def test_invalid_salary_is_rejected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run(capsys, "3", "IN1", "Esi", "0", "5", "6")
    assert (
        "Error: stipend must be greater than 0 (got 0). Employee not added."
        in out
    )
    assert "No employees yet." in out


def test_non_numeric_amount_is_rejected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run(capsys, "2", "CT1", "Kwame", "twenty", "10", "6")
    assert "hourly_rate is not a valid number" in out
    assert "Employee not added." in out


def test_empty_name_is_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, "3", "IN1", "   ", "800", "6")
    assert "Error: Employee name cannot be empty. Employee not added." in out


def test_duplicate_id_is_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, "4", "3", "IN001", "6")
    assert "Error: employee ID IN001 is already in use." in out


# Menu handling and exiting


def test_unknown_option_is_reported(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run(capsys, "9", "6")
    assert "'9' is not an option. Enter a number from 1 to 6." in out


def test_show_with_no_employees(capsys: pytest.CaptureFixture[str]) -> None:
    out = run(capsys, "5", "6")
    assert "No employees yet." in out


def test_end_of_input_exits_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run(capsys, "4")  # input ends without choosing Exit
    assert out.rstrip().endswith("Goodbye.")


def test_ctrl_c_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    def interrupt(prompt: str) -> str:
        raise KeyboardInterrupt

    assert main(interrupt) == 0
    assert capsys.readouterr().out.rstrip().endswith("Goodbye.")


def test_python_main_py_runs_with_piped_input() -> None:
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        input="4\n5\n6\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "PAYROLL SUMMARY BY ROLE" in result.stdout


# Formatting


def test_format_detail_by_unit() -> None:
    money = PayDetail("Annual salary", Decimal("60000"))
    hours = PayDetail("Hours worked", Decimal("172.5"), "hours")
    assert format_detail(money) == "60,000.00"
    assert format_detail(hours) == "172.5"
