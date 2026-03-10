import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    server: {
        port: 3000,
        host: '0.0.0.0',
        proxy: {
            '/api': {
                target: 'http://web:8000',
                changeOrigin: true,
                secure: false
            }
        }
    }
})