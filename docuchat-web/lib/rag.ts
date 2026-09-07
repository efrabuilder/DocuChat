import fs from "fs";
import path from "path";

export interface Chunk {
  text: string;
  source: string;
}

const DOCS_DIR = path.join(process.cwd(), "documents");
const CHUNK_SIZE = 800;
const OVERLAP = 100;

function loadDocuments(): { text: string; source: string }[] {
  if (!fs.existsSync(DOCS_DIR)) return [];
  const files = fs.readdirSync(DOCS_DIR).filter((f) => /\.(txt|md)$/i.test(f));
  return files.map((file) => ({
    source: file,
    text: fs.readFileSync(path.join(DOCS_DIR, file), "utf-8"),
  }));
}

function splitIntoChunks(docs: { text: string; source: string }[]): Chunk[] {
  const chunks: Chunk[] = [];
  for (const doc of docs) {
    let start = 0;
    while (start < doc.text.length) {
      const end = start + CHUNK_SIZE;
      const fragment = doc.text.slice(start, end).trim();
      if (fragment) chunks.push({ text: fragment, source: doc.source });
      start += CHUNK_SIZE - OVERLAP;
    }
  }
  return chunks;
}

function tokenize(text: string): string[] {
  return (
    text
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .match(/[a-z0-9]+/g) ?? []
  );
}

function termFreq(tokens: string[]): Map<string, number> {
  const map = new Map<string, number>();
  for (const t of tokens) map.set(t, (map.get(t) ?? 0) + 1);
  return map;
}

function cosineSim(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (const [term, freq] of a) {
    normA += freq * freq;
    if (b.has(term)) dot += freq * (b.get(term) as number);
  }
  for (const freq of b.values()) normB += freq * freq;
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

let cachedChunks: Chunk[] | null = null;

function getChunks(): Chunk[] {
  if (!cachedChunks) {
    cachedChunks = splitIntoChunks(loadDocuments());
  }
  return cachedChunks;
}

export function retrieveTopK(query: string, k = 4): Chunk[] {
  const chunks = getChunks();
  if (chunks.length === 0) return [];
  const queryVec = termFreq(tokenize(query));
  const scored = chunks.map((c) => ({
    chunk: c,
    score: cosineSim(queryVec, termFreq(tokenize(c.text))),
  }));
  return scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((s) => s.chunk);
}

export function buildContext(chunks: Chunk[]): string {
  return chunks
    .map((c) => `[Fuente: ${c.source}]\n${c.text}`)
    .join("\n\n---\n\n");
}
