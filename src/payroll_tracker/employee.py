"""Employee class hierarchy.

Employee is an abstract base class. Each subclass stores its own pay data in
private attributes and overrides the calculations that differ for its role.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import ClassVar

from payroll_tracker import utils


class Employee(ABC):
    """Base class for every employee role."""

    ROLE: ClassVar[str]

    def __init__(self, employee_id: str, name: str) -> None:
        if not isinstance(employee_id, str) or not employee_id.strip():
            raise ValueError("Employee ID cannot be empty")
        self.__employee_id = employee_id.strip()
        self.__name = ""
        self.name = name  # validated by the property setter

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
        self.annual_salary = annual_salary
        self.bonus = bonus

    @property
    def annual_salary(self) -> Decimal:
        return self.__annual_salary

    @annual_salary.setter
    def annual_salary(self, value: utils.Amount) -> None:
        self.__annual_salary = utils.to_amount(value, "annual_salary")

    @property
    def bonus(self) -> Decimal:
        return self.__bonus

    @bonus.setter
    def bonus(self, value: utils.Amount) -> None:
        self.__bonus = utils.to_amount(value, "bonus")

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
        self.hourly_rate = hourly_rate
        self.hours_worked = hours_worked

    @property
    def hourly_rate(self) -> Decimal:
        return self.__hourly_rate

    @hourly_rate.setter
    def hourly_rate(self, value: utils.Amount) -> None:
        self.__hourly_rate = utils.to_amount(value, "hourly_rate")

    @property
    def hours_worked(self) -> Decimal:
        return self.__hours_worked

    @hours_worked.setter
    def hours_worked(self, value: utils.Amount) -> None:
        self.__hours_worked = utils.to_amount(value, "hours_worked")

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
        self.stipend = stipend

    @property
    def stipend(self) -> Decimal:
        return self.__stipend

    @stipend.setter
    def stipend(self, value: utils.Amount) -> None:
        self.__stipend = utils.to_amount(value, "stipend")

    def calculate_salary(self) -> Decimal:
        return utils.to_money(self.__stipend)
