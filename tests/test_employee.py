"""Tests for employee.py: inheritance, overriding, encapsulation, ranges."""

from decimal import Decimal

import pytest

from employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
    PayDetail,
)


def make_full_timer() -> FullTimeEmployee:
    return FullTimeEmployee("FT1", "Ama", annual_salary=60000, bonus=500)


def make_contractor() -> ContractEmployee:
    return ContractEmployee("CT1", "Kwame", hourly_rate=20, hours_worked=100)


def make_intern() -> Intern:
    return Intern("IN1", "Esi", stipend=800)


# Inheritance


def test_employee_base_class_is_abstract() -> None:
    with pytest.raises(TypeError):
        Employee("E1", "Nobody")  # type: ignore[abstract]


@pytest.mark.parametrize(
    "employee", [make_full_timer(), make_contractor(), make_intern()]
)
def test_subclasses_inherit_from_employee(employee: Employee) -> None:
    assert isinstance(employee, Employee)
    assert employee.name  # inherited property
    assert repr(employee).startswith(type(employee).__name__)


def test_roles() -> None:
    assert make_full_timer().role == "Full-time Employee"
    assert make_contractor().role == "Contract Employee"
    assert make_intern().role == "Intern"


# Method overriding


def test_each_subclass_overrides_calculate_salary() -> None:
    for cls in (FullTimeEmployee, ContractEmployee, Intern):
        assert "calculate_salary" in cls.__dict__


def test_full_time_salary() -> None:
    employee = make_full_timer()
    assert employee.monthly_salary == Decimal("5000")  # 60000 / 12
    assert employee.calculate_salary() == Decimal("5500.00")  # + 500 bonus


def test_contract_salary() -> None:
    # 20 per hour * 100 hours
    assert make_contractor().calculate_salary() == Decimal("2000.00")


def test_intern_salary_is_stipend() -> None:
    assert make_intern().calculate_salary() == Decimal("800.00")


def test_tax_rule_depends_on_role() -> None:
    amount = Decimal("2000")
    assert make_contractor().calculate_tax(amount) == Decimal("300.00")
    assert make_full_timer().calculate_tax(amount) == Decimal("100.00")
    assert make_intern().calculate_tax(amount) == Decimal("100.00")
    assert make_contractor().tax_basis == "flat 15%"
    assert make_intern().tax_basis == "progressive bands"


# Encapsulation


def test_pay_data_is_stored_in_private_attributes() -> None:
    employee = make_full_timer()
    assert "annual_salary" not in vars(employee)
    assert "_FullTimeEmployee__annual_salary" in vars(employee)
    assert "_Employee__employee_id" in vars(employee)


def test_employee_id_is_read_only() -> None:
    employee = make_intern()
    with pytest.raises(AttributeError):
        employee.employee_id = "X"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("employee_id", "name"), [("", "Ama"), ("  ", "Ama"), ("FT1", " ")]
)
def test_empty_id_or_name_rejected(employee_id: str, name: str) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        Intern(employee_id, name, stipend=1)


# Properties & data validation


def test_salary_bonus_and_tax_properties() -> None:
    employee = make_full_timer()
    assert employee.salary == Decimal("5500.00")
    assert employee.bonus == Decimal("500")
    assert employee.tax == Decimal("700.00")  # 0 + 200 + 500 (bands)
    assert employee.net_pay == Decimal("4800.00")


def test_calculated_properties_follow_pay_updates() -> None:
    employee = make_full_timer()
    employee.bonus = 0
    assert employee.salary == Decimal("5000.00")
    assert employee.tax == Decimal("600.00")  # 0 + 200 + 400 (bands)


@pytest.mark.parametrize("field", ["salary", "tax", "net_pay"])
def test_calculated_properties_are_read_only(field: str) -> None:
    employee = make_full_timer()
    with pytest.raises(AttributeError):
        setattr(employee, field, Decimal("1"))


@pytest.mark.parametrize(
    ("employee", "field"),
    [
        (make_full_timer(), "annual_salary"),
        (make_contractor(), "hourly_rate"),
        (make_intern(), "stipend"),
    ],
)
def test_salary_must_be_greater_than_zero(
    employee: Employee, field: str
) -> None:
    with pytest.raises(ValueError, match=f"{field} must be greater than 0"):
        setattr(employee, field, 0)


@pytest.mark.parametrize(
    ("employee", "field", "too_high"),
    [
        (make_full_timer(), "annual_salary", "1000000.01"),
        (make_full_timer(), "bonus", "50001"),
        (make_contractor(), "hourly_rate", "1001"),
        (make_contractor(), "hours_worked", "745"),
        (make_intern(), "stipend", "5001"),
    ],
)
def test_upper_limits_enforced(
    employee: Employee, field: str, too_high: str
) -> None:
    with pytest.raises(ValueError, match=f"{field} cannot exceed"):
        setattr(employee, field, too_high)


def test_negative_bonus_and_hours_rejected() -> None:
    with pytest.raises(ValueError, match="bonus cannot be negative"):
        make_full_timer().bonus = -1
    with pytest.raises(ValueError, match="hours_worked cannot be negative"):
        make_contractor().hours_worked = -5


def test_rejected_update_keeps_old_value() -> None:
    employee = make_intern()
    with pytest.raises(ValueError):
        employee.stipend = 0
    assert employee.stipend == Decimal("800")


def test_setters_accept_numbers_and_strings() -> None:
    employee = make_contractor()
    employee.hourly_rate = "22.50"
    employee.hours_worked = 120
    assert employee.salary == Decimal("2700.00")


# Pay details: raw values, no formatting inside the employee classes


def test_pay_details_hold_raw_values() -> None:
    assert make_full_timer().pay_details() == [
        PayDetail("Annual salary", Decimal("60000")),
        PayDetail("Monthly salary", Decimal("5000")),
        PayDetail("Bonus", Decimal("500")),
    ]
    assert make_contractor().pay_details() == [
        PayDetail("Hourly rate", Decimal("20")),
        PayDetail("Hours worked", Decimal("100"), "hours"),
    ]
    assert make_intern().pay_details() == [
        PayDetail("Monthly stipend", Decimal("800")),
    ]


def test_pay_detail_unit_defaults_to_money() -> None:
    assert PayDetail("Bonus", Decimal("1")).unit == "money"
