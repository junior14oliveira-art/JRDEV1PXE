@echo off
title JRDEV1 PXE — BUILD COMPLETO
color 0A
echo.
echo ============================================================
echo   JRDEV1 PXE — BUILD COMPLETO
echo   WinPE Studio Pro + LicenseManager
echo ============================================================
echo.

cd /d "%~dp0"

:: Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    pause
    exit /b 1
)

:: Verifica PyInstaller
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [+] Instalando PyInstaller...
    pip install pyinstaller --quiet
)

echo.
echo ============================================================
echo   [1/2] BUILD: WinPE Studio Pro
echo ============================================================
echo.
python -m PyInstaller winpe_studio.spec --clean -y
if %errorlevel% neq 0 (
    echo [ERRO] Falha no build do WinPE Studio.
    pause
    exit /b 1
)
echo [OK] WinPE Studio gerado em: dist\WinPE_Studio\

echo.
echo ============================================================
echo   [2/2] BUILD: LicenseManager
echo ============================================================
echo.
python -m PyInstaller --onefile --windowed ^
    --name "LicenseManager" ^
    --paths "%~dp0" ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --distpath "%~dp0" ^
    license_manager\license_manager.py -y
if %errorlevel% neq 0 (
    echo [ERRO] Falha no build do LicenseManager.
    pause
    exit /b 1
)
echo [OK] LicenseManager.exe gerado na raiz.

echo.
echo ============================================================
echo   BUILD COMPLETO!
echo.
echo   WinPE Studio:   dist\WinPE_Studio\WinPE_Studio.exe
echo   LicenseManager: LicenseManager.exe  (SO PARA VOCE)
echo.
echo   Para distribuir ao cliente:
echo   Copie a pasta dist\WinPE_Studio\ inteira
echo   ou gere o instalador com BUILD_INSTALLER.bat
echo ============================================================
echo.
pause
