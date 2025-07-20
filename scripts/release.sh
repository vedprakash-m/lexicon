#!/bin/bash
# Release script for Lexicon Desktop App
# Usage: ./scripts/release.sh 1.0.0

set -e

if [ $# -eq 0 ]; then
    echo "❌ Error: Version number required"
    echo "Usage: ./scripts/release.sh <version>"
    echo "Example: ./scripts/release.sh 1.0.0"
    exit 1
fi

VERSION=$1
TAG="v${VERSION}"

echo "🚀 Preparing Lexicon release ${TAG}"

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (currently on: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update package.json version
echo "📝 Updating package.json version to ${VERSION}"
npm version $VERSION --no-git-tag-version

# Update Tauri version
echo "📝 Updating Tauri version to ${VERSION}"
if command -v jq > /dev/null; then
    jq ".package.version = \"$VERSION\"" src-tauri/tauri.conf.json > tmp.json && mv tmp.json src-tauri/tauri.conf.json
else
    echo "⚠️  jq not found. Please manually update version in src-tauri/tauri.conf.json"
fi

# Commit version changes
echo "💾 Committing version bump"
git add package.json src-tauri/tauri.conf.json
git commit -m "chore: bump version to ${VERSION}"

# Create and push tag
echo "🏷️  Creating and pushing tag ${TAG}"
git tag $TAG
git push origin main
git push origin $TAG

echo "✅ Release ${TAG} initiated!"
echo ""
echo "🔄 CI/CD will now:"
echo "   • Run comprehensive tests (your 288/301 test suite)"
echo "   • Build macOS apps (Apple Silicon + Intel)"
echo "   • Build Windows app (.msi installer)"
echo "   • Create GitHub release with download links"
echo ""
echo "📦 Release will be available at:"
echo "   https://github.com/vedprakash-m/lexicon/releases/tag/${TAG}"
echo ""
echo "⏱️  Build typically takes 10-15 minutes to complete."
