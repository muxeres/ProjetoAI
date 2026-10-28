import json
import time
import pytest
from unittest.mock import MagicMock, patch

from cliente import (
    GeminiClient,
    GeminiClientError,
    GeminiAPIError,
    GeminiValidationError,
)
from metricas import EvaluadorMetricas, MetricasEjecucion


# ==============================================================================
# FIXTURES Y CONFIGURACIÓN INICIAL
# ==============================================================================

@pytest.fixture
def env_api_key(monkeypatch):
    """Setea una API key de prueba en el entorno."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key_12345")


@pytest.fixture
def cliente(env_api_key):
    """Instancia base del cliente Gemini para pruebas."""
    return GeminiClient(model="gemini-1.5-flash", timeout=10, max_retries=3)


@pytest.fixture
def respuesta_api_exitosa():
    """Estructura de respuesta HTTP 200 OK enviada por Gemini."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '{"categoria": "acceso", "confianza": 0.95}'}
                    ]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 35,
            "candidatesTokenCount": 10,
            "thoughtsTokenCount": 0,
        },
    }


# ==============================================================================
# PRUEBAS DE INICIALIZACIÓN
# ==============================================================================

def test_init_sin_api_key(monkeypatch):
    """Verifica que se lance ValueError si no hay API Key disponible."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API Key no configurada"):
        GeminiClient()


def test_headers_configurados_correctamente(cliente):
    """Verifica que los encabezados de sesión incluyan la API Key de forma segura."""
    assert cliente.session.headers["x-goog-api-key"] == "test_api_key_12345"
    assert cliente.session.headers["Content-Type"] == "application/json"


# ==============================================================================
# PRUEBAS DE EXTRACTION Y VALIDACIÓN JSON
# ==============================================================================

def test_extraer_texto_exitoso(respuesta_api_exitosa):
    texto = GeminiClient.extraer_texto(respuesta_api_exitosa)
    assert texto == '{"categoria": "acceso", "confianza": 0.95}'


def test_extraer_texto_estructura_invalida():
    respuesta_malformada = {"candidates": []}
    with pytest.raises(GeminiValidationError, match="Respuesta incompleta"):
        GeminiClient.extraer_texto(respuesta_malformada)


def test_parsear_y_validar_json_exito():
    texto_json = '{"categoria": "acceso", "confianza": 0.98}'
    resultado = GeminiClient.parsear_y_validar_json(
        texto=texto_json,
        claves_esperadas=["categoria", "confianza"],
        categorias_permitidas=["acceso", "facturacion", "otro"],
    )
    assert resultado["categoria"] == "acceso"
    assert resultado["confianza"] == 0.98


def test_parsear_y_validar_json_categoria_no_permitida():
    texto_json = '{"categoria": "invalida", "confianza": 0.5}'
    with pytest.raises(GeminiValidationError, match="fuera del enum permitido"):
        GeminiClient.parsear_y_validar_json(
            texto=texto_json,
            claves_esperadas=["categoria", "confianza"],
            categorias_permitidas=["acceso", "facturacion"],
        )


def test_parsear_y_validar_json_confianza_fuera_de_rango():
    texto_json = '{"categoria": "acceso", "confianza": 1.5}'
    with pytest.raises(GeminiValidationError, match="debe ser un número flotante entre 0 y 1"):
        GeminiClient.parsear_y_validar_json(
            texto=texto_json,
            claves_esperadas=["categoria", "confianza"],
        )


def test_parsear_y_validar_json_claves_faltantes():
    texto_json = '{"categoria": "acceso"}'
    with pytest.raises(GeminiValidationError, match="no coinciden con las esperadas"):
        GeminiClient.parsear_y_validar_json(
            texto=texto_json,
            claves_esperadas=["categoria", "confianza"],
        )


# ==============================================================================
# PRUEBAS HTTP Y REINTENTOS (MOCKING)
# ==============================================================================

@patch("requests.Session.post")
def test_generar_peticion_exitosa(mock_post, cliente, respuesta_api_exitosa):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = respuesta_api_exitosa
    mock_post.return_value = mock_response

    raw_res, metricas = cliente.generar(
        prompt="Hola",
        system_instruction="Sé breve",
        response_schema={"type": "OBJECT"},
    )

    assert mock_post.call_count == 1
    assert isinstance(metricas, MetricasEjecucion)
    assert metricas.input_tokens == 35
    assert metricas.output_tokens == 10


@patch("time.sleep", return_value=None)  # Evita demoras reales en el test
@patch("requests.Session.post")
def test_generar_reintentos_exitosos_tras_429(mock_post, mock_sleep, cliente, respuesta_api_exitosa):
    """Simula un error 429 inicial seguido de una respuesta 200 OK exitosa."""
    res_429 = MagicMock()
    res_429.ok = False
    res_429.status_code = 429

    res_200 = MagicMock()
    res_200.ok = True
    res_200.json.return_value = respuesta_api_exitosa

    mock_post.side_effect = [res_429, res_200]

    raw_res, metricas = cliente.generar("Prompt de prueba")

    assert mock_post.call_count == 2
    assert mock_sleep.call_count == 1


@patch("time.sleep", return_value=None)
@patch("requests.Session.post")
def test_generar_fallo_por_exceso_de_reintentos_500(mock_post, mock_sleep, cliente):
    """Verifica que lance GeminiAPIError tras agotar el número máximo de reintentos."""
    res_500 = MagicMock()
    res_500.ok = False
    res_500.status_code = 500

    mock_post.return_value = res_500

    with pytest.raises(GeminiAPIError) as exc_info:
        cliente.generar("Prompt de prueba")

    assert exc_info.value.status_code == 500
    assert mock_post.call_count == 3


@patch("requests.Session.post")
def test_generar_error_400_sin_reintento(mock_post, cliente):
    """Comprueba que los errores 4xx no reintentables fallen de inmediato."""
    res_400 = MagicMock()
    res_400.ok = False
    res_400.status_code = 400
    res_400.text = "Bad Request - Invalid Schema"

    mock_post.return_value = res_400

    with pytest.raises(GeminiAPIError) as exc_info:
        cliente.generar("Prompt de prueba")

    assert exc_info.value.status_code == 400
    assert mock_post.call_count == 1  # No debe hacer reintentos


# ==============================================================================
# PRUEBAS DEL MÓDULO DE MÉTRICAS
# ==============================================================================

def test_calculo_metricas_y_costos(respuesta_api_exitosa):
    inicio = time.perf_counter() - 0.150  # Simula 150 ms de tiempo transcurrido
    
    metricas = EvaluadorMetricas.procesar_respuesta(
        modelo="gemini-1.5-flash",
        respuesta_api=respuesta_api_exitosa,
        tiempo_inicio=inicio
    )

    assert metricas.latencia_ms >= 100.0
    assert metricas.input_tokens == 35
    assert metricas.output_tokens == 10
    assert metricas.costo_usd > 0