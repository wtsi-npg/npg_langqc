import { defineConfig } from "vite";
import Vue from '@vitejs/plugin-vue';


export default defineConfig({
    plugins: [Vue()],
    test: {
        environment: 'jsdom',
        setupFiles: ['test-setup.js'],
    }
})
