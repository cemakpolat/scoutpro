import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Vendor: React core
          if (id.includes('node_modules/react-dom') || id.includes('node_modules/react/')) {
            return 'vendor-react';
          }
          // Vendor: Charts library  
          if (id.includes('node_modules/recharts') || id.includes('node_modules/d3')) {
            return 'vendor-charts';
          }
          // Vendor: Other large libs
          if (id.includes('node_modules/lucide-react')) {
            return 'vendor-icons';
          }
          // Feature: Analytics & ML
          if (id.includes('/components/AnalyticsDashboard') || id.includes('/components/PerformanceTracker') || id.includes('/components/MLLaboratory')) {
            return 'feature-analytics';
          }
          // Feature: Video & Tactical
          if (id.includes('/components/VideoAnalysis') || id.includes('/components/TacticalAnalyzer')) {
            return 'feature-tactical';
          }
          // Feature: Collaboration
          if (id.includes('/components/CollaborationHub') || id.includes('/components/CalendarScheduling')) {
            return 'feature-collab';
          }
        },
      },
    },
    chunkSizeWarningLimit: 500,
    sourcemap: false,
  },
});
