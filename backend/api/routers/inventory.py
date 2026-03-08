# Importaciones necesarias para FastAPI y base de datos
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud
from backend.api.schemas import PutIn, TakeIn

# Crear router para gestión de inventario con prefijo "/inventory"
router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.post("/put")
def put_item(cellar_id: str, payload: PutIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario tiene permisos (OWNER o ADMIN) para agregar items
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Retornar confirmación de la operación (actualmente es un stub a implementar)
    return {"ok": True, "message": "STUB: put wine into slot", "payload": payload.model_dump()}

@router.post("/take")
def take_item(cellar_id: str, payload: TakeIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario tiene permisos (OWNER o ADMIN) para remover items
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Retornar confirmación de la operación (actualmente es un stub a implementar)
    return {"ok": True, "message": "STUB: take wine from slot", "payload": payload.model_dump()}
