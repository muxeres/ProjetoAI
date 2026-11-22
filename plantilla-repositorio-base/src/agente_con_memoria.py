from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from pydantic import BaseModel, Field, ValidationError

#Configuraciones e Inicializaciones
load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

class ArgumentosConsultaEnvio(BaseModel):
    """
    Esquema para documentar y validar argumentos campo por campo ante el LLM.
    """
    numero_seguimiento: str = Field(
        description="Número de seguimiento del envío, por ejemplo 'AR129012'."
    )
    incluir_historial: bool = Field(
        default=False,
        description="Si es True, incluye en historial completo de los estados, no solo el actual."
    )

#Base de Datos
ESTADOS = {
    "AR129012": {
        "actual": "En tránsito, entrega estimada en 2 días",
        "historial": ["Recibido en Depósito", 
                      "En tránsito", 
                      "Entregado"
                      ]
    }
}
#Herramientas
#@tool("nuevo_nombre")
@tool(args_schema=ArgumentosConsultaEnvio) #LangChain  transforma  esta  clase en un esquema JSON que  se  envia  al  LLM. El modelo  lo lee textualmente
def consultar_estado_envio_detallado(numero_seguimiento: str, incluir_historial: bool = False) :

    """
    Consulta el estado de un envio, con la opcion de incluir el historial completo.
    """
    envio = ESTADOS.get(numero_seguimiento) #AR12346
    #envio={
        #"actual": "Entregado",
        # "historial": [
        # "Recibido en depósito",
        # "En. transito"
    #
    #   ]
    # }
    if envio is None:
        return f"No. se.encontro un envio con el numero {numero_seguimiento}."

    #Si no se solicita el historial, retornamos .solo.el.estado.actual
    if not incluir_historial:
        return envio["actual"]

    #Si sí se solicita el historial, formatear y retornar la info
    historial =",".join(envio["historial"]) #"Recibido en depósito,En tránsito"
    return f"Estado actual: {envio['actual']}. Historial completo: {historial}."

#Listado de herramientas
herramientas = [
    consultar_estado_envio_detallado
]  # lista de herramientas
    #Construcción del agente
prompt_agente = ChatPromptTemplate.from_messages ( [

"system", "Eres un asistente de logistica que responde preguntas usando las herramientas disponibles."
),
#Todo: historial de chats
("human", "{entrada}"),
MessagesPlaceholder("agent_scratchpad")

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

ejecutor_agente = AgentExecutor(
agent=agente,
tools=herramientas,
verbose=True

)

if_name _== " main ":
resultado = ejecutor_agente.invoke(
{"entrada": "¿Cual es el estado del envio AR12345, con su historial?"}

... )

print("Rel')