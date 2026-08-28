from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation

from psycopg.rows import dict_row

from job_tracker.db import connect, get_or_create_account_id, initialize_schema

STATUSES = ("interested", "applied", "interviewing", "offered", "rejected", "withdrawn", "accepted")


def optional_text(value):
    return value.strip() or None if value is not None else None


def parse_money(value):
    value = optional_text(value)
    if value is None:
        return None
    try:
        amount = Decimal(value.replace(",", ""))
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"Invalid money amount: {value}") from exc
    if amount < 0:
        raise argparse.ArgumentTypeError("Money amounts cannot be negative.")
    return amount


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD.") from exc


def parse_skill(specification):
    name, separator, importance_text = specification.rpartition(":")
    if not separator:
        name, importance_text = specification, "3"
    name = name.strip()
    try:
        importance = int(importance_text)
    except ValueError as exc:
        raise ValueError(f"Invalid skill importance: {specification}") from exc
    if not name or importance not in range(1, 6):
        raise ValueError("Skills use NAME[:IMPORTANCE], with importance from 1 to 5.")
    return name, importance


def build_parser():
    parser = argparse.ArgumentParser(prog="job-tracker")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("db-init", help="create database tables")
    add = commands.add_parser("add", help="save a job")
    add.add_argument("--company", required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--company-website")
    add.add_argument("--url", dest="source_url")
    add.add_argument("--source")
    add.add_argument("--source-job-id")
    add.add_argument("--location")
    add.add_argument("--description")
    add.add_argument("--date-found", type=parse_date, default=date.today())
    add.add_argument("--salary-min", type=parse_money)
    add.add_argument("--salary-max", type=parse_money)
    add.add_argument("--currency", type=str.upper)
    add.add_argument("--skill", action="append", default=[], metavar="NAME[:IMPORTANCE]")
    listing = commands.add_parser("list", help="list jobs")
    listing.add_argument("--status", choices=STATUSES)
    listing.add_argument("--limit", type=int, default=50)
    show = commands.add_parser("show", help="show a job")
    show.add_argument("job_id", type=int)
    apply = commands.add_parser("apply", help="record/update an application")
    apply.add_argument("job_id", type=int)
    apply.add_argument("--status", choices=STATUSES, default="applied")
    apply.add_argument("--date", dest="date_applied", type=parse_date)
    apply.add_argument("--notes")
    search = commands.add_parser("search", help="search jobs")
    search.add_argument("term")
    search.add_argument("--limit", type=int, default=50)
    # withdraw = commands.add_parser("withdraw", help="withdraw an existing application")
    # withdraw.add_argument("job_id", type=int)
    # withdraw.add_argument("--notes")
    return parser


def add_job(connection, account_id, args):
    skills = [parse_skill(item) for item in args.skill]
    if (args.source is None) != (args.source_job_id is None):
        raise ValueError("--source and --source-job-id must be supplied together.")
    if args.currency and len(args.currency) != 3:
        raise ValueError("--currency must be a three-letter code such as IDR.")
    with connection.cursor() as cursor:
        cursor.execute("""INSERT INTO companies (account_id,name,website) VALUES (%s,%s,%s)
            ON CONFLICT (account_id,name) DO UPDATE SET website=COALESCE(EXCLUDED.website,companies.website)
            RETURNING id""", (account_id, args.company.strip(), optional_text(args.company_website)))
        company_id = cursor.fetchone()[0]
        cursor.execute("""INSERT INTO jobs
            (account_id,company_id,source,source_job_id,source_url,title,location,salary_min,salary_max,salary_currency,description,date_found)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (account_id,company_id,optional_text(args.source),optional_text(args.source_job_id),
             optional_text(args.source_url),args.title.strip(),optional_text(args.location),args.salary_min,
             args.salary_max,optional_text(args.currency),optional_text(args.description),args.date_found))
        job_id = cursor.fetchone()[0]
        for name, importance in skills:
            cursor.execute("""INSERT INTO skills (account_id,name) VALUES (%s,%s)
                ON CONFLICT (account_id,lower(name)) DO UPDATE SET name=skills.name RETURNING id""",
                (account_id, name))
            cursor.execute("INSERT INTO job_skills VALUES (%s,%s,%s)", (job_id, cursor.fetchone()[0], importance))
    connection.commit()
    print(f"Added job {job_id}.")


def find_jobs(connection, account_id, term=None, status=None, limit=50):
    where, params = ["j.account_id=%s"], [account_id]
    if term:
        where.append("(j.title ILIKE %s OR c.name ILIKE %s OR j.description ILIKE %s OR EXISTS "
                     "(SELECT 1 FROM job_skills js JOIN skills s ON s.id=js.skill_id WHERE js.job_id=j.id AND s.name ILIKE %s))")
        params += [f"%{term}%"] * 4
    if status:
        where.append("a.status=%s"); params.append(status)
    params.append(limit)
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(f"""SELECT j.id,c.name company,j.title,j.date_found,COALESCE(a.status,'saved') status
            FROM jobs j JOIN companies c ON c.id=j.company_id
            LEFT JOIN applications a ON a.job_id=j.id AND a.account_id=j.account_id
            WHERE {' AND '.join(where)} ORDER BY j.date_found DESC,j.id DESC LIMIT %s""", params)
        return cursor.fetchall()


def print_jobs(rows):
    if not rows:
        print("No jobs found."); return
    print(f"{'ID':>4}  {'FOUND':10}  {'STATUS':12}  {'COMPANY':24}  TITLE")
    for row in rows:
        print(f"{row['id']:>4}  {row['date_found']}  {row['status'][:12]:12}  {row['company'][:24]:24}  {row['title']}")


def show_job(connection, account_id, job_id):
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute("""SELECT j.*,c.name company,a.status,a.date_applied,a.notes,
            COALESCE(string_agg(s.name||' ('||js.importance||')',', ' ORDER BY js.importance DESC),'') skills
            FROM jobs j JOIN companies c ON c.id=j.company_id
            LEFT JOIN applications a ON a.job_id=j.id AND a.account_id=j.account_id
            LEFT JOIN job_skills js ON js.job_id=j.id LEFT JOIN skills s ON s.id=js.skill_id
            WHERE j.account_id=%s AND j.id=%s GROUP BY j.id,c.id,a.id""", (account_id, job_id))
        row = cursor.fetchone()
    if not row:
        raise LookupError(f"Job {job_id} was not found.")
    print(f"Job {job_id}")
    for label, key in (("Company","company"),("Title","title"),("Location","location"),("Found","date_found"),
                       ("URL","source_url"),("Skills","skills"),("Status","status"),("Applied","date_applied"),
                       ("Notes","notes"),("Description","description")):
        if row[key] not in (None, ""):
            print(f"{label}: {row[key]}")

def set_application_status(
    connection,
    account_id,
    job_id,
    status,
    date_applied=None,
    notes=None,
):
    cleaned_notes = optional_text(notes)
    applied_on = date_applied or (
        date.today() if status != "interested" else None
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM jobs
            WHERE account_id = %s AND id = %s
            """,
            (account_id, job_id),
        )

        if not cursor.fetchone():
            raise LookupError(f"Job {job_id} was not found.")

        cursor.execute(
            """
            INSERT INTO applications (
                account_id,
                job_id,
                status,
                date_applied,
                notes
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (account_id, job_id)
            DO UPDATE SET
                status = EXCLUDED.status,
                date_applied = COALESCE(
                    EXCLUDED.date_applied,
                    applications.date_applied
                ),
                notes = COALESCE(
                    EXCLUDED.notes,
                    applications.notes
                ),
                updated_at = now()
            """,
            (
                account_id,
                job_id,
                status,
                applied_on,
                cleaned_notes,
            ),
        )

    note_text = f": {cleaned_notes}" if cleaned_notes else ""

    connection.commit()
    print(f"Job {job_id} is now {status}{note_text}.")

def apply_to_job(connection, account_id, args):
    set_application_status(
        connection,
        account_id,
        args.job_id,
        args.status,
        args.date_applied,
        args.notes,
    )

def withdraw_from_job(connection, account_id, args):
    set_application_status(
        connection,
        account_id,
        args.job_id,
        "withdrawn",
        notes=args.notes,
    )

def run(args):
    with connect() as connection:
        if args.command == "db-init":
            initialize_schema(connection); print("Database schema initialized."); return
        account_id = get_or_create_account_id(connection)
        if args.command == "add": add_job(connection, account_id, args)
        elif args.command == "list": print_jobs(find_jobs(connection, account_id, status=args.status, limit=args.limit))
        elif args.command == "show": show_job(connection, account_id, args.job_id)
        elif args.command == "apply": apply_to_job(connection, account_id, args)
        elif args.command == "withdraw": withdraw_from_job(connection, account_id, args)
        elif args.command == "search": print_jobs(find_jobs(connection, account_id, term=args.term, limit=args.limit))


def main(argv=None):
    parser = build_parser(); args = parser.parse_args(argv)
    try:
        run(args)
    except (RuntimeError, ValueError, LookupError) as exc:
        parser.error(str(exc))
    return 0
