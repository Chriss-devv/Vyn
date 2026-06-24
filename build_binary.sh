#!/bin/bash

set -e

echo "🚀 Building VYN v1.0 Binary"
echo "============================"

if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

echo "🔨 Building executable..."

pyinstaller --onefile \
    --name vyn-linux-x64 \
    --add-data "setup_wizard.py:." \
    --add-data "core:core" \
    --add-data "modules:modules" \
    --add-data "ui:ui" \
    --hidden-import=ollama \
    --hidden-import=rich \
    --hidden-import=psutil \
    --hidden-import=paramiko \
    --hidden-import=duckduckgo_search \
    --hidden-import=beautifulsoup4 \
    vyn.py

echo "✅ Build complete!"
echo "📍 Binary location: dist/vyn-linux-x64"
echo ""
echo "Test it with:"
echo "  ./dist/vyn-linux-x64"
