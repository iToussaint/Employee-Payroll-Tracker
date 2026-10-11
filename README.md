# Employee Payroll Tracker

A command-line Python application that computes monthly payslips for three
kinds of employee: **full-time employees**, **contract employees** and
**interns**. Each role has its own pay, pension and tax rules, built with an
object-oriented class hierarchy.

## Features

- Role-specific salary calculation through method overriding
  (`calculate_salary()` behaves differently for each employee type)
- Progressive income tax bands, flat contractor withholding and pension
- Overtime pay for contractors above 160 hours a month
- Validated, encapsulated pay data: private attributes behind `@property`
  setters, with range checks and an audit history of every pay change
- Three reports: detailed payslips, a summary by role, and a payroll table
- Load employees from a JSON file, or use the built-in sample data
- Money handled with `Decimal`, never `float`, so amounts are exact to the cent
- Clear error messages and exit codes for bad input (no tracebacks)

## Requirements

- Python 3.10 or newer
- [Poetry](https://python-poetry.org/) 2.x

## Setup

```bash
git clone <repository-url>
cd Employee-Payroll-Tracker
poetry install
```

`poetry install` creates a virtual environment in `.venv/` (configured in
`poetry.toml`) and installs the project with its development tools (pytest,
mypy, flake8). In VS Code, the interpreter in `.venv/` is selected
automatically and `.vscode/launch.json` provides debug configurations for the
app and the tests.

## Usage

```bash
poetry run python -m payroll_tracker                     # all reports
poetry run python -m payroll_tracker --report payslips   # payslips only
poetry run python -m payroll_tracker --report summary    # totals by role
poetry run python -m payroll_tracker --report table      # one line each
poetry run python -m payroll_tracker --employee CT001    # one employee
poetry run python -m payroll_tracker --data data/employees.json
poetry run python -m payroll_tracker --help
```

| Option | Description |
|---|---|
| `-r`, `--report` | `all` (default), `payslips`, `summary` or `table` |
| `-e`, `--employee ID` | Only include the employee with this ID |
| `-d`, `--data FILE` | JSON file of employees (default: built-in sample) |

The exit code is `0` on success, `1` for invalid data (missing file, bad
JSON, invalid employee record, unknown employee ID) and `2` for invalid
command-line options.

### Employee data file

A JSON list of employee records. The `role` key decides which other fields
are needed. See [`data/employees.json`](data/employees.json).

| Role | Required fields | Optional fields |
|---|---|---|
| `full_time` | `id`, `name`, `annual_salary` | `bonus` (default 0) |
| `contract` | `id`, `name`, `hourly_rate`, `hours_worked` | |
| `intern` | `id`, `name`, `stipend` | |

```json
[
    {"id": "FT001", "name": "Ama Mensah", "role": "full_time",
     "annual_salary": 60000, "bonus": 500},
    {"id": "CT001", "name": "Kwame Boateng", "role": "contract",
     "hourly_rate": 25, "hours_worked": 172},
    {"id": "IN001", "name": "Esi Owusu", "role": "intern", "stipend": 1200}
]
```

## Payroll rules

All amounts are per monthly pay period. Rates and limits are defined as
constants in [`utils.py`](src/payroll_tracker/utils.py).

| | Full-time | Contract | Intern |
|---|---|---|---|
| **Gross pay** | annual salary / 12 + bonus | hours x rate; hours over 160 at 1.5x | fixed stipend |
| **Pension** | 5% of monthly base salary | none | none |
| **Tax** | progressive bands on gross - pension | flat 15% of gross | progressive bands on gross |
| **Net pay** | gross - pension - tax | gross - tax | gross - tax |

**Progressive tax bands (monthly):**

| Taxable income | Rate |
|---|---|
| First 1,000 | 0% |
| Next 2,000 | 10% |
| Next 3,000 | 20% |
| Above 6,000 | 30% |

**Validation ranges:**

| Field | Allowed range |
|---|---|
| `annual_salary` | greater than 0, up to 1,000,000 |
| `hourly_rate` | greater than 0, up to 1,000 |
| `stipend` | greater than 0, up to 5,000 |
| `bonus` | 0 to 50,000 |
| `hours_worked` | 0 to 744 (31 days x 24 hours) |

Amounts may be given as `int`, `Decimal` or numeric strings. Floats are
rejected because they cannot store most decimal amounts exactly.

## Project structure

```
Employee-Payroll-Tracker/
├── src/payroll_tracker/
│   ├── main.py        CLI: argument parsing, JSON loading, error handling
│   ├── employee.py    Employee class hierarchy and create_employee() factory
│   ├── payroll.py     calculate_salary(), apply_tax(), generate_payslip(),
│   │                  payroll totals and reports
│   ├── utils.py       Pay rules, money helpers, validation, formatting
│   └── __main__.py    Enables `python -m payroll_tracker`
├── tests/             pytest suite (one file per module)
├── data/
│   └── employees.json Sample input file
├── pyproject.toml     Project metadata, dependencies, mypy config
├── poetry.lock        Pinned dependency versions
└── .flake8            Style and docstring checks (PEP 8, Google docstrings)
```

## Design

```
                      Employee  (abstract base class)
                      ├── employee_id      read-only property
                      ├── name             validated property
                      ├── salary / pension / tax / net_pay
                      │                    read-only calculated properties
                      ├── pay_history      read-only audit trail
                      ├── calculate_salary()   abstract
                      ├── calculate_pension()  default: no pension
                      ├── calculate_tax()      default: progressive bands
                      ├── pay_details()        abstract
                      └── from_dict()          abstract
                                  │
        ┌─────────────────────────┼─────────────────────────┐
FullTimeEmployee           ContractEmployee                 Intern
 __annual_salary            __hourly_rate                   __stipend
 __bonus                    __hours_worked
 overrides salary,          overrides salary, tax,          overrides salary,
 pension, pay_details       tax_basis, pay_details          pay_details
```

- **Inheritance:** subclasses reuse the base class's identity, validation,
  audit history, calculated properties and default rules.
- **Encapsulation:** pay data lives in name-mangled private attributes
  (`self.__annual_salary`). It can only be changed through property setters,
  which validate the value and record the change in `pay_history`.
  Calculated figures and `employee_id` cannot be assigned at all.
- **Polymorphism:** `payroll.py` never checks an employee's type. It calls
  `calculate_salary()`, `pay_details()` and the other methods, and each
  subclass supplies its own behaviour. A new role only needs a new subclass
  and an entry in `EMPLOYEE_TYPES`.

## Sample output

```
============================================
        PAYSLIP - Contract Employee
============================================
Employee ID                            CT001
Name                           Kwame Boateng
--------------------------------------------
Hourly rate                            25.00
Regular hours                            160
Regular pay                         4,000.00
Overtime hours (x1.5)                     12
Overtime pay                          450.00
--------------------------------------------
Gross pay                           4,450.00
Pension                                 0.00
Tax (flat 15% withholding)            667.50
--------------------------------------------
NET PAY                             3,782.50
============================================

PAYROLL SUMMARY BY ROLE
Role                Count       Gross        Tax    Pension         Net
-----------------------------------------------------------------------
Full-time Employee      2   12,500.00   1,645.00     600.00   10,255.00
Contract Employee       1    4,450.00     667.50       0.00    3,782.50
Intern                  2    2,100.00      20.00       0.00    2,080.00
```

## Testing and quality checks

```bash
poetry run python -m pytest     # unit and CLI tests
poetry run python -m mypy       # strict static type checking
poetry run python -m flake8     # PEP 8 style and docstrings
```

> **Note for Windows machines with Device Guard / Smart App Control:** these
> policies can block compiled extensions and the `.exe` launchers that pip
> creates in `.venv/Scripts/`. Running tools as modules (`python -m ...`)
> avoids the launchers. mypy is pinned to 1.18 and installed as pure Python
> (`no-binary` in `poetry.toml`) for the same reason.
