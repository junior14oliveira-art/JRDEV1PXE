@echo off
title JRDEV1 PXE — Build Go
color 0A
echo.
echo ============================================================
echo   JRDEV1 PXE — Build Go/Wails
echo   Resultado: JRDEV1_PXE.exe (arquivo unico ~15MB)
echo ============================================================
echo.

cd /d "%~dp0"

:: Verifica Go
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Go nao encontrado. Instale em: https://go.dev/dl/
    pause & exit /b 1
)

:: Verifica Wails
wails version >nul 2>&1
if %errorlevel% neq 0 (
    echo [+] Instalando Wails...
    go install github.com/wailsapp/wails/v2/cmd/wails@latest
)

:: Instala dependencias frontend
echo [1/3] Instalando dependencias frontend...
cd frontend && npm install && cd ..

:: Baixa dependencias Go
echo [2/3] Baixando dependencias Go...
go mod tidy

:: Build
echo [3/3] Compilando...
wails build -clean -o JRDEV1_PXE.exe

if exist "build\bin\JRDEV1_PXE.exe" (
    copy /y "build\bin\JRDEV1_PXE.exe" "..\JRDEV1_PXE_GO.exe"
    echo.
    echo ============================================================
    echo   BUILD CONCLUIDO!
    echo   Arquivo: JRDEV1_PXE_GO.exe
    echo   Tamanho: unico executavel sem dependencias externas
    echo ============================================================
) else (
    echo [ERRO] Build falhou. Verifique os erros acima.
)
echo.
pause
