#!/bin/bash
# Windows-specific build script for Lexicon Desktop App

set -e

echo "🖥️  Building Lexicon for Windows"

# Check if we're in the right environment
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    echo "⚠️  Warning: This script is designed for Windows environments"
    echo "   Running on: $OSTYPE"
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Run tests
echo "🧪 Running tests..."
npm run test:run

# Build frontend
echo "🏗️  Building frontend..."
npm run build

# Build Windows app
echo "📦 Building Windows desktop app..."
npm run tauri build

echo "✅ Windows build complete!"
echo ""
echo "📦 Build artifacts:"
echo "   • MSI Installer: src-tauri/target/release/bundle/msi/"
echo "   • NSIS Installer: src-tauri/target/release/bundle/nsis/"
echo ""
echo "🚀 Ready for distribution!"
