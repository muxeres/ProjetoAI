import json
import time
from collections import Counter
from google import genai
from google.genai import types

# Paso 1: Dataset propio del asistente de logística (comportamiento consistente -> JSON fijo)
# Tarea: clasificar la solicitud libre del cliente en intencion, nivel de riesgo y herramienta sugerida.
ejemplos_raw: list[tuple[str, dict]] = [
    (
        "Hola, ¿me dices por donde va mi paquete AR12345 y todo su recorrido?",
        {"intencion": "consulta_estado", "riesgo": "bajo", "herramienta_sugerida": "consultar_estado_envio_detallado"},
    ),
    (
        "Quiero verificar si el envio AR12346 ya figura como entregado en el sistema.",
        {"intencion": "consulta_estado", "riesgo": "bajo", "herramienta_sugerida": "consultar_estado_envio_detallado"},
    ),
    (
        "¿Cual es la situacion actual de la guia AR99812? No necesito el historial.",
        {"intencion": "consulta_estado", "riesgo": "bajo", "herramienta_sugerida": "consultar_estado_envio_detallado"},
    ),
    (
        "¿Cuanto me sale despachar una caja de 4 kg a 180 km de distancia?",
        {"intencion": "cotizacion_envio", "riesgo": "bajo", "herramienta_sugerida": "calcular_costo_envio"},
    ),
    (
        "Necesito saber el costo estimado para enviar un paquete liviano de 1.2 kg a 45 km.",
        {"intencion": "cotizacion_envio", "riesgo": "bajo", "herramienta_sugerida": "calcular_costo_envio"},
    ),
    (
        "Si mando dos bultos que suman 12 kg a 500 km, ¿cuanto seria el flete?",
        {"intencion": "cotizacion_envio", "riesgo": "bajo", "herramienta_sugerida": "calcular_costo_envio"},
    ),
    (
        "Mi pedido PED123 llego roto, exijo el reembolso inmediato de los 25000 pesos.",
        {"intencion": "solicitud_reembolso", "riesgo": "alto", "herramienta_sugerida": "generar_reembolso"},
    ),
    (
        "Me cobraron el envio duplicado en la orden PED456, devuelvanme 4800 pesos.",
        {"intencion": "solicitud_reembolso", "riesgo": "alto", "herramienta_sugerida": "generar_reembolso"},
    ),
    (
        "El producto nunca salio del deposito y cancele la compra PED789; solicito reintegro de 15000.",
        {"intencion": "solicitud_reembolso", "riesgo": "alto", "herramienta_sugerida": "generar_reembolso"},
    ),
    (
        "El repartidor vino pero no habia nadie en casa, ¿como reprogramo la entrega de AR12345?",
        {"intencion": "incidencia_entrega", "riesgo": "medio", "herramienta_sugerida": "escalar_soporte_logistico"},
    ),
    (
        "Cargue mal la direccion de destino en mi envio AR12346, necesito corregir la calle antes del reparto.",
        {"intencion": "incidencia_entrega", "riesgo": "medio", "herramienta_sugerida": "escalar_soporte_logistico"},
    ),
    (
        "El paquete figura entregado pero en la porteria del edificio no recibieron nada.",
        {"intencion": "incidencia_entrega", "riesgo": "medio", "herramienta_sugerida": "escalar_soporte_logistico"},
    ),
]

examples: list[types.TuningExample] = [
    types.TuningExample(
        text_input=texto,
        output=json.dumps(salida, ensure_ascii=False),
    )
    for texto, salida in ejemplos_raw
]


# Paso 2: Revisar el balance entre categorías
def chequear_balance(ejemplos: list[tuple[str, dict]], clave: str = "intencion") -> Counter:
    return Counter(salida[clave] for _, salida in ejemplos)


# Paso 3: Validar estructura, duplicados y claves obligatorias antes de entrenar
def validar_dataset(
    examples: list[types.TuningExample],
    claves_esperadas: tuple[str, ...] = ("intencion", "riesgo", "herramienta_sugerida"),
) -> list[str]:
    problemas: list[str] = []
    vistos: set[str] = set()
    for i, ej in enumerate(examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue
        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)
        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
    return problemas


# Paso 4: Seguimiento de estado del trabajo de tuning (para cuando se ejecute en Vertex AI / Gemini API)
def esperar_a_que_termine(
    client: genai.Client, nombre_trabajo: str, intervalo_segundos: int = 30
) -> types.TuningJob:
    estados_finales = {
        types.JobState.JOB_STATE_SUCCEEDED,
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    }
    while True:
        trabajo = client.tunings.get(name=nombre_trabajo)
        print(f"estado actual: {trabajo.state}")
        if trabajo.state in estados_finales:
            return trabajo
        time.sleep(intervalo_segundos)


if __name__ == "__main__":
    print("=== 1. CONSTRUCCION DEL DATASET ===")
    print(f"{len(examples)} ejemplos construidos")
    print("Muestra[0]:", examples[0])

    print("\n=== 2. BALANCE POR CATEGORIA (intencion) ===")
    balance = chequear_balance(ejemplos_raw, "intencion")
    for categoria, cuenta in balance.most_common():
        print(f"  {categoria}: {cuenta}")

    print("\n=== 3. VALIDACION DEL DATASET ===")
    problemas = validar_dataset(examples)
    print(f"{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)

    print("\n=== 4. PRUEBA NEGATIVA DEL VALIDADOR (detectar errores a proposito) ===")
    ejemplos_rotos = examples + [
        types.TuningExample(
            text_input="Consulta sin clave de riesgo en el JSON",
            output=json.dumps({"intencion": "consulta_estado"}, ensure_ascii=False),
        )
    ]
    problemas_rotos = validar_dataset(ejemplos_rotos)
    print(f"Dataset roto -> {len(problemas_rotos)} problema(s) detectado(s):")
    for p in problemas_rotos:
        print(" -", p)
