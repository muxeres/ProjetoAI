import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Asegura que la carpeta actual sea importable al ejecutar pytest
RAIZ_PROYECTO = Path(__file__).resolve().parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

import cliente
from cliente import GeminiClient
from error import (
    GeminiAuthenticationError,
    GeminiInvalidRequestError,
    GeminiNetworkError,
    GeminiRateLimitError,
    GeminiServerError,
    GeminiValidationError,
)
from metricas import EvaluadorMetricas


# ==============================================================================
# AISLAMIENTO ENTRE PRUEBAS (FIXTURE AUTOUSE)
# ==============================================================================

@pytest.fixture(autouse=True)
def reiniciar_estado_sesion(monkeypatch):
    """Configura API Key de prueba y reinicia acumuladores antes de cada test."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key_12345")
    if hasattr(cliente, "costo_total_sesion"):
        cliente.costo_total_sesion = 0
    yield


@pytest.fixture
def instancia_cliente():
    return GeminiClient(model="gemini-1.5-flash", timeout=10, max_retries=3)


@pytest.fixture
def respuesta_exitosa():
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": '{"categoria": "acceso", "confianza": 0.95}'}]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 500,
            "candidatesTokenCount": 500,
            "thoughtsTokenCount": 0,
        },
    }


def _mock_http(status_code: int, payload: dict | None = None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 300
    resp.headers = {}
    resp.text = text
    if payload is not None:
        resp.json.return_value = payload
    else:
        resp.json.side_effect = ValueError("Respuesta sin JSON")
    return resp


# ==============================================================================
# 1. PRUEBAS DE ENVÍO DE PETICIÓN (HTTP / ERRORES / ÉXITO)
# ==============================================================================

def test_enviar_peticion_credencial_invalida(instancia_cliente):
    resp_401 = _mock_http(401, payload={"error": {"message": "API key inválida"}})
    with patch.object(instancia_cliente.session, "post", return_value=resp_401):
        with pytest.raises(GeminiAuthenticationError):
            instancia_cliente.generar("Pregunta de prueba")


def test_enviar_peticion_limite_de_uso(instancia_cliente):
    resp_429 = _mock_http(429, payload={"error": {"message": "Cuota excedida"}})
    with patch("time.sleep", return_value=None), \
         patch.object(instancia_cliente.session, "post", return_value=resp_429) as mock_post:
        with pytest.raises(GeminiRateLimitError):
            instancia_cliente.generar("Pregunta de prueba")
        assert mock_post.call_count == instancia_cliente.max_retries


def test_enviar_peticion_exito(instancia_cliente, respuesta_exitosa):
    resp_200 = _mock_http(200, payload=respuesta_exitosa)
    with patch.object(instancia_cliente.session, "post", return_value=resp_200):
        raw, metricas = instancia_cliente.generar("Pregunta de prueba")
        texto = GeminiClient.extraer_texto(raw)

    assert texto == '{"categoria": "acceso", "confianza": 0.95}'
    assert metricas.input_tokens == 500
    assert metricas.output_tokens == 500


# ==============================================================================
# 2. PRUEBAS DE REINTENTOS (CON MOCK DE TIME.SLEEP)
# ==============================================================================

def test_con_reintento_agota_intentos(instancia_cliente):
    resp_500 = _mock_http(500, payload={"error": {"message": "Error interno"}})
    with patch("time.sleep", return_value=None) as mock_sleep, \
         patch.object(instancia_cliente.session, "post", return_value=resp_500) as mock_post:
        with pytest.raises(GeminiServerError):
            instancia_cliente._ejecutar_post_con_reintentos(
                "https://ejemplo.invalid/v1beta/models/gemini-1.5-flash:generateContent",
                {"contents": [{"parts": [{"text": "test"}]}]},
            )

    assert mock_post.call_count == instancia_cliente.max_retries
    assert mock_sleep.call_count == instancia_cliente.max_retries - 1


def test_con_reintento_no_reintenta_error_400(instancia_cliente):
    resp_400 = _mock_http(400, payload={"error": {"message": "Petición inválida"}})
    with patch("time.sleep", return_value=None) as mock_sleep, \
         patch.object(instancia_cliente.session, "post", return_value=resp_400) as mock_post:
        with pytest.raises(GeminiInvalidRequestError):
            instancia_cliente._ejecutar_post_con_reintentos(
                "https://ejemplo.invalid/v1beta/models/gemini-1.5-flash:generateContent",
                {"contents": [{"parts": [{"text": "test"}]}]},
            )

    assert mock_post.call_count == 1
    assert mock_sleep.call_count == 0


# ==============================================================================
# 3. PRUEBAS DE REGISTRO DE COSTO
# ==============================================================================

def test_registrar_costo_calcula_por_tokens(respuesta_exitosa):
    costo_esperado = EvaluadorMetricas.calcular_costo(
        modelo="gemini-1.5-flash",
        input_tokens=500,
        output_tokens=500,
    )
    metricas = EvaluadorMetricas.procesar_respuesta(
        modelo="gemini-1.5-flash",
        respuesta_api=respuesta_exitosa,
        tiempo_inicio=0.0,
    )

    assert costo_esperado > 0
    assert pytest.approx(metricas.costo_usd) == costo_esperado


# ==============================================================================
# 4. PRUEBAS DE CONSULTAR MODELO / VALIDACIÓN DE RESPUESTA
# ==============================================================================

def test_consultar_modelo_convierte_error_de_red(instancia_cliente):
    import requests

    with patch.object(instancia_cliente.session, "post", side_effect=requests.exceptions.Timeout):
        with pytest.raises(GeminiNetworkError):
            instancia_cliente.generar("Pregunta de prueba")


def test_consultar_modelo_valida_json_con_error_si_es_invalido():
    with pytest.raises(GeminiValidationError):
        GeminiClient.parsear_y_validar_json("esto no es json")