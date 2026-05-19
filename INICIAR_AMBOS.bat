@echo off
title JRDEV1 PXE — Iniciar Programas
color 0A
echo.
echo ============================================================
echo   JRDEV1 PXE — Iniciando Programas
echo ============================================================
echo.

cd /d "%~dp0"

echo [1] WinPE Studio (Python/PySide6) — versao atual
echo [2] JRDEV1 PXE (Go/Wails) — nova versao em desenvolvimento
echo [3] Ambos
echo.
set /p CHOICE="Escolha (1/2/3): "

if "%CHOICE%"=="1" goto python
if "%CHOICE%"=="2" goto go
if "%CHOICE%"=="3" goto ambos
goto python

:python
echo Iniciando WinPE Studio (Python)...
start "" "dist\JRDEV1_PXE\JRDEV1_PXE.exe"
goto fim

:go
echo Iniciando JRDEV1 PXE (Go)...
if exist "JRDEV1GO\JRDEV1_PXE.exe" (
    start "" "JRDEV1GO\JRDEV1_PXE.exe"
) else (
    echo [AVISO] Build Go nao encontrado. Execute BUILD_GO.bat primeiro.
    cd JRDEV1GO
    wails dev
)
goto fim

:ambos
echo Iniciando ambos...
start "" "dist\JRDEV1_PXE\JRDEV1_PXE.exe"
timeout /t 2 /nobreak >nul
if exist "JRDEV1GO\JRDEV1_PXE.exe" (
    start "" "JRDEV1GO\JRDEV1_PXE.exe"
) else (
    echo [INFO] Go ainda nao compilado — iniciando em modo dev...
    start cmd /k "cd JRDEV1GO && wails dev"
)
goto fim

:fim
echo.
echo Programas iniciados.
pause
