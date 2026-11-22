def recomendar_estrategia(respuestas):
    puntos = {"RAG": 0, "Fine-tuning completo": 0, "PEFT": 0}

    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2

    maximo = max(puntos.values())
    ganadoras = [tecnica for tecnica, p in puntos.items() if p == maximo]
    return puntos, ganadoras


respuestas_mi_caso = {
    "informacion_cambia_seguido": False,        # Las 4 intenciones y claves JSON son fijas; los datos vivos vienen de tools
    "problema_de_formato_o_tono": True,         # 4 de 20 respuestas (20 %) no respetaron el esquema JSON exacto
    "dataset_grande_y_de_calidad": False,       # Actualmente hay 12 ejemplos validados (< 200 del umbral)
    "presupuesto_limitado_o_iterar_rapido": True, # Cuota gratuita / máximo 2 intentos y ciclo de validación < 1 día
    "necesita_multiples_variantes": False,      # Un único clasificador estructurado para todo el asistente
}

if any(valor is None for valor in respuestas_mi_caso.values()):
    raise SystemExit("Completa las cinco respuestas con True o False antes de continuar.")

puntos, ganadoras = recomendar_estrategia(respuestas_mi_caso)
print(puntos)
print("candidatas:", ganadoras)


def generar_esqueleto_decision(problema, puntos, ganadoras):
    empate = len(ganadoras) > 1
    lineas = []
    lineas.append("# Decision de personalizacion")
    lineas.append("")
    lineas.append("## 1. El problema")
    lineas.append(problema)
    lineas.append("")
    lineas.append("## 2. Resultado del metodo de decision")
    for tecnica, p in sorted(puntos.items(), key=lambda x: -x[1]):
        lineas.append(f"- {tecnica}: {p} puntos")
    if empate:
        lineas.append("")
        lineas.append(f"**Empate entre: {', '.join(ganadoras)}**")
    lineas.append("")
    lineas.append("## 3. Tecnica elegida y por que")
    if empate:
        lineas.append(
            "[COMPLETAR: el puntaje no resolvio el empate solo -- "
            "justifica aqui con criterio propio]"
        )
    else:
        lineas.append(f"[COMPLETAR: por que {ganadoras[0]} responde mejor a este caso]")
    lineas.append("")
    lineas.append("## 4. Que necesitarias para ejecutarla")
    lineas.append(
        "[COMPLETAR: corpus faltante, o cantidad de ejemplos etiquetados que faltan]"
    )
    return "\n".join(lineas)


esqueleto = generar_esqueleto_decision(
    "El clasificador de solicitudes del asistente de logistica no siempre responde con el formato JSON fijo esperado (claves intencion, riesgo y herramienta_sugerida).",
    puntos,
    ganadoras,
)
print(esqueleto)

with open("decision_personalizacion.md", "w", encoding="utf-8") as f:
    f.write(esqueleto)
