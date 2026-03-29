Review backend code changes or file(s): $ARGUMENTS

- [ ] All queries use `text()` — no ORM lazy loading
- [ ] Batch: `commit=False` + single `db.commit()` + `db.rollback()` on except
- [ ] Results use `_map_slot_row()` / `_map_cellar_image_row()`
- [ ] Every protected endpoint checks role (OWNER|ADMIN)
- [ ] `normalize_slot_indexes` before `validate_slots_batch` before writes
- [ ] `slot_id` OR `temp_id` present per slot (not both null)
- [ ] Image file deleted from disk on cellar_image delete
- [ ] New column → raw SQL migration provided
- [ ] No SQLAlchemy relationships
- [ ] Stubs not accidentally broken
