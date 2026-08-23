# Job Application Tracker

A learning project for building a practical job-application tracker with Python and PostgreSQL.

## Current scope: Stage 1 only

Build a command-line application using:

- Python
- PostgreSQL
- `psycopg`
- handwritten SQL

The goal is to learn PostgreSQL directly before introducing an ORM or web framework.

## Domain

The first version should track:

- companies
- jobs
- applications
- skills
- skills required by each job
- notes associated with an application

## Suggested database schema

### `companies`

| Column | Purpose |
|---|---|
| `id` | Primary key |
| `name` | Company name |
| `website` | Company website; may be null |

### `jobs`

| Column | Purpose |
|---|---|
| `id` | Primary key |
| `company_id` | Foreign key to `companies` |
| `title` | Job title |
| `url` | Job-posting URL |
| `location` | Job location |
| `salary_min` | Minimum advertised salary; may be null |
| `salary_max` | Maximum advertised salary; may be null |
| `description` | Job description |
| `date_found` | Date the job was found |

### `applications`

| Column | Purpose |
|---|---|
| `id` | Primary key |
| `job_id` | Foreign key to `jobs` |
| `status` | Current application status |
| `date_applied` | Application date; may be null until applied |
| `notes` | Free-form application notes; may be null |

### `skills`

| Column | Purpose |
|---|---|
| `id` | Primary key |
| `name` | Unique skill name |

### `job_skills`

| Column | Purpose |
|---|---|
| `job_id` | Foreign key to `jobs` |
| `skill_id` | Foreign key to `skills` |
| `importance` | How important the skill is for this job |

`job_skills` represents the many-to-many relationship between jobs and skills.

## Required CLI operations

The interface should support commands equivalent to:

```bash
python jobs.py add
python jobs.py list
python jobs.py show 42
python jobs.py apply 42
python jobs.py search "C#"
```

Expected intent:

- `add`: add a job and its associated company/details
- `list`: list saved jobs with useful sorting or filtering
- `show <job_id>`: display one job and its related data
- `apply <job_id>`: record or update an application for a job
- `search <term>`: search jobs, companies, descriptions, or skills

Exact arguments and interaction style are intentionally left for implementation.

## PostgreSQL concepts to practise

The implementation should deliberately exercise:

- primary and foreign keys
- joins
- many-to-many relationships
- indexes
- constraints
- `NULL` handling
- transactions
- aggregation
- sorting
- filtering

## Out of scope

Do not add these during Stage 1:

- React or another frontend
- a web UI
- FastAPI or another HTTP API
- SQLAlchemy or another ORM
- Alembic migrations
- AI features
- the later multi-package application architecture

Keep the first implementation plain: one Python CLI, `psycopg`, PostgreSQL, and SQL written by hand.
