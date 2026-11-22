from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI  # Modelo
from langchain_core.prompts import PromptTemplate  # Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser  # Parsea la respuesta y la transforma en solo textos
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)  # Bifurcaciones/Branches/Ramificaciones

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte en una sola palabra: "
    "pregunta, queja o sugerencia. Responde solo con esa palabra. \n\n {mensaje}"
)

paso_clasificacion = (
    plantilla_clasificacion
    | modelo
    | StrOutputParser()
    | (lambda texto: texto.strip().lower())
)

# mensaje_prueba = "Mi telefono no esta funcionando."

# clasificacion = paso_clasificacion.invoke(
# {"mensaje": mensaje_prueba}
# )
# print(clasificacion)

cadena_pregunta = (
    PromptTemplate.from_template("Responde esta pregunta tecnica con precision: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_queja = (
    PromptTemplate.from_template("Responde esta queja con empatia, reconociendo el problema antes de ofrecer una solucion: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_sugerencia = (
    PromptTemplate.from_template("Responde a esta sugerencia con gratitud y considera su implementacion: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

# Sintaxis RunnableBranch
# caminos = RunnableBranch(
#     (condicion_1, rama_1), #if
#     (condicion_2, rama_2), #elif
#     (condicion_3, rama_3), #elif
#     rama_por_defecto #else
# ) #Cada condicion debe ser una función; suele ser un lambda

# x={"clasificacion": "queja", "mensaje": "Mi telefono no funciona"}
bifurcacion = RunnableBranch(
    (lambda x: x["clasificacion"] == "queja", cadena_queja),  # if x["clasificacion"] == "queja": cadena_queja
    (lambda x: x["clasificacion"] == "sugerencia", cadena_sugerencia),  # elif x["clasificacion"] == "sugerencia": cadena_sugerencia
    cadena_pregunta  # else: cadena_pregunta
)

cadena_con_enrutamiento = (
    RunnablePassthrough.assign(clasificacion=paso_clasificacion)  # {"mensaje": "Deberian de tener mas agentes disponibles.", "clasificacion": resultado de paso_clasificacion}
    | bifurcacion
)

# Fallback: cadena de respaldo. Captura las caidas de mi LLM. (RateLimitError, 401, APIConnectionError, respuestas vacias)
respuesta_generica = RunnableLambda(
    # Todo: log
    lambda x: "Gracias por tu mensaje. Un miembro de nuestro equipo te va a responder pronto."
)

cadena_robusta = cadena_con_enrutamiento.with_fallbacks([respuesta_generica])

def procesar_mensaje_seguro(cadena, mensaje):
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception as error:
        # Todo: log
        print(f"Error al procesar el mensaje: {error}")
        return "No pudimos procesar tu mensaje en este momento. Intenta de nuevo mas tarde"

if __name__ == "__main__":
    mensaje = "Llevo varios dias sin poder entrar a mi cuenta."
    print(procesar_mensaje_seguro(cadena_robusta, mensaje))


