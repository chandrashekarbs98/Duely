/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In Docker the backend is reachable at http://backend:8000; locally at localhost.
const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Bind mounts on Windows/macOS don't deliver file events reliably, so poll instead.
    watch: process.env.VITE_USE_POLLING === "true" ? { usePolling: true } : undefined,
    proxy: {
      "/api": { target: proxyTarget, changeOrigin: true },
    },
  },
  test: {
    environment: "node",
  },
});
