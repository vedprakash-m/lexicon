#!/bin/bash
# Simple script to build macOS app locally

set -e

echo "🧪 Running tests..."
npm run test:run

echo "🏗️  Building for Apple Silicon..."
npm run tauri build -- --target aarch64-apple-darwin

echo "🏗️  Building for Intel..."
npm run tauri build -- --target x86_64-apple-darwin

echo "✅ Build complete!"
echo "📦 Apple Silicon: src-tauri/target/aarch64-apple-darwin/release/bundle/dmg/"
echo "📦 Intel: src-tauri/target/x86_64-apple-darwin/release/bundle/dmg/"
