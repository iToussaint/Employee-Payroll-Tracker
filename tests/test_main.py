import io
import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from payroll_tracker.loader import sample_employees
from payroll_tracker.main import build_report, main, report_choices
from payroll_tracker.reports import REPORTS, Reportable, register_report

SAMPLE_FILE = Path(__file__).parent.parent / "data" / "employees.json"


def write_json(tmp_path: Path, content: object) -> Path:
    path = tmp_path / "employees.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


def test_default_run_prints_every_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert out.count("PAYSLIP - ") == 5
    assert "PAYROLL SUMMARY BY ROLE" in out
    assert "PAYROLL TABLE" in out


@pytest.mark.parametrize(
    ("report", "expected", "absent"),
    [
        ("payslips", "PAYSLIP - ", "PAYROLL TABLE"),
        ("summary", "PAYROLL SUMMARY BY ROLE", "PAYSLIP - "),
        ("table", "PAYROLL TABLE", "PAYROLL SUMMARY"),
    ],
)
def test_report_option_selects_one_report(
    capsys: pytest.CaptureFixture[str],
    report: str,
    expected: str,
    absent: str,
) -> None:
    assert main(["--report", report]) == 0
    out = capsys.readouterr().out
    assert expected in out
    assert absent not in out


def test_employee_option_filters_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["-r", "payslips", "-e", "CT001"]) == 0
    out = capsys.readouterr().out
    assert out.count("PAYSLIP - ") == 1
    assert "Kwame Boateng" in out


def test_unknown_employee_is_a_clean_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["-e", "NOPE"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error: no employee with ID 'NOPE'" in captured.err


def test_invalid_report_choice_exits_with_usage_error() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--report", "bogus"])
    assert exit_info.value.code == 2


def test_sample_data_file_matches_built_in_sample(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["-r", "table"])
    built_in = capsys.readouterr().out
    main(["-r", "table", "--data", str(SAMPLE_FILE)])
    from_file = capsys.readouterr().out
    assert from_file == built_in


def test_missing_file_is_a_clean_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--data", str(tmp_path / "missing.json")]) == 1
    assert "Error: data file not found" in capsys.readouterr().err


def test_malformed_json_is_a_clean_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "broken.json"
    path.write_text("[{", encoding="utf-8")
    assert main(["--data", str(path)]) == 1
    assert "is not valid JSON (line 1" in capsys.readouterr().err


def test_duplicate_ids_in_file_are_a_clean_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = {"id": "IN1", "name": "Esi", "role": "intern", "stipend": 1}
    path = write_json(tmp_path, [record, record])
    assert main(["--data", str(path)]) == 1
    assert "Duplicate employee ID: IN1" in capsys.readouterr().err


def test_build_report_joins_sections_with_blank_line() -> None:
    text = build_report(sample_employees(), "all", "IN001")
    assert "\n\nPAYROLL SUMMARY BY ROLE" in text
    assert "\n\nPAYROLL TABLE" in text


def test_output_streams_can_be_injected() -> None:
    out, err = io.StringIO(), io.StringIO()
    assert main(["-r", "summary"], out=out, err=err) == 0
    assert out.getvalue().startswith("PAYROLL SUMMARY BY ROLE")
    assert err.getvalue() == ""

    assert main(["-e", "NOPE"], out=out, err=err) == 1
    assert "no employee with ID" in err.getvalue()


def test_report_choices_come_from_registry() -> None:
    assert report_choices() == ["all", "payslips", "summary", "table"]


def test_new_report_is_added_by_registering_it() -> None:
    @register_report("headcount")
    def headcount_report(employees: Sequence[Reportable]) -> str:
        return f"HEADCOUNT {len(employees)}"

    try:
        out = io.StringIO()
        assert main(["-r", "headcount"], out=out) == 0
        assert out.getvalue().strip() == "HEADCOUNT 5"
    finally:
        del REPORTS["headcount"]


def test_unknown_report_rejected_by_build_report() -> None:
    with pytest.raises(ValueError, match="unknown report"):
        build_report(sample_employees(), "bogus")
