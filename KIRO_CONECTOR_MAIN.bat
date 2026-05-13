@echo off
setlocal EnableDelayedExpansion
title KIRO CONECTOR
color 0E

:: ══════════════════════════════════════════════════════════════════════
::  KIRO CONECTOR - Conecta ao servidor de imagens via SMB
::  Janela NUNCA fecha sozinha - sempre mostra diagnostico
:: ══════════════════════════════════════════════════════════════════════

:: ── Log ──────────────────────────────────────────────────────────────
set "LOGFILE=C:\KIRO_LOG.txt"
if exist "X:\Users\Default\Desktop\" set "LOGFILE=X:\Users\Default\Desktop\KIRO_LOG.txt"
if exist "X:\" if not exist "X:\Users\Default\Desktop\" set "LOGFILE=X:\KIRO_LOG.txt"

echo. > "%LOGFILE%" 2>nul

call :LOG "====== KIRO CONECTOR %DATE% %TIME% ======"
call :LOG "Script: %~f0"
call :LOG "Log: %LOGFILE%"

echo ============================================================
echo   KIRO CONECTOR - SERVIDOR DE IMAGENS
echo   Log: %LOGFILE%
echo ============================================================
echo.

:: ── Configuracao ─────────────────────────────────────────────────────
set "SHARE=IMG"
set "USER=ACESSO"
set "PASS=REDE"
set "IP_FIXO=192.168.0.21"
set "FOUND_IP="
set "DRIVE="

call :LOG "Config: IP_FIXO=%IP_FIXO% SHARE=%SHARE% USER=%USER%"

:: ── Drive livre ───────────────────────────────────────────────────────
for %%D in (Z Y W V U T S R Q P O N M L K J I H G F E D) do (
    if "!DRIVE!"=="" if not exist %%D:\ set "DRIVE=%%D:"
)
if "!DRIVE!"=="" set "DRIVE=Z:"
call :LOG "Drive: %DRIVE%"
echo [+] Drive selecionado: %DRIVE%
echo.

:: ── Aguardar rede ────────────────────────────────────────────────────
echo [+] Aguardando rede inicializar...
set /a W=0
:AGUARDA
set /a W+=1
ipconfig 2>nul | findstr /R "192\.168\. 10\. 172\." >nul && goto :REDE_OK
call :LOG "Aguardando rede [%W%/30]..."
if %W% geq 30 (
    call :LOG "TIMEOUT - continuando sem confirmacao de rede."
    echo [AVISO] Rede nao confirmada. Tentando mesmo assim...
    goto :TENTAR_FIXO
)
timeout /t 2 /nobreak >nul
goto :AGUARDA

:REDE_OK
call :LOG "Rede detectada."
echo [OK] Rede pronta.
echo.

:: ── DIAGNOSTICO DE REDE ───────────────────────────────────────────────
echo ============================================================
echo   DIAGNOSTICO DE REDE
echo ============================================================
echo.
echo [IPCONFIG]:
call :LOG "--- IPCONFIG ---"
ipconfig 2>nul | findstr /i "IPv4 Gateway Subnet"
ipconfig 2>nul | findstr /i "IPv4 Gateway Subnet" >> "%LOGFILE%" 2>nul
echo.

echo [PING ao servidor %IP_FIXO%]:
call :LOG "--- PING %IP_FIXO% ---"
ping -n 2 -w 500 %IP_FIXO% 2>nul
ping -n 2 -w 500 %IP_FIXO% >> "%LOGFILE%" 2>nul
echo.

echo [CONEXOES NET USE ativas]:
call :LOG "--- NET USE ---"
net use 2>nul
net use >> "%LOGFILE%" 2>nul
echo.
echo ============================================================
echo.

:: ── 1. Tentar IP fixo direto ─────────────────────────────────────────
:TENTAR_FIXO
echo [1/3] Tentando IP fixo: \\%IP_FIXO%\%SHARE% ...
call :LOG "Tentativa direta: \\%IP_FIXO%\%SHARE%"

