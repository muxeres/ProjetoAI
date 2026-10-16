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
            "completada": True  # En Python va con Mayúscula
        },
        {
            "titulo": "Consumo de APIs",
            "completada": False  # En Python va con Mayúscula
        }
    ]
}

# 1. El nombre de la estudiante
nombre_estudiante = estudiante["nombre"]
print("Nombre:", nombre_estudiante)

# 2. La calificación del curso
calificacion = estudiante["curso"]["calificacion"]
print("Calificación:", calificacion)

# 3. El título de la segunda tarea (índice 1 de la lista)
titulo_segunda_tarea = estudiante["tareas"][1]["titulo"]
print("Título de la 2da tarea:", titulo_segunda_tarea)

# 4. Si la primera tarea está completada (índice 0 de la lista)
primera_completada = estudiante["tareas"][0]["completada"]
print("¿Primera tarea completada?:", primera_completada)