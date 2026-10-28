import os
import json
import time
import requests
from typing import Tuple, List

from metricas import EvaluadorMetricas, MetricasEjecucion
from error import (
    ManejadorErroresAPI,
    capturar_errores_gemini,
    GeminiValidationError,
    GeminiEmptyResponseError,
    GeminiRateLimitError,
    GeminiServerError
)

class GeminiClient:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash", timeout: int = 30, max_retries: int = 3):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key no configurada. Establece GEMINI_API_KEY.")

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        })

    def _ejecutar_post_con_reintentos(self, url: str, payload: dict) -> dict:
        delay = 1.0
        for intento in range(1, self.max_retries + 1):
            try:
                response = self.session.post(url, json=payload, timeout=self.timeout)
                
                if response.ok:
                    return response.json()

                # Manejo y clasificación centralizada del error HTTP
                try:
                    ManejadorErroresAPI.procesar_respuesta_error(response)
                except (GeminiRateLimitError, GeminiServerError) as err:
                    if intento == self.max_retries:
                        raise err
                    time.sleep(delay)
                    delay *= 2  # Backoff exponencial
                    continue

            except requests.exceptions.RequestException:
                if intento == self.max_retries:
                    raise
                time.sleep(delay)
                delay *= 2

    @capturar_errores_gemini
    def generar(self, prompt: str, system_instruction: str = None, response_schema: dict = None) -> Tuple[dict, MetricasEjecucion]:
        url = f"{self.BASE_URL}/{self.model}:generateContent"
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        if response_schema:
            payload["generationConfig"] = {
                "responseMimeType": "application/json",
                "responseSchema": response_schema
            }

        inicio = time.perf_counter()
        raw_response = self._ejecutar_post_con_reintentos(url, payload)
        metricas = EvaluadorMetricas.procesar_respuesta(self.model, raw_response, inicio)

        return raw_response, metricas

    @staticmethod
    def extraer_texto(respuesta_api: dict) -> str:
        try:
            return respuesta_api["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise GeminiEmptyResponseError("La respuesta de la API no contiene la estructura de texto esperada.")

    @staticmethod
    @capturar_errores_gemini
    def parsear_y_validar_json(texto: str, claves_esperadas: List[str] = None, categorias_permitidas: List[str] = None) -> dict:
        datos = json.loads(texto.strip())

        if not isinstance(datos, dict):
            raise GeminiValidationError("El resultado devuelto debe ser un objeto JSON.")

        if claves_esperadas and set(datos.keys()) != set(claves_esperadas):
            raise GeminiValidationError(f"Las claves obtenidas {list(datos.keys())} no coinciden con las esperadas {claves_esperadas}")

        if "categoria" in datos and categorias_permitidas and datos["categoria"] not in categorias_permitidas:
            raise GeminiValidationError(f"Categoría '{datos['categoria']}' fuera del enum permitido: {categorias_permitidas}")

        if "confianza" in datos:
            conf = datos["confianza"]
            if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
                raise GeminiValidationError("El campo 'confianza' debe ser un número flotante entre 0.0 y 1.0.")

        return datos