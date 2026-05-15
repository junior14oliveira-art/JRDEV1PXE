@echo off
title JRDEV1 PXE — BUILD FINAL
color 0A
echo.
echo ============================================================
echo   JRDEV1 PXE — BUILD COMPLETO
echo   Resultado: E:\JRDEV1FINAL.EXE
echo ============================================================
echo.

cd /d "%~dp0"

:: Admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Execute como ADMINISTRADOR!
    pause & exit /b 1
)

:: Python oficial
set "PYTHON=C:\Python313\python.exe"
if not exist "%PYTHON%" (
    echo [ERRO] Python nao encontrado em C:\Python313
    echo Instale em: https://www.python.org/downloads/
    pause & exit /b 1
)
echo [OK] Python: 
%PYTHON% --version

:: NSIS
set "MAKENSIS=C:\Program Files (x86)\NSIS\makensis.exe"
if not exist "%MAKENSIS%" set "MAKENSIS=C:\Program Files\NSIS\makensis.exe"
if not exist "%MAKENSIS%" (
    echo [ERRO] NSIS nao encontrado. Instale em: https://nsis.sourceforge.io/Download
    pause & exit /b 1
)
echo [OK] NSIS encontrado.

echo.
echo [1/3] Instalando dependencias...
%PYTHON% -m pip install pyinstaller requests PySide6 loguru pywin32 wmi --quiet
echo [OK] Dependencias OK.

echo.
echo [2/3] Compilando JRDEV1_PXE.exe com PyInstaller...
echo       (pode demorar 3-5 minutos)

:: Limpa builds anteriores
if exist "dist\JRDEV1_PXE" (
    takeown /f "dist\JRDEV1_PXE" /r /d y >nul 2>&1
    icacls "dist\JRDEV1_PXE" /grant *S-1-1-0:F /t /q >nul 2>&1
    rmdir /s /q "dist\JRDEV1_PXE"
)
if exist "build" rmdir /s /q "build"

%PYTHON% -m PyInstaller winpe_studio.spec --clean -y
if %errorlevel% neq 0 (
    echo [ERRO] PyInstaller falhou!
    pause & exit /b 1
)

if not exist "dist\JRDEV1_PXE\JRDEV1_PXE.exe" (
    echo [ERRO] JRDEV1_PXE.exe nao foi gerado!
    pause & exit /b 1
)
echo [OK] JRDEV1_PXE.exe gerado com sucesso.

echo.
echo [3/3] Gerando instalador JRDEV1FINAL.EXE com NSIS...
"%MAKENSIS%" /V2 installer_final.nsi
if %errorlevel% neq 0 (
    echo [ERRO] NSIS falhou! Verifique o installer_final.nsi
    pause & exit /b 1
)

:: Resultado
if exist "E:\JRDEV1FINAL.EXE" (
    for %%F in ("E:\JRDEV1FINAL.EXE") do set SIZE=%%~zF
    set /a SIZE_MB=%SIZE% / 1048576
    echo.
    echo ============================================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo.
    echo   Instalador: E:\JRDEV1FINAL.EXE  (%SIZE_MB% MB)
    echo.
    echo   Para instalar em outro servidor:
    echo   1. Copie E:\JRDEV1FINAL.EXE para o servidor
    echo   2. Execute como Administrador
    echo   3. Siga o assistente de instalacao
    echo ============================================================
) else (
    echo [ERRO] JRDEV1FINAL.EXE nao foi gerado em E:\
)
echo.
pause
