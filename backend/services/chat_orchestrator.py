# Servicio de orquestación de chat con inteligencia artificial
# NOTA: Este es un stub (función temporal) que debe ser reemplazado con:
#       - Enrutamiento de intención (intent routing)
#       - Herramientas de IA (recomendación, valuación, búsqueda)
#       - Integración con servicios de inventario y pricing

from typing import Any

def respond(message: str, context: dict[str, Any]) -> dict[str, Any]:
    # Convertir mensaje a minúsculas para búsqueda de palabras clave
    msg = message.lower()
    # Detectar intención de recomendación de vinos
    if "recomend" in msg or "tomar" in msg:
        return {
            "answer": "STUB: recomendación de hoy (usar inventario + reglas)",
            "actions": [{"type":"SHOW_RECOMMENDATIONS"}]  # Acción para mostrar recomendaciones
        }
    # Detectar intención de valuación o inventario
    if "vale" in msg or "valor" in msg or "stock" in msg:
        return {
            "answer": "STUB: valuación retail ARS/USD (usar pricing + fx)",
            "actions": [{"type":"OPEN_VALUATION"}]  # Acción para mostrar valuación
        }
    # Respuesta por defecto cuando no se detecta intención específica
    return {
        "answer": "STUB: puedo recomendar vinos, ubicar botellas y estimar valuación.",
        "actions": []  # Sin acciones específicas
    }
