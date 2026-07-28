import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
// vitest/config, not vite: the `test` block is not part of Vite's own config type.
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 8420 },
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
