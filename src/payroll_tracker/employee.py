"""Employee class hierarchy.

Employee is an abstract base class. Each subclass stores its own pay data in
private attributes and overrides the calculations that differ for its role.

Pay inputs (salary, rate, hours, bonus, stipend) can only be changed through
validating property setters, and every change is recorded in a PayHistory.
Calculated figures (salary, pension, tax, net pay) are read-only properties.

This module only models employees and their pay rules. Reading employees from
files lives in loader.py and formatting them for output lives in reports.py.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar, Literal, NamedTuple

from payroll_tracker import config
from payroll_tracker.tax import CONTRACT_WITHHOLDING, STANDARD_TAX, TaxPolicy
from payroll_tracker.utils import ZERO, Amount, to_amount, to_money


class PayChange(NamedTuple):
    """One audited change to an employee's pay data."""

    field: str
    old_value: Decimal
    new_value: Decimal
    changed_at: datetime


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PayHistory:
    """Append-only audit log of pay data changes."""

    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        """Create an empty log; clock supplies each change's timestamp."""
        self.__clock = clock
        self.__changes: list[PayChange] = []

    def record(
        self, field: str, old_value: Decimal, new_value: Decimal
    ) -> None:
        """Log a change. Setting a field to its current value is ignored."""
        if old_value != new_value:
            change = PayChange(field, old_value, new_value, self.__clock())
            self.__changes.append(change)

    @property
    def changes(self) -> tuple[PayChange, ...]:
        """Every recorded change, oldest first, as an immutable tuple."""
        return tuple(self.__changes)


class PayDetail(NamedTuple):
    """One line explaining how an employee's gross pay was reached."""

    label: str
    value: Decimal
    unit: Literal["money", "hours"] = "money"


class Employee(ABC):
    """Base class for every employee role.

    Subclasses must set ROLE and ROLE_TITLE and implement calculate_salary()
    and pay_details(). They may override calculate_pension() and
    DEFAULT_TAX_POLICY when their role uses different rules.
    """

    ROLE: ClassVar[str]
    ROLE_TITLE: ClassVar[str]
    DEFAULT_TAX_POLICY: ClassVar[TaxPolicy] = STANDARD_TAX

    def __init__(
        self,
        employee_id: str,
        name: str,
        *,
        tax_policy: TaxPolicy | None = None,
    ) -> None:
        """Create an employee with a non-empty ID and name.

        Args:
            employee_id: Unique, non-empty ID.
            name: Non-empty full name.
            tax_policy: Overrides the role's DEFAULT_TAX_POLICY.
        """
        if not isinstance(employee_id, str) or not employee_id.strip():
            raise ValueError("Employee ID cannot be empty")
        self.__employee_id = employee_id.strip()
        self.__name = ""
        self.name = name  # validated by the property setter
        self.__tax_policy = tax_policy or self.DEFAULT_TAX_POLICY
        self.__history = PayHistory()

    # Identity

    @property
    def employee_id(self) -> str:
        """Unique employee ID. Read-only: it never changes."""
        return self.__employee_id

    @property
    def name(self) -> str:
        """Employee's full name."""
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Employee name cannot be empty")
        self.__name = value.strip()

    @property
    def role(self) -> str:
        """Machine-readable role key, such as 'full_time'."""
        return self.ROLE

    @property
    def role_title(self) -> str:
        """Human-readable role name, such as 'Full-time Employee'."""
        return self.ROLE_TITLE

    # Audit history

    @property
    def pay_history(self) -> tuple[PayChange, ...]:
        """Read-only record of every change to this employee's pay data."""
        return self.__history.changes

    def _track(
        self, field: str, old_value: Decimal, new_value: Decimal
    ) -> Decimal:
        """Record a validated pay change and return the new value to store."""
        self.__history.record(field, old_value, new_value)
        return new_value

    # Calculated figures: read-only, always reflect the current pay data.

    @property
    def salary(self) -> Decimal:
        """Monthly gross pay."""
        return self.calculate_salary()

    @property
    def pension(self) -> Decimal:
        """Monthly pension contribution."""
        return self.calculate_pension()

    @property
    def taxable_income(self) -> Decimal:
        """Monthly gross pay less pension: the amount tax is charged on."""
        return self.salary - self.pension

    @property
    def tax(self) -> Decimal:
        """Monthly tax on taxable income."""
        return self.calculate_tax(self.taxable_income)

    @property
    def net_pay(self) -> Decimal:
        """Monthly take-home pay: gross pay less tax and pension."""
        return self.salary - self.tax - self.pension

    @property
    def tax_basis(self) -> str:
        """Short description of how this employee's tax is calculated."""
        return self.__tax_policy.description

    # Role rules

    @abstractmethod
    def calculate_salary(self) -> Decimal:
        """Return monthly gross pay. Every role must provide its own rule."""

    @abstractmethod
    def pay_details(self) -> list[PayDetail]:
        """Return the figures that explain how gross pay was reached."""

    def calculate_pension(self) -> Decimal:
        """Return the monthly pension contribution (none by default)."""
        return ZERO

    def calculate_tax(self, taxable: Decimal) -> Decimal:
        """Return tax on a taxable amount using this employee's policy."""
        return self.__tax_policy.calculate(taxable)

    def __repr__(self) -> str:
        """Return a short developer-facing description."""
        return (
            f"{type(self).__name__}(employee_id={self.employee_id!r}, "
            f"name={self.name!r})"
        )


