@echo off
title KIRO BG - BUILD
color 0B
cd /d "%~dp0"

echo ============================================================
echo   KIRO Conector Background - BUILD
echo   Gera: kiro_bg.exe (sem janela, roda silencioso no WinPE)
echo ============================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado.
    pause & exit /b 1
)

python -m pip install pyinstaller -q
python -m PyInstaller kiro_bg.spec --noconfirm --clean --distpath dist

if exist "dist\kiro_bg.exe" (
    copy /y "dist\kiro_bg.exe" "..\kiro_bg.exe" >nul
    echo.
    echo ============================================================
    echo   [OK] kiro_bg.exe gerado!
    echo   Copie kiro_bg.exe para o WinPE e configure para iniciar
    echo   automaticamente (igual ao Explorer++).
    echo ============================================================
) else (
    echo [ERRO] Build falhou.
)
echo.
pause
