import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/static/',
//root: '.',
  build: {
    manifest: true,
    outDir: 'project/static/build',
//  target: 'es2015',
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
