import json
import time
from pathlib import Path
from src.cliente import consultar_modelo
from src.precision import calcular_metricas

ruta_resultados = Path("resultados_metricas.json")

with ruta_resultados.open("r", encoding="utf-8-sig") as f:
    resultados = json.load(f)

consultas_existentes = {item["consulta"] for item in resultados}

pares_objetivo = [
    ("¿Qué es Python?", "Python es un lenguaje de programación interpretado."),
    ("¿En qué año fue la primera publicación de Python?", "La primera publicación de Python fue en 1991."),
    ("¿Qué es una lista en Python?", "Una lista en Python es una colección ordenada y mutable de elementos."),
    ("¿Qué diferencia hay entre una lista y una tupla?", "La lista es mutable y la tupla es inmutable."),
    ("¿Para qué sirve la palabra clave def?", "La palabra clave def se usa para definir funciones en Python."),
    ("¿Qué es un diccionario en Python?", "Un diccionario en Python almacena pares de clave y valor."),
    ("¿Qué hace el método append() en una lista?", "El método append agrega un elemento al final de la lista."),
    ("¿Qué es pip en Python?", "pip es el gestor de paquetes estándar de Python."),
    ("¿Qué es un entorno virtual venv?", "Un entorno virtual aísla las dependencias de un proyecto Python."),
    ("¿Qué devuelve la función len()?", "La función len devuelve la cantidad de elementos de un objeto."),
    ("¿Qué es una excepción en Python?", "Una excepción es un evento que interrumpe el flujo normal durante la ejecución."),
    ("¿Para qué sirve try y except?", "try y except permiten capturar y manejar excepciones en tiempo de ejecución."),
    ("¿Qué es JSON?", "JSON es un formato ligero de intercambio de datos basado en texto."),
    ("¿Qué hace json.loads()?", "json.loads convierte una cadena JSON en un objeto de Python."),
    ("¿Qué es una API REST?", "Una API REST es una interfaz web que usa peticiones HTTP para intercambiar recursos."),
    ("¿Qué código HTTP indica éxito en una petición?", "El código HTTP 200 indica que la petición se procesó con éxito."),
    ("¿Qué significa el error HTTP 429?", "El error HTTP 429 indica que se superó el límite de peticiones permitidas."),
    ("¿Qué es un token en modelos de lenguaje?", "Un token es una unidad básica de texto procesada por el modelo."),
    ("¿Qué mide la métrica F1?", "La métrica F1 es la media armónica entre precisión y cobertura."),
    ("¿Para qué sirve pytest?", "pytest es un framework para escribir y ejecutar pruebas automatizadas en Python."),
]

siguiente_id = max((item.get("id", 0) for item in resultados), default=0) + 1

for consulta, referencia in pares_objetivo:
    if consulta in consultas_existentes:
        print(f"Ya guardada: {consulta}")
        continue

    try:
        respuesta = consultar_modelo(consulta)
        metricas = calcular_metricas(referencia, respuesta)
        resultados.append({
            "id": siguiente_id,
            "consulta": consulta,
            "referencia": referencia,
            "respuesta": respuesta,
            "precision": metricas["precision"],
            "cobertura": metricas["cobertura"],
            "f1": metricas["f1"],
        })
        siguiente_id += 1

        with ruta_resultados.open("w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)

        print(f"Guardada ({len(resultados)}/20): {consulta} -> F1={metricas['f1']:.3f}")
        time.sleep(15)  # Pausa para no exceder el límite por minuto de Gemini

    except RuntimeError as e:
        print(f"\nSe detuvo temporalmente ({len(resultados)}/20 guardadas): {e}")
        print("Espera 1 minuto y vuelve a ejecutar `python pipeline_generarmetricas.py` para continuar.")
        break

print(f"\nTotal en {ruta_resultados}: {len(resultados)}")