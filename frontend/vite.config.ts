import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev-server proxy so `npm run dev` talks to a locally running backend
// the same way the production nginx container proxies /api and /ws.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});
