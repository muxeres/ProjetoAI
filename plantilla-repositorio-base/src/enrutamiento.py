import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="error.log",
    filemode="a",
    encoding="utf-8",
    force=True,
)
logger = logging.getLogger(__name__)

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte en una sola palabra: "
    "pregunta, queja o sugerencia. Responde solo con esa palabra. \n\n {mensaje}"
)


def construir_paso_clasificacion(llm=modelo):
    return (
        plantilla_clasificacion
        | llm
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )


paso_clasificacion = construir_paso_clasificacion(modelo)

cadena_pregunta = (
    PromptTemplate.from_template("Responde esta pregunta técnica con precisión: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_queja = (
    PromptTemplate.from_template(
        "Responde esta queja con empatía, reconociendo el problema antes de ofrecer una solución: \n\n {mensaje}"
    )
    | modelo
    | StrOutputParser()
)

cadena_sugerencia = (
    PromptTemplate.from_template(
        "Agradece esta sugerencia y explica cómo se evaluará dentro del producto: \n\n {mensaje}"
    )
    | modelo
    | StrOutputParser()
)


def fallback_con_log(x):
    error = x.get("error") if isinstance(x, dict) else None
    logger.warning("Cadena principal falló. Activando respuesta genérica. Error: %s", error)
    return "Gracias por tu mensaje. Un miembro de nuestro equipo te va a responder pronto."


respuesta_generica = RunnableLambda(fallback_con_log)


def construir_cadena_queja_segura(rama_queja=cadena_queja):
    return rama_queja.with_fallbacks([respuesta_generica], exception_key="error")


cadena_queja_segura = construir_cadena_queja_segura(cadena_queja)


def construir_cadena_con_enrutamiento(
    paso_clasificacion=paso_clasificacion,
    rama_queja=cadena_queja_segura,
    rama_sugerencia=cadena_sugerencia,
    rama_pregunta=cadena_pregunta,
):
    bifurcacion = RunnableBranch(
        (lambda x: x["clasificacion"] == "queja", rama_queja),
        (lambda x: x["clasificacion"] == "sugerencia", rama_sugerencia),
        rama_pregunta,
    )
    return RunnablePassthrough.assign(clasificacion=paso_clasificacion) | bifurcacion


cadena_con_enrutamiento = construir_cadena_con_enrutamiento()
cadena_robusta = cadena_con_enrutamiento.with_fallbacks(
    [respuesta_generica], exception_key="error"
)


def procesar_mensaje_seguro(cadena, mensaje):
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception as error:
        logger.error("Error procesando mensaje: %s", error)
        return "No pudimos procesar tu mensaje en este momento. Intenta de nuevo más tarde"


if __name__ == "__main__":
    mensaje = "Llevo varios días sin poder entrar a mi cuenta."
    print(procesar_mensaje_seguro(cadena_robusta, mensaje))