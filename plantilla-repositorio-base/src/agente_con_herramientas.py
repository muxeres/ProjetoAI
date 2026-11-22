from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Tool/Herramienta es una función común de Python. Descripción en lenguaje natural será lo que el modelo lea (prompt) para decidir si elige o no esa herramienta
@tool
def buscar_en_documentacion(consulta: str) -> str:
    """
    Busca información relevante de la documentación interna del producto.
    Usar cuando la pregunta es sobre cómo funciona algo del sistema.
    """
    documentacion = {
        "reintentos": "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente",
        "costos": "El costo se calcula a partir de totalTokenCount, según la tarifa vigente."
    }

    for clave, texto in documentacion.items():
        if clave in consulta.lower():
            return texto

    return "No se encontró información sobre esa cosulta en la documentación."
def calcular(expresion: str) -> str:
    """
    Calcula una expresión matemática simple.
    Usar cuando la pregunta es sobre cálculos matemáticos."""
    permitido = set("0123456789+-*/().") 
    if not set(expresion)<= permitido:
        return "Error: La expresión contiene caracteres no permitidos."
    try:
        resultado = eval(expresion)
        return str(resultado)
    except Exception as e:
        return f"Error al calcular la expresión: {e}"
    
herramientas = [
    tool(buscar_en_documentacion, name="buscar_en_documentacion", description="Busca información relevante de la documentación interna del producto. Usar cuando la pregunta es sobre cómo funciona algo del sistema."),
    tool(calcular, name="calcular", description="Calcula una expresión matemática simple. Usar cuando la pregunta es sobre cálculos matemáticos.")
]#lista de herramientas
#Plantilla con system instruction
prompt_agente = ChatPromptTemplate.from_messages(
    [
        ("system", "Eres un asistente que responde preguntas usando las herramientas disponibles cuando las necesitas."),
        ("human", "{entrada}"),
        MessagesPlaceholder(variable_name="intermediate_steps"),
        ("human", "{input}"),
    ]
)
def crear_agente() -> AgentExecutor:
    """
    Crea un agente que puede usar herramientas para responder preguntas.
    """
    herramientas = [
        buscar_en_documentacion,
        tool(calcular, name="calcular", description="Calcula una expresión matemática simple. Usar cuando la pregunta es sobre cálculos matemáticos.")
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Eres un asistente útil y conocedor del producto."),
            MessagesPlaceholder(variable_name="intermediate_steps"),
            ("human", "{input}"),
        ]
    )

    agente = create_tool_calling_agent(
        llm=modelo,
        tools=herramientas,
        prompt=prompt,
        verbose=True
    )

    return AgentExecutor(agent=agente, tools=herramientas, verbose=True)