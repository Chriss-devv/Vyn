#!/bin/bash

set -e

echo "🪟 VYN v1.2 - Cross-compile for Windows"
echo "========================================"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required for cross-compilation"
    echo ""
    echo "Install Docker first:"
    echo "  sudo pacman -S docker"
    echo "  sudo systemctl start docker"
    echo ""
    echo "Or build natively on Windows using build_windows.bat"
    exit 1
fi

VERSION="1.2.0"

echo "📦 Creating Windows build using Docker..."
echo "⏳ This may take 5-10 minutes on first run..."

# Use batonogov/pyinstaller-windows which is maintained and works
docker run --rm -v "$(pwd)":/src \
    batonogov/pyinstaller-windows:latest \
    "cd /src && \
    pip install --upgrade pip && \
    pip install rich psutil paramiko duckduckgo-search beautifulsoup4 requests httpx && \
    pyinstaller --onefile \
        --name vyn-windows-x64-v${VERSION} \
        --add-data 'setup_wizard.py;.' \
        --add-data 'i18n.py;.' \
        --add-data 'core;core' \
        --add-data 'modules;modules' \
        --add-data 'ui;ui' \
        --hidden-import=rich \
        --hidden-import=psutil \
        --hidden-import=paramiko \
        --hidden-import=httpx \
        --hidden-import=requests \
        vyn.py"

# Move the output
mkdir -p dist/windows
if [ -f "dist/vyn-windows-x64-v${VERSION}.exe" ]; then
    mv "dist/vyn-windows-x64-v${VERSION}.exe" "dist/windows/"
    echo ""
    echo "✅ Windows build complete!"
    echo "📍 Binary: dist/windows/vyn-windows-x64-v${VERSION}.exe"
else
    echo ""
    echo "⚠️  Build may have completed. Check dist/ folder."
fi

echo ""
echo "📝 Note: Windows users need to install Ollama separately:"
echo "   https://ollama.com/download/windows"


