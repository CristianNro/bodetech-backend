Generate a schema change for BodeTech.

Change: $ARGUMENTS

⚠️ No Alembic. `create_all` does NOT alter existing tables.

- New table → SQLAlchemy model in `models.py` only
- New column → model change + raw SQL:
  ```sql
  ALTER TABLE <table> ADD COLUMN <col> <type> DEFAULT <val>;
  ```
- Always warn: "Run SQL before restarting the server"
- Update `_map_*_row()` if column order changes
