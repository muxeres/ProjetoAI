from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.enrutamiento import (
    construir_paso_clasificacion,
    construir_cadena_con_enrutamiento,
    construir_cadena_queja_segura,
    procesar_mensaje_seguro,
)


def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Queja \n")

    paso = construir_paso_clasificacion(modelo_falso)
    resultado = paso.invoke({"mensaje": "algo salió mal"})

    assert resultado == "queja"


def test_enrutamiento_va_a_cadena_queja():
    clasificacion_falsa = RunnableLambda(lambda x: "queja")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        rama_queja=RunnableLambda(lambda x: "ruta_queja"),
        rama_sugerencia=RunnableLambda(lambda x: "ruta_sugerencia"),
        rama_pregunta=RunnableLambda(lambda x: "ruta_pregunta"),
    )

    assert cadena.invoke({"mensaje": "mi cuenta falló"}) == "ruta_queja"


def test_enrutamiento_va_a_cadena_sugerencia():
    clasificacion_falsa = RunnableLambda(lambda x: "sugerencia")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        rama_queja=RunnableLambda(lambda x: "ruta_queja"),
        rama_sugerencia=RunnableLambda(lambda x: "ruta_sugerencia"),
        rama_pregunta=RunnableLambda(lambda x: "ruta_pregunta"),
    )

    assert cadena.invoke({"mensaje": "agreguen modo oscuro"}) == "ruta_sugerencia"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    clasificacion_falsa = RunnableLambda(lambda x: "desconocida")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        rama_queja=RunnableLambda(lambda x: "ruta_queja"),
        rama_sugerencia=RunnableLambda(lambda x: "ruta_sugerencia"),
        rama_pregunta=RunnableLambda(lambda x: "ruta_pregunta"),
    )

    assert cadena.invoke({"mensaje": "hola"}) == "ruta_pregunta"


def test_cadena_queja_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(x):
        raise ConnectionError("simulado")

    cadena_queja_falsa = RunnableLambda(fallar_a_proposito)
    cadena_queja_segura = construir_cadena_queja_segura(cadena_queja_falsa)

    resultado = cadena_queja_segura.invoke({"mensaje": "esto no funciona"})

    assert "equipo" in resultado.lower()


def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")

    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
    )

    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert "no pudimos procesar" in resultado.lower()