import os
import psycopg
import pytest

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

        clean_database(connection)

        try:
            yield connection
        finally:
            connection.rollback()
            clean_database(connection)

@pytest.fixture
def saved_job(database_connection):
    connection = database_connection

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO accounts (name) VALUES (%s) RETURNING id",
            ("Test Account",),
        )
        account_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO companies (account_id, name)
            VALUES (%s, %s)
            RETURNING id
            """,
            (account_id, "Test Company"),
        )
        company_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO jobs (account_id, company_id, title)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (account_id, company_id, "Test Developer"),
        )
        job_id = cursor.fetchone()[0]

    connection.commit()

    return account_id, job_id

