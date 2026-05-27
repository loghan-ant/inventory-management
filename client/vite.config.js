import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000
  },
  // Use Homebrew esbuild (Santa blocks npm-downloaded binary).
  // esbuild 0.28 + vite 5 needs esnext target to avoid destructuring-transform errors.
  esbuild: {
    target: 'esnext'
  },
  optimizeDeps: {
    esbuildOptions: {
      target: 'esnext'
    }
  }
})
