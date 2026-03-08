# Importaciones necesarias para FastAPI y base de datos
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud
from backend.api.schemas import ChatMessageIn, ChatMessageOut
from backend.services.chat_orchestrator import respond

# Crear router para mensajes de chat con prefijo "/chat"
router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=ChatMessageOut)
def chat_message(cellar_id: str, payload: ChatMessageIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Obtener el rol del usuario en la bodega
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))
    # Validar que el usuario tiene permisos (OWNER o ADMIN) para enviar mensajes
    if role not in ("OWNER","ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Procesar el mensaje y obtener respuesta del servicio de chat
    out = respond(payload.message, context={})
    # Retornar la respuesta y acciones asociadas
    return ChatMessageOut(answer=out["answer"], actions=out.get("actions", []))
