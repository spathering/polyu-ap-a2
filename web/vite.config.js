import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  publicDir: 'public',
  build: {
    outDir: '../site',
    emptyOutDir: true,
    sourcemap: false,
    target: 'es2022',
  },
});
