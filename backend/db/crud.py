from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.db.models import User
import uuid


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