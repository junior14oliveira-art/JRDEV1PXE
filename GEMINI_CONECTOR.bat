@echo off
setlocal EnableDelayedExpansion
title GEMINI CONECTOR
color 0E

:: Auto-relanca com cmd /k para a janela nao fechar (duplo clique no Explorer++)
:: No WinPE o cmd.exe fica em X:\Windows\System32\cmd.exe
if "%1"=="__RUNNING__" goto :MAIN

:: Tenta o cmd do WinPE primeiro, depois o padrao
if exist "X:\Windows\System32\cmd.exe" (
    "X:\Windows\System32\cmd.exe" /k "%~f0" __RUNNING__
) else (
    cmd /k "%~f0" __RUNNING__
)
exit /b

:MAIN

:: Log em arquivo para debug
:: No WinPE o Desktop fica em X:\Users\Default\Desktop ou X:\Windows\System32
if exist "X:\Users\Default\Desktop\" (
    set "LOGFILE=X:\Users\Default\Desktop\GEMINI_LOG.txt"
) else if exist "X:\" (
    set "LOGFILE=X:\GEMINI_LOG.txt"
) else (
    set "LOGFILE=%~dp0GEMINI_CONECTOR_LOG.txt"
)
echo. > "%LOGFILE%"
call :LOG "====== GEMINI CONECTOR - %DATE% %TIME% ======"
call :LOG "Script: %~f0"
call :LOG "Logfile: %LOGFILE%"

echo ============================================================
echo   GEMINI CONECTOR - BUSCA DE SERVIDOR DE IMAGENS
echo ============================================================
echo.

set "SHARE_NAME=IMG"
set "USER=ACESSO"
set "PASS=REDE"
set "IP_FIXO=192.168.0.21"
set "IP_BASE=192.168.0"
set "FOUND_IP="

call :LOG "SHARE_NAME=%SHARE_NAME% IP_FIXO=%IP_FIXO%"

:: Detecta primeira letra de drive livre (evita conflito com X: do WinPE)
set "DRIVE="
for %%D in (Z Y W V U T S R Q P O N M L K J I H G F E D) do (
    if "!DRIVE!"=="" (
        subst %%D: >nul 2>&1
        if !errorlevel! neq 0 (
            if not exist %%D:\ (
                set "DRIVE=%%D:"
            )
        ) else (
            subst %%D: /d >nul 2>&1
        )
    )
)
if "!DRIVE!"=="" set "DRIVE=Z:"
call :LOG "Drive selecionado: !DRIVE!"
echo [+] Drive selecionado: !DRIVE!

:: ── 1. AGUARDAR REDE SUBIR ────────────────────────────────────────────
echo [+] Aguardando rede inicializar...
call :LOG "Aguardando rede..."
set /a WAIT=0
:WAIT_NET
ipconfig 2>nul | findstr /r "192\.168\. 10\. 172\." >nul 2>&1
if %errorlevel% neq 0 (
    set /a WAIT+=1
    call :LOG "Rede nao pronta, tentativa !WAIT!/15"
    if !WAIT! geq 15 (
        call :LOG "AVISO: Rede nao detectada apos 30s"
        echo [AVISO] Rede nao detectada apos 30s. Continuando mesmo assim...
        goto TENTA_FIXO
    )
    timeout /t 2 /nobreak >nul
    goto WAIT_NET
)
call :LOG "Rede pronta."
echo [OK] Rede pronta.
echo.

:: ── 2. TENTA IP FIXO PRIMEIRO ─────────────────────────────────────────
:TENTA_FIXO
echo [+] Testando servidor em %IP_FIXO%...
call :LOG "Testando IP fixo: %IP_FIXO%"

net use %DRIVE% "\\%IP_FIXO%\%SHARE_NAME%" %PASS% /user:%USER% /persistent:no >nul 2>&1
set "ERR=%errorlevel%"
call :LOG "net use resultado: %ERR%"
if %ERR% equ 0 (
    echo [OK] Servidor encontrado em %IP_FIXO%.
    set "FOUND_IP=%IP_FIXO%"
    goto SUCESSO
)

