"""Employee class hierarchy.

Employee is an abstract base class. Each subclass stores its own pay data in
private attributes and overrides the calculations that differ for its role.

Pay inputs (salary, rate, hours, bonus, stipend) can only be changed through
validating property setters, and every change is recorded in an audit history.
Calculated figures (salary, pension, tax, net pay) are read-only properties.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar, NamedTuple

from payroll_tracker import utils


class PayChange(NamedTuple):
    """One audited change to an employee's pay data."""

    field: str
    old_value: Decimal
    new_value: Decimal
    changed_at: datetime


class Employee(ABC):
    """Base class for every employee role."""

    ROLE: ClassVar[str]

    def __init__(self, employee_id: str, name: str) -> None:
        if not isinstance(employee_id, str) or not employee_id.strip():
            raise ValueError("Employee ID cannot be empty")
        self.__employee_id = employee_id.strip()
        self.__name = ""
        self.name = name  # validated by the property setter
        self.__pay_history: list[PayChange] = []

    @property
    def employee_id(self) -> str:
        """Read-only: an employee's ID never changes."""
        return self.__employee_id

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Employee name cannot be empty")
        self.__name = value.strip()

    @property
    def role(self) -> str:
        return self.ROLE

    @property
    def pay_history(self) -> tuple[PayChange, ...]:
        """Read-only record of every change to this employee's pay data."""
        return tuple(self.__pay_history)

    def _record_change(self, field: str, old_value: Decimal, new_value: Decimal) -> None:
        """Log a pay data change. Called by subclass setters after validation."""
        if old_value != new_value:
            change = PayChange(field, old_value, new_value, datetime.now(timezone.utc))
            self.__pay_history.append(change)

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
    def tax(self) -> Decimal:
        """Monthly tax on gross pay less pension."""
        return self.calculate_tax(self.salary - self.pension)

    @property
    def net_pay(self) -> Decimal:
        """Monthly take-home pay."""
        return self.salary - self.tax - self.pension

    # Role rules: subclasses override these.

    @abstractmethod
    def calculate_salary(self) -> Decimal:
        """Monthly gross pay. Every role must provide its own rule."""

    def calculate_pension(self) -> Decimal:
        """Monthly pension contribution. No pension unless a role overrides this."""
        return Decimal("0.00")

    def calculate_tax(self, taxable: Decimal) -> Decimal:
        """Tax on a taxable amount. Progressive bands unless a role overrides this."""
        return utils.progressive_tax(taxable)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(employee_id={self.employee_id!r}, name={self.name!r})"


def _valid_annual_salary(value: utils.Amount) -> Decimal:
    return utils.to_amount(value, "annual_salary", positive=True, maximum=utils.MAX_ANNUAL_SALARY)


def _valid_bonus(value: utils.Amount) -> Decimal:
    return utils.to_amount(value, "bonus", maximum=utils.MAX_BONUS)


def _valid_hourly_rate(value: utils.Amount) -> Decimal:
    return utils.to_amount(value, "hourly_rate", positive=True, maximum=utils.MAX_HOURLY_RATE)


def _valid_hours_worked(value: utils.Amount) -> Decimal:
    return utils.to_amount(value, "hours_worked", maximum=utils.MAX_MONTHLY_HOURS)


def _valid_stipend(value: utils.Amount) -> Decimal:
    return utils.to_amount(value, "stipend", positive=True, maximum=utils.MAX_STIPEND)


class FullTimeEmployee(Employee):
    """Salaried employee: annual salary paid monthly, plus bonus, with pension."""

    ROLE = utils.FULL_TIME

    def __init__(
        self,
        employee_id: str,
        name: str,
        annual_salary: utils.Amount,
        bonus: utils.Amount = 0,
    ) -> None:
        super().__init__(employee_id, name)
        self.__annual_salary = _valid_annual_salary(annual_salary)
        self.__bonus = _valid_bonus(bonus)

    @property
    def annual_salary(self) -> Decimal:
        return self.__annual_salary

    @annual_salary.setter
    def annual_salary(self, value: utils.Amount) -> None:
        new_value = _valid_annual_salary(value)
        self._record_change("annual_salary", self.__annual_salary, new_value)
        self.__annual_salary = new_value

    @property
    def bonus(self) -> Decimal:
        return self.__bonus

    @bonus.setter
    def bonus(self, value: utils.Amount) -> None:
        new_value = _valid_bonus(value)
        self._record_change("bonus", self.__bonus, new_value)
        self.__bonus = new_value

    @property
    def base_monthly_salary(self) -> Decimal:
        return self.__annual_salary / utils.MONTHS_PER_YEAR

    def calculate_salary(self) -> Decimal:
        return utils.to_money(self.base_monthly_salary + self.__bonus)

    def calculate_pension(self) -> Decimal:
        return utils.to_money(self.base_monthly_salary * utils.PENSION_RATE)


class ContractEmployee(Employee):
    """Hourly contractor: overtime above standard hours, flat tax withholding."""

    ROLE = utils.CONTRACT

    def __init__(
        self,
        employee_id: str,
        name: str,
        hourly_rate: utils.Amount,
        hours_worked: utils.Amount,
    ) -> None:
        super().__init__(employee_id, name)
        self.__hourly_rate = _valid_hourly_rate(hourly_rate)
        self.__hours_worked = _valid_hours_worked(hours_worked)

    @property
    def hourly_rate(self) -> Decimal:
        return self.__hourly_rate

    @hourly_rate.setter
    def hourly_rate(self, value: utils.Amount) -> None:
        new_value = _valid_hourly_rate(value)
        self._record_change("hourly_rate", self.__hourly_rate, new_value)
        self.__hourly_rate = new_value

    @property
    def hours_worked(self) -> Decimal:
        return self.__hours_worked

    @hours_worked.setter
    def hours_worked(self, value: utils.Amount) -> None:
        new_value = _valid_hours_worked(value)
        self._record_change("hours_worked", self.__hours_worked, new_value)
        self.__hours_worked = new_value

    @property
    def overtime_hours(self) -> Decimal:
        return max(self.__hours_worked - utils.STANDARD_MONTHLY_HOURS, Decimal("0"))

    def calculate_salary(self) -> Decimal:
        regular_hours = self.__hours_worked - self.overtime_hours
        regular_pay = self.__hourly_rate * regular_hours
        overtime_pay = self.__hourly_rate * utils.OVERTIME_MULTIPLIER * self.overtime_hours
        return utils.to_money(regular_pay + overtime_pay)

    def calculate_tax(self, taxable: Decimal) -> Decimal:
        utils.require_non_negative(taxable, "taxable amount")
        return utils.to_money(taxable * utils.CONTRACT_WITHHOLDING_RATE)


class Intern(Employee):
    """Intern on a fixed monthly stipend."""

    ROLE = utils.INTERN

    def __init__(self, employee_id: str, name: str, stipend: utils.Amount) -> None:
        super().__init__(employee_id, name)
        self.__stipend = _valid_stipend(stipend)

    @property
    def stipend(self) -> Decimal:
        return self.__stipend

    @stipend.setter
    def stipend(self, value: utils.Amount) -> None:
        new_value = _valid_stipend(value)
        self._record_change("stipend", self.__stipend, new_value)
        self.__stipend = new_value

    def calculate_salary(self) -> Decimal:
        return utils.to_money(self.__stipend)