net use %DRIVE% "\\%IP_FIXO%\%SHARE%" %PASS% /user:%USER% /persistent:no >nul 2>&1
set "ERR_FIXO=!errorlevel!"
call :LOG "Resultado IP fixo: !ERR_FIXO!"

if !ERR_FIXO! equ 0 (
    set "FOUND_IP=%IP_FIXO%"
    goto :SUCESSO
)

echo [!] IP fixo falhou (erro !ERR_FIXO!). Detectando redes...
call :LOG "IP fixo falhou com erro !ERR_FIXO!"
echo.

:: ── 2. Detectar redes do notebook ────────────────────────────────────
set "REDES_COUNT=0"

for /f "tokens=2 delims=:" %%A in ('ipconfig 2^>nul ^| findstr /i "IPv4"') do (
    set "IP_RAW=%%A"
    for /f "tokens=1" %%B in ("!IP_RAW!") do set "IP_CLEAN=%%B"
    for /f "tokens=1-3 delims=." %%X in ("!IP_CLEAN!") do (
        set "PREFIXO=%%X.%%Y.%%Z"
        if not "%%X"=="127" if not "%%X.%%Y"=="169.254" (
            set /a REDES_COUNT+=1
            set "REDE_!REDES_COUNT!=!PREFIXO!"
            call :LOG "Rede detectada: !PREFIXO!.x"
            echo [+] Rede detectada: !PREFIXO!.x
        )
    )
)

:: Sempre adiciona a rede do servidor fixo
set "IP_FIXO_BASE=192.168.0"
set "JA_TEM=0"
for /L %%N in (1,1,%REDES_COUNT%) do (
    if "!REDE_%%N!"=="%IP_FIXO_BASE%" set "JA_TEM=1"
)
if !JA_TEM! equ 0 (
    set /a REDES_COUNT+=1
    set "REDE_!REDES_COUNT!=%IP_FIXO_BASE%"
    call :LOG "Adicionando rede do servidor: %IP_FIXO_BASE%.x"
    echo [+] Adicionando rede do servidor: %IP_FIXO_BASE%.x
)

if %REDES_COUNT% equ 0 (
    call :LOG "Nenhuma rede detectada."
    echo [ERRO] Nenhuma rede detectada.
    goto :ERRO_FINAL
)

echo.

:: ── 3. Varrer cada rede ───────────────────────────────────────────────
echo [2/3] Varrendo %REDES_COUNT% rede(s) em busca do servidor...
call :LOG "Varrendo %REDES_COUNT% rede(s)..."
echo.

for /L %%N in (1,1,%REDES_COUNT%) do (
    if "!FOUND_IP!"=="" (
        set "BASE=!REDE_%%N!"
        echo [Rede %%N/%REDES_COUNT%] Varrendo !BASE!.x ...
        call :LOG "Varrendo !BASE!.x"

        :: IPs mais provaveis primeiro (rapido)
        for %%P in (1 21 100 200 254 2 10 50 150) do (
            if "!FOUND_IP!"=="" (
                ping -n 1 -w 200 !BASE!.%%P >nul 2>&1
                if !errorlevel! equ 0 (
                    net use %DRIVE% "\\!BASE!.%%P\%SHARE%" %PASS% /user:%USER% /persistent:no >nul 2>&1
                    if !errorlevel! equ 0 (
                        set "FOUND_IP=!BASE!.%%P"
                        call :LOG "ENCONTRADO (rapido): !BASE!.%%P"
                        goto :SUCESSO
                    )
                )
            )
        )

        :: Varredura completa
        for /L %%i in (1,1,254) do (
            if "!FOUND_IP!"=="" (
                ping -n 1 -w 150 !BASE!.%%i >nul 2>&1
                if !errorlevel! equ 0 (
                    net use %DRIVE% "\\!BASE!.%%i\%SHARE%" %PASS% /user:%USER% /persistent:no >nul 2>&1
                    if !errorlevel! equ 0 (
                        set "FOUND_IP=!BASE!.%%i"
                        call :LOG "ENCONTRADO: !BASE!.%%i"
                        goto :SUCESSO
                    )
                )
                set /a DOT=%%i %% 30
                if !DOT! equ 0 echo|set /p="  .!BASE!.%%i"
            )
        )
        echo.
    )
)

