from cliente import GeminiClient
from banco_prompts import BANCO_DE_PROMPTS
from error import (
    GeminiAuthenticationError,
    GeminiRateLimitError,
    GeminiInvalidRequestError,
    GeminiValidationError,
    GeminiNetworkError,
    GeminiBaseException,
)

if __name__ == "__main__":
    try:
        cliente = GeminiClient(model="gemini-1.5-flash")
        
        for item in BANCO_DE_PROMPTS:
            raw_res, metricas = cliente.generar(
                prompt=item["ejemplo_usuario"],
                system_instruction=item.get("system_instruction"),
                response_schema=item.get("response_schema")
            )
            
            texto = cliente.extraer_texto(raw_res)
            datos = cliente.parsear_y_validar_json(
                texto=texto,
                claves_esperadas=item.get("claves_esperadas"),
                categorias_permitidas=item.get("categorias_permitidas")
            )
            
            print(f"Prompt: {item['nombre']}")
            print(f"Resultado: {datos}")
            print(f"Latencia: {metricas.latencia_ms:.2f} ms")
            print(f"Tokens Entrada: {metricas.input_tokens} | Tokens Salida: {metricas.output_tokens}")
            print(f"Costo: ${metricas.costo_usd:.8f} USD")
            print("-" * 40)

    except GeminiAuthenticationError as e:
        print("Error de autenticacion:", e)

    except GeminiRateLimitError as e:
        print("Limite de peticiones excedido:", e)

    except GeminiInvalidRequestError as e:
        print("Peticion invalida:", e)

    except GeminiValidationError as e:
        print("Error de validacion JSON:", e)

    except GeminiNetworkError as e:
        print("Error de red:", e)

    except GeminiBaseException as e:
        print("Error en API de Gemini:", e)

    except Exception as e:
        print("Error inesperado:", e)