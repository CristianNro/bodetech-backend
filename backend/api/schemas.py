# Importaciones para validación de datos con Pydantic
from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional

# Esquema para entrada de registro de usuario
class RegisterIn(BaseModel):
    email: EmailStr  # Email del usuario (debe ser válido)
    password: str = Field(min_length=8)  # Contraseña con mínimo 8 caracteres
    full_name: Optional[str] = None  # (Opcional) Nombre completo del usuario

# Esquema para entrada de login de usuario
class LoginIn(BaseModel):
    email: EmailStr  # Email del usuario
    password: str  # Contraseña del usuario

# Esquema de salida con datos del usuario
class UserOut(BaseModel):
    user_id: str  # UUID del usuario
    email: EmailStr  # Email del usuario
    full_name: Optional[str] = None  # (Opcional) Nombre completo del usuario

# Esquema de salida con tokens de autenticación
class TokenOut(BaseModel):
    access_token: str  # Token JWT de acceso (corta duración)
    refresh_token: str  # Token JWT de refresco (larga duración)
    user: UserOut  # Información del usuario autenticado

# Esquemas para gestión de bodegas y roles de miembros

# Esquema para crear una bodega
class CellarCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)  # Nombre de la bodega

# Esquema de salida de información de bodega
class CellarOut(BaseModel):
    cellar_id: str  # ID único de la bodega
    name: str  # Nombre de la bodega
    role: Literal["OWNER","ADMIN"]  # Rol del usuario en la bodega

# Esquema para agregar un miembro a una bodega
class MemberAddIn(BaseModel):
    email: EmailStr  # Email del usuario a agregar
    role: Literal["ADMIN"] = "ADMIN"  # Rol del nuevo miembro (solo ADMIN en MVP)

# Esquema de salida de información de miembro
class MemberOut(BaseModel):
    user_id: str  # ID del usuario miembro
    email: EmailStr  # Email del miembro
    full_name: Optional[str] = None  # Nombre completo del miembro
    role: Literal["OWNER","ADMIN"]  # Rol del miembro en la bodega
    created_at: str  # Fecha de creación de la membresía

# Esquema para actualizar el rol de un miembro
class MemberRolePatchIn(BaseModel):
    role: Literal["OWNER","ADMIN"]  # Nuevo rol a asignar

# Esquemas para gestión de inventario

# Esquema para agregar una botella al inventario
class PutIn(BaseModel):
    slot_code: str  # Código de ubicación en la bodega
    wine_id: str  # ID del vino a almacenar
    source: Literal["MANUAL","AI_CONFIRMED"] = "MANUAL"  # Origen de la información (manual o IA)

# Esquema para remover una botella del inventario
class TakeIn(BaseModel):
    slot_code: str  # Código de ubicación de la botella a remover

# Esquemas para gestión de vinos

class WineCreateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    winery: str = Field(min_length=1, max_length=100)
    varietal: str = Field(min_length=1, max_length=80)
    vintage: Optional[int] = None
    region: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    quantity: int = Field(default=0, ge=0)

class WineUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    winery: Optional[str] = Field(None, max_length=100)
    varietal: Optional[str] = Field(None, max_length=80)
    vintage: Optional[int] = None
    region: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)

class WineOut(BaseModel):
    wine_id: str
    user_id: str
    name: Optional[str]
    winery: str
    varietal: str
    vintage: Optional[int]
    region: Optional[str]
    notes: Optional[str]
    quantity: int
    created_at: str
    updated_at: str


# Esquemas para comunicación con chat

# Esquema para entrada de mensaje de chat
class ChatMessageIn(BaseModel):
    thread_id: Optional[str] = None  # (Opcional) ID del hilo de conversación
    message: str  # Mensaje del usuario

# Esquema de salida de respuesta de chat
class ChatMessageOut(BaseModel):
    answer: str  # Respuesta del asistente de IA
    actions: list[dict] = []  # (Opcional) Acciones para ejecutar en el frontend
