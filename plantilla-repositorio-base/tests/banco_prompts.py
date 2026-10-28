from typing import List, Dict, Any

def crear_esquema_clasificacion(enum_valores: List[str]) -> Dict[str, Any]:
    """Genera un esquema JSON restrictivo con validación estricta por enum."""
    return {
        "type": "OBJECT",
        "properties": {
            "categoria": {
                "type": "STRING",
                "enum": enum_valores
            },
            "confianza": {
                "type": "NUMBER",
                "description": "Nivel de certeza entre 0.0 y 1.0"
            }
        },
        "required": ["categoria", "confianza"]
    }

MENSAJE_PRUEBA = (
    "No puedo acceder al portal desde ayer. "
    "Ya cambié mi contraseña y sigo bloqueado. "
    "Hoy vence la entrega de mi informe y estoy muy molesto."
)

BANCO_DE_PROMPTS = [
    {
        "nombre": "clasificar_tema",
        "system_instruction": (
            "Clasifica el tema del ticket. "
            "Valores: 'acceso' (ingreso/contraseña), 'facturacion' (cobros/pagos), 'otro'."
        ),
        "ejemplo_usuario": MENSAJE_PRUEBA,
        "claves_esperadas": ["categoria", "confianza"],
        "categorias_permitidas": ["acceso", "facturacion", "otro"],
        "response_schema": crear_esquema_clasificacion(["acceso", "facturacion", "otro"]),
    },
    {
        "nombre": "clasificar_prioridad",
        "system_instruction": (
            "Clasifica la prioridad. "
            "Valores: 'alta' (bloqueo con vencimiento hoy), 'media' (bloqueo sin plazo hoy), 'baja' (consulta)."
        ),
        "ejemplo_usuario": MENSAJE_PRUEBA,
        "claves_esperadas": ["categoria", "confianza"],
        "categorias_permitidas": ["alta", "media", "baja"],
        "response_schema": crear_esquema_clasificacion(["alta", "media", "baja"]),
    },
    {
        "nombre": "clasificar_sentimiento",
        "system_instruction": (
            "Clasifica el sentimiento expresado. "
            "Valores: 'positivo' (satisfacción), 'negativo' (molestia/frustración), 'neutro'."
        ),
        "ejemplo_usuario": MENSAJE_PRUEBA,
        "claves_esperadas": ["categoria", "confianza"],
        "categorias_permitidas": ["positivo", "negativo", "neutro"],
        "response_schema": crear_esquema_clasificacion(["positivo", "negativo", "neutro"]),
    },
]