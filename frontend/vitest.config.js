import { fileURLToPath, URL } from 'node:url';

import { defineConfig } from "vite";
import Vue from '@vitejs/plugin-vue';


export default defineConfig({
    plugins: [Vue()],
    test: {
        environment: 'jsdom',
        setupFiles: ['test-setup.js'],
    },
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    }
})
