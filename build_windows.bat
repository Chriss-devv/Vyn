@echo off
echo ====================================
echo VYN v1.2 - Build Windows Executable
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)

echo Installing dependencies...
pip install pyinstaller rich psutil ollama paramiko duckduckgo-search beautifulsoup4 requests

echo.
echo Building VYN executable...
echo.

pyinstaller --onefile ^
    --name vyn-windows-x64-v1.2.0 ^
    --add-data "setup_wizard.py;." ^
    --add-data "i18n.py;." ^
    --add-data "core;core" ^
    --add-data "modules;modules" ^
    --add-data "ui;ui" ^
    --hidden-import=ollama ^
    --hidden-import=rich ^
    --hidden-import=psutil ^
    --hidden-import=paramiko ^
    --hidden-import=duckduckgo_search ^
    --hidden-import=beautifulsoup4 ^
    --hidden-import=requests ^
    --icon=NONE ^
    vyn.py

echo.
echo ====================================
echo Build Complete!
echo ====================================
echo.
echo Binary location: dist\vyn-windows-x64.exe
echo.
echo To run VYN:
echo   1. Install Ollama for Windows: https://ollama.com/download
echo   2. Run: ollama pull llama3.1:8b
echo   3. Double-click vyn-windows-x64.exe
echo.
pause
