#!/bin/bash

set -e

echo "🚀 VYN v1.0 - Build & Obfuscate"
echo "================================"

VERSION="1.0.0"
BUILD_DIR="build_release"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "📦 Installing dependencies..."
pip install pyinstaller pyarmor -q

echo "🔒 Ofuscando código..."
pyarmor obfuscate --recursive --output "$BUILD_DIR/obfuscated" vyn.py
pyarmor obfuscate --recursive --output "$BUILD_DIR/obfuscated" setup_wizard.py

cd "$BUILD_DIR/obfuscated"

echo "🔨 Compilando binario..."
pyinstaller --onefile \
    --name "vyn-linux-x64-v${VERSION}" \
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
    --hidden-import=requests \
    vyn.py

cd ../..

mv "$BUILD_DIR/obfuscated/dist/vyn-linux-x64-v${VERSION}" "./vyn-linux-x64-v${VERSION}"

echo "✅ Build complete!"
echo "📍 Binary: ./vyn-linux-x64-v${VERSION}"
echo ""
echo "🎉 Ready to upload to GitHub Releases!"
