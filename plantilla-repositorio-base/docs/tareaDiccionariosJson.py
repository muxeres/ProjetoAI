def obtener_info_estudiante(datos):
    nombre = datos["nombre"]
    calificacion = datos["curso"]["calificacion"]
    titulo_segunda_tarea = datos["tareas"][1]["titulo"]
    
    # Convertimos True -> "Sí" y False -> "No"
    primera_completada = "Sí" if datos["tareas"][0]["completada"] else "No"
    
    return {
        "nombre": nombre,
        "calificacion": calificacion,
        "titulo_segunda_tarea": titulo_segunda_tarea,
        "primera_completada": primera_completada
    }


# Estructura de datos
estudiante = {
    "nombre": "Ana",
    "edad": 24,
    "curso": {
        "nombre": "Python",
        "calificacion": 92
    },
    "tareas": [
        {
            "titulo": "Variables",
            "completada": True
        },
        {
            "titulo": "Consumo de APIs",
            "completada": False
        }
    ]
}

# Prueba
resultado = obtener_info_estudiante(estudiante)
print(resultado)
# Llamada a la función
resultado = obtener_info_estudiante(estudiante)
print(resultado)