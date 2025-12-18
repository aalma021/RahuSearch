import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  // DEV
  server: {
    host: true,
    port: 3000,
    allowedHosts: true,

    proxy: {
      "/search": {
        target: "https://cqldq-212-253-200-248.a.free.pinggy.link",
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // 🔥 PREVIEW (PINGGY FIX)
  preview: {
    host: true,
    port: 4173,
    allowedHosts: [
      "localhost",
      "127.0.0.1",
      "jtxsk-212-253-200-248.a.free.pinggy.link",
      ".free.pinggy.link" // 🔥 wildcard (çok önemli)
    ]
  }
});