# Validators shared by __init__ and the property setters of each subclass.


def _valid_annual_salary(value: Amount) -> Decimal:
    return to_amount(
        value, "annual_salary", positive=True,
        maximum=config.MAX_ANNUAL_SALARY,
    )


def _valid_bonus(value: Amount) -> Decimal:
    return to_amount(value, "bonus", maximum=config.MAX_BONUS)


def _valid_hourly_rate(value: Amount) -> Decimal:
    return to_amount(
        value, "hourly_rate", positive=True, maximum=config.MAX_HOURLY_RATE
    )


def _valid_hours_worked(value: Amount) -> Decimal:
    return to_amount(value, "hours_worked", maximum=config.MAX_MONTHLY_HOURS)


def _valid_stipend(value: Amount) -> Decimal:
    return to_amount(
        value, "stipend", positive=True, maximum=config.MAX_STIPEND
    )


class FullTimeEmployee(Employee):
    """Salaried employee: annual salary paid monthly, plus bonus, pension."""

    ROLE = config.FULL_TIME
    ROLE_TITLE = "Full-time Employee"

    def __init__(
        self,
        employee_id: str,
        name: str,
        annual_salary: Amount,
        bonus: Amount = 0,
        *,
        tax_policy: TaxPolicy | None = None,
    ) -> None:
        """Create a full-time employee; annual_salary must be above 0."""
        super().__init__(employee_id, name, tax_policy=tax_policy)
        self.__annual_salary = _valid_annual_salary(annual_salary)
        self.__bonus = _valid_bonus(bonus)

    @property
    def annual_salary(self) -> Decimal:
        """Yearly base salary, before bonus and deductions."""
        return self.__annual_salary

    @annual_salary.setter
    def annual_salary(self, value: Amount) -> None:
        self.__annual_salary = self._track(
            "annual_salary", self.__annual_salary, _valid_annual_salary(value)
        )

    @property
    def bonus(self) -> Decimal:
        """One-off bonus added to this month's pay."""
        return self.__bonus

    @bonus.setter
    def bonus(self, value: Amount) -> None:
        self.__bonus = self._track("bonus", self.__bonus, _valid_bonus(value))

    @property
    def base_monthly_salary(self) -> Decimal:
        """Annual salary divided evenly across the year."""
        return self.__annual_salary / config.MONTHS_PER_YEAR

    def calculate_salary(self) -> Decimal:
        """Return monthly base salary plus bonus."""
        return to_money(self.base_monthly_salary + self.__bonus)

    def calculate_pension(self) -> Decimal:
        """Return PENSION_RATE of the monthly base salary (bonus excluded)."""
        return to_money(self.base_monthly_salary * config.PENSION_RATE)

    def pay_details(self) -> list[PayDetail]:
        """Return annual salary, monthly base salary and bonus."""
        return [
            PayDetail("Annual salary", self.__annual_salary),
            PayDetail("Monthly base salary", self.base_monthly_salary),
            PayDetail("Bonus", self.__bonus),
        ]


