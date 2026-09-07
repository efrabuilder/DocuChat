"""
rag_utils.py
------------
Funciones para cargar documentos propios, dividirlos en fragmentos (chunks)
y recuperar los fragmentos más relevantes para una pregunta usando
similitud TF-IDF (sin necesidad de una base de datos vectorial).

Esto es "RAG" en su forma más simple: Retrieval-Augmented Generation
básico, suficiente para demostrar prompt engineering con contexto.
"""

import os
import glob
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from pypdf import PdfReader
except ImportError:  # la dependencia es opcional si no se usan PDFs
    PdfReader = None


@dataclass
class Chunk:
    text: str
    source: str


def _read_txt_or_md(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf(path: str) -> str:
    if PdfReader is None:
        raise RuntimeError(
            "Falta la librería 'pypdf'. Instalala con: pip install pypdf"
        )
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_documents(folder: str) -> List[Chunk]:
    """Carga todos los .txt, .md y .pdf de una carpeta como texto crudo."""
    docs = []
    patterns = ["*.txt", "*.md", "*.pdf"]
    for pattern in patterns:
        for path in glob.glob(os.path.join(folder, "**", pattern), recursive=True):
            ext = os.path.splitext(path)[1].lower()
            text = _read_pdf(path) if ext == ".pdf" else _read_txt_or_md(path)
            if text.strip():
                docs.append(Chunk(text=text, source=os.path.basename(path)))
    return docs


def split_into_chunks(
    docs: List[Chunk], chunk_size: int = 800, overlap: int = 100
) -> List[Chunk]:
    """Divide cada documento en fragmentos de tamaño fijo con solapamiento,
    para no perder contexto en los bordes de cada corte."""
    chunks = []
    for doc in docs:
        text = doc.text
        start = 0
        while start < len(text):
            end = start + chunk_size
            fragment = text[start:end].strip()
            if fragment:
                chunks.append(Chunk(text=fragment, source=doc.source))
            start += chunk_size - overlap
    return chunks


class Retriever:
    """Indexa los chunks con TF-IDF y devuelve los más parecidos a una consulta."""

    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words=None)
        self.matrix = self.vectorizer.fit_transform([c.text for c in chunks])

    def top_k(self, query: str, k: int = 4) -> List[Chunk]:
        if not self.chunks:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(
            range(len(self.chunks)), key=lambda i: scores[i], reverse=True
        )
        return [self.chunks[i] for i in ranked[:k] if scores[i] > 0]


def build_context(chunks: List[Chunk]) -> str:
    """Arma el bloque de contexto que se inyecta en el prompt del sistema."""
    parts = []
    for c in chunks:
        parts.append(f"[Fuente: {c.source}]\n{c.text}")
    return "\n\n---\n\n".join(parts)
