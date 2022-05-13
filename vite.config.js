import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/static/',
  build: {
    lib: {
        entry: 'src/main.js',
        formats: ['es'],
        fileName: (format) => 'main.js',
    },
    manifest: true,
    outDir: 'var/build',
  },
  plugins: [
    svelte(),
  ]
})
