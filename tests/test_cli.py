from datetime import date
from decimal import Decimal

import os
import psycopg
import pytest

from job_tracker.cli import build_parser, optional_text, parse_money, parse_skill

@pytest.fixture
def database_connection():
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not set.")

    with psycopg.connect(database_url) as connection:
        yield connection

@pytest.fixture
def database_connection():
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not set.")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            database_name = cursor.fetchone()[0]

        if not database_name.endswith("_test"):
            pytest.fail(
                f"Refusing to run integration tests against {database_name!r}."
            )

        yield connection

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

def test_withdraw_command_parses_fields():
    args = build_parser().parse_args(["withdraw", "--job-id", "123", "--notes", "Withdrawing my application."])
    assert (args.job_id, args.notes) == ("123", "Withdrawing my application.")