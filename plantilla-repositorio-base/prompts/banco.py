# Esquema base parametrizable para reutilizar estructuras
def crear_esquema_clasificacion(enum_valores):
    return {
        "type": "OBJECT",
        "properties": {
            "categoria": {
                "type": "STRING", 
                "enum": enum_valores
            },
            "confianza": {
                "type": "NUMBER",
                "description": "Valor entre 0.0 y 1.0"
            },
        },
        "required": ["categoria", "confianza"],
    }

MENSAJE = (
    "No puedo acceder al portal desde ayer. "
    "Ya cambié mi contraseña y sigo bloqueado. "
    "Hoy vence la entrega de mi informe y estoy muy molesto."
)

BANCO_DE_PROMPTS = [
    {
        "nombre": "clasificar_tema",
        "system_instruction": (
            "Clasifica el tema principal del ticket. "
            "Valores: 'acceso' (problemas de ingreso/contraseña), "
            "'facturacion' (cobros/pagos), 'otro' (demás casos)."
        ),
        "ejemplo_usuario": MENSAJE,
        "claves_esperadas": ["categoria", "confianza"],
        "categorias_permitidas": ["acceso", "facturacion", "otro"],
        "response_schema": crear_esquema_clasificacion(["acceso", "facturacion", "otro"]),
    },
    {
        "nombre": "clasificar_prioridad",
        "system_instruction": (
            "Clasifica la prioridad del ticket. "
            "Valores: 'alta' (bloqueo con vencimiento hoy), "
            "'media' (bloqueo sin plazo hoy), "
            "'baja' (consulta sin bloqueo)."
        ),
        "ejemplo_usuario": MENSAJE,
        "claves_esperadas": ["categoria", "confianza"],
        "categorias_permitidas": ["alta", "media", "baja"],
        "response_schema": crear_esquema_clasificacion(["alta", "media", "baja"]),
    },
    {
        "nombre": "clasificar_sentimiento",
        "system_instruction": (
            "Clasifica el sentimiento expresado en el ticket. "
            "Valores: 'positivo' (satisfacción), "
            "'negativo' (molestia/frustración), "
            "'neutro' (sin tono marcado)."
        ),
        "ejemplo_usuario": MENSAJE,
        "claves_esperadas": ["categoria", "confianza"],
        "categorias_permitidas": ["positivo", "negativo", "neutro"],
        "response_schema": crear_esquema_clasificacion(["positivo", "negativo", "neutro"]),
    },
]