import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/static/',
  build: {
    manifest: true,
    outDir: 'var/build',
    rollupOptions: {
      input: {
        main: 'src/main.js',
      }
    }
  },
  plugins: [svelte({
    //preserveLocalState: true,
  })]
})
