# Importar configuración de variables de entorno de Pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict

# Clase que define todas las variables de configuración de la aplicación
class Settings(BaseSettings):
    # Configurar que las variables se carguen del archivo .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # URL de conexión a la base de datos PostgreSQL (obligatorio)
    DATABASE_URL: str
    # Clave secreta para firmar JWT (por defecto, DEBE cambiarse en producción)
    JWT_SECRET: str = "change_me"
    # Duración de tokens de acceso en minutos
    JWT_ACCESS_MINUTES: int = 30
    # Duración de tokens de refresco en días
    JWT_REFRESH_DAYS: int = 30
    # Directorio para almacenar archivos subidos
    UPLOAD_DIR: str = "./uploads"
    # API key de Anthropic para análisis de etiquetas con Claude Vision
    ANTHROPIC_API_KEY: str = ""
    # API key de Tavily para verificación de datos de vinos en la web
    TAVILY_API_KEY: str = ""

# Instancia global de configuración
settings = Settings()
