# Importaciones para manejo de autenticación, JWT y base de datos
from fastapi import Depends, HTTPException, status, Header
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.db.session import get_db
from backend.db import crud

def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    # Validar que el header Authorization está presente
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    # Dividir el header en formato "Bearer <token>"
    parts = authorization.split()
    # Verificar que el formato es válido (debe tener 2 partes y la primera debe ser "Bearer")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    # Extraer el token JWT
    token = parts[1]
    try:
        # Decodificar el token JWT usando la clave secreta
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        # Validar que el tipo de token es "access" (no refresh)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        # Obtener el user_id del payload del token
        user_id = payload.get("sub")
        # Buscar el usuario en la base de datos
        user = crud.get_user_by_id(db, user_id)
        # Validar que el usuario existe
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        # Retornar el usuario autenticado
        return user
    except JWTError:
        # Si hay error al decodificar el JWT, lanzar excepción
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token decode failed")

def require_cellar_role(cellar_id: str, allowed: set[str]):
    # Función que crea una dependencia parametrizada para validar roles en una bodega
    def _dep(db: Session = Depends(get_db), user=Depends(get_current_user)):
        # Obtener el rol del usuario en la bodega especificada
        role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
        # Validar que el usuario tiene uno de los roles permitidos
        if role is None or role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        # Retornar usuario y rol para uso en el endpoint
        return {"user": user, "role": role}
    return _dep
