/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Sin esto, Vercel puede "podar" la carpeta documents/ del bundle
    // de la función serverless porque se lee dinámicamente (fs.readdirSync)
    // y no se detecta como import estático.
    // (En Next.js 14 esta opción va dentro de "experimental"; en Next.js 15+
    // se volvió estable y se mueve al nivel raíz de nextConfig).
    outputFileTracingIncludes: {
      "/api/chat": ["./documents/**/*"],
    },
  },
};

module.exports = nextConfig;
