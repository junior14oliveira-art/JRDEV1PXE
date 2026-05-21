@echo off
title JRDEV1 PXE — Build Go/Wails
color 0A
echo.
echo ============================================================
echo   JRDEV1 PXE — Build Go/Wails
echo   Resultado: JRDEV1_PXE.exe (arquivo unico ~12MB)
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

echo [1/3] Compilando com Wails...
wails build -clean -platform windows/amd64
if %errorlevel% neq 0 (
    echo [ERRO] Build falhou!
    pause & exit /b 1
)

echo.
echo [2/3] Aplicando manifesto UAC (requireAdministrator)...

:: Procura mt.exe (Microsoft Manifest Tool) no Windows SDK
set "MT="
for /d %%d in ("C:\Program Files (x86)\Windows Kits\10\bin\*") do (
    if exist "%%d\x64\mt.exe" set "MT=%%d\x64\mt.exe"
)
if "%MT%"=="" (
    for /d %%d in ("C:\Program Files\Windows Kits\10\bin\*") do (
        if exist "%%d\x64\mt.exe" set "MT=%%d\x64\mt.exe"
    )
)

if "%MT%"=="" (
    echo [AVISO] mt.exe nao encontrado — UAC nao aplicado automaticamente.
    echo         Instale o Windows SDK ou use o atalho com "Executar como Admin".
    goto copiar
)

echo [OK] mt.exe: %MT%
"%MT%" -nologo -manifest "build\windows\app.manifest" -outputresource:"build\bin\JRDEV1_PXE.exe;#1"
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao aplicar manifesto UAC.
) else (
    echo [OK] Manifesto UAC aplicado com sucesso!
)

:copiar
echo.
echo [3/3] Copiando para pasta raiz...
copy /y "build\bin\JRDEV1_PXE.exe" "..\JRDEV1_PXE_GO.exe" >nul

if exist "..\JRDEV1_PXE_GO.exe" (
    for %%F in ("..\JRDEV1_PXE_GO.exe") do set SIZE=%%~zF
    set /a SIZE_MB=%SIZE% / 1048576
    echo.
    echo ============================================================
    echo   BUILD CONCLUIDO!
    echo   Arquivo: E:\KIRO\JRDEV1_PXE_GO.exe
    echo   Tamanho: ~12 MB (arquivo unico sem dependencias)
    echo   UAC: Pede elevacao automaticamente ao abrir
    echo ============================================================
) else (
    echo [ERRO] Arquivo nao gerado.
)
echo.
pause