class ContractEmployee(Employee):
    """Hourly contractor: overtime above standard hours, flat tax."""

    ROLE = config.CONTRACT
    ROLE_TITLE = "Contract Employee"
    DEFAULT_TAX_POLICY = CONTRACT_WITHHOLDING

    def __init__(
        self,
        employee_id: str,
        name: str,
        hourly_rate: Amount,
        hours_worked: Amount,
        *,
        tax_policy: TaxPolicy | None = None,
    ) -> None:
        """Create a contractor; hourly_rate must be above 0."""
        super().__init__(employee_id, name, tax_policy=tax_policy)
        self.__hourly_rate = _valid_hourly_rate(hourly_rate)
        self.__hours_worked = _valid_hours_worked(hours_worked)

    @property
    def hourly_rate(self) -> Decimal:
        """Pay per regular hour."""
        return self.__hourly_rate

    @hourly_rate.setter
    def hourly_rate(self, value: Amount) -> None:
        self.__hourly_rate = self._track(
            "hourly_rate", self.__hourly_rate, _valid_hourly_rate(value)
        )

    @property
    def hours_worked(self) -> Decimal:
        """Total hours worked this month, including overtime."""
        return self.__hours_worked

    @hours_worked.setter
    def hours_worked(self, value: Amount) -> None:
        self.__hours_worked = self._track(
            "hours_worked", self.__hours_worked, _valid_hours_worked(value)
        )

    @property
    def overtime_hours(self) -> Decimal:
        """Hours worked beyond STANDARD_MONTHLY_HOURS."""
        extra = self.__hours_worked - config.STANDARD_MONTHLY_HOURS
        return max(extra, Decimal("0"))

    @property
    def regular_hours(self) -> Decimal:
        """Hours worked up to STANDARD_MONTHLY_HOURS."""
        return self.__hours_worked - self.overtime_hours

    @property
    def overtime_rate(self) -> Decimal:
        """Pay per overtime hour."""
        return self.__hourly_rate * config.OVERTIME_MULTIPLIER

    @property
    def regular_pay(self) -> Decimal:
        """Pay for regular hours."""
        return self.__hourly_rate * self.regular_hours

    @property
    def overtime_pay(self) -> Decimal:
        """Pay for overtime hours."""
        return self.overtime_rate * self.overtime_hours

    def calculate_salary(self) -> Decimal:
        """Return regular pay plus overtime pay."""
        return to_money(self.regular_pay + self.overtime_pay)

    def pay_details(self) -> list[PayDetail]:
        """Return hourly rate, regular and overtime hours and pay."""
        overtime_label = f"Overtime hours (x{config.OVERTIME_MULTIPLIER})"
        return [
            PayDetail("Hourly rate", self.__hourly_rate),
            PayDetail("Regular hours", self.regular_hours, "hours"),
            PayDetail("Regular pay", self.regular_pay),
            PayDetail(overtime_label, self.overtime_hours, "hours"),
            PayDetail("Overtime pay", self.overtime_pay),
        ]


class Intern(Employee):
    """Intern on a fixed monthly stipend."""

    ROLE = config.INTERN
    ROLE_TITLE = "Intern"

    def __init__(
        self,
        employee_id: str,
        name: str,
        stipend: Amount,
        *,
        tax_policy: TaxPolicy | None = None,
    ) -> None:
        """Create an intern; stipend must be above 0."""
        super().__init__(employee_id, name, tax_policy=tax_policy)
        self.__stipend = _valid_stipend(stipend)

    @property
    def stipend(self) -> Decimal:
        """Fixed monthly stipend."""
        return self.__stipend

    @stipend.setter
    def stipend(self, value: Amount) -> None:
        self.__stipend = self._track(
            "stipend", self.__stipend, _valid_stipend(value)
        )

    def calculate_salary(self) -> Decimal:
        """Return the stipend."""
        return to_money(self.__stipend)

    def pay_details(self) -> list[PayDetail]:
        """Return the monthly stipend."""
        return [PayDetail("Monthly stipend", self.__stipend)]
