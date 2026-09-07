"""
DocuChat — Chatbot con tu propia data
=====================================
Chat que responde preguntas basándose únicamente en los documentos
que vos le proporciones (carpeta ./sample_docs por defecto).

Stack: Streamlit + API de Claude (Anthropic) + recuperación TF-IDF
       + prompt engineering básico (contexto inyectado en el system prompt).
"""

import os
import streamlit as st
from dotenv import load_dotenv
import anthropic

from rag_utils import load_documents, split_into_chunks, Retriever, build_context

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
DOCS_FOLDER = os.getenv("DOCS_FOLDER", "sample_docs")
TOP_K = 4

SYSTEM_PROMPT_TEMPLATE = """Sos un asistente que responde preguntas ÚNICAMENTE \
usando la información contenida en el CONTEXTO que se te provee a continuación, \
extraído de los documentos del usuario.

Reglas:
- Si la respuesta no está en el contexto, decí explícitamente que no encontraste \
esa información en los documentos, no inventes datos.
- Citá la fuente (el nombre de archivo) cuando sea posible.
- Sé claro, breve y directo.

CONTEXTO:
{context}
"""

st.set_page_config(page_title="DocuChat", page_icon="📄")
st.title("📄 DocuChat")
st.caption("Chatbot que responde preguntas sobre tus propios documentos")


@st.cache_resource(show_spinner="Indexando documentos...")
def get_retriever(folder: str):
    docs = load_documents(folder)
    if not docs:
        return None, 0
    chunks = split_into_chunks(docs)
    return Retriever(chunks), len(docs)


retriever, n_docs = get_retriever(DOCS_FOLDER)

with st.sidebar:
    st.header("⚙️ Configuración")
    st.write(f"**Carpeta de documentos:** `{DOCS_FOLDER}`")
    st.write(f"**Documentos cargados:** {n_docs}")
    st.write(f"**Modelo:** `{MODEL}`")
    api_key = st.text_input(
        "ANTHROPIC_API_KEY",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        type="password",
        help="También podés definirla en un archivo .env",
    )
    if st.button("🔄 Reindexar documentos"):
        get_retriever.clear()
        st.rerun()

if retriever is None:
    st.warning(
        f"No se encontraron documentos en `{DOCS_FOLDER}/`. "
        "Agregá archivos .txt, .md o .pdf y reindexá."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Preguntá algo sobre tus documentos...")

if question:
    if not api_key:
        st.error("Falta la ANTHROPIC_API_KEY (barra lateral o archivo .env).")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    relevant_chunks = retriever.top_k(question, k=TOP_K) if retriever else []
    context = build_context(relevant_chunks) if relevant_chunks else "Sin contexto disponible."
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    client = anthropic.Anthropic(api_key=api_key)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)

        if relevant_chunks:
            with st.expander("📎 Fragmentos usados como contexto"):
                for c in relevant_chunks:
                    st.markdown(f"**{c.source}**")
                    st.text(c.text[:400] + ("..." if len(c.text) > 400 else ""))

    st.session_state.messages.append({"role": "assistant", "content": full_response})
