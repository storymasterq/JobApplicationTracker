# Development plan

## 0.1 — implemented

- PostgreSQL schema: accounts, companies, jobs, applications, skills, and job skills.
- One personal account selected by `JOB_TRACKER_ACCOUNT`; no users or login yet.
- Handwritten SQL through Psycopg 3.
- CLI to initialize, add, list, show, search, and update applications.
- Source metadata for future importers without implementing provider lookup.
- Unit tests for CLI parsing and validation.

## Later, deliberately outside 0.1

1. Users, account membership, authentication, and PostgreSQL row-level security.
2. A web API and browser interface, after the CLI and data model are understood.
3. Structured import from supplied JSON.
4. LinkedIn/JobStreet ID lookup, subject to provider access and terms.
5. SaaS registration, authorization, billing, deployment, and backups.

## Why `account_id` exists now

Retrofitting tenant ownership touches nearly every table, constraint, and query. Version 0.1 remains
single-user, but stores ownership now so later multi-tenancy is an extension instead of a rewrite.
