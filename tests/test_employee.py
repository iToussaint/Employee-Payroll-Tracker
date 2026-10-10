from decimal import Decimal

import pytest

from payroll_tracker.employee import ContractEmployee, Employee, FullTimeEmployee, Intern


def make_full_timer() -> FullTimeEmployee:
    return FullTimeEmployee("FT1", "Ama", annual_salary=Decimal("60000"), bonus=Decimal("500"))


def make_contractor(hours: str = "100") -> ContractEmployee:
    return ContractEmployee("CT1", "Kwame", hourly_rate=Decimal("20"), hours_worked=Decimal(hours))


def make_intern() -> Intern:
    return Intern("IN1", "Esi", stipend=Decimal("800"))


# Inheritance


def test_employee_base_class_is_abstract() -> None:
    with pytest.raises(TypeError):
        Employee("E1", "Nobody")  # type: ignore[abstract]


@pytest.mark.parametrize("employee", [make_full_timer(), make_contractor(), make_intern()])
def test_subclasses_inherit_from_employee(employee: Employee) -> None:
    assert isinstance(employee, Employee)
    assert employee.name  # inherited property
    assert repr(employee).startswith(type(employee).__name__)


def test_roles() -> None:
    assert make_full_timer().role == "full_time"
    assert make_contractor().role == "contract"
    assert make_intern().role == "intern"


# Method overriding


def test_each_subclass_overrides_calculate_salary() -> None:
    for cls in (FullTimeEmployee, ContractEmployee, Intern):
        assert "calculate_salary" in cls.__dict__


def test_full_time_salary_and_pension() -> None:
    employee = make_full_timer()
    assert employee.calculate_salary() == Decimal("5500.00")  # 60000 / 12 + 500
    assert employee.calculate_pension() == Decimal("250.00")  # 5% of 5000


def test_contract_salary_without_overtime() -> None:
    employee = make_contractor("160")
    assert employee.overtime_hours == Decimal("0")
    assert employee.calculate_salary() == Decimal("3200.00")


def test_contract_salary_with_overtime() -> None:
    employee = make_contractor("170")  # 160h * 20 + 10h * 20 * 1.5
    assert employee.overtime_hours == Decimal("10")
    assert employee.calculate_salary() == Decimal("3500.00")


def test_contract_overrides_tax_with_flat_rate() -> None:
    assert make_contractor().calculate_tax(Decimal("2000")) == Decimal("300.00")
    assert make_intern().calculate_tax(Decimal("2000")) == Decimal("100.00")  # bands


def test_only_full_time_overrides_pension() -> None:
    assert make_contractor().calculate_pension() == Decimal("0.00")
    assert make_intern().calculate_pension() == Decimal("0.00")


def test_intern_salary_is_stipend() -> None:
    assert make_intern().calculate_salary() == Decimal("800.00")


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


def test_setters_validate_and_convert() -> None:
    employee = make_contractor()
    employee.hours_worked = 120
    assert employee.hours_worked == Decimal("120")
    employee.hourly_rate = "22.50"
    assert employee.hourly_rate == Decimal("22.50")
    with pytest.raises(ValueError, match="hours_worked cannot be negative"):
        employee.hours_worked = -1
    assert employee.hours_worked == Decimal("120")  # unchanged after rejected update


@pytest.mark.parametrize("bad", ["-5", "abc", "NaN", "Infinity"])
def test_invalid_amounts_rejected(bad: str) -> None:
    with pytest.raises(ValueError, match="stipend"):
        Intern("IN1", "Esi", stipend=bad)


def test_float_amounts_rejected() -> None:
    with pytest.raises(TypeError, match="annual_salary"):
        FullTimeEmployee("FT1", "Ama", annual_salary=60000.5)  # type: ignore[arg-type]


@pytest.mark.parametrize(("employee_id", "name"), [("", "Ama"), ("  ", "Ama"), ("FT1", " ")])
def test_empty_id_or_name_rejected(employee_id: str, name: str) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        Intern(employee_id, name, stipend=1)


def test_name_can_be_updated() -> None:
    employee = make_intern()
    employee.name = "  Esi Owusu "
    assert employee.name == "Esi Owusu"
