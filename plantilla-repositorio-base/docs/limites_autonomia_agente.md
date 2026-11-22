# Límites de autonomía: Asistente de Logística (`agente_con_memoria.py`)

## Herramientas y nivel de riesgo

- `consultar_estado_envio_detallado`: **bajo — solo lectura** (consulta el diccionario `ESTADOS` por número de seguimiento sin modificar registros ni ejecutar acciones externas).
- `calcular_costo_envio`: **bajo — solo lectura** (realiza un cálculo aritmético local en función de peso y distancia sin alterar estado ni comprometer recursos).
- `generar_reembolso`: **alto — escritura irreversible con impacto económico** (emite una devolución monetaria asociada a un pedido; requiere aprobación humana explícita antes de ejecutarse).

## Herramientas que requieren aprobación humana

- `generar_reembolso`: requiere confirmación explícita de un operador mediante `esperar_aprobacion(mensaje, tiempo_limite_segundos=15)` y registro en `registro_aprobaciones` a través de `registrar_aprobacion()`, porque el reembolso tiene impacto económico directo y no puede deshacerse automáticamente una vez ejecutado. Si el operador responde distinto de `"s"` o vence el límite de 15 segundos, la acción se cancela. Las herramientas `consultar_estado_envio_detallado` y `calcular_costo_envio` no requieren aprobación por ser de solo lectura y bajo riesgo, evitando diluir la atención del operador humano.

## Revisión de trazas

- **Frecuencia:** cada 20 interacciones o de forma semanal en `trazas_agente.jsonl`, y de manera inmediata ante cualquier rechazo o vencimiento de tiempo en `registro_aprobaciones`.
- **Qué se busca:**
  - Llamadas repetidas en bucle a la misma herramienta con idénticos argumentos dentro de un mismo `session_id`.
  - Intentos de invocar `generar_reembolso` sin solicitud explícita del usuario o con montos/números de pedido inventados que no provienen de la conversación.
  - Secuencias de `acciones` anormalmente largas para preguntas simples de consulta o cálculo.
  - Inconsistencias entre la `observacion` devuelta por la herramienta y la `respuesta_final` entregada al cliente (por ejemplo, confirmar un reembolso cuando la observación indica que fue rechazado o cancelado por timeout).

## Qué hacer ante un comportamiento inesperado

1. **Contener la ejecución:** retirar temporalmente `generar_reembolso` de la lista `herramientas` en `src/agente_con_memoria.py` para impedir nuevas ejecuciones de alto riesgo mientras se diagnostica el incidente.
2. **Inspeccionar la traza completa:** localizar el `session_id` y `timestamp` afectados en `trazas_agente.jsonl` para revisar la `entrada` del usuario, el historial de sesión y los `argumentos` y `observacion` de cada paso en `acciones`.
3. **Ajustar reglas y validaciones:** refinar el *docstring* y el esquema `BaseModel` de la herramienta involucrada (por ejemplo, validar límites de monto o formato de pedido), o endurecer las instrucciones del `prompt_agente` para evitar invocaciones indebidas.
4. **Probar y reactivar de forma controlada:** reproducir el caso problemático en entorno local verificando que `esperar_aprobacion()` y `registrar_traza()` actúen según lo esperado antes de volver a habilitar la herramienta.
