import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // Local Django. For ESP32, run: python manage.py runserver 0.0.0.0:8000
        // (ESP32 posts to the PC LAN IP directly; Vite still uses localhost.)
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
