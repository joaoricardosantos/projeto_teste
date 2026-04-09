import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    allowedHosts: ["pratikacobranca.com.br", "www.pratikacobranca.com.br"],
    proxy: {
      "/api": {
        target: "http://web:8000",
        changeOrigin: true,
        ws: true,
        proxyTimeout: 120000,
        timeout: 120000,
      },
    },
  },
});
