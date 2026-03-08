# Importaciones necesarias para FastAPI y base de datos
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud

# Crear router para valuación de bodegas con prefijo "/valuation"
router = APIRouter(prefix="/valuation", tags=["valuation"])

@router.get("/current")
def current(cellar_id: str, fx_mode: str = "MEP", db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario tiene permisos (OWNER o ADMIN) para ver valuación
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Retornar valuación actual de la bodega (stub con valores de prueba)
    return {
        "total_ars": 0,
        "total_usd": 0,
        "fx_used": {"name": fx_mode, "ars_per_usd": 0},
        "priced_items": 0,
        "unpriced_items": 0,
        "top_items": []
    }

@router.post("/refresh")
def refresh(cellar_id: str, fx_mode: str = "MEP", db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario tiene permisos (OWNER o ADMIN) para actualizar valuación
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Encolar tarea de actualización de valuación con el modo de cambio especificado (stub a implementar)
    return {"ok": True, "message": "STUB: valuation refresh queued", "fx_mode": fx_mode}
