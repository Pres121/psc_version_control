# models/

This project talks to Supabase via the `supabase-py` client rather than
an ORM, so there are no SQLAlchemy model classes here. The source of
truth for table structure is `supabase/migrations/001_init_schema.sql`.

Request/response shapes live in `app/schemas/` (Pydantic models).

If you later add a full ORM (e.g. SQLAlchemy + asyncpg against
`DATABASE_URL`), this is where those model classes would go.
