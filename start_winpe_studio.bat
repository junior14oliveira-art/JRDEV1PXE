@echo off
setlocal
cd /d "%~dp0"

:: Tenta rodar um comando que exige admin para checar status
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Solicitando permissao de Administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"cd /d %~dp0 && python -m app.main\"' -Verb RunAs"
    exit /b
)

:: Se já for admin, roda direto
python -m app.main
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERRO] O programa fechou com erro ou o Python nao foi encontrado.
    echo Verifique se o Python esta instalado e no PATH.
    pause
)
