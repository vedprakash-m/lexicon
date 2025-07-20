#!/bin/bash

# Fix Lexicon macOS "damaged app" error
# This script removes the quarantine attribute that causes the security warning

echo "🔧 Fixing Lexicon macOS Security Issue..."
echo ""

# Check if Lexicon.app exists in Applications
if [ ! -d "/Applications/Lexicon.app" ]; then
    echo "❌ Lexicon.app not found in /Applications/"
    echo "Please make sure you have installed Lexicon.app to your Applications folder first."
    echo ""
    echo "Download from: https://github.com/vedprakash-m/lexicon/releases"
    exit 1
fi

echo "📱 Found Lexicon.app in Applications folder"
echo ""

# Remove quarantine attribute
echo "🛡️  Removing quarantine attribute..."
sudo xattr -rd com.apple.quarantine /Applications/Lexicon.app

if [ $? -eq 0 ]; then
    echo "✅ Successfully removed quarantine attribute!"
    echo ""
    echo "🎉 Lexicon should now launch normally!"
    echo "You can find it in your Applications folder or Launchpad."
    echo ""
    echo "If you still have issues, please visit:"
    echo "https://github.com/vedprakash-m/lexicon#%EF%B8%8F-troubleshooting"
else
    echo "❌ Failed to remove quarantine attribute."
    echo "Please try running the command manually:"
    echo "sudo xattr -rd com.apple.quarantine /Applications/Lexicon.app"
fi

echo ""
echo "Done! 🚀"
