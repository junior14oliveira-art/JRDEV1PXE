@echo off
setlocal EnableDelayedExpansion
title KIRO SMB - JANELA ABERTA
color 0A

:: =====================================================================
:: KIRO SMB - Conecta pasta de imagens do servidor
:: Esta janela NUNCA fecha sozinha
:: =====================================================================

set "IP=192.168.0.21"
set "SHARE=IMG"
set "USER=ACESSO"
set "PASS=REDE"
set "DRIVE=Z:"

:: Log no desktop do WinPE ou C:\
set "LOG=C:\KIRO_SMB_LOG.txt"
if exist "X:\Users\Default\Desktop\" set "LOG=X:\Users\Default\Desktop\KIRO_SMB_LOG.txt"

echo. > "%LOG%" 2>nul

echo ============================================================
echo   KIRO SMB CONECTOR
echo   %DATE% %TIME%
echo ============================================================
echo.
echo [LOG] %LOG%
echo.

:: ── STEP 1: Mostrar IP do notebook ───────────────────────────────────
echo [STEP 1] IP do notebook:
echo ----------------------------------------
ipconfig | findstr /i "IPv4 Subnet Gateway"
echo ----------------------------------------
echo.
ipconfig | findstr /i "IPv4 Subnet Gateway" >> "%LOG%" 2>nul

:: ── STEP 2: Ping ao servidor ─────────────────────────────────────────
echo [STEP 2] Ping ao servidor %IP%:
echo ----------------------------------------
ping -n 3 -w 1000 %IP%
ping -n 3 -w 1000 %IP% >> "%LOG%" 2>nul
echo ----------------------------------------
echo.

:: ── STEP 3: Testar porta 445 ─────────────────────────────────────────
echo [STEP 3] Testando porta SMB 445 em %IP%:
echo ----------------------------------------
powershell -NoProfile -Command "try{$c=New-Object Net.Sockets.TcpClient('%IP%',445);Write-Host 'PORTA 445: ABERTA - SMB acessivel';$c.Close()}catch{Write-Host 'PORTA 445: FECHADA - firewall ou servidor offline'}" 2>nul
if %errorlevel% neq 0 echo PORTA 445: PowerShell indisponivel - teste manual necessario
echo ----------------------------------------
echo.

:: ── STEP 4: Limpar conexao anterior ──────────────────────────────────
echo [STEP 4] Limpando conexao anterior em %DRIVE%...
net use %DRIVE% /delete /yes >nul 2>&1
echo OK.
echo.

:: ── STEP 5: Conectar ─────────────────────────────────────────────────
echo [STEP 5] Conectando \\%IP%\%SHARE% como %USER% ...
echo ----------------------------------------
net use %DRIVE% "\\%IP%\%SHARE%" %PASS% /user:%USER% /persistent:no
set "ERRO=%errorlevel%"
echo ----------------------------------------
echo.
echo [RESULTADO] Codigo de erro: %ERRO%
echo.

if %ERRO% equ 0 goto :SUCESSO

:: ── STEP 6: Falhou - mostrar diagnostico ─────────────────────────────
echo ============================================================
echo   [FALHOU] Codigo %ERRO% - Diagnostico:
echo ============================================================
echo.

if %ERRO% equ 53  echo ERRO 53  = Host nao encontrado - servidor offline ou rede diferente
if %ERRO% equ 67  echo ERRO 67  = Nome de rede nao encontrado - share IMG nao existe
if %ERRO% equ 86  echo ERRO 86  = Senha incorreta - verifique PASS=REDE
if %ERRO% equ 1219 echo ERRO 1219 = Conflito de credenciais - ja conectado com outro usuario
if %ERRO% equ 1326 echo ERRO 1326 = Usuario ou senha invalidos
if %ERRO% equ 1231 echo ERRO 1231 = Rede inacessivel - sub-redes diferentes sem rota
if %ERRO% equ 2    echo ERRO 2    = Arquivo nao encontrado - share nao existe
echo.

echo [IPCONFIG COMPLETO]:
ipconfig
echo.

echo [NET USE ATIVO]:
net use
echo.

echo [ROTAS]:
route print | findstr "0.0.0.0"
echo.

echo ============================================================
echo   VERIFIQUE NO SERVIDOR (192.168.0.21):
echo   1. Execute GEMINI_HOST.bat como Administrador
echo   2. Confirme: net share  (deve listar IMG)
echo   3. Firewall porta 445 TCP liberada
echo   4. Mesmo switch/roteador que o notebook
echo ============================================================
echo.
goto :FIM

:SUCESSO
echo ============================================================
echo   [OK] CONECTADO!  %DRIVE% = \\%IP%\%SHARE%
echo ============================================================
echo.
echo [Conteudo de %DRIVE%\]:
dir %DRIVE%\ /w 2>nul
echo.

:: Abre Explorer
for %%E in (
    "X:\Windows\System32\explorer.exe"
    "X:\Windows\explorer.exe"
    "C:\Windows\System32\explorer.exe"
) do (
    if exist %%~E (
        echo [+] Abrindo Explorer...
        start "" %%~E %DRIVE%\
        goto :FIM
    )
)
echo [INFO] Abra manualmente: %DRIVE%\

:FIM
echo.
echo ============================================================
echo   FIM - JANELA PERMANECE ABERTA
echo   Feche esta janela manualmente quando quiser
echo ============================================================
echo.
echo Salvando log em %LOG%...
echo ====== FIM %DATE% %TIME% ====== >> "%LOG%" 2>nul

:KEEPOPEN
echo.
set /p "DUMMY=Pressione ENTER para fechar (ou feche a janela): "
goto :KEEPOPEN
