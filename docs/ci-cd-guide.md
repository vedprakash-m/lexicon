# Lexicon Desktop CI/CD Guide

## 🚀 Automated Release Process

This CI/CD pipeline automatically builds and distributes Lexicon desktop apps for macOS and Windows.

### What Gets Built

#### 📱 macOS Apps
- **Apple Silicon** (.dmg) - M1/M2/M3 Macs
- **Intel** (.dmg) - Older Intel Macs
- **Unsigned** - Users right-click "Open" to bypass Gatekeeper

#### 🖥️ Windows Apps  
- **x64 Installer** (.msi) - Standard Windows installer
- **Unsigned** - Users click "More info" → "Run anyway"

## 🔄 How to Release

### Method 1: Using Release Script (Recommended)
```bash
# Create and push a new release
./scripts/release.sh 1.0.0

# This will:
# 1. Update package.json and Tauri versions
# 2. Commit version bump
# 3. Create and push git tag
# 4. Trigger automated CI/CD build
```

### Method 2: Manual Git Tags
```bash
# Update versions manually, then:
git add .
git commit -m "chore: bump version to 1.0.0"
git tag v1.0.0
git push origin main
git push origin v1.0.0
```

## 🧪 Quality Assurance Pipeline

Every release automatically runs:

### Code Quality Checks
- ✅ **ESLint** - Code style and quality
- ✅ **TypeScript** - Type checking  
- ✅ **Test Suite** - Your 288/301 tests
- ✅ **Coverage** - Test coverage reporting
- ✅ **Build Validation** - Production build success

### Security Audits
- ✅ **npm audit** - Dependency vulnerability scan
- ✅ **depcheck** - Unused dependency detection
- ✅ **Tauri security** - Configuration validation

## 📦 Release Artifacts

### For Users
GitHub Releases page provides:
```
📦 Lexicon v1.0.0

Downloads:
• Lexicon-1.0.0-aarch64.dmg     (macOS Apple Silicon - 15MB)
• Lexicon-1.0.0-x86_64.dmg      (macOS Intel - 16MB)  
• Lexicon_1.0.0_x64_en-US.msi   (Windows Installer - 18MB)

Installation instructions included in release notes
```

### For Developers  
- **Test coverage** reports via CodeCov
- **Component docs** deployed to GitHub Pages
- **Build logs** for debugging

## 🔧 CI/CD Triggers

### Automatic Builds
- ✅ **Version tags** (`v1.0.0`) - Full release build
- ✅ **Main branch** pushes - Development builds  
- ✅ **Pull requests** - Quality checks only

### Manual Controls
- 🚫 **No builds** on feature branches (unless PR)
- 🚫 **No releases** without version tags
- ✅ **Documentation** deploys on main branch

## ⚙️ Development Workflow

### Daily Development
```bash
# Normal development - no builds triggered
git checkout -b feature/new-feature
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Create PR - triggers quality checks only
```

### Releasing
```bash
# When ready to release
git checkout main
git pull origin main
./scripts/release.sh 1.2.3
# Watch GitHub Actions for build progress
```

## 🐛 Troubleshooting

### Build Failures
1. **Check GitHub Actions** tab for detailed logs
2. **Common issues**:
   - Test failures (fix tests first)
   - TypeScript errors (run `npx tsc --noEmit`)
   - Dependency issues (run `npm audit fix`)

### Release Issues
1. **Tag not triggering build**:
   ```bash
   # Check if tag was pushed
   git ls-remote --tags origin
   
   # Re-push if needed
   git push origin v1.0.0
   ```

2. **Version conflicts**:
   ```bash
   # Delete and recreate tag
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   git tag v1.0.0
   git push origin v1.0.0
   ```

## 📊 Monitoring

### Build Status
- **GitHub Actions** tab shows real-time progress
- **Notifications** on build completion (if enabled)
- **CodeCov** reports test coverage trends

### Release Analytics  
- **GitHub Insights** shows download statistics
- **Release notes** track feature additions
- **User feedback** via GitHub Issues

## 🔐 Security Notes

### Code Signing
- **macOS**: Apps are unsigned (no developer account)
- **Windows**: Apps are unsigned (no code signing certificate)
- **Users**: Must manually approve unsigned apps

### Future Enhancements
- Add code signing certificates for seamless installation
- Implement auto-updater for automatic app updates
- Add analytics for usage tracking

## 🎯 Next Steps

This CI/CD setup provides:
- ✅ **Professional distribution** via GitHub Releases
- ✅ **Cross-platform builds** for macOS and Windows
- ✅ **Quality assurance** with comprehensive testing
- ✅ **Zero-maintenance** automated releases

Your Lexicon app is now ready for professional desktop distribution!
