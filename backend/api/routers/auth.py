# Importaciones necesarias para FastAPI
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import hashlib
import logging

# Importaciones de la base de datos y seguridad
from backend.db.session import get_db
from backend.db import crud
from backend.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from backend.core.config import settings
from backend.api.schemas import RegisterIn, LoginIn, TokenOut, UserOut

# Configurar logger para registrar información y errores
logger = logging.getLogger(__name__)
# Crear router de autenticación con prefijo "/auth"
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    try:
        # Verificar si el email ya está registrado en la base de datos
        if crud.get_user_by_email(db, payload.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        # Crear nuevo usuario con contraseña hasheada
        user = crud.create_user(db, payload.email, hash_password(payload.password), payload.full_name)
        # Generar token de acceso JWT para la sesión actual
        access = create_access_token(str(user.user_id))
        # Generar token de refresco para renovar sesiones
        refresh = create_refresh_token(str(user.user_id))
        # Hashear el token de refresco para almacenarlo de forma segura en BD
        rth = hashlib.sha256(refresh.encode("utf-8")).hexdigest()
        # Calcular fecha de expiración del token de refresco
        expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_DAYS)
        # Guardar la sesión de refresco en la base de datos
        crud.create_refresh_session(db, str(user.user_id), rth, expires)
        # Registrar el nuevo usuario en los logs
        logger.info(f"Usuario creado: {user.user_id}")
        # Retornar tokens y datos del usuario
        return TokenOut(access_token=access, refresh_token=refresh,
                        user=UserOut(user_id=str(user.user_id), email=user.email, full_name=user.full_name))
    except Exception as e:
        # Registrar cualquier error que ocurra durante el registro
        logger.error(f"Error en registro: {e}", exc_info=True)
        raise

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    # Buscar el usuario en la base de datos por su email
    user = crud.get_user_by_email(db, payload.email)
    # Validar que el usuario existe y la contraseña es correcta
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # Generar token de acceso JWT para la sesión actual
    access = create_access_token(str(user.user_id))
    # Generar token de refresco para renovar sesiones futuras
    refresh = create_refresh_token(str(user.user_id))
    # Hashear el token de refresco para almacenarlo de forma segura
    rth = hashlib.sha256(refresh.encode("utf-8")).hexdigest()
    # Calcular fecha de expiración del token de refresco
    expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_DAYS)
    # Guardar la sesión de refresco en la base de datos
    crud.create_refresh_session(db, str(user.user_id), rth, expires)
    # Retornar los tokens de acceso y refresco junto con datos del usuario
    return TokenOut(access_token=access, refresh_token=refresh,
                    user=UserOut(user_id=str(user.user_id), email=user.email, full_name=user.full_name))