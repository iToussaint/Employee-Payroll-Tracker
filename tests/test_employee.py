from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from payroll_tracker.employee import (
    ContractEmployee,
    Employee,
    FullTimeEmployee,
    Intern,
    PayDetail,
    PayHistory,
)
from payroll_tracker.tax import FlatTax


def make_full_timer() -> FullTimeEmployee:
    return FullTimeEmployee("FT1", "Ama", annual_salary=60000, bonus=500)


def make_contractor(hours: str = "100") -> ContractEmployee:
    return ContractEmployee(
        "CT1", "Kwame", hourly_rate=20, hours_worked=Decimal(hours)
    )


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
    assert make_full_timer().role == "full_time"
    assert make_contractor().role == "contract"
    assert make_intern().role == "intern"


# Method overriding


def test_each_subclass_overrides_calculate_salary() -> None:
    for cls in (FullTimeEmployee, ContractEmployee, Intern):
        assert "calculate_salary" in cls.__dict__


def test_full_time_salary_and_pension() -> None:
    employee = make_full_timer()
    # 60000 / 12 + 500 bonus; pension is 5% of the 5000 base
    assert employee.calculate_salary() == Decimal("5500.00")
    assert employee.calculate_pension() == Decimal("250.00")


def test_contract_salary_without_overtime() -> None:
    employee = make_contractor("160")
    assert employee.overtime_hours == Decimal("0")
    assert employee.calculate_salary() == Decimal("3200.00")


def test_contract_salary_with_overtime() -> None:
    employee = make_contractor("170")  # 160h * 20 + 10h * 20 * 1.5
    assert employee.regular_hours == Decimal("160")
    assert employee.overtime_hours == Decimal("10")
    assert employee.calculate_salary() == Decimal("3500.00")


def test_contract_uses_flat_tax_policy_by_default() -> None:
    amount = Decimal("2000")
    assert make_contractor().calculate_tax(amount) == Decimal("300.00")
    assert make_contractor().tax_basis == "flat 15% withholding"
    assert make_intern().calculate_tax(amount) == Decimal("100.00")  # bands
    assert make_intern().tax_basis == "progressive bands"


def test_tax_policy_can_be_injected() -> None:
    intern = Intern("IN1", "Esi", stipend=800, tax_policy=FlatTax(
        Decimal("0.10")
    ))
    assert intern.tax == Decimal("80.00")
    assert intern.tax_basis == "flat 10% withholding"


def test_pay_details_are_raw_values_with_units() -> None:
    assert make_contractor("170").pay_details() == [
        PayDetail("Hourly rate", Decimal("20")),
        PayDetail("Regular hours", Decimal("160"), "hours"),
        PayDetail("Regular pay", Decimal("3200")),
        PayDetail("Overtime hours (x1.5)", Decimal("10"), "hours"),
        PayDetail("Overtime pay", Decimal("300.0")),
    ]


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
    # A rejected update leaves the old value in place.
    assert employee.hours_worked == Decimal("120")


@pytest.mark.parametrize("bad", ["-5", "abc", "NaN", "Infinity"])
def test_invalid_amounts_rejected(bad: str) -> None:
    with pytest.raises(ValueError, match="stipend"):
        Intern("IN1", "Esi", stipend=bad)


def test_float_amounts_rejected() -> None:
    with pytest.raises(TypeError, match="annual_salary"):
        FullTimeEmployee(
            "FT1", "Ama", annual_salary=60000.5  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("employee_id", "name"), [("", "Ama"), ("  ", "Ama"), ("FT1", " ")]
)
def test_empty_id_or_name_rejected(employee_id: str, name: str) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        Intern(employee_id, name, stipend=1)


def test_name_can_be_updated() -> None:
    employee = make_intern()
    employee.name = "  Esi Owusu "
    assert employee.name == "Esi Owusu"


# Properties & data validation


def test_calculated_properties_match_payslip_figures() -> None:
    employee = make_full_timer()
    assert employee.salary == Decimal("5500.00")
    assert employee.pension == Decimal("250.00")
    assert employee.taxable_income == Decimal("5250.00")
    assert employee.tax == Decimal("650.00")
    assert employee.net_pay == Decimal("4600.00")


def test_calculated_properties_follow_pay_updates() -> None:
    employee = make_full_timer()
    employee.bonus = 0
    assert employee.salary == Decimal("5000.00")
    assert employee.tax == Decimal("550.00")  # bands on 4750


@pytest.mark.parametrize("field", ["salary", "tax", "pension", "net_pay"])
def test_calculated_properties_are_read_only(field: str) -> None:
    employee = make_full_timer()
    with pytest.raises(AttributeError):
        setattr(employee, field, Decimal("1"))


@pytest.mark.parametrize(
    ("factory", "field"),
    [
        (
            lambda v: FullTimeEmployee("FT1", "Ama", annual_salary=v),
            "annual_salary",
        ),
        (
            lambda v: ContractEmployee(
                "CT1", "Kwame", hourly_rate=v, hours_worked=1
            ),
            "hourly_rate",
        ),
        (lambda v: Intern("IN1", "Esi", stipend=v), "stipend"),
    ],
)
def test_base_pay_must_be_greater_than_zero(
    factory: Callable[[int], Employee], field: str
) -> None:
    with pytest.raises(ValueError, match=f"{field} must be greater than 0"):
        factory(0)


def test_zero_bonus_and_zero_hours_are_allowed() -> None:
    full_timer = FullTimeEmployee("FT1", "Ama", annual_salary=1, bonus=0)
    contractor = ContractEmployee(
        "CT1", "Kwame", hourly_rate=1, hours_worked=0
    )
    assert full_timer.bonus == 0
    assert contractor.salary == 0


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


def test_pay_changes_are_recorded() -> None:
    employee = make_full_timer()
    assert employee.pay_history == ()  # initial values are not changes

    employee.annual_salary = 72000
    employee.bonus = 500  # same value: not recorded
    employee.bonus = 0

    history = employee.pay_history
    assert [(c.field, c.old_value, c.new_value) for c in history] == [
        ("annual_salary", Decimal("60000"), Decimal("72000")),
        ("bonus", Decimal("500"), Decimal("0")),
    ]
    assert all(c.changed_at.tzinfo is not None for c in history)


def test_rejected_updates_are_not_recorded() -> None:
    employee = make_intern()
    with pytest.raises(ValueError):
        employee.stipend = 0
    assert employee.pay_history == ()
    assert employee.stipend == Decimal("800")


def test_pay_history_cannot_be_modified_from_outside() -> None:
    employee = make_intern()
    employee.stipend = 900
    history = employee.pay_history
    assert isinstance(history, tuple)
    with pytest.raises(AttributeError):
        employee.pay_history = ()  # type: ignore[misc]
    assert len(employee.pay_history) == 1


# Pay history


def test_pay_history_uses_injected_clock() -> None:
    moment = datetime(2026, 1, 31, tzinfo=timezone.utc)
    history = PayHistory(clock=lambda: moment)
    history.record("stipend", Decimal("1"), Decimal("2"))
    history.record("stipend", Decimal("2"), Decimal("2"))  # no change
    assert [c.changed_at for c in history.changes] == [moment]
