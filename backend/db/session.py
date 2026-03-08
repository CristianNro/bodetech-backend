# Importaciones para crear conexión a base de datos
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

# Crear motor de SQLAlchemy con la URL de la base de datos
# pool_pre_ping=True verifica la conexión antes de usarla
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
# Crear factory para crear sesiones de base de datos
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    # Crear una nueva sesión de base de datos
    db = SessionLocal()
    try:
        # Retornar la sesión para uso en la petición
        yield db
    finally:
        # Cerrar la sesión después de usar (cleanup)
        db.close()
