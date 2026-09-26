import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api and /admin to the Django backend so the frontend
// can use same-origin requests with session cookies (no CORS in dev).
const target = process.env.VITE_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target, changeOrigin: true },
      "/admin": { target, changeOrigin: true },
      "/static": { target, changeOrigin: true },
    },
  },
});
