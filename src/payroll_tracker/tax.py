"""Tax policies.

Each policy turns a taxable amount into tax owed. Employees are given a
policy rather than hard-coding a tax rule, so a new rule is added by writing a
new TaxPolicy subclass, without changing any employee class.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from decimal import Decimal

from payroll_tracker import config
from payroll_tracker.utils import require_non_negative, to_money

TaxBand = tuple[Decimal | None, Decimal]


class TaxPolicy(ABC):
    """A rule for calculating tax on a monthly taxable amount."""

    @abstractmethod
    def calculate(self, taxable: Decimal) -> Decimal:
        """Return the tax owed on a non-negative taxable amount."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of the rule, for reports."""


class ProgressiveTax(TaxPolicy):
    """Tax charged band by band, each band at its own rate."""

    def __init__(self, bands: Sequence[TaxBand] = config.TAX_BANDS) -> None:
        """Create a policy from (band width, rate) pairs.

        Only the last band may have a width of None, meaning "everything
        that is left".
        """
        if not bands:
            raise ValueError("at least one tax band is required")
        if any(width is None for width, _ in bands[:-1]):
            raise ValueError("only the last tax band may be open-ended")
        self.__bands = tuple(bands)

    def calculate(self, taxable: Decimal) -> Decimal:
        """Apply each band in turn until the whole amount is taxed."""
        require_non_negative(taxable, "taxable amount")
        tax = Decimal("0")
        remaining = taxable
        index = 0
        while remaining > 0 and index < len(self.__bands):
            width, rate = self.__bands[index]
            # The open-ended last band takes whatever is left.
            portion = remaining if width is None else min(remaining, width)
            tax += portion * rate
            remaining -= portion
            index += 1
        return to_money(tax)

    @property
    def description(self) -> str:
        """Describe the rule for reports."""
        return "progressive bands"


class FlatTax(TaxPolicy):
    """A single rate charged on the whole taxable amount."""

    def __init__(self, rate: Decimal) -> None:
        """Create a policy with a rate between 0 and 1."""
        if not 0 <= rate <= 1:
            raise ValueError(f"tax rate must be between 0 and 1 (got {rate})")
        self.__rate = rate

    def calculate(self, taxable: Decimal) -> Decimal:
        """Return the rate multiplied by the taxable amount."""
        require_non_negative(taxable, "taxable amount")
        return to_money(taxable * self.__rate)

    @property
    def description(self) -> str:
        """Describe the rule for reports, e.g. 'flat 15% withholding'."""
        return f"flat {self.__rate:.0%} withholding"


# Shared default policies. They hold no mutable state, so sharing is safe.
STANDARD_TAX = ProgressiveTax()
CONTRACT_WITHHOLDING = FlatTax(config.CONTRACT_WITHHOLDING_RATE)
