@echo off
setlocal EnableDelayedExpansion
title GEMINI HOST - SERVIDOR DE IMAGENS
color 0B

:: ── VERIFICAR ADMINISTRADOR ───────────────────────────────────────────
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [!] EXECUTE COMO ADMINISTRADOR!
    echo     Clique direito no arquivo e escolha "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo ============================================================
echo   GEMINI HOST - CONFIGURANDO SERVIDOR DE IMAGENS
echo ============================================================
echo.

:: ── 1. CRIAR USUARIO ACESSO ───────────────────────────────────────────
echo [+] Criando usuario 'ACESSO' (senha: REDE)...
net user ACESSO REDE /add /expires:never /passwordchg:no /comment:"GEMINI PXE" >nul 2>&1
:: Se ja existe, apenas atualiza a senha
net user ACESSO REDE >nul 2>&1
:: Adiciona ao grupo Administradores (tenta PT e EN para compatibilidade)
net localgroup Administradores ACESSO /add >nul 2>&1
net localgroup Administrators  ACESSO /add >nul 2>&1
echo    OK.

:: ── 2. REGISTROS LSA/UAC ─────────────────────────────────────────────
echo [+] Configurando registros de acesso remoto...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v "forceguest"             /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v "LimitBlankPasswordUse"  /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "LocalAccountTokenFilterPolicy" /t REG_DWORD /d 1 /f >nul
echo    OK.

:: ── 3. POLITICA DE LOGON DE REDE (secedit) ───────────────────────────
:: IMPORTANTE: secedit no Win10/11 exige UTF-16 LE — usar PowerShell para gerar o .inf
echo [+] Aplicando politica de logon de rede...
set "SEC_INF=%temp%\gemini_sec.inf"
set "SEC_DB=%temp%\gemini_sec.sdb"

if exist "%SEC_INF%" del /f /q "%SEC_INF%" >nul 2>&1
if exist "%SEC_DB%"  del /f /q "%SEC_DB%"  >nul 2>&1

:: Gera o .inf em UTF-16 LE via PowerShell (unico formato aceito pelo secedit)
powershell -NoProfile -Command ^
  "$content = \"[Unicode]`r`nUnicode=yes`r`n[Version]`r`nsignature=`\"`$CHICAGO`$`\"`r`nRevision=1`r`n[Privilege Rights]`r`nSeNetworkLogonRight = *S-1-1-0,ACESSO,Guest`r`nSeDenyNetworkLogonRight = `r`n\"; [System.IO.File]::WriteAllText('%SEC_INF%', $content, [System.Text.Encoding]::Unicode)"

if exist "%SEC_INF%" (
    secedit /configure /db "%SEC_DB%" /cfg "%SEC_INF%" /areas USER_RIGHTS /quiet >nul 2>&1
    echo    OK.
) else (
    echo    [AVISO] Nao foi possivel gerar politica via secedit. Continuando...
)

:: ── 4. COMPARTILHAMENTO SMB ───────────────────────────────────────────
echo [+] Configurando compartilhamento 'IMG'...
set "FOLDER=E:\IMAGENS\IMG"

if not exist "%FOLDER%" (
    echo    [INFO] Pasta nao existe. Criando: %FOLDER%
    mkdir "%FOLDER%" >nul 2>&1
    if %errorlevel% neq 0 (
        echo    [ERRO] Nao foi possivel criar a pasta %FOLDER%
        echo    Verifique se o disco E: existe e tem espaco.
        goto :ERRO_FATAL
    )
)

:: Remove share anterior sem derrubar o LanmanServer
net share IMG /delete >nul 2>&1
timeout /t 1 /nobreak >nul

:: Cria o share
net share IMG="%FOLDER%" /grant:ACESSO,FULL /unlimited >nul 2>&1
if %errorlevel% neq 0 (
    echo    [ERRO] Falha ao criar share IMG.
    goto :ERRO_FATAL
)

:: Grants adicionais (sem repetir o caminho)
net share IMG /grant:Everyone,FULL >nul 2>&1
net share IMG /grant:Todos,FULL    >nul 2>&1

:: Permissoes NTFS por SID (funciona em qualquer idioma do Windows)
icacls "%FOLDER%" /grant *S-1-1-0:(OI)(CI)F /T /C /Q >nul 2>&1
icacls "%FOLDER%" /grant ACESSO:(OI)(CI)F    /T /C /Q >nul 2>&1
echo    OK.

:: ── 5. FIREWALL ───────────────────────────────────────────────────────
echo [+] Abrindo porta 445 (SMB) no Firewall...
netsh advfirewall firewall add rule name="GEMINI SMB" dir=in action=allow protocol=TCP localport=445 profile=any >nul 2>&1
echo    OK.

:: ── 6. GARANTIR QUE O LANMANSERVER ESTA RODANDO ──────────────────────
:: NAO reinicia se ja estiver rodando (evita derrubar conexoes ativas)
echo [+] Verificando servico de compartilhamento...
sc query LanmanServer | findstr /i "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [OK] LanmanServer ja esta rodando. Nenhuma interrupcao necessaria.
) else (
    echo    [INFO] Iniciando LanmanServer...
    net start LanmanServer >nul 2>&1
    echo    OK.
)

:: ── RESULTADO FINAL ───────────────────────────────────────────────────
echo.
echo ============================================================
echo   VERIFICACAO FINAL
echo ============================================================
net share IMG
echo.
echo ============================================================
echo   SERVIDOR PRONTO!
echo.
echo   Pasta compartilhada : %FOLDER%
echo   Acesso pela rede    : \\%COMPUTERNAME%\IMG
echo   Usuario             : ACESSO
echo   Senha               : REDE
echo.
echo   Execute GEMINI_CONECTOR.bat no WinPE para conectar.
echo ============================================================
echo.
pause
exit /b 0

:ERRO_FATAL
echo.
echo ============================================================
echo   [ERRO FATAL] Configuracao incompleta.
echo   Corrija os erros acima e execute novamente.
echo ============================================================
echo.
pause
exit /b 1
