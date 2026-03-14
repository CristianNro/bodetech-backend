from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.db.models import User
import uuid
import json


# ========== FUNCIONES DE USUARIOS ==========

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    try:
        uid = uuid.UUID(user_id)
    except Exception:
        return None

    return db.query(User).filter(User.user_id == uid).first()


def create_user(db: Session, email: str, password_hash: str, full_name: str | None):
    user = User(
        user_id=uuid.uuid4(),
        email=email,
        password_hash=password_hash,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_refresh_session(db: Session, user_id: str, refresh_token_hash: str, expires_at):
    db.execute(
        text("""
            INSERT INTO sessions(session_id, user_id, refresh_token_hash, expires_at)
            VALUES (:sid, :uid, :rth, :exp)
        """),
        {
            "sid": str(uuid.uuid4()),
            "uid": user_id,
            "rth": refresh_token_hash,
            "exp": expires_at,
        },
    )
    db.commit()


# ========== FUNCIONES DE BODEGAS Y ROLES ==========

def create_cellar(db: Session, name: str) -> str:
    cellar_id = str(uuid.uuid4())

    row = db.execute(
        text("""
            INSERT INTO cellars(cellar_id, name)
            VALUES (:cid, :n)
            RETURNING cellar_id
        """),
        {
            "cid": cellar_id,
            "n": name,
        },
    ).fetchone()

    db.commit()
    return str(row[0])


def add_member(db: Session, cellar_id: str, user_id: str, role: str):
    db.execute(
        text("""
            INSERT INTO cellar_members(cellar_member_id, cellar_id, user_id, role)
            VALUES (:cmid, :c, :u, :r)
            ON CONFLICT (cellar_id, user_id)
            DO UPDATE SET role = EXCLUDED.role
        """),
        {
            "cmid": str(uuid.uuid4()),
            "c": cellar_id,
            "u": user_id,
            "r": role,
        },
    )
    db.commit()


def list_my_cellars(db: Session, user_id: str):
    rows = db.execute(
        text("""
            SELECT c.cellar_id, c.name, cm.role
            FROM cellars c
            JOIN cellar_members cm ON cm.cellar_id = c.cellar_id
            WHERE cm.user_id = :u
            ORDER BY c.created_at DESC
        """),
        {"u": user_id},
    ).fetchall()

    return [
        {
            "cellar_id": str(r[0]),
            "name": r[1],
            "role": r[2],
        }
        for r in rows
    ]


def get_user_role_in_cellar(db: Session, cellar_id: str, user_id: str):
    row = db.execute(
        text("""
            SELECT role
            FROM cellar_members
            WHERE cellar_id = :c AND user_id = :u
        """),
        {"c": cellar_id, "u": user_id},
    ).fetchone()

    return row[0] if row else None


def list_members(db: Session, cellar_id: str):
    rows = db.execute(
        text("""
            SELECT u.user_id, u.email, u.full_name, cm.role, cm.created_at
            FROM cellar_members cm
            JOIN users u ON u.user_id = cm.user_id
            WHERE cm.cellar_id = :c
            ORDER BY cm.created_at
        """),
        {"c": cellar_id},
    ).fetchall()

    return [
        {
            "user_id": str(r[0]),
            "email": r[1],
            "full_name": r[2],
            "role": r[3],
            "created_at": r[4].isoformat() if r[4] else None,
        }
        for r in rows
    ]


def set_member_role(db: Session, cellar_id: str, user_id: str, role: str):
    db.execute(
        text("""
            UPDATE cellar_members
            SET role = :r
            WHERE cellar_id = :c AND user_id = :u
        """),
        {"r": role, "c": cellar_id, "u": user_id},
    )
    db.commit()


def remove_member(db: Session, cellar_id: str, user_id: str):
    db.execute(
        text("""
            DELETE FROM cellar_members
            WHERE cellar_id = :c AND user_id = :u
        """),
        {"c": cellar_id, "u": user_id},
    )
    db.commit()


def delete_cellar(db: Session, cellar_id: str) -> bool:
    db.execute(
        text("""
            DELETE FROM cellar_members
            WHERE cellar_id = :c
        """),
        {"c": cellar_id},
    )

    result = db.execute(
        text("""
            DELETE FROM cellars
            WHERE cellar_id = :c
        """),
        {"c": cellar_id},
    )

    db.commit()
    return result.rowcount > 0


# ========== HELPERS PRIVADOS ==========

def _map_cellar_image_row(row):
    if not row:
        return None

    return {
        "image_id": str(row[0]),
        "cellar_id": str(row[1]),
        "uploaded_by": str(row[2]),
        "original_filename": row[3],
        "image_path": row[4],
        "image_url": row[5],
        "width": row[6],
        "height": row[7],
        "status": row[8],
        "created_at": row[9].isoformat() if row[9] else None,
    }


def _map_slot_row(row):
    if not row:
        return None

    return {
        "slot_id": str(row[0]),
        "cellar_id": str(row[1]),
        "image_id": str(row[2]),
        "slot_index": row[3],
        "label": row[4],
        "polygon_json": row[5],
        "bbox_json": row[6],
        "center_x": row[7],
        "center_y": row[8],
        "status": row[9],
        "confidence": row[10],
        "is_active": row[11],
        "is_user_corrected": row[12],
        "created_at": row[13].isoformat() if row[13] else None,
        "updated_at": row[14].isoformat() if row[14] else None,
    }


# ========== FUNCIONES DE IMÁGENES DE BODEGA ==========

def create_cellar_image(
    db: Session,
    cellar_id: str,
    uploaded_by: str,
    original_filename: str | None,
    image_path: str,
    width: int | None,
    height: int | None,
    status: str = "pending",
    image_url: str | None = None,
    commit: bool = True,
):
    image_id = str(uuid.uuid4())

    row = db.execute(
        text("""
            INSERT INTO cellar_images(
                image_id,
                cellar_id,
                uploaded_by,
                original_filename,
                image_path,
                image_url,
                width,
                height,
                status
            )
            VALUES (
                :image_id,
                :cellar_id,
                :uploaded_by,
                :original_filename,
                :image_path,
                :image_url,
                :width,
                :height,
                :status
            )
            RETURNING image_id, cellar_id, uploaded_by, original_filename,
                      image_path, image_url, width, height, status, created_at
        """),
        {
            "image_id": image_id,
            "cellar_id": cellar_id,
            "uploaded_by": uploaded_by,
            "original_filename": original_filename,
            "image_path": image_path,
            "image_url": image_url,
            "width": width,
            "height": height,
            "status": status,
        },
    ).fetchone()

    if commit:
        db.commit()

    return _map_cellar_image_row(row)


def get_cellar_image_by_id(db: Session, image_id: str):
    row = db.execute(
        text("""
            SELECT image_id, cellar_id, uploaded_by, original_filename,
                   image_path, image_url, width, height, status, created_at
            FROM cellar_images
            WHERE image_id = :image_id
        """),
        {"image_id": image_id},
    ).fetchone()

    return _map_cellar_image_row(row)


def get_cellar_image_in_cellar(db: Session, cellar_id: str, image_id: str):
    row = db.execute(
        text("""
            SELECT image_id, cellar_id, uploaded_by, original_filename,
                   image_path, image_url, width, height, status, created_at
            FROM cellar_images
            WHERE cellar_id = :cellar_id
              AND image_id = :image_id
        """),
        {
            "cellar_id": cellar_id,
            "image_id": image_id,
        },
    ).fetchone()

    return _map_cellar_image_row(row)


def list_cellar_images(db: Session, cellar_id: str):
    rows = db.execute(
        text("""
            SELECT image_id, cellar_id, uploaded_by, original_filename,
                   image_path, image_url, width, height, status, created_at
            FROM cellar_images
            WHERE cellar_id = :cellar_id
            ORDER BY created_at DESC
        """),
        {"cellar_id": cellar_id},
    ).fetchall()

    return [_map_cellar_image_row(row) for row in rows]


def update_cellar_image_status(db: Session, image_id: str, status: str, commit: bool = True):
    row = db.execute(
        text("""
            UPDATE cellar_images
            SET status = :status
            WHERE image_id = :image_id
            RETURNING image_id, cellar_id, uploaded_by, original_filename,
                      image_path, image_url, width, height, status, created_at
        """),
        {
            "image_id": image_id,
            "status": status,
        },
    ).fetchone()

    if commit:
        db.commit()

    return _map_cellar_image_row(row)


def get_latest_cellar_image(db: Session, cellar_id: str):
    row = db.execute(
        text("""
            SELECT image_id, cellar_id, uploaded_by, original_filename,
                   image_path, image_url, width, height, status, created_at
            FROM cellar_images
            WHERE cellar_id = :cellar_id
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"cellar_id": cellar_id},
    ).fetchone()

    return _map_cellar_image_row(row)


def delete_cellar_image(db: Session, cellar_id: str, image_id: str, commit: bool = True):
    row = db.execute(
        text("""
            DELETE FROM cellar_images
            WHERE cellar_id = :cellar_id
            AND image_id = :image_id
            RETURNING image_id, image_path
        """),
        {
            "cellar_id": cellar_id,
            "image_id": image_id,
        },
    ).fetchone()

    if commit:
        db.commit()

    if not row:
        return None

    return {
        "image_id": str(row[0]),
        "image_path": row[1],
    }

def delete_slots_by_image(db: Session, image_id: str, commit: bool = True):
    result = db.execute(
        text("""
            DELETE FROM cellar_slots
            WHERE image_id = :image_id
        """),
        {"image_id": image_id},
    )

    if commit:
        db.commit()

    return result.rowcount


# ========== FUNCIONES DE SLOTS DE BODEGA ==========

def mark_old_slots_inactive(db: Session, cellar_id: str):
    db.execute(
        text("""
            UPDATE cellar_slots
            SET is_active = FALSE,
                updated_at = NOW()
            WHERE cellar_id = :cellar_id
              AND is_active = TRUE
        """),
        {"cellar_id": cellar_id},
    )
    db.commit()


def create_cellar_slot(
    db: Session,
    cellar_id: str,
    image_id: str,
    slot_index: int,
    polygon_json,
    bbox_json,
    center_x: float | None = None,
    center_y: float | None = None,
    label: str | None = None,
    status: str = "unknown",
    confidence: float | None = None,
    is_active: bool = True,
    is_user_corrected: bool = False,
):
    slot_id = str(uuid.uuid4())

    row = db.execute(
        text("""
            INSERT INTO cellar_slots(
                slot_id,
                cellar_id,
                image_id,
                slot_index,
                label,
                polygon_json,
                bbox_json,
                center_x,
                center_y,
                status,
                confidence,
                is_active,
                is_user_corrected
            )
            VALUES (
                :slot_id,
                :cellar_id,
                :image_id,
                :slot_index,
                :label,
                CAST(:polygon_json AS JSONB),
                CAST(:bbox_json AS JSONB),
                :center_x,
                :center_y,
                :status,
                :confidence,
                :is_active,
                :is_user_corrected
            )
            RETURNING slot_id, cellar_id, image_id, slot_index, label,
                      polygon_json, bbox_json, center_x, center_y,
                      status, confidence, is_active, is_user_corrected,
                      created_at, updated_at
        """),
        {
            "slot_id": slot_id,
            "cellar_id": cellar_id,
            "image_id": image_id,
            "slot_index": slot_index,
            "label": label,
            "polygon_json": json.dumps(polygon_json),
            "bbox_json": json.dumps(bbox_json),
            "center_x": center_x,
            "center_y": center_y,
            "status": status,
            "confidence": confidence,
            "is_active": is_active,
            "is_user_corrected": is_user_corrected,
        },
    ).fetchone()

    return _map_slot_row(row)


def get_active_slots_by_cellar(db: Session, cellar_id: str):
    rows = db.execute(
        text("""
            SELECT slot_id, cellar_id, image_id, slot_index, label,
                   polygon_json, bbox_json, center_x, center_y,
                   status, confidence, is_active, is_user_corrected,
                   created_at, updated_at
            FROM cellar_slots
            WHERE cellar_id = :cellar_id
              AND is_active = TRUE
            ORDER BY slot_index
        """),
        {"cellar_id": cellar_id},
    ).fetchall()

    return [_map_slot_row(r) for r in rows]


def get_slots_by_image_id(db: Session, image_id: str, only_active: bool = False):
    sql = """
        SELECT slot_id, cellar_id, image_id, slot_index, label,
               polygon_json, bbox_json, center_x, center_y,
               status, confidence, is_active, is_user_corrected,
               created_at, updated_at
        FROM cellar_slots
        WHERE image_id = :image_id
    """

    if only_active:
        sql += " AND is_active = TRUE"

    sql += " ORDER BY slot_index"

    rows = db.execute(
        text(sql),
        {"image_id": image_id},
    ).fetchall()

    return [_map_slot_row(r) for r in rows]


def get_slot_by_id(db: Session, slot_id: str):
    row = db.execute(
        text("""
            SELECT slot_id, cellar_id, image_id, slot_index, label,
                   polygon_json, bbox_json, center_x, center_y,
                   status, confidence, is_active, is_user_corrected,
                   created_at, updated_at
            FROM cellar_slots
            WHERE slot_id = :slot_id
        """),
        {"slot_id": slot_id},
    ).fetchone()

    return _map_slot_row(row)


def update_slot_geometry(
    db: Session,
    slot_id: str,
    polygon_json=None,
    bbox_json=None,
    label: str | None = None,
    status: str | None = None,
):
    current = get_slot_by_id(db, slot_id)
    if not current:
        return None

    new_polygon = polygon_json if polygon_json is not None else current["polygon_json"]
    new_bbox = bbox_json if bbox_json is not None else current["bbox_json"]
    new_label = label if label is not None else current["label"]
    new_status = status if status is not None else current["status"]

    row = db.execute(
        text("""
            UPDATE cellar_slots
            SET polygon_json = CAST(:polygon_json AS JSONB),
                bbox_json = CAST(:bbox_json AS JSONB),
                label = :label,
                status = :status,
                is_user_corrected = TRUE,
                updated_at = NOW()
            WHERE slot_id = :slot_id
            RETURNING slot_id, cellar_id, image_id, slot_index, label,
                      polygon_json, bbox_json, center_x, center_y,
                      status, confidence, is_active, is_user_corrected,
                      created_at, updated_at
        """),
        {
            "slot_id": slot_id,
            "polygon_json": json.dumps(new_polygon),
            "bbox_json": json.dumps(new_bbox),
            "label": new_label,
            "status": new_status,
        },
    ).fetchone()

    db.commit()
    return _map_slot_row(row)


def delete_slots_by_ids(db: Session, image_id: str, slot_ids: list[str], commit: bool = True):
    if not slot_ids:
        return 0

    result = db.execute(
        text("""
            DELETE FROM cellar_slots
            WHERE image_id = :image_id
              AND slot_id = ANY(:slot_ids)
        """),
        {
            "image_id": image_id,
            "slot_ids": slot_ids,
        },
    )

    if commit:
        db.commit()

    return result.rowcount


def create_cellar_slot_with_commit_control(
    db: Session,
    cellar_id: str,
    image_id: str,
    slot_index: int,
    polygon_json,
    bbox_json,
    center_x: float | None = None,
    center_y: float | None = None,
    label: str | None = None,
    status: str = "unknown",
    confidence: float | None = None,
    is_active: bool = True,
    is_user_corrected: bool = False,
    commit: bool = True,
):
    slot_id = str(uuid.uuid4())

    row = db.execute(
        text("""
            INSERT INTO cellar_slots(
                slot_id,
                cellar_id,
                image_id,
                slot_index,
                label,
                polygon_json,
                bbox_json,
                center_x,
                center_y,
                status,
                confidence,
                is_active,
                is_user_corrected
            )
            VALUES (
                :slot_id,
                :cellar_id,
                :image_id,
                :slot_index,
                :label,
                CAST(:polygon_json AS JSONB),
                CAST(:bbox_json AS JSONB),
                :center_x,
                :center_y,
                :status,
                :confidence,
                :is_active,
                :is_user_corrected
            )
            RETURNING slot_id, cellar_id, image_id, slot_index, label,
                      polygon_json, bbox_json, center_x, center_y,
                      status, confidence, is_active, is_user_corrected,
                      created_at, updated_at
        """),
        {
            "slot_id": slot_id,
            "cellar_id": cellar_id,
            "image_id": image_id,
            "slot_index": slot_index,
            "label": label,
            "polygon_json": json.dumps(polygon_json),
            "bbox_json": json.dumps(bbox_json),
            "center_x": center_x,
            "center_y": center_y,
            "status": status,
            "confidence": confidence,
            "is_active": is_active,
            "is_user_corrected": is_user_corrected,
        },
    ).fetchone()

    if commit:
        db.commit()

    return _map_slot_row(row)


def update_slot_geometry_with_commit_control(
    db: Session,
    slot_id: str,
    polygon_json=None,
    bbox_json=None,
    label: str | None = None,
    status: str | None = None,
    center_x: float | None = None,
    center_y: float | None = None,
    is_active: bool | None = None,
    is_user_corrected: bool | None = None,
    commit: bool = True,
):
    current = get_slot_by_id(db, slot_id)
    if not current:
        return None

    row = db.execute(
        text("""
            UPDATE cellar_slots
            SET polygon_json = CAST(:polygon_json AS JSONB),
                bbox_json = CAST(:bbox_json AS JSONB),
                center_x = :center_x,
                center_y = :center_y,
                label = :label,
                status = :status,
                is_active = :is_active,
                is_user_corrected = :is_user_corrected,
                updated_at = NOW()
            WHERE slot_id = :slot_id
            RETURNING slot_id, cellar_id, image_id, slot_index, label,
                      polygon_json, bbox_json, center_x, center_y,
                      status, confidence, is_active, is_user_corrected,
                      created_at, updated_at
        """),
        {
            "slot_id": slot_id,
            "polygon_json": json.dumps(polygon_json),
            "bbox_json": json.dumps(bbox_json),
            "center_x": center_x,
            "center_y": center_y,
            "label": label,
            "status": status,
            "is_active": is_active if is_active is not None else current["is_active"],
            "is_user_corrected": (
                is_user_corrected
                if is_user_corrected is not None
                else current["is_user_corrected"]
            ),
        },
    ).fetchone()

    if commit:
        db.commit()

    return _map_slot_row(row)
