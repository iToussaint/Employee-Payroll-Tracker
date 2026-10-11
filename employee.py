"""Employee class hierarchy.

Employee is the abstract base class. FullTimeEmployee, ContractEmployee and
Intern inherit from it, keep their pay data in private attributes, and each
override calculate_salary() with the rule for their role.

Pay inputs can only be changed through validating property setters, and the
calculated figures (salary, tax, net pay) are read-only properties.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import ClassVar, Literal, NamedTuple

import utils


class PayDetail(NamedTuple):
    """One figure explaining how an employee's gross pay was reached.

    Holds the raw value; formatting it for display is left to the caller.
    """

    label: str
    value: Decimal
    unit: Literal["money", "hours"] = "money"


class Employee(ABC):
    """Base class for every employee role."""

    ROLE: ClassVar[str]

    def __init__(self, employee_id: str, name: str) -> None:
        """Create an employee with a non-empty ID and name."""
        # A double underscore makes an attribute private: Python renames it
        # to _Employee__employee_id, so it cannot be changed by accident from
        # outside the class. Access goes through the properties below.
        self.__employee_id = utils.to_text(employee_id, "Employee ID")
        self.name = name  # validated by the property setter

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
        """Set the name; it cannot be empty or only spaces."""
        self.__name = utils.to_text(value, "Employee name")

    @property
    def role(self) -> str:
        """Role name, such as 'Full-time Employee'."""
        return self.ROLE

    @property
    def salary(self) -> Decimal:
        """Monthly gross pay. Read-only: calculated from the pay data."""
        return self.calculate_salary()

    @property
    def tax(self) -> Decimal:
        """Monthly tax on gross pay. Read-only."""
        return self.calculate_tax(self.salary)

    @property
    def net_pay(self) -> Decimal:
        """Monthly take-home pay: gross pay less tax. Read-only."""
        return self.salary - self.tax

    @abstractmethod
    def calculate_salary(self) -> Decimal:
        """Return monthly gross pay. Every role overrides this."""

    def calculate_tax(self, taxable: Decimal) -> Decimal:
        """Return tax on an amount, using the tax rule for this role."""
        return utils.apply_tax(taxable, self.role)

    @property
    def tax_basis(self) -> str:
        """Short description of how tax is calculated, for reports."""
        return utils.tax_basis(self.role)

    @abstractmethod
    def pay_details(self) -> list[PayDetail]:
        """Return the figures that explain how gross pay was reached."""

    def __repr__(self) -> str:
        """Return a short developer-facing description."""
        return (
            f"{type(self).__name__}(employee_id={self.employee_id!r}, "
            f"name={self.name!r})"
        )


class FullTimeEmployee(Employee):
    """Salaried employee: annual salary paid monthly, plus any bonus."""

    ROLE = utils.FULL_TIME

    def __init__(
        self,
        employee_id: str,
        name: str,
        annual_salary: utils.Amount,
        bonus: utils.Amount = 0,
    ) -> None:
        """Create a full-time employee; annual_salary must be above 0."""
        super().__init__(employee_id, name)
        self.annual_salary = annual_salary  # validated by the setter
        self.bonus = bonus  # validated by the setter

    @property
    def annual_salary(self) -> Decimal:
        """Yearly base salary, before bonus and tax."""
        return self.__annual_salary

    @annual_salary.setter
    def annual_salary(self, value: utils.Amount) -> None:
        """Set the annual salary.

        Must be above 0 and at most MAX_ANNUAL_SALARY.
        """
        self.__annual_salary = utils.to_amount(
            value, "annual_salary", positive=True,
            maximum=utils.MAX_ANNUAL_SALARY,
        )

    @property
    def bonus(self) -> Decimal:
        """One-off bonus added to this month's pay."""
        return self.__bonus

    @bonus.setter
    def bonus(self, value: utils.Amount) -> None:
        """Set the bonus; must be between 0 and MAX_BONUS."""
        self.__bonus = utils.to_amount(
            value, "bonus", maximum=utils.MAX_BONUS
        )

    @property
    def monthly_salary(self) -> Decimal:
        """Annual salary spread evenly over the year."""
        return self.__annual_salary / utils.MONTHS_PER_YEAR

    def calculate_salary(self) -> Decimal:
        """Return monthly salary plus bonus."""
        return utils.to_money(self.monthly_salary + self.__bonus)

    def pay_details(self) -> list[PayDetail]:
        """Return annual salary, monthly salary and bonus."""
        return [
            PayDetail("Annual salary", self.__annual_salary),
            PayDetail("Monthly salary", self.monthly_salary),
            PayDetail("Bonus", self.__bonus),
        ]


class ContractEmployee(Employee):
    """Contractor paid by the hour."""

    ROLE = utils.CONTRACT

    def __init__(
        self,
        employee_id: str,
        name: str,
        hourly_rate: utils.Amount,
        hours_worked: utils.Amount,
    ) -> None:
        """Create a contractor; hourly_rate must be above 0."""
        super().__init__(employee_id, name)
        self.hourly_rate = hourly_rate  # validated by the setter
        self.hours_worked = hours_worked  # validated by the setter

    @property
    def hourly_rate(self) -> Decimal:
        """Pay per hour."""
        return self.__hourly_rate

    @hourly_rate.setter
    def hourly_rate(self, value: utils.Amount) -> None:
        """Set the hourly rate.

        Must be above 0 and at most MAX_HOURLY_RATE.
        """
        self.__hourly_rate = utils.to_amount(
            value, "hourly_rate", positive=True,
            maximum=utils.MAX_HOURLY_RATE,
        )

    @property
    def hours_worked(self) -> Decimal:
        """Hours worked this month."""
        return self.__hours_worked

    @hours_worked.setter
    def hours_worked(self, value: utils.Amount) -> None:
        """Set the hours worked.

        Must be between 0 and MAX_MONTHLY_HOURS.
        """
        self.__hours_worked = utils.to_amount(
            value, "hours_worked", maximum=utils.MAX_MONTHLY_HOURS
        )

    def calculate_salary(self) -> Decimal:
        """Return hourly rate x hours worked."""
        return utils.to_money(self.__hourly_rate * self.__hours_worked)

    def pay_details(self) -> list[PayDetail]:
        """Return hourly rate and hours worked."""
        return [
            PayDetail("Hourly rate", self.__hourly_rate),
            PayDetail("Hours worked", self.__hours_worked, "hours"),
        ]


class Intern(Employee):
    """Intern on a fixed monthly stipend."""

    ROLE = utils.INTERN

    def __init__(
        self, employee_id: str, name: str, stipend: utils.Amount
    ) -> None:
        """Create an intern; stipend must be above 0."""
        super().__init__(employee_id, name)
        self.stipend = stipend  # validated by the setter

    @property
    def stipend(self) -> Decimal:
        """Fixed monthly stipend."""
        return self.__stipend

    @stipend.setter
    def stipend(self, value: utils.Amount) -> None:
        """Set the stipend; must be above 0 and at most MAX_STIPEND."""
        self.__stipend = utils.to_amount(
            value, "stipend", positive=True, maximum=utils.MAX_STIPEND
        )

    def calculate_salary(self) -> Decimal:
        """Return the stipend."""
        return utils.to_money(self.__stipend)

    def pay_details(self) -> list[PayDetail]:
        """Return the monthly stipend."""
        return [PayDetail("Monthly stipend", self.__stipend)]
