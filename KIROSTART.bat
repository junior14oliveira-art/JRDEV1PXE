@echo off
title JRDEV1 PXE — Instalacao e Inicializacao
color 0A
echo.
echo ============================================================
echo   JRDEV1 PXE — WinPE Studio Pro
echo   Instalacao automatica de dependencias
echo ============================================================
echo.

cd /d "%~dp0"

:: ── Verifica Admin ────────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Executando sem privilegios de administrador.
    echo         Algumas funcoes podem nao funcionar corretamente.
    echo         Recomendado: clique com botao direito e "Executar como administrador"
    echo.
    timeout /t 3 /nobreak >nul
)

:: ── Verifica se o exe compilado existe ───────────────────────────────
if exist "dist\JRDEV1_PXE\JRDEV1_PXE.exe" (
    echo [OK] Executavel encontrado. Iniciando...
    start "" "dist\JRDEV1_PXE\JRDEV1_PXE.exe"
    exit /b 0
)

echo [INFO] Executavel nao encontrado. Verificando Python...
echo.

:: ── Verifica Python ───────────────────────────────────────────────────
set "PYTHON="

:: Tenta Python oficial em C:\Python313
if exist "C:\Python313\python.exe" (
    set "PYTHON=C:\Python313\python.exe"
    echo [OK] Python encontrado em C:\Python313
    goto :PYTHON_FOUND
)

:: Tenta Python do PATH
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('where python') do (
        set "PYTHON=%%i"
        goto :PYTHON_FOUND
    )
)

:: Python nao encontrado — baixa e instala
echo [INFO] Python nao encontrado. Baixando Python 3.13...
echo.
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe' -OutFile 'C:\Temp\python-3.13.3-amd64.exe' -UseBasicParsing"
if not exist "C:\Temp\python-3.13.3-amd64.exe" (
    echo [ERRO] Falha ao baixar Python. Verifique a conexao com a internet.
    echo        Baixe manualmente em: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [INFO] Instalando Python 3.13...
start /wait "C:\Temp\python-3.13.3-amd64.exe" /quiet InstallAllUsers=0 TargetDir=C:\Python313 PrependPath=0 Include_test=0
set "PYTHON=C:\Python313\python.exe"
echo [OK] Python instalado em C:\Python313

:PYTHON_FOUND
echo [OK] Usando Python: %PYTHON%
echo.

:: ── Instala dependencias Python ───────────────────────────────────────
echo [1/4] Instalando dependencias Python...
%PYTHON% -m pip install --upgrade pip --quiet 2>nul
%PYTHON% -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [AVISO] Algumas dependencias podem nao ter instalado corretamente.
    echo         Tentando instalar individualmente...
    %PYTHON% -m pip install PySide6 loguru pydantic requests pywin32 wmi --quiet
)
echo [OK] Dependencias Python instaladas.
echo.

:: ── Verifica 7-Zip ────────────────────────────────────────────────────
echo [2/4] Verificando 7-Zip...
if exist "C:\Program Files\7-Zip\7z.exe" (
    echo [OK] 7-Zip ja instalado.
    goto :7ZIP_OK
)
if exist "app\resources\tools\7z.exe" (
    echo [OK] 7-Zip embutido encontrado.
    goto :7ZIP_OK
)
echo [INFO] Baixando 7-Zip...
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.7-zip.org/a/7z2408-x64.exe' -OutFile 'C:\Temp\7z-setup.exe' -UseBasicParsing" 2>nul
if exist "C:\Temp\7z-setup.exe" (
    start /wait "C:\Temp\7z-setup.exe" /S
    echo [OK] 7-Zip instalado.
) else (
    echo [AVISO] Nao foi possivel baixar o 7-Zip automaticamente.
    echo         Instale manualmente em: https://www.7-zip.org/
)
:7ZIP_OK
echo.

:: ── Verifica Windows ADK (oscdimg) ────────────────────────────────────
echo [3/4] Verificando Windows ADK (oscdimg)...
if exist "app\resources\tools\oscdimg.exe" (
    echo [OK] oscdimg embutido encontrado.
    goto :ADK_OK
)
set "ADK_PATH=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe"
if exist "%ADK_PATH%" (
    echo [OK] Windows ADK ja instalado.
    goto :ADK_OK
)
echo [AVISO] oscdimg nao encontrado.
echo         Para gerar ISOs, instale o Windows ADK:
echo         https://learn.microsoft.com/windows-hardware/get-started/adk-install
echo         (Selecione apenas "Deployment Tools")
:ADK_OK
echo.

:: ── Inicia o programa ─────────────────────────────────────────────────
echo [4/4] Iniciando JRDEV1 PXE...
echo.

:: Tenta iniciar via Python diretamente
%PYTHON% -m app.main
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao iniciar o programa.
    echo        Verifique se todas as dependencias foram instaladas.
    echo        Tente executar como Administrador.
    pause
    exit /b 1
)

exit /b 0
