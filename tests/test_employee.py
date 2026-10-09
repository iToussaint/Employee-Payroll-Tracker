from decimal import Decimal

import pytest

from payroll_tracker.employee import EmployeeRecord, validate_employee


def test_valid_records_pass() -> None:
    records: list[EmployeeRecord] = [
        {
            "id": "FT1",
            "name": "A",
            "role": "full_time",
            "annual_salary": Decimal("1"),
            "bonus": Decimal("0"),
        },
        {
            "id": "CT1",
            "name": "B",
            "role": "contract",
            "hourly_rate": Decimal("1"),
            "hours_worked": Decimal("0"),
        },
        {"id": "IN1", "name": "C", "role": "intern", "stipend": Decimal("0")},
    ]
    for record in records:
        validate_employee(record)


def test_negative_values_rejected() -> None:
    with pytest.raises(ValueError, match="stipend"):
        validate_employee({"id": "IN1", "name": "C", "role": "intern", "stipend": Decimal("-1")})
    with pytest.raises(ValueError, match="hours_worked"):
        validate_employee(
            {
                "id": "CT1",
                "name": "B",
                "role": "contract",
                "hourly_rate": Decimal("20"),
                "hours_worked": Decimal("-5"),
            }
        )


def test_empty_id_rejected() -> None:
    with pytest.raises(ValueError, match="ID"):
        validate_employee({"id": "  ", "name": "C", "role": "intern", "stipend": Decimal("1")})


def test_unknown_role_rejected() -> None:
    record: dict[str, object] = {"id": "X1", "name": "D", "role": "manager"}
    with pytest.raises(ValueError, match="Unknown role"):
        validate_employee(record)  # type: ignore[arg-type]
