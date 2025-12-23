import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * DEV mod (npm run dev):
 * - Browser -> http://localhost:3000/search
 * - Vite proxy -> http://localhost:8000/search (docker API publish)
 *
 * PROD mod (docker frontend):
 * - Vite yok, nginx var
 * - nginx /search -> http://api:8000/search
 */
export default defineConfig({
  plugins: [react()],

  // DEV server
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    proxy: {
      "/search": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },

  // Preview (istersen local prod-like test)
  preview: {
    host: true,
    port: 4173,
    strictPort: true,
  },
});
