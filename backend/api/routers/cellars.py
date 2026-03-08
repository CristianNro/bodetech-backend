# Importaciones necesarias para FastAPI y gestión de base de datos
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Importaciones de bases de datos, autenticación y esquemas
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud
from backend.api.schemas import CellarCreateIn, CellarOut, MemberAddIn, MemberOut, MemberRolePatchIn

# Crear router para gestión de bodegas con prefijo "/cellars"
router = APIRouter(prefix="/cellars", tags=["cellars"])

@router.get("", response_model=list[CellarOut])
def list_cellars(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener todas las bodegas del usuario autenticado
    return crud.list_my_cellars(db, str(user.user_id))

@router.post("", response_model=CellarOut)
def create_cellar(payload: CellarCreateIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Crear una nueva bodega con el nombre proporcionado
    cellar_id = crud.create_cellar(db, payload.name)
    # Agregar al usuario como propietario (OWNER) de la bodega creada
    crud.add_member(db, cellar_id, str(user.user_id), "OWNER")
    # Retornar información de la bodega creada
    return {"cellar_id": cellar_id, "name": payload.name, "role": "OWNER"}

@router.get("/{cellar_id}/members", response_model=list[MemberOut])
def list_members(cellar_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario es OWNER o ADMIN para ver miembros
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Retornar lista de miembros de la bodega
    return crud.list_members(db, cellar_id)

@router.post("/{cellar_id}/members", response_model=dict)
def add_admin(cellar_id: str, payload: MemberAddIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Solo OWNER puede invitar miembros
    if role != "OWNER":
        raise HTTPException(status_code=403, detail="Only OWNER can add admins")
    # Buscar el usuario a agregar por su email
    target = crud.get_user_by_email(db, payload.email)
    # Validar que el usuario existe
    if not target:
        raise HTTPException(status_code=404, detail="User not found (must be registered)")
    # Agregar el usuario a la bodega con el rol especificado
    crud.add_member(db, cellar_id, str(target.user_id), payload.role)
    # Retornar confirmación de éxito
    return {"ok": True}

@router.patch("/{cellar_id}/members/{member_user_id}", response_model=dict)
def set_role(cellar_id: str, member_user_id: str, payload: MemberRolePatchIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Solo OWNER puede cambiar roles de otros miembros
    if role != "OWNER":
        raise HTTPException(status_code=403, detail="Only OWNER can change roles")
    # Actualizar el rol del miembro en la bodega
    crud.set_member_role(db, cellar_id, member_user_id, payload.role)
    # Retornar confirmación de éxito
    return {"ok": True}

@router.delete("/{cellar_id}/members/{member_user_id}", response_model=dict)
def remove_member(cellar_id: str, member_user_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Solo OWNER puede eliminar miembros
    if role != "OWNER":
        raise HTTPException(status_code=403, detail="Only OWNER can remove members")
    # Eliminar el miembro de la bodega
    crud.remove_member(db, cellar_id, member_user_id)
    # Retornar confirmación de éxito
    return {"ok": True}
