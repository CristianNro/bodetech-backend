# backend/ — DB & Services details

## DB Schema

```sql
users / sessions / cellars / cellar_members(UNIQUE cellar_id+user_id)
cellar_images(image_id, cellar_id, uploaded_by, image_path, image_url, width, height, status)
cellar_slots(slot_id, cellar_id, image_id, slot_index, label,
             polygon_json JSONB, bbox_json JSONB, center_x, center_y,
             status, confidence, is_active, is_user_corrected)
```

⚠️ No Alembic. New tables → model + create_all. New columns → raw `ALTER TABLE` SQL.

## Data shape pipeline

```
DB row (_map_slot_row):   polygon_json, bbox_json
serialize_slot output:    polygon,      bbox
Frontend slot object:     slot.bbox.{x,y,w,h}
```

Cualquier feature que toque geometría cruza este rename. No usar `slot.polygon_json` en frontend ni `slot.bbox` en backend.

## Auth guard pattern

- `get_current_user(db, authorization)` — Depends, usar siempre
- `ensure_cellar_access(db, cellar_id, user_id)` — definida en `vision.py`, llamar al inicio de endpoints vision/inventory
- `require_cellar_role` — definida en `deps.py`, **NO usada todavía** (reservada para role checks parametrizados)

## crud.py rules

- `text()` named params only — no ORM lazy loading ever
- Mappers: `_map_cellar_image_row(row)` / `_map_slot_row(row)` — always use
- Ambas funciones de escritura tienen `commit=True` por defecto. Usar `commit=False` en batch ops.
- `create_cellar_slot(..., commit=False)` — para batch inserts
- `update_slot_geometry(..., commit=False)` — para batch updates
- Batch pattern:
  ```python
  try:
      op1(db, ..., commit=False); op2(db, ..., commit=False)
      db.commit()
  except: db.rollback(); raise
  ```

## slot_geometry.py

```python
bbox_to_polygon(bbox)         → [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
bbox_center(bbox)             → (cx, cy)
normalize_slot_indexes(slots) → reindexes 0-based
validate_slots_batch(slots, W, H, max=40) → raises ValueError
```

Order: normalize → validate → write ops.

## vision_wall.py

```python
save_cellar_image(bytes, cellar_id, filename)
  → {image_id, image_path="/uploads/cellars/{id}/{uuid}.ext", image_url, width, height}

generate_fake_slots(width, height, rows=3, cols=4)
  → list[{slot_index, label, bbox, polygon, center_x, center_y, confidence=0.35}]
```

## serialize_slot output

```python
{slot_id, image_id, slot_index, label, polygon, bbox, center_x, center_y,
 status, confidence, is_active, is_user_corrected}
```
