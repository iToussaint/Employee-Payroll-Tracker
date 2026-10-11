"""Employee class hierarchy.

Employee is an abstract base class. Each subclass stores its own pay data in
private attributes and overrides the calculations that differ for its role.

Pay inputs (salary, rate, hours, bonus, stipend) can only be changed through
validating property setters. Calculated figures (salary, pension, tax, net
pay) are read-only properties.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import ClassVar

from payroll_tracker import utils


class Employee(ABC):
    """Base class for every employee role.

    Subclasses must set ROLE and ROLE_TITLE and implement calculate_salary()
    and pay_details(). They may override calculate_pension(),
    calculate_tax() and tax_basis when their role uses different rules.
    """

    ROLE: ClassVar[str]
    ROLE_TITLE: ClassVar[str]

    def __init__(self, employee_id: str, name: str) -> None:
        """Create an employee with a non-empty ID and name."""
        if not isinstance(employee_id, str) or not employee_id.strip():
            raise ValueError("Employee ID cannot be empty")
        self.__employee_id = employee_id.strip()
        self.__name = ""
        self.name = name  # validated by the property setter

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

    # Role rules: subclasses override these.

    @abstractmethod
    def calculate_salary(self) -> Decimal:
        """Return monthly gross pay. Every role must provide its own rule."""

    def calculate_pension(self) -> Decimal:
        """Return the monthly pension contribution (none by default)."""
        return utils.ZERO

    def calculate_tax(self, taxable: Decimal) -> Decimal:
        """Return tax on a taxable amount (progressive bands by default)."""
        return utils.progressive_tax(taxable)

    @property
    def tax_basis(self) -> str:
        """Short description of how tax is calculated, for reports."""
        return "progressive bands"

    @abstractmethod
    def pay_details(self) -> list[tuple[str, str]]:
        """Return (label, value) lines explaining how gross pay was reached."""

    def __repr__(self) -> str:
        """Return a short developer-facing description."""
        return (
            f"{type(self).__name__}(employee_id={self.employee_id!r}, "
            f"name={self.name!r})"
        )


# Validators shared by __init__ and the property setters of each subclass.


def _valid_annual_salary(value: utils.Amount) -> Decimal:
    return utils.to_amount(
        value, "annual_salary", positive=True,
        maximum=utils.MAX_ANNUAL_SALARY,
    )


def _valid_bonus(value: utils.Amount) -> Decimal:
    return utils.to_amount(value, "bonus", maximum=utils.MAX_BONUS)


def _valid_hourly_rate(value: utils.Amount) -> Decimal:
    return utils.to_amount(
        value, "hourly_rate", positive=True, maximum=utils.MAX_HOURLY_RATE
    )


def _valid_hours_worked(value: utils.Amount) -> Decimal:
    return utils.to_amount(
        value, "hours_worked", maximum=utils.MAX_MONTHLY_HOURS
    )


def _valid_stipend(value: utils.Amount) -> Decimal:
    return utils.to_amount(
        value, "stipend", positive=True, maximum=utils.MAX_STIPEND
    )


class FullTimeEmployee(Employee):
    """Salaried employee: annual salary paid monthly, plus bonus, pension."""

    ROLE = utils.FULL_TIME
    ROLE_TITLE = "Full-time Employee"

    def __init__(
        self,
        employee_id: str,
        name: str,
        annual_salary: utils.Amount,
        bonus: utils.Amount = 0,
    ) -> None:
        """Create a full-time employee; annual_salary must be above 0."""
        super().__init__(employee_id, name)
        self.__annual_salary = _valid_annual_salary(annual_salary)
        self.__bonus = _valid_bonus(bonus)

    @property
    def annual_salary(self) -> Decimal:
        """Yearly base salary, before bonus and deductions."""
        return self.__annual_salary

    @annual_salary.setter
    def annual_salary(self, value: utils.Amount) -> None:
        self.__annual_salary = _valid_annual_salary(value)

    @property
    def bonus(self) -> Decimal:
        """One-off bonus added to this month's pay."""
        return self.__bonus

    @bonus.setter
    def bonus(self, value: utils.Amount) -> None:
        self.__bonus = _valid_bonus(value)

    @property
    def base_monthly_salary(self) -> Decimal:
        """Annual salary divided evenly across the year."""
        return self.__annual_salary / utils.MONTHS_PER_YEAR

    def calculate_salary(self) -> Decimal:
        """Return monthly base salary plus bonus."""
        return utils.to_money(self.base_monthly_salary + self.__bonus)

    def calculate_pension(self) -> Decimal:
        """Return PENSION_RATE of the monthly base salary (bonus excluded)."""
        return utils.to_money(self.base_monthly_salary * utils.PENSION_RATE)

    def pay_details(self) -> list[tuple[str, str]]:
        """Return annual salary, monthly base salary and bonus lines."""
        return [
            ("Annual salary", utils.format_money(self.__annual_salary)),
            (
                "Monthly base salary",
                utils.format_money(self.base_monthly_salary),
            ),
            ("Bonus", utils.format_money(self.__bonus)),
        ]


