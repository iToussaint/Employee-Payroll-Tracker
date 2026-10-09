from decimal import Decimal

import pytest

from payroll_tracker.payroll import (
    EmployeeRecord,
    calculate_payslip,
    contract_gross,
    payroll_totals,
    process_payroll,
    progressive_tax,
)


@pytest.mark.parametrize(
    ("taxable", "expected"),
    [
        ("0", "0.00"),
        ("1000", "0.00"),  # entirely in the 0% band
        ("1500", "50.00"),  # 500 at 10%
        ("3000", "200.00"),  # 2000 at 10%
        ("6000", "800.00"),  # 200 + 3000 at 20%
        ("7000", "1100.00"),  # 800 + 1000 at 30%
    ],
)
def test_progressive_tax_bands(taxable: str, expected: str) -> None:
    assert progressive_tax(Decimal(taxable)) == Decimal(expected)


def test_contract_gross_without_overtime() -> None:
    assert contract_gross(Decimal("20"), Decimal("160")) == Decimal("3200.00")


def test_contract_gross_with_overtime() -> None:
    # 160h * 20 + 10h * 20 * 1.5
    assert contract_gross(Decimal("20"), Decimal("170")) == Decimal("3500.00")


def test_full_time_payslip() -> None:
    slip = calculate_payslip(
        {
            "id": "FT1",
            "name": "A",
            "role": "full_time",
            "annual_salary": Decimal("60000"),
            "bonus": Decimal("500"),
        }
    )
    # gross 5000 + 500; pension 5% of 5000 = 250; taxable 5250 -> tax 650
    assert slip["gross_pay"] == Decimal("5500.00")
    assert slip["pension"] == Decimal("250.00")
    assert slip["tax"] == Decimal("650.00")
    assert slip["net_pay"] == Decimal("4600.00")


def test_contract_payslip_has_flat_tax_and_no_pension() -> None:
    slip = calculate_payslip(
        {
            "id": "CT1",
            "name": "B",
            "role": "contract",
            "hourly_rate": Decimal("20"),
            "hours_worked": Decimal("100"),
        }
    )
    assert slip["gross_pay"] == Decimal("2000.00")
    assert slip["tax"] == Decimal("300.00")
    assert slip["pension"] == Decimal("0.00")
    assert slip["net_pay"] == Decimal("1700.00")


def test_intern_below_tax_threshold_pays_no_tax() -> None:
    slip = calculate_payslip({"id": "IN1", "name": "C", "role": "intern", "stipend": Decimal("800")})
    assert slip["tax"] == Decimal("0.00")
    assert slip["net_pay"] == Decimal("800.00")


def test_negative_values_rejected() -> None:
    with pytest.raises(ValueError, match="stipend"):
        calculate_payslip({"id": "IN1", "name": "C", "role": "intern", "stipend": Decimal("-1")})
    with pytest.raises(ValueError, match="hours_worked"):
        contract_gross(Decimal("20"), Decimal("-5"))


def test_unknown_role_rejected() -> None:
    record: dict[str, object] = {"id": "X1", "name": "D", "role": "manager"}
    with pytest.raises(ValueError, match="Unknown role"):
        calculate_payslip(record)  # type: ignore[arg-type]


def test_process_payroll_maps_ids_and_totals() -> None:
    records: list[EmployeeRecord] = [
        {"id": "IN1", "name": "C", "role": "intern", "stipend": Decimal("800")},
        {
            "id": "CT1",
            "name": "B",
            "role": "contract",
            "hourly_rate": Decimal("20"),
            "hours_worked": Decimal("100"),
        },
    ]
    payroll = process_payroll(records)
    assert list(payroll) == ["IN1", "CT1"]
    totals = payroll_totals(payroll)
    assert totals["gross_pay"] == Decimal("2800.00")
    assert totals["net_pay"] == Decimal("2500.00")


def test_duplicate_ids_rejected() -> None:
    record: EmployeeRecord = {"id": "IN1", "name": "C", "role": "intern", "stipend": Decimal("800")}
    with pytest.raises(ValueError, match="Duplicate"):
        process_payroll([record, record])
