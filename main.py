from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.router import api_router
from backend.db.models import Base
from backend.db.session import engine
import logging
import traceback
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="BodeTech API (Monolith MVP) - Roles")
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEBUG_ERRORS = os.getenv("DEBUG_ERRORS", "true").lower() == "true"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error en {request.url.path}: {exc}")
    logger.error(traceback.format_exc())

    if DEBUG_ERRORS:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        },
    )


app.include_router(api_router)


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")