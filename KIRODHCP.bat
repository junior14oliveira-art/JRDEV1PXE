@echo off
:: ============================================================
:: KIRODHCP - Conector SMB silencioso para WinPE
:: Inicia servicos de rede, renova DHCP e conecta Z:
:: Roda em segundo plano - para quando conectar
:: ============================================================
setlocal EnableDelayedExpansion

set "SERVER=192.168.0.21"
set "SHARE=IMG"
set "USER=ACESSO"
set "PASS=REDE"
set "DRIVE=Z:"
set "MAX=60"
set "WAIT=10"

:: Log no desktop do WinPE
set "LOG=C:\KIRODHCP.log"
if exist "X:\Users\Default\Desktop\" set "LOG=X:\Users\Default\Desktop\KIRODHCP.log"

echo. > "%LOG%" 2>nul
call :L "====== KIRODHCP %DATE% %TIME% ======"
call :L "Servidor: %SERVER% | Drive: %DRIVE%"

:: Se ja conectado, encerra
if exist "%DRIVE%\" (
    call :L "Drive %DRIVE% ja conectado. Encerrando."
    exit /b 0
)

:: ── STEP 1: Iniciar servicos de rede ─────────────────────────────────
call :L "--- Iniciando servicos de rede ---"
for %%S in (Dhcp LanmanWorkstation Netman nsi ndis MRxSmb20) do (
    sc start %%S >nul 2>&1
    call :L "  sc start %%S"
)
timeout /t 3 /nobreak >nul

:: ── STEP 2: Habilitar adaptadores ────────────────────────────────────
call :L "--- Habilitando adaptadores ---"
for %%I in ("Ethernet" "Ethernet 2" "Ethernet 3" "Local Area Connection" "LAN") do (
    netsh interface set interface %%I enable >nul 2>&1
)
netsh interface show interface >> "%LOG%" 2>nul
timeout /t 2 /nobreak >nul

:: ── STEP 3: Renovar DHCP ─────────────────────────────────────────────
call :L "--- Renovando DHCP ---"
ipconfig /renew >nul 2>&1
timeout /t 5 /nobreak >nul
ipconfig | findstr /i "IPv4" >> "%LOG%" 2>nul

:: ── STEP 4: Loop de conexao ───────────────────────────────────────────
set /a N=0
:LOOP
set /a N+=1
call :L "[%N%/%MAX%] Tentando \\%SERVER%\%SHARE% ..."

:: Verificar se tem IP real
set "TEM_IP=0"
for /f "tokens=2 delims=:" %%A in ('ipconfig 2^>nul ^| findstr /i "IPv4"') do (
    set "IP_RAW=%%A"
    for /f "tokens=1" %%B in ("!IP_RAW!") do (
        echo %%B | findstr /v "169.254" | findstr "192.168. 10. 172." >nul 2>&1
        if !errorlevel! equ 0 set "TEM_IP=1"
    )
)

if "!TEM_IP!"=="0" (
    call :L "  Sem IP valido. Renovando DHCP..."
    ipconfig /renew >nul 2>&1
    timeout /t 5 /nobreak >nul
)

:: Tentar conectar
net use %DRIVE% /delete /yes >nul 2>&1
net use %DRIVE% "\\%SERVER%\%SHARE%" %PASS% /user:%USER% /persistent:no >nul 2>&1
set "ERR=!errorlevel!"

if !ERR! equ 0 (
    call :L "=== SUCESSO: %DRIVE% = \\%SERVER%\%SHARE% ==="
    :: Abrir Explorer
    if exist "X:\Windows\System32\explorer.exe" (
        start "" "X:\Windows\System32\explorer.exe" %DRIVE%\
        call :L "Explorer aberto em %DRIVE%\"
    ) else if exist "C:\Windows\System32\explorer.exe" (
        start "" "C:\Windows\System32\explorer.exe" %DRIVE%\
    )
    call :L "KIRODHCP encerrado com sucesso."
    exit /b 0
)

call :L "  Falhou (erro !ERR!). Aguardando %WAIT%s..."
if !N! geq %MAX% goto :TIMEOUT
timeout /t %WAIT% /nobreak >nul
goto :LOOP

:TIMEOUT
call :L "=== TIMEOUT: nao conectou apos %MAX% tentativas ==="
call :L "Verifique: GEMINI_HOST.bat rodou no servidor %SERVER%?"
exit /b 1

:L
echo [%TIME%] %~1
echo [%TIME%] %~1 >> "%LOG%" 2>nul
goto :eof
