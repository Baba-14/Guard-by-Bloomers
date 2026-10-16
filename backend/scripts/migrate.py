"""Apply Guard SQL migrations to DATABASE_URL exactly once.

Run from the repository root with: backend/.venv/bin/python backend/scripts/migrate.py
"""

from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def connection_url() -> str:
    value = os.getenv("DATABASE_URL", "")
    if not value:
        raise SystemExit("DATABASE_URL is required")
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def main() -> None:
    migrations = sorted((BACKEND_DIR / "migrations").glob("*.sql"))
    with psycopg.connect(connection_url(), autocommit=True) as connection:
        connection.execute(
            "create table if not exists public.guard_schema_migrations "
            "(name text primary key, applied_at timestamptz not null default now())"
        )
        applied = {
            row[0]
            for row in connection.execute("select name from public.guard_schema_migrations")
        }
        for migration in migrations:
            if migration.name in applied:
                print(f"skip  {migration.name}")
                continue
            print(f"apply {migration.name}")
            connection.execute(migration.read_text())
            connection.execute(
                "insert into public.guard_schema_migrations(name) values (%s)",
                (migration.name,),
            )
    print("Database migrations are up to date.")


if __name__ == "__main__":
    main()
