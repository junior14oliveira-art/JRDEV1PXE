@echo off
setlocal EnableDelayedExpansion
title WinPE Studio - SETUP AMBIENTE DE DESENVOLVIMENTO
color 0A
cd /d "%~dp0"

echo ============================================================
echo   WinPE Studio - SETUP COMPLETO DO AMBIENTE
echo   Para servidor com NADA instalado
echo   Instala: Python, pip, dependencias, NSIS, 7-Zip
echo ============================================================
echo.

:: ── Admin ────────────────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Elevando para Administrador...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

echo [OK] Rodando como Administrador.
echo.

:: ── Verificar conexao com internet ───────────────────────────────────
ping -n 1 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Sem conexao com a internet.
    echo        Este script precisa baixar arquivos.
    pause & exit /b 1
)
echo [OK] Internet disponivel.
echo.

set "ERROS=0"
set "LOG=%~dp0SETUP_DEV_LOG.txt"
echo Setup iniciado em %DATE% %TIME% > "%LOG%"

:: ════════════════════════════════════════════════════════════════════
echo [1/6] Verificando/Instalando Python 3.13...
:: ════════════════════════════════════════════════════════════════════
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%V in ('python --version 2^>^&1') do set "PY_VER=%%V"
    echo [OK] Python ja instalado: !PY_VER!
    echo Python ja instalado: !PY_VER! >> "%LOG%"
    goto :python_ok
)

echo [+] Baixando Python 3.13...
powershell -NoProfile -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
     Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' ^
     -OutFile '%TEMP%\python_setup.exe' -UseBasicParsing"

if not exist "%TEMP%\python_setup.exe" (
    echo [ERRO] Falha ao baixar Python.
    set /a ERROS+=1
    goto :python_skip
)

echo [+] Instalando Python 3.13 (silencioso)...
"%TEMP%\python_setup.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0
timeout /t 10 /nobreak >nul

:: Recarregar PATH
call :refresh_path

where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python instalado com sucesso.
    echo Python instalado OK >> "%LOG%"
) else (
    echo [ERRO] Python nao foi instalado corretamente.
    echo [ERRO] Instale manualmente: https://www.python.org/downloads/
    set /a ERROS+=1
)
:python_ok
:python_skip

:: ════════════════════════════════════════════════════════════════════
echo.
echo [2/6] Atualizando pip e instalando dependencias Python...
:: ════════════════════════════════════════════════════════════════════
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Python nao encontrado - pulando pip.
    goto :pip_skip
)

python -m pip install --upgrade pip --quiet
python -m pip install -r "%~dp0requirements.txt" --quiet
if %errorlevel% equ 0 (
    echo [OK] Dependencias Python instaladas.
    echo Dependencias Python OK >> "%LOG%"
) else (
    echo [ERRO] Falha ao instalar dependencias Python.
    set /a ERROS+=1
)

python -m pip install pyinstaller --quiet
if %errorlevel% equ 0 (
    echo [OK] PyInstaller instalado.
) else (
    echo [AVISO] Falha ao instalar PyInstaller.
)
:pip_skip

:: ════════════════════════════════════════════════════════════════════
echo.
echo [3/6] Verificando/Instalando 7-Zip...
:: ════════════════════════════════════════════════════════════════════
if exist "C:\Program Files\7-Zip\7z.exe" (
    echo [OK] 7-Zip ja instalado.
    echo 7-Zip ja instalado >> "%LOG%"
    goto :7zip_ok
)
if exist "C:\Program Files (x86)\7-Zip\7z.exe" (
    echo [OK] 7-Zip ja instalado.
    goto :7zip_ok
)

echo [+] Baixando 7-Zip...
powershell -NoProfile -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
     Invoke-WebRequest -Uri 'https://www.7-zip.org/a/7z2408-x64.exe' ^
     -OutFile '%TEMP%\7zip_setup.exe' -UseBasicParsing"

if exist "%TEMP%\7zip_setup.exe" (
    echo [+] Instalando 7-Zip...
    "%TEMP%\7zip_setup.exe" /S
    timeout /t 5 /nobreak >nul
    if exist "C:\Program Files\7-Zip\7z.exe" (
        echo [OK] 7-Zip instalado.
        echo 7-Zip instalado OK >> "%LOG%"
    ) else (
        echo [AVISO] 7-Zip pode nao ter instalado corretamente.
    )
) else (
    echo [AVISO] Falha ao baixar 7-Zip. Instale manualmente: https://www.7-zip.org
)
:7zip_ok

:: ════════════════════════════════════════════════════════════════════
echo.
echo [4/6] Verificando/Instalando NSIS...
:: ════════════════════════════════════════════════════════════════════
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo [OK] NSIS ja instalado.
    echo NSIS ja instalado >> "%LOG%"
    goto :nsis_ok
)
if exist "C:\Program Files\NSIS\makensis.exe" (
    echo [OK] NSIS ja instalado.
    goto :nsis_ok
)

