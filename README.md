# Job Application Tracker 0.1

A small CLI for learning Python and PostgreSQL directly. It uses Psycopg 3 and handwritten SQL—no
ORM, web framework, or frontend.

## Features

- Save companies, job postings, source IDs/URLs, salary details, and skills.
- List, inspect, and search jobs.
- Record and update application statuses and notes.
- Account-scope records now in preparation for later multi-tenancy.

This release remains single-user. It has no login, members, web UI, scraping, or automatic
LinkedIn/JobStreet lookup. See [the plan](docs/PLAN.md).

## Setup

Requires Python 3.11+ and PostgreSQL. From the repository folder:

```bash
createdb job_tracker
python -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/job_tracker"
export JOB_TRACKER_ACCOUNT="Personal"
job-tracker db-init
```

On Windows PowerShell, activation and configuration are:

```powershell
.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/job_tracker"
$env:JOB_TRACKER_ACCOUNT = "Personal"
job-tracker db-init
```

Adjust the database username/password for your PostgreSQL installation.

## Example

```bash
job-tracker add --company "Example Pty Ltd" --title "Backend Engineer" \
  --location "Remote" --source linkedin --source-job-id 123456789 \
  --url "https://www.linkedin.com/jobs/view/123456789" \
  --skill "C#:5" --skill "PostgreSQL:4"

job-tracker list
job-tracker show 1
job-tracker apply 1 --notes "Submitted through company website"
job-tracker apply 1 --status interviewing
job-tracker search "PostgreSQL"
job-tracker list --status interviewing
```

Use `job-tracker COMMAND --help` for options. Run tests with `pytest`.

More detail is in [the implementation notes](docs/IMPLEMENTATION.md).
