# Production Optimization Notes

## Frontend Build Optimization
Add the following to your vite.config.ts:

```typescript
export default defineConfig({
  build: {
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['lodash', 'date-fns']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  define: {
    __DEV__: JSON.stringify(false)
  }
})
```

## Tauri Bundle Optimization
Consider enabling these in tauri.conf.json:

```json
{
  "bundle": {
    "resources": ["resources/*"],
    "externalBin": [],
    "copyright": "",
    "category": "Productivity",
    "shortDescription": "",
    "longDescription": "",
    "deb": {
      "depends": []
    },
    "macOS": {
      "frameworks": [],
      "minimumSystemVersion": "10.13",
      "exceptionDomain": ""
    },
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": ""
    }
  }
}
```
