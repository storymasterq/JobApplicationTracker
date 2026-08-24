from __future__ import annotations

import os
from pathlib import Path

import psycopg


def connect() -> psycopg.Connection:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example and export the value first."
        )
    return psycopg.connect(database_url)


def initialize_schema(connection: psycopg.Connection) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    with connection.cursor() as cursor:
        cursor.execute(schema_path.read_text(encoding="utf-8"))
    connection.commit()


def get_or_create_account_id(connection: psycopg.Connection) -> int:
    account_name = os.getenv("JOB_TRACKER_ACCOUNT", "Personal").strip() or "Personal"
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO accounts (name)
            VALUES (%s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (account_name,),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Could not create or find the account.")
    return row[0]