:: ── 3. BUSCA AUTOMATICA ───────────────────────────────────────────────
echo [!] Nao conectou em %IP_FIXO%. Iniciando busca na rede...
echo [+] Testando %IP_BASE%.1 ate %IP_BASE%.254 ...
echo [+] Aguarde (pode levar ate 2 minutos)...
echo.

for /L %%i in (1,1,254) do (
    if not "%IP_BASE%.%%i"=="%IP_FIXO%" (
        :: Ping rapido para nao perder tempo em IPs mortos
        ping -n 1 -w 150 %IP_BASE%.%%i >nul 2>&1
        if !errorlevel! equ 0 (
            :: Tenta montar direto — unico metodo confiavel no WinPE
            net use %DRIVE% "\\%IP_BASE%.%%i\%SHARE_NAME%" %PASS% /user:%USER% /persistent:no >nul 2>&1
            if !errorlevel! equ 0 (
                echo [OK] Servidor encontrado em: %IP_BASE%.%%i
                set "FOUND_IP=%IP_BASE%.%%i"
                goto SUCESSO
            )
        )
        :: Progresso visual
        set /a DOT=%%i %% 20
        if !DOT! equ 0 echo|set /p="."
    )
)

:: ── 4. NAO ENCONTROU ──────────────────────────────────────────────────
echo.
echo.
echo ============================================================
echo   [ERRO] SERVIDOR NAO ENCONTRADO
echo ============================================================
echo.
echo Verifique no servidor (192.168.0.21):
echo   1. GEMINI_HOST.bat foi executado como Administrador
echo   2. Share 'IMG' esta ativo  (net share IMG)
echo   3. Usuario 'ACESSO' existe (net user ACESSO)
echo   4. Firewall permite porta 445 TCP
echo.
call :LOG "ERRO: Servidor nao encontrado"
call :LOG "Log salvo em: %LOGFILE%"
echo Log de diagnostico salvo em:
echo %LOGFILE%
echo.
pause
exit /b 1

:: ── 5. SUCESSO ────────────────────────────────────────────────────────
:SUCESSO
echo.
echo ============================================================
echo   [OK] CONECTADO!
echo   Drive %DRIVE% = \\%FOUND_IP%\%SHARE_NAME%
echo ============================================================
echo.
call :LOG "SUCESSO: conectado em \\%FOUND_IP%\%SHARE_NAME% como %DRIVE%"

:: Lista o conteudo para confirmar que esta acessivel
echo [+] Conteudo da pasta de imagens:
dir %DRIVE%\ /w 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Pasta vazia ou sem permissao de leitura.
)

echo.
:: Abre o Explorer — tenta caminhos conhecidos no WinPE e no Windows normal
set "EXPLORER_EXE="
for %%E in (
    "X:\Windows\System32\explorer.exe"
    "X:\Windows\explorer.exe"
    "C:\Windows\System32\explorer.exe"
    "Explorer++.exe"
    "Explorer++\Explorer++.exe"
) do (
    if "!EXPLORER_EXE!"=="" (
        if exist %%~E set "EXPLORER_EXE=%%~E"
    )
)
:: Fallback: tenta via where
if "!EXPLORER_EXE!"=="" (
    for /f "delims=" %%F in ('where explorer.exe 2^>nul') do (
        if "!EXPLORER_EXE!"=="" set "EXPLORER_EXE=%%F"
    )
)

if not "!EXPLORER_EXE!"=="" (
    echo [+] Abrindo !EXPLORER_EXE!...
    start "" "!EXPLORER_EXE!" %DRIVE%\
) else (
    echo [INFO] Explorer nao encontrado.
    echo [INFO] Drive mapeado: %DRIVE%\ — abra manualmente no seu gerenciador de arquivos.
)

echo.
pause
exit /b 0

:: ── FUNCAO DE LOG ─────────────────────────────────────────────────────
:LOG
echo [%TIME%] %~1 >> "%LOGFILE%"
goto :eof
