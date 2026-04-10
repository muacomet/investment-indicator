import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/investment-indicator/',
  publicDir: '../data',
  build: {
    outDir: '../docs',
  },
});
