import json
from decimal import Decimal
from pathlib import Path

import pytest

from payroll_tracker.employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
)
from payroll_tracker.loader import (
    BUILDERS,
    Record,
    create_employee,
    load_employees,
    register_builder,
    sample_employees,
)


def write_json(tmp_path: Path, content: object) -> Path:
    path = tmp_path / "employees.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


def test_builtin_roles_are_registered() -> None:
    assert {"full_time", "contract", "intern"} <= set(BUILDERS)


def test_create_employee_builds_each_role() -> None:
    full_timer = create_employee(
        {"id": "FT1", "name": "Ama", "role": "full_time",
         "annual_salary": 60000}
    )
    contractor = create_employee(
        {"id": "CT1", "name": "Kwame", "role": "contract",
         "hourly_rate": "20", "hours_worked": Decimal("100.5")}
    )
    intern = create_employee(
        {"id": "IN1", "name": "Esi", "role": "intern", "stipend": 800}
    )
    assert isinstance(full_timer, FullTimeEmployee)
    assert full_timer.bonus == 0  # optional field defaults to 0
    assert isinstance(contractor, ContractEmployee)
    assert contractor.hours_worked == Decimal("100.5")
    assert isinstance(intern, Intern)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"id": "X", "name": "A", "role": "manager"}, "unknown role"),
        ({"id": "X", "name": "A"}, "unknown role"),
        ({"id": "X", "name": "A", "role": "intern"}, "missing field"),
        (
            {"id": "X", "name": "A", "role": "intern", "stipend": 1,
             "bonus": 5},
            "unknown field",
        ),
        ({"id": 7, "name": "A", "role": "intern", "stipend": 1}, "text"),
        (
            {"id": "X", "name": "A", "role": "intern", "stipend": 0},
            "greater than 0",
        ),
    ],
)
def test_create_employee_rejects_bad_data(
    data: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        create_employee(data)


def test_new_role_is_added_by_registering_a_builder() -> None:
    @register_builder("apprentice")
    def build_apprentice(data: Record) -> Employee:
        return Intern(str(data["id"]), str(data["name"]), stipend=500)

    try:
        employee = create_employee(
            {"id": "AP1", "name": "Kojo", "role": "apprentice"}
        )
        assert employee.salary == Decimal("500.00")
    finally:
        del BUILDERS["apprentice"]


def test_registering_a_role_twice_is_rejected() -> None:
    with pytest.raises(ValueError, match="already registered"):
        register_builder("intern")(BUILDERS["intern"])


def test_load_employees_reads_decimals_exactly(tmp_path: Path) -> None:
    path = tmp_path / "employees.json"
    path.write_text(
        '[{"id": "IN1", "name": "Esi", "role": "intern", "stipend": 0.1}]',
        encoding="utf-8",
    )
    [intern] = load_employees(path)
    assert str(intern.salary) == "0.10"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ({"id": "IN1"}, "must contain a JSON list"),
        ([], "contains no employees"),
        (["IN1"], "record 1: expected a JSON object"),
        (
            [{"id": "IN1", "name": "Esi", "role": "intern", "stipend": 1},
             {"id": "IN2", "name": "Abena", "role": "intern"}],
            "record 2: missing field",
        ),
    ],
)
def test_load_employees_rejects_bad_files(
    tmp_path: Path, content: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        load_employees(write_json(tmp_path, content))


def test_sample_employees_returns_fresh_objects() -> None:
    first, second = sample_employees(), sample_employees()
    assert [e.employee_id for e in first] == [e.employee_id for e in second]
    assert first[0] is not second[0]
