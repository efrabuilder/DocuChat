# 📄 DocuChat (Next.js) — versión para Vercel

Misma idea que la versión Python (chatbot que responde sobre tus documentos
usando la API de Claude + contexto inyectado en el prompt), reescrita en
**Next.js** para poder desplegarla en **Vercel**.

## 🧠 Cómo funciona

1. Los archivos `.txt`/`.md` de `documents/` se dividen en fragmentos al arrancar
   la función serverless.
2. Cada pregunta se compara contra esos fragmentos con similitud TF-IDF
   (implementada a mano en `lib/rag.ts`, sin dependencias de ML).
3. Los fragmentos más relevantes se insertan en el **system prompt** que se
   envía a la API de Claude (`app/api/chat/route.ts`).
4. La respuesta se muestra en un chat simple hecho con React (`app/page.tsx`).

## 🚀 Desplegar en Vercel

1. Subí esta carpeta a un repo de GitHub (puede ser su propio repo, o un
   subdirectorio del repo de la versión Python — en ese caso, configurá el
   **Root Directory** de Vercel apuntando a esta carpeta).
2. En [vercel.com](https://vercel.com) → **Add New Project** → importá el repo.
3. Vercel detecta Next.js automáticamente. Antes de desplegar, agregá las
   variables de entorno en **Settings → Environment Variables**:
   - `ANTHROPIC_API_KEY`
   - `CLAUDE_MODEL` (opcional, default `claude-sonnet-4-6`)
4. Deploy. Listo — te da una URL pública tipo `https://docuchat.vercel.app`.

## 💻 Correrlo en local

```bash
npm install
cp .env.example .env.local   # completá tu ANTHROPIC_API_KEY
npm run dev
```

Abrí http://localhost:3000

## 📁 Documentos propios

Reemplazá o agregá archivos `.txt`/`.md` en `documents/`. Cada vez que hagas
un nuevo deploy en Vercel, se vuelven a indexar automáticamente.

> Nota: por ahora solo soporta `.txt` y `.md` (no PDF), para no depender de
> librerías binarias en el entorno serverless.

## 📁 Estructura

```
docuchat-web/
├── app/
│   ├── page.tsx           # Interfaz de chat (cliente)
│   ├── layout.tsx
│   └── api/chat/route.ts  # Endpoint que arma el prompt y llama a Claude
├── lib/rag.ts              # Chunking + recuperación TF-IDF en TypeScript
├── documents/              # Tus documentos de contexto
├── package.json
├── next.config.js
└── .env.example
```