echo [+] Instalando NSIS via winget...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    winget install NSIS.NSIS --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    timeout /t 8 /nobreak >nul
)

if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo [OK] NSIS instalado via winget.
    echo NSIS instalado OK >> "%LOG%"
    goto :nsis_ok
)

echo [+] Baixando NSIS diretamente...
powershell -NoProfile -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
     Invoke-WebRequest -Uri 'https://prdownloads.sourceforge.net/nsis/nsis-3.10-setup.exe' ^
     -OutFile '%TEMP%\nsis_setup.exe' -UseBasicParsing" >nul 2>&1

if exist "%TEMP%\nsis_setup.exe" (
    "%TEMP%\nsis_setup.exe" /S
    timeout /t 8 /nobreak >nul
    if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
        echo [OK] NSIS instalado.
        echo NSIS instalado OK >> "%LOG%"
    ) else (
        echo [AVISO] NSIS nao instalado. Baixe em: https://nsis.sourceforge.io/Download
    )
) else (
    echo [AVISO] Falha ao baixar NSIS. Baixe em: https://nsis.sourceforge.io/Download
)
:nsis_ok

:: ════════════════════════════════════════════════════════════════════
echo.
echo [5/6] Verificando Windows ADK (oscdimg)...
:: ════════════════════════════════════════════════════════════════════
set "OSCDIMG_FOUND=0"
if exist "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe" set "OSCDIMG_FOUND=1"
if exist "C:\Program Files\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe" set "OSCDIMG_FOUND=1"

if "!OSCDIMG_FOUND!"=="1" (
    echo [OK] Windows ADK ja instalado ^(oscdimg encontrado^).
    echo ADK ja instalado >> "%LOG%"
    goto :adk_ok
)

:: Verifica se oscdimg esta embutido no programa
if exist "%~dp0app\resources\tools\oscdimg.exe" (
    echo [OK] oscdimg embutido no programa ^(nao precisa do ADK^).
    goto :adk_ok
)

echo [AVISO] Windows ADK nao encontrado.
echo         O oscdimg esta embutido no programa para uso normal.
echo         Para desenvolvimento/build, instale o ADK:
echo         https://learn.microsoft.com/windows-hardware/get-started/adk-install
echo         ^(Instale apenas "Deployment Tools"^)
echo ADK nao instalado - usar oscdimg embutido >> "%LOG%"
:adk_ok

:: ════════════════════════════════════════════════════════════════════
echo.
echo [6/6] Verificando Git...
:: ════════════════════════════════════════════════════════════════════
where git >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%V in ('git --version 2^>^&1') do set "GIT_VER=%%V"
    echo [OK] Git ja instalado: !GIT_VER!
    goto :git_ok
)

echo [+] Instalando Git via winget...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    winget install Git.Git --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    call :refresh_path
    where git >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Git instalado.
        echo Git instalado OK >> "%LOG%"
    ) else (
        echo [AVISO] Git nao instalado. Baixe em: https://git-scm.com/download/win
    )
) else (
    echo [AVISO] winget nao disponivel. Baixe Git em: https://git-scm.com/download/win
)
:git_ok

:: ════════════════════════════════════════════════════════════════════
echo.
echo ============================================================
echo   RESUMO DA INSTALACAO
echo ============================================================

:: Verificacao final
set "STATUS_PY=[FALTA]" & where python >nul 2>&1 && set "STATUS_PY=[OK]   "
set "STATUS_7Z=[FALTA]" & if exist "C:\Program Files\7-Zip\7z.exe" set "STATUS_7Z=[OK]   "
set "STATUS_7Z2=[FALTA]" & if exist "C:\Program Files (x86)\7-Zip\7z.exe" set "STATUS_7Z2=[OK]   "
if "!STATUS_7Z!"=="[OK]   " set "STATUS_7Z2=[OK]   "
set "STATUS_NS=[FALTA]" & if exist "C:\Program Files (x86)\NSIS\makensis.exe" set "STATUS_NS=[OK]   "
set "STATUS_GT=[FALTA]" & where git >nul 2>&1 && set "STATUS_GT=[OK]   "

echo   !STATUS_PY! Python 3.x
echo   !STATUS_7Z2! 7-Zip
echo   !STATUS_NS! NSIS (para gerar instalador)
echo   !STATUS_GT! Git
echo   [OK]    oscdimg (embutido no programa)
echo   [OK]    DISM (nativo do Windows)
echo.

if %ERROS% gtr 0 (
    echo   [!] %ERROS% erro^(s^) encontrado^(s^). Verifique acima.
) else (
    echo   Ambiente pronto! Execute BUILD_INSTALLER.bat para gerar o Setup.
)

echo.
echo   Log salvo em: %LOG%
echo ============================================================
echo.
pause
goto :EOF

:: ── Funcao: recarregar PATH sem reiniciar ────────────────────────────
:refresh_path
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%B"
set "PATH=!SYS_PATH!;!USR_PATH!"
goto :eof
