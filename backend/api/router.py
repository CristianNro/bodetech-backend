# Importar FastAPI router y todos los routers específicos de cada módulo
from fastapi import APIRouter
from backend.api.routers.auth import router as auth_router
from backend.api.routers.cellars import router as cellars_router
from backend.api.routers.vision import router as vision_router
from backend.api.routers.inventory import router as inventory_router
from backend.api.routers.chat import router as chat_router
from backend.api.routers.valuation import router as valuation_router

# Crear router principal de la API
api_router = APIRouter()
# Incluir router de autenticación (registro, login)
api_router.include_router(auth_router)
# Incluir router de gestión de bodegas y miembros
api_router.include_router(cellars_router)
# Incluir router de análisis de visión por computadora
api_router.include_router(vision_router)
# Incluir router de gestión de inventario
api_router.include_router(inventory_router)
# Incluir router de chat con IA
api_router.include_router(chat_router)
# Incluir router de valuación de bodegas
api_router.include_router(valuation_router)