:: ── Erro final com diagnostico completo ──────────────────────────────
:ERRO_FINAL
echo.
echo ============================================================
echo   [ERRO] SERVIDOR NAO ENCONTRADO
echo ============================================================
echo.
call :LOG "FALHA FINAL - executando diagnostico completo..."

echo [DIAGNOSTICO COMPLETO]:
echo.

echo --- Todos os IPs do notebook ---
ipconfig 2>nul | findstr /i "IPv4 Subnet Gateway"
ipconfig 2>nul | findstr /i "IPv4 Subnet Gateway" >> "%LOGFILE%" 2>nul
echo.

echo --- Ping ao servidor %IP_FIXO% ---
ping -n 3 -w 1000 %IP_FIXO%
ping -n 3 -w 1000 %IP_FIXO% >> "%LOGFILE%" 2>nul
echo.

echo --- Teste porta SMB 445 ---
call :LOG "Testando porta 445..."
powershell -NoProfile -Command "try { $t = New-Object Net.Sockets.TcpClient('%IP_FIXO%',445); Write-Host '[OK] Porta 445 ABERTA'; $t.Close() } catch { Write-Host '[ERRO] Porta 445 FECHADA ou inacessivel' }" 2>nul
echo.

echo --- Net use atual ---
net use 2>nul
echo.

echo --- Rotas de rede ---
route print 2>nul | findstr /i "0.0.0.0 192.168"
echo.

echo ============================================================
echo   POSSIVEIS CAUSAS:
echo   1. Servidor nao executou GEMINI_HOST.bat como Admin
echo   2. Firewall bloqueando porta 445
echo   3. Notebook e servidor em redes fisicamente separadas
echo   4. Usuario ACESSO / senha REDE incorretos
echo ============================================================
echo.
call :LOG "FALHA FINAL: servidor nao encontrado."
goto :FIM

:: ── Sucesso ───────────────────────────────────────────────────────────
:SUCESSO
echo.
echo ============================================================
echo   [OK] CONECTADO COM SUCESSO!
echo   %DRIVE% = \\%FOUND_IP%\%SHARE%
echo ============================================================
echo.
call :LOG "SUCESSO: %DRIVE% = \\%FOUND_IP%\%SHARE%"

echo [+] Conteudo da pasta de imagens:
dir %DRIVE%\ /w 2>nul
echo.

:: Abre Explorer
set "EXP="
for %%E in (
    "X:\Windows\System32\explorer.exe"
    "X:\Windows\explorer.exe"
    "C:\Windows\System32\explorer.exe"
    "C:\Windows\explorer.exe"
) do (
    if "!EXP!"=="" if exist %%~E set "EXP=%%~E"
)

if not "!EXP!"=="" (
    echo [+] Abrindo pasta no Explorer...
    start "" "!EXP!" %DRIVE%\
    call :LOG "Explorer aberto: %DRIVE%\"
) else (
    echo [INFO] Abra manualmente: %DRIVE%\
)
call :LOG "FIM OK."

:: ── Fim - janela NUNCA fecha ──────────────────────────────────────────
:FIM
echo.
echo ============================================================
echo   LOG COMPLETO SALVO EM: %LOGFILE%
echo ============================================================
echo.
type "%LOGFILE%" 2>nul
echo.
echo ============================================================
echo   JANELA ABERTA - pressione qualquer tecla para fechar
echo ============================================================
echo.
:LOOP_ABERTO
timeout /t 60 /nobreak >nul 2>&1
echo [ainda aberto - pressione qualquer tecla para fechar]
goto :LOOP_ABERTO

:: ── Funcao LOG ────────────────────────────────────────────────────────
:LOG
echo [%TIME%] %~1
echo [%TIME%] %~1 >> "%LOGFILE%" 2>nul
goto :eof
