/** @type {import('next').NextConfig} */
const nextConfig = {
  // Sin esto, Vercel puede "podar" la carpeta documents/ del bundle
  // de la función serverless porque se lee dinámicamente (fs.readdirSync)
  // y no se detecta como import estático.
  outputFileTracingIncludes: {
    "/api/chat": ["./documents/**/*"],
  },
};

module.exports = nextConfig;
