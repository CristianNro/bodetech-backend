# Importaciones para FastAPI y middleware
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.router import api_router

# Importaciones para base de datos
from backend.db.models import Base
from backend.db.session import engine

# Importaciones para logging y manejo de errores
import logging
import traceback

# Configurar logging en modo debug
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(title="BodeTech API (Monolith MVP) - Roles")

# Crear todas las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

# Configurar middleware CORS para permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las origins (cambiar en producción)
    allow_credentials=True,  # Permitir cookies y credentials
    allow_methods=["*"],  # Permitir todos los métodos HTTP
    allow_headers=["*"],  # Permitir todos los headers
)

# Manejador global de excepciones para capturar errores no tratados
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Registrar el error en los logs
    logger.error(f"Error en {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    # Retornar respuesta de error con detalles (cambiar en producción)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )

# Incluir todos los routers de API
app.include_router(api_router)

# Endpoint de salud para verificar que el servidor está funcionando
@app.get("/health")
def health():
    # Retornar respuesta de que el servidor está activo
    return {"ok": True}


# Punto de entrada de la aplicación
if __name__ == "__main__":
    # Importar y ejecutar servidor Uvicorn
    import uvicorn
    logger.info("Iniciando servidor...")
    # Iniciar servidor en localhost:8000 con logs en debug
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")