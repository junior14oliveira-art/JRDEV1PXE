@echo off
setlocal EnableDelayedExpansion
title WinPE Studio — BUILD INSTALADOR
color 0D
cd /d "%~dp0"

echo ============================================================
echo   WinPE Studio Pro — BUILD INSTALADOR COMPLETO
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
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo [OK] %%V

:: ── NSIS ─────────────────────────────────────────────────────────────
set "MAKENSIS="
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set "MAKENSIS=C:\Program Files (x86)\NSIS\makensis.exe"
if exist "C:\Program Files\NSIS\makensis.exe"       set "MAKENSIS=C:\Program Files\NSIS\makensis.exe"

if "!MAKENSIS!"=="" (
    echo.
    echo [!] NSIS nao encontrado. Instalando...
    echo.

    :: Tenta winget primeiro (Windows 10/11 moderno)
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo [+] Instalando via winget...
        winget install NSIS.NSIS --silent --accept-package-agreements --accept-source-agreements
        timeout /t 5 /nobreak >nul
    )

    :: Verifica se winget funcionou
    if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
        set "MAKENSIS=C:\Program Files (x86)\NSIS\makensis.exe"
        echo [OK] NSIS instalado via winget.
        goto :nsis_ok
    )

    :: Fallback: download direto com PowerShell
    echo [+] Baixando NSIS via PowerShell...
    set "NSIS_URL=https://prdownloads.sourceforge.net/nsis/nsis-3.10-setup.exe?download"
    set "NSIS_OUT=%TEMP%\nsis_setup.exe"

    powershell -NoProfile -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
         $wc = New-Object System.Net.WebClient; ^
         $wc.Headers.Add('User-Agent','Mozilla/5.0'); ^
         $wc.DownloadFile('https://github.com/nicehash/NiceHashQuickMiner/releases/download/v0.5.4.4/nsis-3.08-setup.exe', '%NSIS_OUT%')" 2>nul

    :: Se ainda nao baixou, tenta URL alternativa
    if not exist "%NSIS_OUT%" (
        powershell -NoProfile -Command ^
            "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
             Invoke-WebRequest -Uri 'https://sourceforge.net/projects/nsis/files/NSIS%%203/3.10/nsis-3.10-setup.exe/download' ^
             -OutFile '%NSIS_OUT%' -UserAgent 'Mozilla/5.0'" 2>nul
    )

    if exist "%NSIS_OUT%" (
        echo [+] Instalando NSIS...
        start /wait "" "%NSIS_OUT%" /S
        timeout /t 8 /nobreak >nul
    )

    :: Verifica instalacao
    if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
        set "MAKENSIS=C:\Program Files (x86)\NSIS\makensis.exe"
        echo [OK] NSIS instalado.
        goto :nsis_ok
    )
    if exist "C:\Program Files\NSIS\makensis.exe" (
        set "MAKENSIS=C:\Program Files\NSIS\makensis.exe"
        echo [OK] NSIS instalado.
        goto :nsis_ok
    )

    :: Nao conseguiu instalar automaticamente
    echo.
    echo [ERRO] Nao foi possivel instalar o NSIS automaticamente.
    echo.
    echo Instale manualmente:
    echo   1. Acesse: https://nsis.sourceforge.io/Download
    echo   2. Baixe "nsis-3.xx-setup.exe"
    echo   3. Instale normalmente
    echo   4. Execute este script novamente
    echo.
    pause & exit /b 1
)
:nsis_ok
echo [OK] NSIS: !MAKENSIS!

:: ── STEP 1: Dependencias Python ──────────────────────────────────────
echo.
echo [1/4] Instalando dependencias Python...
python -m pip install -r requirements.txt --quiet
python -m pip install pyinstaller --quiet
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
    echo [ERRO] PyInstaller falhou!
    pause & exit /b 1
)
echo [OK] PyInstaller concluido.

:: ── STEP 3: Copiar extras para dist ──────────────────────────────────
echo.
echo [3/4] Copiando arquivos de suporte...
copy /y "GEMINI_HOST.bat"        "dist\WinPE_Studio\" >nul
copy /y "KIRO_SMB.bat"           "dist\WinPE_Studio\" >nul
copy /y "KIRO_CONECTOR.bat"      "dist\WinPE_Studio\" >nul
copy /y "KIRO_CONECTOR_MAIN.bat" "dist\WinPE_Studio\" >nul
if exist "README.md" copy /y "README.md" "dist\WinPE_Studio\" >nul
echo [OK] Arquivos copiados.

:: ── STEP 4: NSIS — gerar Setup.exe ───────────────────────────────────
echo.
echo [4/4] Gerando instalador com NSIS...
"!MAKENSIS!" /V2 installer.nsi
if %errorlevel% neq 0 (
    echo [ERRO] NSIS falhou!
    pause & exit /b 1
)

:: ── Resultado ─────────────────────────────────────────────────────────
echo.
if exist "WinPE_Studio_Setup.exe" (
    for %%F in ("WinPE_Studio_Setup.exe") do set "SIZE=%%~zF"
    set /a SIZE_MB=!SIZE! / 1048576
    echo ============================================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo.
    echo   Arquivo : WinPE_Studio_Setup.exe
    echo   Tamanho : ~!SIZE_MB! MB
    echo.
    echo   O instalador:
    echo   - Tela de boas-vindas e escolha de pasta
    echo   - Instala em Arquivos de Programas
    echo   - Cria atalho na Area de Trabalho
    echo   - Configura Firewall automaticamente
    echo   - Cria usuario ACESSO/REDE e share IMG
    echo   - Aparece em "Adicionar/Remover Programas"
    echo   - Tem desinstalador completo
    echo ============================================================
) else (
    echo [ERRO] WinPE_Studio_Setup.exe nao foi gerado.
)
echo.
pause
