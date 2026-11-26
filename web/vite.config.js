import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// ===========
// Vite
// ===========

export default defineConfig({
  plugins: [react()],
  // O build funciona em qualquer pasta (ex.: GitHub Pages)
  base: "./",
  server: {
    port: 5173,
    // Permite importar os .py que ficam na raiz do projeto
    fs: { allow: [".."] },
  },
});
