"""Payroll rules, rates and validation limits.

All amounts are per monthly pay period. Change the values here to adjust how
every payslip is calculated; no other module hard-codes these numbers.
"""

from decimal import Decimal
from typing import Final

# Role keys, as used in data files.
FULL_TIME: Final = "full_time"
CONTRACT: Final = "contract"
INTERN: Final = "intern"

MONTHS_PER_YEAR: Final = Decimal("12")

# Full-time: pension contribution taken from base monthly salary.
PENSION_RATE: Final = Decimal("0.05")

# Contract: hours beyond the standard month earn the overtime multiplier.
STANDARD_MONTHLY_HOURS: Final = Decimal("160")
OVERTIME_MULTIPLIER: Final = Decimal("1.5")
CONTRACT_WITHHOLDING_RATE: Final = Decimal("0.15")

# Progressive monthly income tax bands as (band width, rate).
# A width of None means "everything above the previous bands".
TAX_BANDS: Final[tuple[tuple[Decimal | None, Decimal], ...]] = (
    (Decimal("1000"), Decimal("0.00")),
    (Decimal("2000"), Decimal("0.10")),
    (Decimal("3000"), Decimal("0.20")),
    (None, Decimal("0.30")),
)

# Upper limits on pay inputs, to catch data-entry mistakes (an extra zero).
MAX_ANNUAL_SALARY: Final = Decimal("1000000")
MAX_BONUS: Final = Decimal("50000")
MAX_HOURLY_RATE: Final = Decimal("1000")
MAX_MONTHLY_HOURS: Final = Decimal("744")  # 31 days * 24 hours
MAX_STIPEND: Final = Decimal("5000")
