import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
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
          // Vendor: Export/report generation
          if (id.includes('node_modules/jspdf') || id.includes('node_modules/jspdf-autotable')) {
            return 'vendor-pdf';
          }
          if (
            id.includes('node_modules/html2canvas')
            || id.includes('node_modules/stackblur-canvas')
            || id.includes('node_modules/css-line-break')
            || id.includes('node_modules/text-segmentation')
          ) {
            return 'vendor-capture';
          }
          // Vendor: Other large libs
          if (id.includes('node_modules/lucide-react')) {
            return 'vendor-icons';
          }
          // Feature: Keep heavy top-level pages in isolated async chunks.
          if (id.includes('/components/AnalyticsDashboard')) {
            return 'feature-analytics-dashboard';
          }
          if (id.includes('/components/MLLaboratory')) {
            return 'feature-ml-lab';
          }
          if (id.includes('/components/PerformanceTracker')) {
            return 'feature-performance';
          }
          if (id.includes('/components/ModelCenter')) {
            return 'feature-model-center';
          }
          if (id.includes('/components/TransferHub')) {
            return 'feature-transfer';
          }
          if (id.includes('/components/ScoutingDashboard')) {
            return 'feature-scouting';
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
