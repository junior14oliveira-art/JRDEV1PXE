@echo off
setlocal EnableDelayedExpansion
title WinPE Studio — Iniciando...
cd /d "%~dp0"

:: ============================================================
::  WinPE Studio — Launcher com elevacao automatica
::  Garante: Admin + PATH correto + venv/Poetry + janela visivel
:: ============================================================

:: --- Verificar se ja e Administrador ---
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Elevando para Administrador...
    powershell -NoProfile -Command ^
        "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

:: --- A partir daqui: rodando como Admin ---
title WinPE Studio Pro

:: --- Detectar Python: tenta venv local, depois Poetry, depois PATH global ---
set "PYTHON_EXE="

:: 1. Venv local (.venv na raiz do projeto)
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    echo [OK] Python encontrado: venv local
    goto :run
)

:: 2. Poetry (resolve automaticamente o venv do projeto)
where poetry >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Usando Poetry para executar...
    poetry run python -m app.main
    goto :check_exit
)

:: 3. Python no PATH do sistema
where python >nul 2>&1
if %ERRORLEVEL% == 0 (
    set "PYTHON_EXE=python"
    echo [OK] Python encontrado no PATH do sistema
    goto :run
)

:: 4. Python na pasta padrao do usuario (instalacao tipica do Windows)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        echo [OK] Python encontrado em: %%D
        goto :run
    )
)

:: Nenhum Python encontrado
echo.
echo [ERRO] Python nao encontrado!
echo Instale o Python 3.12+ em https://www.python.org/downloads/
echo e marque a opcao "Add Python to PATH" durante a instalacao.
echo.
pause
exit /b 1

:run
"%PYTHON_EXE%" -m app.main

:check_exit
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERRO] WinPE Studio encerrou com codigo de erro: %ERRORLEVEL%
    echo Verifique os logs em: %~dp0logs\winpe_studio.log
    echo.
    pause
)
