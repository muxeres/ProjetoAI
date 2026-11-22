import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI  # Modelo
from langchain_core.prompts import PromptTemplate  # Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser  # Parsea la respuesta y la transforma en solo textos
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)  # Bifurcaciones/Branches/Ramificaciones
# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]  # Imprime logs por consola
)
logger = logging.getLogger("SoporteLLM")

# Modificación en la respuesta genérica para registrar cuando ocurre un fallback
def log_y_responder_fallback(x):
    logger.warning("Falló la llamada principal al LLM. Ejecutando respuesta de respaldo (fallback).")
    return "Gracias por tu mensaje. Un miembro de nuestro equipo te va a responder pronto."

respuesta_generica = RunnableLambda(log_y_responder_fallback)

cadena_robusta = cadena_con_enrutamiento.with_fallbacks([respuesta_generica])

def procesar_mensaje_seguro(cadena, mensaje):
    logger.info(f"Iniciando procesamiento de mensaje: '{mensaje}'")
    try:
        resultado = cadena.invoke({"mensaje": mensaje})
        logger.info("Mensaje procesado con éxito.")
        return resultado
    except Exception as error:
        logger.error(f"Error procesando mensaje: {error}", exc_info=True)
        return "No pudimos procesar tu mensaje en este momento. Intenta de nuevo mas tarde"

if __name__ == "__main__":
    mensaje = "Llevo varios dias sin poder entrar a mi cuenta."
    print(procesar_mensaje_seguro(cadena_robusta, mensaje))