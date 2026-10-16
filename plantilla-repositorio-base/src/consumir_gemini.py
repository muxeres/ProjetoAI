import os
import requests
from dotenv import load_dotenv

load_dotenv()

def armar_peticion(pregunta):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("No se encontró la variable de entorno API_KEY")
        
    # Cambiado a un modelo compatible con la API (puedes ajustarlo según tu preferencia, ej. gemini-1.5-flash)
    modelo = "gemini-3.6-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {"contents": [{"parts": [{"text": pregunta}]}]}
    return url, body

def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body)
        # Opcional pero recomendado: lanza una excepción si la API devuelve un código de error HTTP (4xx o 5xx)
        respuesta.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos segundos.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Error en la petición HTTP: {e.response.text}")
        
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

def extraer_texto(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"La respuesta no trae el texto generado en el lugar esperado. Datos recibidos: {datos}")

def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, body)
    return extraer_texto(datos)

# Ejemplo de uso:
if __name__ == "__main__":
    try:
        respuesta_ia = obtener_dato_de_prueba("¡Hola! ¿Cómo estás?")
        print(respuesta_ia)
    except Exception as e:
        print(f"Ocurrió un error: {e}")