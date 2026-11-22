# Decisión de personalización: clasificador de solicitudes del asistente de logística

## 1. El problema
El módulo de clasificación inicial del asistente de logística y envíos recibe mensajes libres de clientes y debe devolver siempre un objeto JSON estricto con tres claves (`intencion`, `riesgo` y `herramienta_sugerida`). En una revisión de 20 respuestas actuales, 4 (20 %) incumplieron el formato esperado al incluir texto explicativo fuera del JSON o alterar nombres de claves, aunque el modelo comprende correctamente la intención del usuario.

## 2. Resultado del método de decisión
- PEFT: 3 puntos
- RAG: 2 puntos
- Fine-tuning completo: 1 punto

Ganadora clara según el método: **PEFT** (3 puntos frente a 2 de RAG y 1 de Fine-tuning completo).

## 3. Técnica elegida y por qué
Elijo **PEFT (adapters)**. El puntaje dio como ganadora clara a PEFT porque el problema es de consistencia de formato (`problema_de_formato_o_tono = True`, +2 puntos) y operamos con presupuesto y tiempo acotados (`presupuesto_limitado_o_iterar_rapido = True`, +1 punto). Entrenar un adapter pequeño (`ADAPTER_SIZE_FOUR`) ajusta el comportamiento de salida sin reentrenar todos los parámetros del modelo ni exigir cientos de ejemplos desde el inicio. Descarto RAG para esta tarea porque al modelo no le falta conocimiento cambiante sobre políticas o guías (eso ya lo resuelven las herramientas de consulta), sino disciplina de formato.

## 4. Qué necesitarías para ejecutarla
Hoy cuento con **12 ejemplos** etiquetados y validados en `dataset_tuning.py` (3 por cada una de las 4 categorías: `consulta_estado`, `cotizacion_envio`, `solicitud_reembolso` e `incidencia_entrega`), revisados al 100 % sin errores de esquema. Para llevar cada categoría de 3 a un mínimo operativo de 25 ejemplos (100 ejemplos en total), me faltan **88 ejemplos** etiquetados: a un ritmo de 5 minutos por ejemplo, esto representa **7,3 horas** de etiquetado y validación, más 1 o 2 corridas de entrenamiento PEFT de 3 a 5 épocas. No necesito indexar un corpus documental adicional porque la técnica elegida no es RAG.
