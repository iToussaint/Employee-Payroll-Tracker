"""Payroll rules and rates.

All amounts are per monthly pay period. Change the values here to adjust
how every payslip is calculated.
"""

from decimal import Decimal
from typing import Final

# Roles
FULL_TIME: Final = "full_time"
CONTRACT: Final = "contract"
INTERN: Final = "intern"
VALID_ROLES = (FULL_TIME, CONTRACT, INTERN)

MONTHS_PER_YEAR = Decimal("12")

# Full-time: pension contribution taken from base monthly salary.
PENSION_RATE = Decimal("0.05")

# Contract: hours beyond the standard month are paid at the overtime multiplier.
STANDARD_MONTHLY_HOURS = Decimal("160")
OVERTIME_MULTIPLIER = Decimal("1.5")
CONTRACT_WITHHOLDING_RATE = Decimal("0.15")

# Progressive monthly income tax bands as (band width, rate).
# A width of None means "everything above the previous bands".
TAX_BANDS: list[tuple[Decimal | None, Decimal]] = [
    (Decimal("1000"), Decimal("0.00")),
    (Decimal("2000"), Decimal("0.10")),
    (Decimal("3000"), Decimal("0.20")),
    (None, Decimal("0.30")),
]
