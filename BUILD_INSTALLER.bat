@echo off
setlocal EnableDelayedExpansion
title WinPE Studio - BUILD INSTALADOR
color 0D
cd /d "%~dp0"

echo ============================================================
echo   WinPE Studio Pro - BUILD INSTALADOR COMPLETO
echo   Resultado: WinPE_Studio_Setup.exe
echo ============================================================
echo.

:: ── Admin ────────────────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Execute como Administrador!
    pause & exit /b 1
)

:: ── Python ───────────────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado.
    pause & exit /b 1
)
python --version

:: ── NSIS ─────────────────────────────────────────────────────────────
set "MAKENSIS=C:\Program Files (x86)\NSIS\makensis.exe"
if not exist "%MAKENSIS%" set "MAKENSIS=C:\Program Files\NSIS\makensis.exe"
if not exist "%MAKENSIS%" (
    echo [ERRO] NSIS nao encontrado em:
    echo   C:\Program Files (x86)\NSIS\makensis.exe
    echo   C:\Program Files\NSIS\makensis.exe
    echo.
    echo Instale em: https://nsis.sourceforge.io/Download
    pause & exit /b 1
)
echo [OK] NSIS: %MAKENSIS%

:: ── STEP 1: Dependencias Python ──────────────────────────────────────
echo.
echo [1/4] Instalando dependencias Python...
python -m pip install -r requirements.txt -q
python -m pip install pyinstaller -q
echo [OK] Dependencias OK.

:: ── STEP 2: PyInstaller ──────────────────────────────────────────────
echo.
echo [2/4] Compilando com PyInstaller...
echo       (pode demorar 5-10 min por causa dos drivers)
echo.

if exist "dist\WinPE_Studio" rmdir /s /q "dist\WinPE_Studio"
if exist "build\WinPE_Studio" rmdir /s /q "build\WinPE_Studio"

python -m PyInstaller winpe_studio.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] PyInstaller falhou!
    pause & exit /b 1
)
echo [OK] PyInstaller concluido.

:: ── STEP 3: Copiar extras para dist ──────────────────────────────────
echo.
echo [3/4] Copiando arquivos de suporte...
copy /y "GEMINI_HOST.bat"        "dist\WinPE_Studio\" >nul 2>&1
copy /y "KIRO_SMB.bat"           "dist\WinPE_Studio\" >nul 2>&1
copy /y "KIRO_CONECTOR.bat"      "dist\WinPE_Studio\" >nul 2>&1
copy /y "KIRO_CONECTOR_MAIN.bat" "dist\WinPE_Studio\" >nul 2>&1
if exist "README.md" copy /y "README.md" "dist\WinPE_Studio\" >nul 2>&1
echo [OK] Arquivos copiados.

:: ── STEP 4: NSIS ─────────────────────────────────────────────────────
echo.
echo [4/4] Gerando instalador com NSIS...
"%MAKENSIS%" /V2 installer.nsi
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] NSIS falhou! Verifique o installer.nsi
    pause & exit /b 1
)

:: ── Resultado ─────────────────────────────────────────────────────────
echo.
if exist "WinPE_Studio_Setup.exe" (
    for %%F in ("WinPE_Studio_Setup.exe") do (
        set /a SIZE_MB=%%~zF / 1048576
    )
    echo ============================================================
    echo   BUILD CONCLUIDO!
    echo.
    echo   Arquivo : %~dp0WinPE_Studio_Setup.exe
    echo   Tamanho : !SIZE_MB! MB
    echo.
    echo   Para instalar em outro servidor:
    echo   Copie WinPE_Studio_Setup.exe e execute como Admin
    echo ============================================================
) else (
    echo [ERRO] WinPE_Studio_Setup.exe nao foi gerado.
)
echo.
pause
