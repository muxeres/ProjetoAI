import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Cargar variables de entorno (API Key)
load_dotenv()

# Inicializar el modelo
modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

# Definir la plantilla del prompt
plantilla_extraccion = PromptTemplate.from_template(
    "Lee el siguiente texto y devuelve solo sus 3 puntos clave, uno por línea, sin desarrollarlos: \n\n {texto}"
)

# Construir la cadena LCEL
paso_extraccion = plantilla_extraccion | modelo | StrOutputParser()

# Texto de prueba
texto_prueba = (
    "Los modelos de lenguaje grandes generan texto "
    "prediciendo un token a la vez, basándose en el "
    "texto que ya generaron antes. Cada token puede "
    "ser una palabra completa, parte de una palabra, "
    "o un signo de puntuación. Antes de que el modelo "
    "genere una respuesta, el texto de entrada se "
    "divide en tokens, un proceso llamado tokenización."
)

# Ejecutar la cadena
puntos = paso_extraccion.invoke({"texto": texto_prueba})

# Imprimir el resultado
print(puntos)