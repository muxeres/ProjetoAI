import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class GeminiClientError(Exception):
    """Excepción base para errores del cliente Gemini."""
    pass

class GeminiAPIError(GeminiClientError):
    """Errores reportados directamente por la API de Google."""
    def __init__(self, message, status_code, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

class GeminiValidationError(GeminiClientError):
    """Errores en la validación o estructura del JSON retornado."""
    pass


class GeminiClient:
    """Cliente HTTP optimizado para interactuar con la API REST de Gemini."""

    BASE_URL = "[https://generativelanguage.googleapis.com/v1beta/models](https://generativelanguage.googleapis.com/v1beta/models)"

    # Precios de referencia por millón de tokens (por defecto: gemini-2.5/3.6 flash estimaciones)
    PRICING = {
        "prompt_token_price": 0.075 / 1_000_000,     # $0.075 por 1M tokens
        "candidate_token_price": 0.30 / 1_000_000,   # $0.30 por 1M tokens
    }

    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash", timeout: int = 30):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en las variables de entorno.")

        self.model = model
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key  # Envío seguro mediante Header en lugar de Query Param
        })

    def _armar_payload(self, prompt: str, system_instruction: str = None, response_schema: dict = None) -> dict:
        if not prompt or not prompt.strip():
            raise ValueError("El prompt/pregunta no puede estar vacío.")

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        generation_config = {}
        if response_schema:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = response_schema

        if generation_config:
            payload["generationConfig"] = generation_config

        return payload

    def generar_contenido(self, prompt: str, system_instruction: str = None, response_schema: dict = None) -> dict:
        """Ejecuta una petición POST a la API de Gemini."""
        url = f"{self.BASE_URL}/{self.model}:generateContent"
        payload = self._armar_payload(prompt, system_instruction, response_schema)

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise GeminiClientError(f"El servicio no respondió dentro del límite de {self.timeout}s.") from None
        except requests.exceptions.ConnectionError:
            raise GeminiClientError("Error de conexión con la API de Gemini.") from None
        except requests.exceptions.RequestException as e:
            raise GeminiClientError(f"Error HTTP durante la petición: {str(e)}") from None

        if not response.ok:
            try:
                error_body = response.json().get("error", {})
                msg = error_body.get("message", f"HTTP Error {response.status_code}")
            except Exception:
                msg = f"HTTP Error {response.status_code}"
            raise GeminiAPIError(msg, response.status_code)

        try:
            return response.json()
        except json.JSONDecodeError:
            raise GeminiClientError("La respuesta no contiene un JSON válido.") from None

    @staticmethod
    def extraer_texto(respuesta_api: dict) -> str:
        """Extrae el contenido de texto generado por el modelo."""
        try:
            return respuesta_api["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise GeminiValidationError("La estructura de la respuesta API no contiene candidates válidos.")

    @classmethod
    def calcular_costo(cls, respuesta_api: dict) -> dict:
        """Calcula el costo estimado de la operación según los tokens consumidos."""
        uso = respuesta_api.get("usageMetadata", {})
        input_tokens = uso.get("promptTokenCount", 0)
        output_tokens = uso.get("candidatesTokenCount", 0)
        thinking_tokens = uso.get("thoughtsTokenCount", 0)

        total_output_tokens = output_tokens + thinking_tokens

        costo_total = (
            (input_tokens * cls.PRICING["prompt_token_price"]) +
            (total_output_tokens * cls.PRICING["candidate_token_price"])
        )

        return {
            "input_tokens": input_tokens,
            "output_tokens": total_output_tokens,
            "costo_usd": costo_total
        }

    def ejecutar_prompt_del_banco(self, item_banco: dict) -> dict:
        """Procesa un elemento directo de BANCO_DE_PROMPTS y valida su contrato."""
        raw_response = self.generar_contenido(
            prompt=item_banco["ejemplo_usuario"],
            system_instruction=item_banco.get("system_instruction"),
            response_schema=item_banco.get("response_schema")
        )

        texto = self.extraer_texto(raw_response)
        datos = self.parsear_y_validar_json(
            texto=texto,
            claves_esperadas=item_banco.get("claves_esperadas"),
            categorias_permitidas=item_banco.get("categorias_permitidas")
        )

        costo_info = self.calcular_costo(raw_response)
        datos["_metadatos"] = costo_info
        return datos

    @staticmethod
    def parsear_y_validar_json(texto: str, claves_esperadas: list = None, categorias_permitidas: list = None) -> dict:
        """Valida rigurosamente la salida estructurada."""
        try:
            datos = json.loads(texto.strip())
        except json.JSONDecodeError:
            raise GeminiValidationError("El texto retornado no es un JSON válido.") from None

        if not isinstance(datos, dict):
            raise GeminiValidationError("El resultado devuelto debe ser un objeto JSON (dict).")

        if claves_esperadas:
            if set(datos.keys()) != set(claves_esperadas):
                raise GeminiValidationError(
                    f"Claves incorrectas. Esperadas: {claves_esperadas}, Obtenidas: {list(datos.keys())}"
                )

        if "categoria" in datos and not isinstance(datos["categoria"], str):
            raise GeminiValidationError("El campo 'categoria' debe ser un string.")

        if categorias_permitidas and datos.get("categoria") not in categorias_permitidas:
            raise GeminiValidationError(
                f"Categoría '{datos.get('categoria')}' no está en la lista permitida: {categorias_permitidas}"
            )

        if "confianza" in datos:
            confianza = datos["confianza"]
            if not isinstance(confianza, (int, float)) or not (0.0 <= confianza <= 1.0):
                raise GeminiValidationError("El campo 'confianza' debe ser un float entre 0.0 y 1.0.")

        return datos