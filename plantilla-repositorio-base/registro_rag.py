import time
import json
from contextlib import contextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


def formatear_contexto(chunks_recuperados):
    lineas = []
    for i, doc in enumerate(chunks_recuperados, start=1):
        lineas.append(f"[{i}] {doc.page_content}")
    return "\n\n".join(lineas)


@contextmanager
def medir(tiempos, etapa):
    inicio = time.perf_counter()
    yield
    tiempos[etapa] = time.perf_counter() - inicio


def registrar_consulta(pregunta, persist_directory="vectorstore/", k=3):
    """Corre una consulta RAG real, midiendo tiempo por etapa y tokens reales
    de la respuesta del modelo."""
    tiempos = {}

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    chat_model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)

    with medir(tiempos, "embed_y_busqueda"):
        vectorstore = Chroma(
            persist_directory=persist_directory, embedding_function=embeddings
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        chunks = retriever.invoke(pregunta)

    contexto = formatear_contexto(chunks)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    with medir(tiempos, "generacion"):
        respuesta = chat_model.invoke(prompt)

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {etapa: round(s * 1000, 2) for etapa, s in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": dict(respuesta.usage_metadata) if respuesta.usage_metadata else None,
    }
    return registro


def guardar_registro(registro, ruta="registros_latencia_costo.jsonl"):
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    ruta_jsonl = "registros_latencia_costo.jsonl"
    open(ruta_jsonl, "w", encoding="utf-8").close()

    print("=" * 60)
    print("PASO 1: registrando 3 consultas distintas (Como se prueba, chequeo 1)")
    print("=" * 60)
    preguntas = [
        "Que hace el cliente si hay un TimeoutError?",
        "Como se calcula el costo de una llamada?",
        "Como decide el agente que herramienta usar?",
    ]
    registros_paso1 = []
    for q in preguntas:
        reg = registrar_consulta(q, persist_directory="vectorstore/", k=3)
        guardar_registro(reg, ruta_jsonl)
        registros_paso1.append(reg)

    print(json.dumps(registros_paso1, indent=2, ensure_ascii=False))

    print("=" * 60)
    print("PASO 2: misma pregunta con k=3 y k=6 (Como se prueba, chequeo 2)")
    print("=" * 60)
    pregunta_k = "Que hace el cliente si hay un TimeoutError?"
    reg_k3 = registrar_consulta(pregunta_k, persist_directory="vectorstore/", k=3)
    guardar_registro(reg_k3, ruta_jsonl)

    reg_k6 = registrar_consulta(pregunta_k, persist_directory="vectorstore/", k=6)
    guardar_registro(reg_k6, ruta_jsonl)

    print(f"k=3 -> input_tokens: {reg_k3['tokens']['input_tokens']}")
    print(f"k=6 -> input_tokens: {reg_k6['tokens']['input_tokens']}")

    print("=" * 60)
    print("PASO 3: confirmando el archivo de registros")
    print("=" * 60)
    with open(ruta_jsonl, encoding="utf-8") as f:
        total_lineas = sum(1 for _ in f)
    print(f"{ruta_jsonl} tiene {total_lineas} lineas (una por corrida)")
