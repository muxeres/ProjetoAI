# Decisión de arquitectura: elección de modelo

## Modelo elegido

**Gemini 2.5 Flash Lite**, para la funcionalidad principal de la miniaplicación.

## Diagrama de arquitectura

El flujo completo va desde la pregunta del usuario hasta la respuesta final, pasando por `armar_peticion`, `enviar_peticion` (con la credencial `API_KEY` leída desde `.env`) y el manejo de errores en `try/except` y `extraer_texto` (que además calcula el costo a partir de `usageMetadata`). El diagrama completo está en `docs/diagrama-arquitectura.png`.

## Comparación de candidatos

| Criterio | Gemini 2.5 Flash Lite | Modelo Alternativo (Ej. Pro / Flash) |
| ----- | ----- | ----- |
| Costo por 1000 tokens de entrada | 0,0001 USD | 0,0005 USD |
| Costo por 1000 tokens de salida | 0,0003 USD | 0,0015 USD |
| Latencia promedio observada | 1,8 segundos | 4,6 segundos |
| Calidad de respuesta para el caso | Buena: cubre lo esencial en las 3 preguntas de prueba | Muy buena: más detalle y matices en las mismas 3 respuestas |
| Fecha de medición | 2026-10-19 | 2026-10-19 |

## Justificación

Para esta miniaplicación, un asistente simple donde "cubrir lo esencial" ya satisface lo que el usuario necesita, el criterio que más pesó fue el costo y la latencia combinados: el modelo alternativo cuesta cinco veces más y tarda más del doble en responder, a cambio de un nivel de detalle que esta aplicación no requiere. El Gemini 2.5 Flash Lite entrega una calidad suficiente para el caso de uso a una fracción del costo y con una respuesta notablemente más rápida, por lo que es la elección más razonable con los datos disponibles.

## Alternativa descartada y por qué

Se descartó el **Modelo Alternativo**. Aunque ofrece respuestas con más detalle, esa diferencia de calidad no justifica pagar cinco veces más por cada interacción ni que el usuario espere más del doble de tiempo por una respuesta, dado que esta miniaplicación no tiene un requisito real de ese nivel de detalle adicional.