import { resolve } from 'path'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
    const admin = resolve(__dirname, 'src/admin.js')
    const front = resolve(__dirname, 'src/front.js')

    let config = {
        base: '/static/',
        build: {
            cssCodeSplit: true,
            manifest: 'manifest.json',
            outDir: 'var/build',
            rollupOptions: {
            }
        },
        plugins: [
        ]
    }

    if (command === 'serve') {
        config.build.rollupOptions = {
            input: {admin}
        }
    }
    else { // build
        config.build.lib = {
            entry: {admin},
            formats: ['es'],
            fileName: (format, entryName) => `${entryName}.js`,
        }
        // In lib mode filenames don't include a hash by default, add one here
        config.build.rollupOptions.output = {
            entryFileNames: '[name]-[hash].js',
            assetFileNames: '[name]-[hash][extname]',
        }
    }

    //console.log('CONFIG', config);
    return config;
})
