@echo off
setlocal EnableDelayedExpansion
title KIRO - Injetar Driver de Rede no WinPE
color 0B

:: =====================================================================
:: Injeta driver Intel I219-LM no boot.wim para Dell Latitude 5420
:: Requer: DISM, pasta do driver Intel extraida
:: =====================================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Execute como Administrador!
    pause & exit /b 1
)

set "LOGFILE=%~dp0INJETAR_LOG.txt"
echo. > "%LOGFILE%"
call :L "====== INJETAR DRIVER REDE %DATE% %TIME% ======"

:: ── Limpar mounts travados do DISM ───────────────────────────────────
echo [+] Verificando mounts DISM travados...
dism /Cleanup-Wim >nul 2>&1
call :L "Cleanup-Wim executado."

:: ── Configuracoes ─────────────────────────────────────────────────────
set "SDI_LAN_INTEL=E:\snappidriver\SDI\Drivers\DP_LAN_Intel_26044.7z"
set "EXTRACT_DIR=C:\KIRO_Driver_Intel_Temp"
set "MOUNT_DIR=C:\WinPE_Mount_Temp"
set "WIM="
set "DRIVER_DIR="

:: Lista os boot.wim disponiveis e pede para escolher
echo.
echo [+] boot.wim encontrados no workspace:
echo.
set /a COUNT=0
for /d %%D in ("E:\WinPE_Studio_Workspace\*") do (
    if exist "%%D\sources\boot.wim" (
        set /a COUNT+=1
        set "WIM_!COUNT!=%%D\sources\boot.wim"
        echo   [!COUNT!] %%D\sources\boot.wim
    )
    if exist "%%D\SOURCES\BOOT.WIM" (
        set /a COUNT+=1
        set "WIM_!COUNT!=%%D\SOURCES\BOOT.WIM"
        echo   [!COUNT!] %%D\SOURCES\BOOT.WIM
    )
)

if %COUNT% equ 0 (
    echo [!] Nenhum boot.wim encontrado automaticamente.
    echo     Informe o caminho completo:
    set /p "WIM=Caminho do boot.wim: "
    goto :VALIDA_WIM
)

echo.
set /p "ESCOLHA=Escolha o numero (ou pressione ENTER para o ultimo [%COUNT%]): "
if "!ESCOLHA!"=="" set "ESCOLHA=%COUNT%"
set "WIM=!WIM_%ESCOLHA%!"

echo ============================================================
echo   KIRO - INJETAR DRIVER INTEL I219-LM NO WINPE
echo ============================================================
echo.

:VALIDA_WIM
:: ── Validar WIM ───────────────────────────────────────────────────────
if "!WIM!"=="" (
    echo [!] boot.wim nao encontrado automaticamente.
    echo     Informe o caminho completo do boot.wim:
    set /p "WIM=Caminho: "
)
if not exist "!WIM!" (
    call :L "ERRO: boot.wim nao encontrado: !WIM!"
    echo [ERRO] Arquivo nao encontrado: !WIM!
    goto :FIM_ERRO
)
call :L "WIM: !WIM!"
echo [OK] boot.wim: !WIM!

:: ── Validar Driver — extrai do SDI se necessario ─────────────────────
if "!DRIVER_DIR!"=="" (
    echo [+] Extraindo driver Intel do Snappy Driver Pack...
    call :L "Extraindo: %SDI_LAN_INTEL%"

    if not exist "%SDI_LAN_INTEL%" (
        call :L "ERRO: Arquivo SDI nao encontrado: %SDI_LAN_INTEL%"
        echo [ERRO] Arquivo nao encontrado: %SDI_LAN_INTEL%
        goto :FIM_ERRO
    )

    :: Usa o 7-Zip para extrair
    set "SEVENZIP="
    for %%Z in ("C:\Program Files\7-Zip\7z.exe" "C:\Program Files (x86)\7-Zip\7z.exe") do (
        if "!SEVENZIP!"=="" if exist %%~Z set "SEVENZIP=%%~Z"
    )
    if "!SEVENZIP!"=="" (
        call :L "ERRO: 7-Zip nao encontrado"
        echo [ERRO] 7-Zip nao encontrado. Instale em C:\Program Files\7-Zip\
        goto :FIM_ERRO
    )

    if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%" >nul 2>&1
    mkdir "%EXTRACT_DIR%"
    "!SEVENZIP!" x "%SDI_LAN_INTEL%" -o"%EXTRACT_DIR%" -y >nul 2>&1
    call :L "Extracao concluida."

    :: Procura o .inf do I219 dentro do extraido
    for /r "%EXTRACT_DIR%" %%F in (e1d68x64.inf e1d65x64.inf e1d62x64.inf) do (
        if "!DRIVER_DIR!"=="" if exist "%%F" set "DRIVER_DIR=%%~dpF"
    )

    if "!DRIVER_DIR!"=="" (
        call :L "ERRO: .inf Intel nao encontrado no pacote SDI"
        echo [ERRO] Driver Intel nao encontrado dentro do pacote SDI.
        echo        Arquivos extraidos em: %EXTRACT_DIR%
        goto :FIM_ERRO
    )
)
call :L "Driver dir: !DRIVER_DIR!"
echo [OK] Driver: !DRIVER_DIR!

