import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // Or the correct import for the v4 plugin

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // Initialize the Tailwind CSS Vite plugin
  ],
})
