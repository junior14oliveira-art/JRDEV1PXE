@echo off
setlocal EnableDelayedExpansion
title WinPE Studio - SETUP AMBIENTE
color 0A
cd /d "%~dp0"

echo ============================================================
echo   WinPE Studio - SETUP COMPLETO DO AMBIENTE
echo   Instala: Python 3.13, dependencias, 7-Zip, NSIS, Git
echo ============================================================
echo.

:: ── Admin ────────────────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Elevando para Administrador...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)
echo [OK] Administrador confirmado.
echo.

:: ── Internet ─────────────────────────────────────────────────────────
ping -n 1 -w 3000 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Sem conexao com a internet. Necessaria para baixar arquivos.
    pause & exit /b 1
)
echo [OK] Internet disponivel.
echo.

set "LOG=%~dp0SETUP_DEV_LOG.txt"
echo ====== SETUP %DATE% %TIME% ====== > "%LOG%"

:: ════════════════════════════════════════════════════════════════════
echo [1/5] Python 3.13...
:: ════════════════════════════════════════════════════════════════════
set "PYTHON_EXE="

:: Procura Python em locais comuns
for %%P in (
    "python"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Program Files\Python313\python.exe"
) do (
    if "!PYTHON_EXE!"=="" (
        where %%~P >nul 2>&1 && set "PYTHON_EXE=%%~P"
        if "!PYTHON_EXE!"=="" if exist "%%~P" set "PYTHON_EXE=%%~P"
    )
)

if not "!PYTHON_EXE!"=="" (
    for /f "tokens=2" %%V in ('"!PYTHON_EXE!" --version 2^>^&1') do echo [OK] Python ja instalado: %%V
    echo Python ja instalado >> "%LOG%"
    goto :python_ok
)

echo [+] Baixando Python 3.13.0...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile '%TEMP%\python_setup.exe'"

if not exist "%TEMP%\python_setup.exe" (
    echo [ERRO] Falha ao baixar Python. Instale manualmente: https://www.python.org/downloads/
    echo        Marque "Add Python to PATH" durante a instalacao.
    pause & exit /b 1
)

echo [+] Instalando Python 3.13...
"%TEMP%\python_setup.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1
timeout /t 15 /nobreak >nul

:: Recarregar PATH do registro
for /f "skip=2 tokens=3*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "PATH=%%A %%B"
for /f "skip=2 tokens=3*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH=!PATH!;%%A %%B"

:: Tenta achar python apos instalacao
for %%P in (
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files (x86)\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "C:\Python313\python.exe"
) do (
    if "!PYTHON_EXE!"=="" if exist "%%~P" set "PYTHON_EXE=%%~P"
)

if "!PYTHON_EXE!"=="" (
    echo [AVISO] Python instalado mas nao encontrado no PATH ainda.
    echo         FECHE esta janela, abra uma nova como Admin e execute novamente.
    echo         Ou reinicie o PC e execute novamente.
    pause & exit /b 1
)
echo [OK] Python instalado: !PYTHON_EXE!
echo Python instalado OK >> "%LOG%"

:python_ok

:: ════════════════════════════════════════════════════════════════════
echo.
echo [2/5] Dependencias Python (PySide6, loguru, wmi...)...
:: ════════════════════════════════════════════════════════════════════
echo [+] Atualizando pip...
"!PYTHON_EXE!" -m pip install --upgrade pip --quiet --no-warn-script-location

echo [+] Instalando dependencias do requirements.txt...
"!PYTHON_EXE!" -m pip install -r "%~dp0requirements.txt" --quiet --no-warn-script-location
if %errorlevel% equ 0 (
    echo [OK] Dependencias instaladas.
    echo Dependencias OK >> "%LOG%"
) else (
    echo [ERRO] Falha ao instalar dependencias.
    echo [ERRO] Tente manualmente: python -m pip install -r requirements.txt
    echo Dependencias FALHOU >> "%LOG%"
)

echo [+] Instalando PyInstaller...
"!PYTHON_EXE!" -m pip install pyinstaller --quiet --no-warn-script-location
echo [OK] PyInstaller instalado.

:: ════════════════════════════════════════════════════════════════════
echo.
echo [3/5] 7-Zip...
:: ════════════════════════════════════════════════════════════════════
if exist "C:\Program Files\7-Zip\7z.exe" goto :7zip_ok
if exist "C:\Program Files (x86)\7-Zip\7z.exe" goto :7zip_ok

echo [+] Baixando 7-Zip 24.08...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri 'https://www.7-zip.org/a/7z2408-x64.exe' -OutFile '%TEMP%\7zip_setup.exe'"

