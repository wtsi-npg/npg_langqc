import { fileURLToPath, URL } from 'node:url';
import process from 'node:process';
import { defineConfig } from 'vite';
import Vue from '@vitejs/plugin-vue';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [Vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  define: {
    "APP_VERSION": JSON.stringify(process.env.npm_package_version),
  }
})
