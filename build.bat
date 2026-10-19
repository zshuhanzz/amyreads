@echo off
REM AmyReads - Build Script for Windows EXE
REM Run this from the AmyReads project directory
REM Requirements: Python 3.10+ with pip

echo ================================================
echo  AmyReads - Building Windows Executable
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

python --version

REM Install dependencies
echo.
echo [1/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements.
    pause
    exit /b 1
)

REM Install PyInstaller
echo.
echo [2/4] Installing PyInstaller...
pip install "pyinstaller>=6.0"
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    pause
    exit /b 1
)

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist AmyReads.spec del AmyReads.spec

REM Build the executable
echo.
echo [3/4] Building AmyReads.exe (this may take 2-5 minutes)...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name AmyReads ^
    --hidden-import PySide6.QtSvg ^
    --hidden-import PySide6.QtPrintSupport ^
    --hidden-import PySide6.QtNetwork ^
    --collect-all pymupdf ^
    --collect-all PySide6 ^
    --noconfirm ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed. See above for details.
    pause
    exit /b 1
)

echo.
echo ================================================
echo  [4/4] BUILD COMPLETE!
echo ================================================
echo.
echo  Output: dist\AmyReads.exe
echo.
echo  The executable is self-contained and runs on any
echo  Windows 10/11 machine without Python installed.
echo.
pause