if exist "%TEMP%\7zip_setup.exe" (
    echo [+] Instalando 7-Zip...
    "%TEMP%\7zip_setup.exe" /S
    timeout /t 6 /nobreak >nul
    if exist "C:\Program Files\7-Zip\7z.exe" (
        echo [OK] 7-Zip instalado.
        echo 7-Zip OK >> "%LOG%"
    ) else (
        echo [AVISO] 7-Zip nao instalado. Baixe em: https://www.7-zip.org
    )
) else (
    echo [AVISO] Falha ao baixar 7-Zip. Baixe em: https://www.7-zip.org
)
:7zip_ok
echo [OK] 7-Zip disponivel.

:: ════════════════════════════════════════════════════════════════════
echo.
echo [4/5] NSIS (para gerar instalador)...
:: ════════════════════════════════════════════════════════════════════
if exist "C:\Program Files (x86)\NSIS\makensis.exe" goto :nsis_ok
if exist "C:\Program Files\NSIS\makensis.exe" goto :nsis_ok

echo [+] Tentando instalar NSIS via winget...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    winget install NSIS.NSIS --silent --accept-package-agreements --accept-source-agreements
    timeout /t 10 /nobreak >nul
)

if exist "C:\Program Files (x86)\NSIS\makensis.exe" goto :nsis_ok
if exist "C:\Program Files\NSIS\makensis.exe" goto :nsis_ok

echo.
echo [AVISO] NSIS nao instalado automaticamente.
echo         Necessario apenas para gerar o Setup.exe (BUILD_INSTALLER.bat).
echo         Para instalar: https://nsis.sourceforge.io/Download
echo         Ou: winget install NSIS.NSIS
echo NSIS nao instalado >> "%LOG%"
goto :nsis_fim
:nsis_ok
echo [OK] NSIS disponivel.
echo NSIS OK >> "%LOG%"
:nsis_fim

:: ════════════════════════════════════════════════════════════════════
echo.
echo [5/5] Git...
:: ════════════════════════════════════════════════════════════════════
where git >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%V in ('git --version 2^>^&1') do echo [OK] Git ja instalado: %%V
    goto :git_ok
)

echo [+] Instalando Git via winget...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
    timeout /t 15 /nobreak >nul
    where git >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Git instalado.
        echo Git OK >> "%LOG%"
    ) else (
        echo [AVISO] Git instalado mas PATH nao atualizado ainda.
        echo         Feche e reabra o terminal para usar git.
    )
) else (
    echo [AVISO] winget nao disponivel. Baixe Git em: https://git-scm.com/download/win
)
:git_ok

:: ════════════════════════════════════════════════════════════════════
echo.
echo ============================================================
echo   VERIFICACAO FINAL
echo ============================================================

set "OK_PY=[ FALTA ]"
"!PYTHON_EXE!" --version >nul 2>&1 && set "OK_PY=[  OK   ]"

set "OK_PS=[ FALTA ]"
"!PYTHON_EXE!" -c "import PySide6" >nul 2>&1 && set "OK_PS=[  OK   ]"

set "OK_7Z=[ FALTA ]"
if exist "C:\Program Files\7-Zip\7z.exe"       set "OK_7Z=[  OK   ]"
if exist "C:\Program Files (x86)\7-Zip\7z.exe" set "OK_7Z=[  OK   ]"

set "OK_NS=[ FALTA ]"
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set "OK_NS=[  OK   ]"
if exist "C:\Program Files\NSIS\makensis.exe"       set "OK_NS=[  OK   ]"

set "OK_GT=[ FALTA ]"
where git >nul 2>&1 && set "OK_GT=[  OK   ]"

echo.
echo   !OK_PY! Python 3.x
echo   !OK_PS! PySide6 (interface grafica)
echo   !OK_7Z! 7-Zip
echo   !OK_NS! NSIS (para BUILD_INSTALLER.bat)
echo   !OK_GT! Git
echo   [  OK   ] DISM (nativo do Windows)
echo   [  OK   ] oscdimg (embutido em app\resources\tools\)
echo.

if "!OK_PY!"=="[ FALTA ]" (
    echo [!] Python nao encontrado. Reinicie o PC e execute novamente.
) else if "!OK_PS!"=="[ FALTA ]" (
    echo [!] PySide6 nao instalado. Execute:
    echo     !PYTHON_EXE! -m pip install -r requirements.txt
) else (
    echo   Ambiente pronto!
    echo   Para rodar o programa: start.bat
    echo   Para gerar instalador: BUILD_INSTALLER.bat
)

echo.
echo   Log: %LOG%
echo ============================================================
echo.
pause
