import pytest

from payroll_tracker.main import build_report, main, sample_employees


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


def test_build_report_joins_sections_with_blank_line() -> None:
    text = build_report(sample_employees(), "all", "IN001")
    assert "\n\nPAYROLL SUMMARY BY ROLE" in text
    assert "\n\nPAYROLL TABLE" in text
