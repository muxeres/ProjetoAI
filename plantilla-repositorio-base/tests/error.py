import json
import logging
import requests
from typing import Callable, Any

# Configuración básica de logging para trazabilidad de errores
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiErrorHandler")


# ==============================================================================
# 1. JERARQUÍA DE EXCEPCIONES PERSONALIZADAS
# ==============================================================================

class GeminiBaseException(Exception):
    """Excepción base para cualquier fallo dentro de la integración con Gemini."""
    pass


class GeminiNetworkError(GeminiBaseException):
    """Errores relacionados con fallos físicos o timeouts en la conexión HTTP."""
    pass


class GeminiAuthenticationError(GeminiBaseException):
    """Errores HTTP 401/403: API Key ausente, inválida o sin permisos."""
    pass


class GeminiRateLimitError(GeminiBaseException):
    """Error HTTP 429: Se ha superado el límite de peticiones (RPM/TPM/cuota)."""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class GeminiInvalidRequestError(GeminiBaseException):
    """Error HTTP 400: Parámetros inválidos, modelo no existente o payload malformado."""
    pass


class GeminiServerError(GeminiBaseException):
    """Errores HTTP 5xx: Fallos internos del servicio de Google/Gemini."""
    pass


class GeminiValidationError(GeminiBaseException):
    """Errores en la estructura, tipos o enum del JSON devuelto por el modelo."""
    pass


class GeminiEmptyResponseError(GeminiBaseException):
    """Ocurre cuando el modelo devuelve una respuesta sin candidatos o vacía."""
    pass


# ==============================================================================
# 2. MANEJADOR Y PARSEADOR DE ERRORES HTTP
# ==============================================================================

class ManejadorErroresAPI:
    """Procesa respuestas HTTP fallidas y las mapea a excepciones específicas."""

    @staticmethod
    def procesar_respuesta_error(response: requests.Response):
        status_code = response.status_code
        
        # Intenta extraer el mensaje detallado enviado por la API de Google
        try:
            error_json = response.json().get("error", {})
            mensaje_api = error_json.get("message", response.text)
        except Exception:
            mensaje_api = response.text

        if status_code in (401, 403):
            raise GeminiAuthenticationError(
                f"Error de Autenticación ({status_code}): {mensaje_api}"
            )
        
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            segundos = int(retry_after) if retry_after and retry_after.isdigit() else None
            raise GeminiRateLimitError(
                f"Límite de peticiones o cuota excedida (429): {mensaje_api}",
                retry_after=segundos
            )
            
        elif status_code == 400:
            raise GeminiInvalidRequestError(
                f"Petición Inválida (400): {mensaje_api}"
            )
            
        elif status_code >= 500:
            raise GeminiServerError(
                f"Error interno del servidor de Gemini ({status_code}): {mensaje_api}"
            )
            
        else:
            raise GeminiBaseException(
                f"Error HTTP no clasificado ({status_code}): {mensaje_api}"
            )


# ==============================================================================
# 3. DECORADOR REUTILIZABLE PARA MANEJO ROBUSTO DE TRY / EXCEPT
# ==============================================================================

def capturar_errores_gemini(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorador que envuelve cualquier función ejecutor de API/Parsing,
    atrapando excepciones genéricas de requests o JSON y convirtiéndolas 
    en excepciones personalizadas del dominio de Gemini.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
            
        except requests.exceptions.Timeout:
            logger.error("Timeout agotado durante la llamada a Gemini.")
            raise GeminiNetworkError("El tiempo de espera (timeout) con la API de Gemini fue superado.") from None
            
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión de red.")
            raise GeminiNetworkError("No se pudo establecer conexión con los servidores de Google Gemini.") from None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error HTTP no controlado: {str(e)}")
            raise GeminiNetworkError(f"Error en la petición de red: {str(e)}") from None
            
        except json.JSONDecodeError as e:
            logger.error("Error decodificando el contenido JSON.")
            raise GeminiValidationError(f"La respuesta no contenía un JSON válido: {str(e)}") from None
            
        except (GeminiBaseException, ValueError) as e:
            # Re-eleva las excepciones de dominio sin alterarlas
            raise e
            
        except Exception as e:
            logger.critical(f"Error no previsto capturado: {str(e)}")
            raise GeminiBaseException(f"Ocurrió un error inesperado: {str(e)}") from None

    return wrapper