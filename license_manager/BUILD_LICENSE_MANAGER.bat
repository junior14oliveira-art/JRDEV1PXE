@echo off
title Build — WinPE License Manager
color 0A
echo.
echo ============================================================
echo   BUILD — WinPE Studio License Manager (painel admin)
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

:: Instala dependencias se necessario
echo [1/3] Verificando dependencias...
pip install pyinstaller PySide6 --quiet

echo.
echo [2/3] Compilando LicenseManager.exe...
pyinstaller --onefile --windowed ^
    --name "LicenseManager" ^
    --add-data "..\app\core\license_service.py;app\core" ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    license_manager.py

echo.
echo [3/3] Verificando resultado...
if exist "dist\LicenseManager.exe" (
    echo.
    echo ============================================================
    echo   [OK] LicenseManager.exe gerado com sucesso!
    echo   Arquivo: %~dp0dist\LicenseManager.exe
    echo.
    echo   IMPORTANTE: Este executavel e EXCLUSIVO para voce.
    echo   NAO distribua para clientes.
    echo ============================================================
) else (
    echo [ERRO] Falha na compilacao. Verifique os logs acima.
)

echo.
pause
