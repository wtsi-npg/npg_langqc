# Database migrations with [Alembic](https://alembic.sqlalchemy.org/en/latest/)

## Testing proposed changes

Planned changes should be applied in [lang_qc/db/qc_schema.py](../lang_qc/db/qc_schema.py).
We recommend doing this manually.

Changes to unit tests, test fixtures and the source code should be applied as
appropriate. 

## Creating migrations for the QC database schema

What you need:

- a database with the schema from which you want to migrate.
- the URL for that database set in `ALEMBIC_DB_URL`

Set `ALEMBIC_DB_URL` env. variable to the SQLAlchemy URL for the database you
want to operate on. The format is `driver://user:pass@host:port/dbname`, where
for MySQL and our software stack the driver is `mysql+pymysql`.

Ensure `alembic` is on your PATH. Run all commands from the root of the
repository, where the configuration for alembic `alembic.ini` resides.

Create a revision:

```
 # This example command generates alembic/versions/2.0.0_drop_json_properties_column.py
 # python script, which contains an empty template for defining the migration.
 alembic revision -m 'drop_json_properties_column' --rev-id 2.0.0 --head 3814003a709a
```

If `--rev_id` is not specified, `alembic` generates a random id for the migration,
which does not present the problem immideately, but makes it difficult long term to
understand the order of migrations and identify the latest migration. Set `--rev_id`
to the next release version.

The value of the `--head` argument is the version of the previous migration.

Edit the newly generated script. Define explicitly SQL statements that have to be
executed both for the `upgrade` and `downgrade` function definitions in the
script. Call execution of these statements, one at a time. Executing multiple
statements in one go does not work. See examples in the [versions](./versions)
directory.

We do not recommend a 'pure' alembic migration path since this would require
maintainers to know the syntax used by `alembic`. Besides, there is
[a list of changes Alembic might not detect correctly]. This includes
table/column name changes, which generate deletion and creation of tables/columns,
so these must be changed manually. It also includes uncommon index properties,
such as sorting dates in descending order.

Both DDL and DML statements can be included into the  migration. However, we
recommend that DML statements change only those tables that perform the
role of static dictionaries.

## Running migrations

Migrations should be run on the dev database first. The timing of the
production database update might vary depending of the nature of the
applied change. 

Check what is going to be executed by generating an SQL script. Use

```alembic upgrade start:end --sql```

where start and end are revision identifiers. Your SQL script will be printed to
standard out. If you need to generate SQL to go from scratch, only specify the
end revision or `head`.

Run a migration with

```alembic upgrade revision```

where `revision` is the revision identifier. Your database will now have the
updated schema. Note that the start:end syntax is not recognised for running
the migration.

[a list of changes Alembic might not detect correctly]: https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect

## Making sure the ORM model has not diverged from the DB schema

As of alembic 1.9, we gain the `alembic check` command, that generates errors
if the server and ORM model are different. If there are changes,
`alembic revision --autogenerate` can create a revision to alter the DB schema
to match the ORM model. This may not be precisely what you want it to do!

CAVEAT: alembic does not do a good job of handling indexes created by hand in
a previous migration. It will try to drop and recreate them with different
names. It will also lose any properties that alembic is not able to detect.
This situation may be improved with updates for sqlalchemy 2.0 in the future.
