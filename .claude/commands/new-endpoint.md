Add a new FastAPI endpoint to BodeTech backend.

Spec: $ARGUMENTS

Rules:
1. Router: correct `backend/api/routers/*.py`. New domain → new file + register in `router.py`
2. Auth: `Depends(get_current_user)` + role check → `HTTPException(403)` if not OWNER|ADMIN
3. DB: `text()` named params in `crud.py`. Use `_map_*_row()` mappers.
4. Batch: `commit=False` each op + single `db.commit()`. try/except + `db.rollback()`
5. Schemas: `backend/api/schemas.py` (or `backend/schemas/vision_slots.py` if slot-specific)
6. No ORM `.relationship()` — ever
