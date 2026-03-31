import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 6001,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/tn_assembly.geojson': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/constituencies.json': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('leaflet') || id.includes('react-leaflet')) return 'map'
          if (id.includes('recharts')) return 'charts'
          if (id.includes('react') || id.includes('framer-motion')) return 'vendor'
          return 'vendor'
        },
      },
    },
  },
})
