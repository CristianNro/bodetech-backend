# Importaciones para seguridad criptográfica y JWT
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from .config import settings

# Contexto para hash de contraseñas usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # Convertir contraseña a string
    password = str(password)
    # Limitar a 72 caracteres (límite de bcrypt)
    password = password[:72]
    # Retornar hash bcrypt de la contraseña
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    # Verificar que la contraseña coincide con el hash almacenado
    return pwd_context.verify(password, password_hash)

def create_access_token(user_id: str) -> str:
    # Obtener fecha y hora actual en UTC
    now = datetime.now(timezone.utc)
    # Calcular fecha de expiración (sumando minutos configurados)
    exp = now + timedelta(minutes=settings.JWT_ACCESS_MINUTES)
    # Crear payload del token JWT
    payload = {
        "sub": user_id,  # Subject: ID del usuario
        "type": "access",  # Tipo de token (diferencia access de refresh)
        "iat": int(now.timestamp()),  # Emitido en (issued at)
        "exp": int(exp.timestamp())  # Expira en (expiration)
    }
    # Codificar y firmar el JWT con la clave secreta
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def create_refresh_token(user_id: str) -> str:
    # Obtener fecha y hora actual en UTC
    now = datetime.now(timezone.utc)
    # Calcular fecha de expiración (sumando días configurados)
    exp = now + timedelta(days=settings.JWT_REFRESH_DAYS)
    # Crear payload del token JWT de refresco
    payload = {
        "sub": user_id,  # Subject: ID del usuario
        "type": "refresh",  # Tipo de token (diferencia refresh de access)
        "iat": int(now.timestamp()),  # Emitido en (issued at)
        "exp": int(exp.timestamp())  # Expira en (expiration)
    }
    # Codificar y firmar el JWT con la clave secreta
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")