import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";
import type { OutputOptions } from "rollup";

// https://vitejs.dev/config/
export default defineConfig(() => ({
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
      // Let Vite handle dynamic imports automatically for code splitting
      // Manual chunks for vendor libraries only
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'router-vendor': ['react-router-dom'],
          'ui-vendor': ['@headlessui/react', '@radix-ui/react-tooltip', 'lucide-react'],
          'state-vendor': ['zustand', '@tanstack/react-query', 'immer'],
          'utility-vendor': ['date-fns', 'uuid', 'clsx', 'tailwind-merge', 'class-variance-authority'],
        },
      },
    },
    target: 'esnext',
    minify: 'terser' as const,
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'],
        passes: 2,
      },
      mangle: {
        safari10: true,
      },
    },
    chunkSizeWarningLimit: 1000,
    reportCompressedSize: true,
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
