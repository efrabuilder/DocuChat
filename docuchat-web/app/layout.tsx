import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "DocuChat",
  description: "Chatbot que responde preguntas sobre tus propios documentos",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
