import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,

    // 🔥 BUNU AÇMADAN allowedHosts ÇALIŞMAZ
    host: true, // veya "0.0.0.0"

    // 🔥 Pinggy gibi dynamic hostlar için
    allowedHosts: "all",

    // 🔥 Backend proxy (dokunma)
    proxy: {
      "/search": {
        target: "https://eayvp-212-253-200-248.a.free.pinggy.link",
        changeOrigin: true,
        secure: false
      }
    }
  }
});
