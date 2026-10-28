import time
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MetricasEjecucion:
    latencia_ms: float
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    costo_usd: float

    def a_dict(self) -> Dict[str, Any]:
        return {
            "latencia_ms": round(self.latencia_ms, 2),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "thinking_tokens": self.thinking_tokens,
            "costo_usd": round(self.costo_usd, 8),
        }


class EvaluadorMetricas:
    # Tarifas estimadas por 1M de tokens (Ajustar según lista oficial de Google)
    TARIFAS_POR_MILLON = {
        "gemini-1.5-flash": {"entrada": 0.075, "salida": 0.30},
        "gemini-1.5-pro": {"entrada": 1.25, "salida": 5.00},
        "gemini-2.5-flash": {"entrada": 0.075, "salida": 0.30},
        "gemini-3.6-flash": {"entrada": 0.075, "salida": 0.30},
    }

    @classmethod
    def calcular_costo(cls, modelo: str, input_tokens: int, output_tokens: int) -> float:
        tarifas = cls.TARIFAS_POR_MILLON.get(modelo, cls.TARIFAS_POR_MILLON["gemini-1.5-flash"])
        costo_in = (input_tokens / 1_000_000) * tarifas["entrada"]
        costo_out = (output_tokens / 1_000_000) * tarifas["salida"]
        return costo_in + costo_out

    @classmethod
    def procesar_respuesta(cls, modelo: str, respuesta_api: dict, tiempo_inicio: float) -> MetricasEjecucion:
        latencia_ms = (time.perf_counter() - tiempo_inicio) * 1000

        uso = respuesta_api.get("usageMetadata", {})
        input_tokens = uso.get("promptTokenCount", 0)
        output_tokens = uso.get("candidatesTokenCount", 0)
        thinking_tokens = uso.get("thoughtsTokenCount", 0)

        total_output = output_tokens + thinking_tokens
        costo_total = cls.calcular_costo(modelo, input_tokens, total_output)

        return MetricasEjecucion(
            latencia_ms=latencia_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            costo_usd=costo_total
        )