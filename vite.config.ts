import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// https://vitejs.dev/config/
export default defineConfig(async () => ({
  plugins: [react()],
  
  // Tauri expects a specific base path for assets
  base: "./",
  
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', '@heroicons/react'],
          // Feature chunks
          'catalog': [
            './src/components/catalog/EnhancedCatalogInterface.tsx',
            './src/components/catalog/IntegratedCatalogInterface.tsx',
          ],
          'processing': [
            './src/components/batch/BatchProcessing.tsx',
            './src/components/chunking/AdvancedChunking.tsx',
          ],
        },
      },
    },
    target: 'esnext',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
      },
    },
  },
  
  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 5173,
    strictPort: true,
    watch: {
      // 3. tell vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
}));
