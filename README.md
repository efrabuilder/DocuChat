# 📄 DocuChat

Chatbot que responde preguntas usando **tus propios documentos** (.txt, .md, .pdf) como contexto.

Proyecto de práctica para demostrar:
- Integración con la **API de Claude (Anthropic)**
- **Prompt engineering básico**: el contexto relevante se inyecta en el system prompt
- Recuperación simple de información (TF-IDF) — un mini "RAG" sin necesidad de base de datos vectorial

## 🧠 Cómo funciona

1. Los documentos de `sample_docs/` se dividen en fragmentos (chunks).
2. Cuando hacés una pregunta, se buscan los fragmentos más parecidos con similitud TF-IDF.
3. Esos fragmentos se insertan en el **system prompt** junto con instrucciones claras
   (responder solo con esa info, citar la fuente, no inventar).
4. El prompt completo se envía a la API de Claude y la respuesta se muestra en el chat.

## 🚀 Uso rápido

```bash
git clone https://github.com/tu-usuario/docuchat.git
cd docuchat
python -m venv venv
source venv/bin/activate  # en Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# editá .env y agregá tu ANTHROPIC_API_KEY

streamlit run app.py
```

Abrí el link que te muestra Streamlit (por defecto http://localhost:8501),
agregá tus propios archivos en `sample_docs/` (o cambiá `DOCS_FOLDER` en `.env`)
y empezá a preguntar.

## 🖥️ App de escritorio (Tkinter)

Además de la versión web, hay una versión de **escritorio nativa** que usa la misma
lógica de recuperación (`rag_utils.py`) y no agrega dependencias nuevas (Tkinter
viene incluido con Python).

```bash
python desktop_app.py
```

- Si no hay `ANTHROPIC_API_KEY` configurada, te la pide en una ventana emergente
  y la guarda en `.env` para la próxima vez (menú **Configuración → Configurar API key**).
- Desde el mismo menú podés **reindexar** los documentos si agregaste archivos nuevos.
- En Linux puede que necesites instalar Tkinter con tu gestor de paquetes, por ejemplo:
  `sudo apt install python3-tk`.

### Empaquetarla como ejecutable (opcional)

Si querés un `.exe` (Windows) o `.app` (macOS) para distribuirla sin pedir instalar Python:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "sample_docs:sample_docs" desktop_app.py
```

El ejecutable queda en `dist/`. Recordá que igual necesita la `ANTHROPIC_API_KEY`
en un `.env` junto al ejecutable (o pedirla al abrir la app).

## 📁 Estructura

```
docuchat/
├── app.py            # Interfaz de chat (Streamlit, versión web)
├── desktop_app.py     # Interfaz de chat (Tkinter, versión de escritorio)
├── rag_utils.py       # Carga de documentos, chunking y recuperación TF-IDF
├── sample_docs/       # Documentos de ejemplo (reemplazalos por los tuyos)
├── requirements.txt
├── .env.example
└── README.md
```

## 🔑 Variables de entorno

| Variable            | Descripción                                   | Default            |
|---------------------|------------------------------------------------|---------------------|
| `ANTHROPIC_API_KEY` | Tu API key de Anthropic                        | (requerida)          |
| `CLAUDE_MODEL`      | Modelo de Claude a usar                        | `claude-sonnet-4-6`  |
| `DOCS_FOLDER`       | Carpeta con tus documentos                     | `sample_docs`        |

## 🛠️ Posibles mejoras

- Cambiar TF-IDF por embeddings semánticos (ej. `voyageai` o `sentence-transformers`)
- Guardar el índice en una base vectorial (Chroma, FAISS, Pinecone) para escalar
- Soportar `.docx` y `.csv`
- Historial de conversación multi-turno con memoria de contexto

## 📄 Licencia

MIT
