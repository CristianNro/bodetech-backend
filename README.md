# BodeTech Backend (FastAPI Monolith) - Roles (OWNER/ADMIN)

- Auth email+password (JWT access + refresh sessions)
- Multi-bodega: cellar_members with roles OWNER/ADMIN
- CRUD Cellars + Members (invite admin by email)
- Vision/Inventory/Chat/Valuation stubs

## Start
docker compose up -d
psql -h localhost -U postgres -d bodetech -f bodetech_schema_roles.sql
pip install -r requirements.txt
uvicorn backend.main:app --reload
