# Importaciones necesarias para FastAPI, manejo de archivos y base de datos
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud
from backend.services.vision_wall import analyze_wall_image
from backend.services.vision_wine import identify_wine

# Crear router para análisis de visión por computadora con prefijo "/vision"
router = APIRouter(prefix="/vision", tags=["vision"])

@router.post("/wall/analyze")
async def wall_analyze(cellar_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario tiene permisos (OWNER o ADMIN) para analizar imágenes
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Leer contenido del archivo y analizar la imagen de la pared con visión por computadora
    return analyze_wall_image(await file.read())

@router.post("/wine/identify")
async def wine_identify(cellar_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario tiene permisos (OWNER o ADMIN) para identificar vinos
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Leer contenido del archivo e identificar el vino en la imagen usando visión por computadora
    return identify_wine(await file.read())
