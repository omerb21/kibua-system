import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175, // ← הפורט שאתה רוצה
    proxy: {
      '/api': 'http://localhost:5001', // ← הפרוקסי ל־Flask
    },
  },
});
