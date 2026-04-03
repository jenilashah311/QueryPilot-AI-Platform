import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const api = process.env.VITE_API_URL || "http://localhost:28181";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    proxy: {
      "/auth": api,
      "/me": api,
      "/datasets": api,
      "/query": api,
      "/health": api,
      "/billing": api,
      "/oauth": api,
    },
  },
});
