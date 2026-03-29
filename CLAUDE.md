# bodetech-backend

FastAPI 0.115 + SQLAlchemy 2.0 + PostgreSQL 16

## Running

```bash
docker compose up -d
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

## Key files

```
main.py                   ← FastAPI app, CORS, global error handler, create_all
backend/api/
  deps.py                 ← get_current_user, require_cellar_role
  router.py               ← master router
  schemas.py              ← Pydantic I/O
  routers/auth.py         ← register, login
  routers/cellars.py      ← CRUD + members
  routers/vision.py       ← upload, list, get, batch save, delete
  routers/inventory.py    ← STUB
backend/core/
  config.py               ← Settings(.env)
  security.py             ← hash/verify password, create tokens
backend/db/
  models.py               ← ORM models
  crud.py                 ← ALL db ops — raw text() only
  session.py              ← engine, get_db()
backend/schemas/vision_slots.py  ← BBoxInput, BatchSlotInput, SaveSlotsBatchRequest
backend/services/
  vision_wall.py          ← save_cellar_image, generate_fake_slots
  slot_geometry.py        ← bbox math, validation
```

## Auth & roles

- Access: 30 min. Refresh: 30 days (stored SHA-256 hashed). No refresh endpoint yet.
- All vision endpoints: `ensure_cellar_access(db, cellar_id, user_id)` → OWNER|ADMIN
- `DEBUG_ERRORS=true` by default → full tracebacks in 500s