:: ── Criar pasta de montagem ───────────────────────────────────────────
echo.
echo [+] Preparando pasta de montagem...
if exist "%MOUNT_DIR%" (
    dism /Unmount-Image /MountDir:"%MOUNT_DIR%" /Discard >nul 2>&1
    rmdir /s /q "%MOUNT_DIR%" >nul 2>&1
)
mkdir "%MOUNT_DIR%"
call :L "Mount dir: %MOUNT_DIR%"

:: ── Montar WIM ────────────────────────────────────────────────────────
echo [+] Montando boot.wim (pode demorar 1-2 min)...
call :L "Montando WIM..."
dism /Mount-Image /ImageFile:"!WIM!" /Index:1 /MountDir:"%MOUNT_DIR%"
if %errorlevel% neq 0 (
    call :L "ERRO: Falha ao montar WIM"
    echo [ERRO] Falha ao montar o boot.wim
    goto :FIM_ERRO
)
call :L "WIM montado OK."
echo [OK] WIM montado.

:: ── Injetar driver ────────────────────────────────────────────────────
echo [+] Injetando driver Intel I219-LM...
call :L "Injetando driver..."
dism /Image:"%MOUNT_DIR%" /Add-Driver /Driver:"!DRIVER_DIR!\e1d68x64.inf" /ForceUnsigned
set "DISM_ERR=%errorlevel%"
call :L "DISM Add-Driver resultado: %DISM_ERR%"

if %DISM_ERR% neq 0 (
    echo [AVISO] Tentando com /Recurse na pasta pai...
    dism /Image:"%MOUNT_DIR%" /Add-Driver /Driver:"!DRIVER_DIR!" /Recurse /ForceUnsigned
    set "DISM_ERR=%errorlevel%"
    call :L "DISM Recurse resultado: %DISM_ERR%"
)

if %DISM_ERR% neq 0 (
    call :L "ERRO: Falha ao injetar driver"
    echo [ERRO] Falha ao injetar driver. Desmontando sem salvar...
    dism /Unmount-Image /MountDir:"%MOUNT_DIR%" /Discard
    goto :FIM_ERRO
)
echo [OK] Driver injetado com sucesso.

:: ── Verificar driver injetado ─────────────────────────────────────────
echo [+] Verificando drivers no WIM:
dism /Image:"%MOUNT_DIR%" /Get-Drivers | findstr /i "intel\|e1d\|I219"
call :L "Verificacao de drivers concluida."

:: ── Desmontar e salvar ────────────────────────────────────────────────
echo.
echo [+] Salvando alteracoes no boot.wim (pode demorar 2-3 min)...
call :L "Desmontando e salvando..."
dism /Unmount-Image /MountDir:"%MOUNT_DIR%" /Commit
if %errorlevel% neq 0 (
    call :L "ERRO: Falha ao salvar WIM"
    echo [ERRO] Falha ao salvar. Tentando descartar...
    dism /Unmount-Image /MountDir:"%MOUNT_DIR%" /Discard
    goto :FIM_ERRO
)
call :L "WIM salvo com sucesso."
echo [OK] boot.wim atualizado com driver de rede!

:: ── Limpeza ───────────────────────────────────────────────────────────
rmdir /s /q "%MOUNT_DIR%" >nul 2>&1
rmdir /s /q "%EXTRACT_DIR%" >nul 2>&1

echo.
echo ============================================================
echo   [SUCESSO] Driver Intel I219-LM injetado!
echo.
echo   Proximo passo:
echo   1. Abra o WinPE Studio
echo   2. Va em "Gerar ISO" e gere a nova ISO
echo   3. Suba via PXE e teste a rede
echo ============================================================
call :L "CONCLUIDO COM SUCESSO."
goto :FIM

:FIM_ERRO
echo.
echo ============================================================
echo   [ERRO] Processo falhou. Veja o log:
echo   %LOGFILE%
echo ============================================================
call :L "PROCESSO FALHOU."

:FIM
echo.
type "%LOGFILE%"
echo.
pause
exit /b

:L
echo [%TIME%] %~1
echo [%TIME%] %~1 >> "%LOGFILE%"
goto :eof
