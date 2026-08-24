from datetime import date
from decimal import Decimal

import pytest

from job_tracker.cli import build_parser, optional_text, parse_money, parse_skill


def test_add_command_parses_core_fields():
    args = build_parser().parse_args(["add", "--company", "Example", "--title", "Engineer", "--skill", "C#:5"])
    assert (args.company, args.title, args.skill) == ("Example", "Engineer", ["C#:5"])
    assert args.date_found == date.today()


@pytest.mark.parametrize(("value", "expected"), [("PostgreSQL", ("PostgreSQL", 3)), ("C#:5", ("C#", 5))])
def test_parse_skill(value, expected):
    assert parse_skill(value) == expected


@pytest.mark.parametrize("value", ["", "Python:0", "Python:6", "Python:high"])
def test_parse_skill_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        parse_skill(value)


def test_helpers():
    assert parse_money("1,500,000.50") == Decimal("1500000.50")
    assert parse_money("") is None
    assert optional_text("  ") is None
    assert optional_text(" Bali ") == "Bali"
