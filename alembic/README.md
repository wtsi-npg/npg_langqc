# Database migrations with Alembic

You need to set `ALEMBIC_DB_URL` to the SQLAlchemy URL for the database you want
to operate on.
The format is `driver://user:pass@host:port/dbname`.

## Creating migrations for the QC database schema

What you need:

- a database with the schema from which you want to migrate.
- the URL for that database set in ALEMBIC_DB_URL
- the changes already applied in `lang_qc/db/qc_schema`

Then you create a revision:
`alembic revision --autogenerate -m 'This is a revision description'`
You must then go check the generated revision (alembic should show you the path
to it), and modify it as necessary. There is [a list of changes Alembic might
not detect correctly]. This includes table/column name changes, which generate
deletions and creations of tables/columns, so these must be changed manually.

## Running migrations

Run a migration with `alembic upgrade revision` where `revision` is the revision
identifier. Your database will now have the updated schema.

To generate a SQL script instead, use `alembic upgrade start:end` where start
and end are revision indentifiers. Your SQL script will be printed to standard
out. If you need to generate SQL to go from scratch, only specify the end
revision.

[a list of changes Alembic might not detect correctly]: https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect
