"""
DocuChat — App de escritorio
=============================
Versión nativa (Tkinter, sin dependencias extra) del mismo chatbot:
responde preguntas usando tus documentos como contexto.

Reutiliza rag_utils.py, así que la lógica de recuperación es idéntica
a la de la versión web (app.py). Corré esta con:

    python desktop_app.py
"""

import os
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk

from dotenv import load_dotenv, set_key
import anthropic

from rag_utils import load_documents, split_into_chunks, Retriever, build_context

load_dotenv()

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
DOCS_FOLDER = os.getenv("DOCS_FOLDER", "sample_docs")
DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
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


class DocuChatDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📄 DocuChat — Escritorio")
        self.geometry("720x600")
        self.minsize(480, 400)

        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = DEFAULT_MODEL
        self.retriever = None
        self.n_docs = 0
        self.response_queue = queue.Queue()

        self._build_menu()
        self._build_widgets()
        self._reindex()
        self.after(100, self._poll_queue)

        if not self.api_key:
            self.after(300, self._ask_api_key)

    # ---------- UI ----------
    def _build_menu(self):
        menubar = tk.Menu(self)
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Configurar API key...", command=self._ask_api_key)
        config_menu.add_command(label="Reindexar documentos", command=self._reindex)
        menubar.add_cascade(label="Configuración", menu=config_menu)
        self.config(menu=menubar)

    def _build_widgets(self):
        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=8, pady=(8, 0))
        self.status_label = tk.Label(status_frame, text="", anchor="w", fg="#555")
        self.status_label.pack(fill=tk.X)

        self.chat_area = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, state="disabled", font=("Segoe UI", 10)
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.chat_area.tag_config("user", foreground="#1a73e8", font=("Segoe UI", 10, "bold"))
        self.chat_area.tag_config("assistant", foreground="#188038", font=("Segoe UI", 10, "bold"))
        self.chat_area.tag_config("sources", foreground="#888", font=("Segoe UI", 8, "italic"))

        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.entry = tk.Entry(input_frame, font=("Segoe UI", 10))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self.entry.bind("<Return>", lambda e: self._send())

        self.send_btn = ttk.Button(input_frame, text="Enviar", command=self._send)
        self.send_btn.pack(side=tk.LEFT, padx=(6, 0))

    # ---------- Lógica ----------
    def _reindex(self):
        docs = load_documents(DOCS_FOLDER)
        self.n_docs = len(docs)
        if docs:
            chunks = split_into_chunks(docs)
            self.retriever = Retriever(chunks)
        else:
            self.retriever = None
        self.status_label.config(
            text=f"Carpeta: {DOCS_FOLDER}  |  Documentos: {self.n_docs}  |  Modelo: {self.model}"
        )

    def _ask_api_key(self):
        key = simpledialog.askstring(
            "API key de Anthropic",
            "Pegá tu ANTHROPIC_API_KEY:",
            show="*",
            initialvalue=self.api_key,
        )
        if key:
            self.api_key = key.strip()
            try:
                if not os.path.exists(ENV_PATH):
                    open(ENV_PATH, "a").close()
                set_key(ENV_PATH, "ANTHROPIC_API_KEY", self.api_key)
            except Exception:
                pass  # si falla el guardado, igual queda en memoria para esta sesión

    def _append(self, text, tag=None):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, text, tag)
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def _send(self):
        question = self.entry.get().strip()
        if not question:
            return
        if not self.api_key:
            messagebox.showwarning("Falta API key", "Configurá tu ANTHROPIC_API_KEY primero.")
            return

        self.entry.delete(0, tk.END)
        self._append("Vos: ", "user")
        self._append(question + "\n")
        self.send_btn.config(state="disabled")
        self._append("Claude está escribiendo...\n")

        threading.Thread(target=self._call_api, args=(question,), daemon=True).start()

    def _call_api(self, question: str):
        try:
            relevant = self.retriever.top_k(question, k=TOP_K) if self.retriever else []
            context = build_context(relevant) if relevant else "Sin contexto disponible."
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

            client = anthropic.Anthropic(api_key=self.api_key)
            reply = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": question}],
            )
            answer = "".join(block.text for block in reply.content if block.type == "text")
            sources = ", ".join(sorted({c.source for c in relevant})) if relevant else "ninguna"
            self.response_queue.put(("ok", answer, sources))
        except Exception as e:
            self.response_queue.put(("error", str(e), ""))

    def _poll_queue(self):
        try:
            status, payload, sources = self.response_queue.get_nowait()
            self._remove_last_line("Claude está escribiendo...\n")
            if status == "ok":
                self._append("Claude: ", "assistant")
                self._append(payload + "\n")
                self._append(f"(Fuentes: {sources})\n\n", "sources")
            else:
                self._append(f"⚠️ Error: {payload}\n\n", "sources")
            self.send_btn.config(state="normal")
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _remove_last_line(self, marker: str):
        self.chat_area.config(state="normal")
        content = self.chat_area.get("1.0", tk.END)
        idx = content.rfind(marker)
        if idx != -1:
            start = f"1.0+{idx}c"
            end = f"1.0+{idx + len(marker)}c"
            self.chat_area.delete(start, end)
        self.chat_area.config(state="disabled")


if __name__ == "__main__":
    app = DocuChatDesktop()
    app.mainloop()
