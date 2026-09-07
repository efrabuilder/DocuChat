import Anthropic from "@anthropic-ai/sdk";
import { NextRequest, NextResponse } from "next/server";
import { retrieveTopK, buildContext } from "@/lib/rag";

export const runtime = "nodejs";

const MODEL = process.env.CLAUDE_MODEL || "claude-sonnet-4-6";

function systemPrompt(context: string): string {
  return `Sos un asistente que responde preguntas ÚNICAMENTE usando la información contenida en el CONTEXTO que se te provee a continuación, extraído de los documentos del usuario.

Reglas:
- Si la respuesta no está en el contexto, decí explícitamente que no encontraste esa información en los documentos, no inventes datos.
- Citá la fuente (el nombre de archivo) cuando sea posible.
- Sé claro, breve y directo.

CONTEXTO:
${context}`;
}

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();
    if (!message || typeof message !== "string") {
      return NextResponse.json({ error: "Falta el mensaje" }, { status: 400 });
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: "Falta configurar ANTHROPIC_API_KEY en las variables de entorno de Vercel" },
        { status: 500 }
      );
    }

    const chunks = retrieveTopK(message, 4);
    const context = chunks.length ? buildContext(chunks) : "Sin contexto disponible.";
    const sources = Array.from(new Set(chunks.map((c) => c.source)));

    const client = new Anthropic({ apiKey });
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 1024,
      system: systemPrompt(context),
      messages: [{ role: "user", content: message }],
    });

    const answer = response.content
      .filter((b): b is Anthropic.TextBlock => b.type === "text")
      .map((b) => b.text)
      .join("");

    return NextResponse.json({ answer, sources });
  } catch (err: any) {
    console.error(err);
    return NextResponse.json(
      { error: err?.message || "Error interno" },
      { status: 500 }
    );
  }
}
