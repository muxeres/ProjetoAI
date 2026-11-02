import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser



load_dotenv()

#api_key = os.getenv("API_KEY_AI")
#modelo =ChatGoogleGenerativeAI(model="gemini-3.6-flash", api_key=api_key)
modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
#respuesta = modelo.invoke("¿Qué es un token?")
#print(respuesta.content)

#f-strings
plantilla = PromptTemplate. from_template(
"Explica el concepto de {tema} en un parrafo, para alguien que recien comienza en {area}." )                                                                                         

# prompt = plantilla. invoke({"tema": "tokenizacion", "area": "procesamiento de texto"})

# print(prompt.text)

cadena_simple = plantilla | modelo
respuesta = cadena_simple.invoke({"tema": "embedding", "area": "búsqueda semántica"})
print(respuesta.content)