class ContractEmployee(Employee):
    """Hourly contractor: overtime above standard hours, flat tax."""

    ROLE = utils.CONTRACT
    ROLE_TITLE = "Contract Employee"

    def __init__(
        self,
        employee_id: str,
        name: str,
        hourly_rate: utils.Amount,
        hours_worked: utils.Amount,
    ) -> None:
        """Create a contractor; hourly_rate must be above 0."""
        super().__init__(employee_id, name)
        self.__hourly_rate = _valid_hourly_rate(hourly_rate)
        self.__hours_worked = _valid_hours_worked(hours_worked)

    @property
    def hourly_rate(self) -> Decimal:
        """Pay per regular hour."""
        return self.__hourly_rate

    @hourly_rate.setter
    def hourly_rate(self, value: utils.Amount) -> None:
        self.__hourly_rate = _valid_hourly_rate(value)

    @property
    def hours_worked(self) -> Decimal:
        """Total hours worked this month, including overtime."""
        return self.__hours_worked

    @hours_worked.setter
    def hours_worked(self, value: utils.Amount) -> None:
        self.__hours_worked = _valid_hours_worked(value)

    @property
    def overtime_hours(self) -> Decimal:
        """Hours worked beyond STANDARD_MONTHLY_HOURS."""
        extra = self.__hours_worked - utils.STANDARD_MONTHLY_HOURS
        return max(extra, Decimal("0"))

    @property
    def regular_hours(self) -> Decimal:
        """Hours worked up to STANDARD_MONTHLY_HOURS."""
        return self.__hours_worked - self.overtime_hours

    @property
    def overtime_rate(self) -> Decimal:
        """Pay per overtime hour."""
        return self.__hourly_rate * utils.OVERTIME_MULTIPLIER

    def calculate_salary(self) -> Decimal:
        """Return regular pay plus overtime pay."""
        regular_pay = self.__hourly_rate * self.regular_hours
        overtime_pay = self.overtime_rate * self.overtime_hours
        return utils.to_money(regular_pay + overtime_pay)

    def calculate_tax(self, taxable: Decimal) -> Decimal:
        """Return a flat CONTRACT_WITHHOLDING_RATE of the taxable amount."""
        utils.require_non_negative(taxable, "taxable amount")
        return utils.to_money(taxable * utils.CONTRACT_WITHHOLDING_RATE)

    @property
    def tax_basis(self) -> str:
        """Describe the flat withholding rate, e.g. 'flat 15% withholding'."""
        return f"flat {utils.CONTRACT_WITHHOLDING_RATE:.0%} withholding"

    def pay_details(self) -> list[tuple[str, str]]:
        """Return hourly rate, regular and overtime hours and pay lines."""
        regular_pay = self.__hourly_rate * self.regular_hours
        overtime_pay = self.overtime_rate * self.overtime_hours
        overtime_label = f"Overtime hours (x{utils.OVERTIME_MULTIPLIER})"
        return [
            ("Hourly rate", utils.format_money(self.__hourly_rate)),
            ("Regular hours", f"{self.regular_hours:,}"),
            ("Regular pay", utils.format_money(regular_pay)),
            (overtime_label, f"{self.overtime_hours:,}"),
            ("Overtime pay", utils.format_money(overtime_pay)),
        ]


class Intern(Employee):
    """Intern on a fixed monthly stipend."""

    ROLE = utils.INTERN
    ROLE_TITLE = "Intern"

    def __init__(
        self, employee_id: str, name: str, stipend: utils.Amount
    ) -> None:
        """Create an intern; stipend must be above 0."""
        super().__init__(employee_id, name)
        self.__stipend = _valid_stipend(stipend)

    @property
    def stipend(self) -> Decimal:
        """Fixed monthly stipend."""
        return self.__stipend

    @stipend.setter
    def stipend(self, value: utils.Amount) -> None:
        self.__stipend = _valid_stipend(value)

    def calculate_salary(self) -> Decimal:
        """Return the stipend."""
        return utils.to_money(self.__stipend)

    def pay_details(self) -> list[tuple[str, str]]:
        """Return the monthly stipend line."""
        return [("Monthly stipend", utils.format_money(self.__stipend))]
