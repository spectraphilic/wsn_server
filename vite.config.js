import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
    let entry = 'src/main.js';
    let config = {
        base: '/static/',
        build: {
            manifest: true,
            outDir: 'var/build',
            rollupOptions: {
            }
        },
        plugins: [
            svelte({}),
        ]
    }

    if (command === 'serve') {
        config.build.rollupOptions = {
            input: {
                main: entry,
            }
        }
    } else { // build
        config.build.lib = {
            entry,
            formats: ['es'],
            fileName: (format) => 'main.js',
        }
    }

    return config;
})
