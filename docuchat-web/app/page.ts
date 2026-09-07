"use client";

import { useEffect, useRef, useState } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Error desconocido");

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `⚠️ Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1>📄 DocuChat</h1>
      <p style={{ color: "#666" }}>Chatbot que responde sobre tus propios documentos</p>

      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          height: 420,
          overflowY: "auto",
          marginBottom: 12,
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: "#999" }}>Preguntá algo sobre los documentos cargados en /documents.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 12 }}>
            <strong style={{ color: m.role === "user" ? "#1a73e8" : "#188038" }}>
              {m.role === "user" ? "Vos" : "Claude"}:
            </strong>{" "}
            <span style={{ whiteSpace: "pre-wrap" }}>{m.content}</span>
            {m.sources && m.sources.length > 0 && (
              <div style={{ fontSize: 12, color: "#888", fontStyle: "italic" }}>
                Fuentes: {m.sources.join(", ")}
              </div>
            )}
          </div>
        ))}
        {loading && <div style={{ color: "#888" }}>Claude está escribiendo...</div>}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Preguntá algo sobre tus documentos..."
          style={{ flex: 1, padding: 10, borderRadius: 6, border: "1px solid #ccc" }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{ padding: "10px 20px", borderRadius: 6, border: "none", background: "#1a73e8", color: "white" }}
        >
          Enviar
        </button>
      </div>
    </main>
  );
}
