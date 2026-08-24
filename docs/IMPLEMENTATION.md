# Version 0.1 implementation notes

The installable package lives under `src/job_tracker`. `argparse` provides the CLI, Psycopg 3
connects to PostgreSQL, and `schema.sql` is an idempotent initial schema. SQL remains visible on
purpose: no ORM or migration framework hides the joins, transactions, or upserts.

Every command operates within one automatically created account. Adding a job creates or reuses
its company in the same transaction, then adds supplied skills. Applying uses an upsert, preventing
duplicate application rows.

Commands: `db-init`, `add`, `list`, `show`, `apply`, and `search`.

## Known limitations

- Tests currently cover input parsing, not a live PostgreSQL instance.
- There are no edit or delete commands.
- Company deduplication uses exact name within an account.
- Search uses `ILIKE`, not PostgreSQL full-text search.
- Schema changes remain manual SQL for this learning stage.
