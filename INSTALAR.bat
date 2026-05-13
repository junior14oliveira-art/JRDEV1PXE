@echo off
setlocal EnableDelayedExpansion
title WinPE Studio — INSTALADOR
color 0A
cd /d "%~dp0"

echo ============================================================
echo   WinPE Studio Pro — INSTALADOR
echo   Instala o programa e configura o servidor PXE
echo ============================================================
echo.

:: ── Verificar Admin ──────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Elevando para Administrador...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

:: ── Destino da instalacao ─────────────────────────────────────────────
set "INSTALL_DIR=E:\WinPE_Studio"
echo [+] Diretorio de instalacao: %INSTALL_DIR%
echo.

:: Pergunta se quer mudar o destino
set /p "CUSTOM=Pressione ENTER para instalar em %INSTALL_DIR% ou digite outro caminho: "
if not "!CUSTOM!"=="" set "INSTALL_DIR=!CUSTOM!"

:: ── Criar estrutura de pastas ─────────────────────────────────────────
echo.
echo [1/6] Criando estrutura de pastas...
mkdir "%INSTALL_DIR%" >nul 2>&1
mkdir "%INSTALL_DIR%\WinPE_Studio_Workspace" >nul 2>&1
mkdir "%INSTALL_DIR%\logs" >nul 2>&1
mkdir "%INSTALL_DIR%\IMAGENS\IMG" >nul 2>&1
echo [OK] Pastas criadas.

:: ── Copiar programa ───────────────────────────────────────────────────
echo.
echo [2/6] Copiando programa...
xcopy /e /i /y /q "%~dp0*" "%INSTALL_DIR%\" >nul
echo [OK] Programa copiado para %INSTALL_DIR%

:: ── Criar atalho na Area de Trabalho ─────────────────────────────────
echo.
echo [3/6] Criando atalho na Area de Trabalho...
set "SHORTCUT=%PUBLIC%\Desktop\WinPE Studio.lnk"
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%SHORTCUT%'); ^
   $s.TargetPath = '%INSTALL_DIR%\WinPE_Studio.exe'; ^
   $s.WorkingDirectory = '%INSTALL_DIR%'; ^
   $s.Description = 'WinPE Studio Pro'; ^
   $s.Save()" >nul 2>&1
if exist "%SHORTCUT%" (
    echo [OK] Atalho criado: %SHORTCUT%
) else (
    echo [AVISO] Atalho nao criado - crie manualmente se necessario.
)

:: ── Configurar Firewall ───────────────────────────────────────────────
echo.
echo [4/6] Configurando Firewall para PXE...
netsh advfirewall firewall delete rule name="WinPE Studio PXE" >nul 2>&1
netsh advfirewall firewall add rule name="WinPE Studio PXE DHCP"  dir=in action=allow protocol=UDP localport=67   profile=any >nul
netsh advfirewall firewall add rule name="WinPE Studio PXE TFTP"  dir=in action=allow protocol=UDP localport=69   profile=any >nul
netsh advfirewall firewall add rule name="WinPE Studio PXE HTTP"  dir=in action=allow protocol=TCP localport=8080 profile=any >nul
netsh advfirewall firewall add rule name="WinPE Studio SMB"       dir=in action=allow protocol=TCP localport=445  profile=any >nul
echo [OK] Firewall configurado (DHCP/TFTP/HTTP/SMB).

:: ── Configurar compartilhamento SMB ──────────────────────────────────
echo.
echo [5/6] Configurando compartilhamento de imagens (SMB)...
net user ACESSO REDE /add /expires:never /passwordchg:no >nul 2>&1
net user ACESSO REDE >nul 2>&1
net localgroup Administradores ACESSO /add >nul 2>&1
net localgroup Administrators  ACESSO /add >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v "forceguest"            /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v "LimitBlankPasswordUse" /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "LocalAccountTokenFilterPolicy" /t REG_DWORD /d 1 /f >nul
net share IMG /delete >nul 2>&1
net share IMG="%INSTALL_DIR%\IMAGENS\IMG" /grant:ACESSO,FULL /unlimited >nul 2>&1
net share IMG /grant:Everyone,FULL >nul 2>&1
icacls "%INSTALL_DIR%\IMAGENS\IMG" /grant *S-1-1-0:(OI)(CI)F /T /C /Q >nul 2>&1
echo [OK] Compartilhamento IMG configurado.

:: ── Criar atalho GEMINI HOST na area de trabalho ─────────────────────
echo.
echo [6/6] Criando atalhos de suporte...
set "HOST_SHORTCUT=%PUBLIC%\Desktop\GEMINI HOST (Servidor).lnk"
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%HOST_SHORTCUT%'); ^
   $s.TargetPath = '%INSTALL_DIR%\GEMINI_HOST.bat'; ^
   $s.WorkingDirectory = '%INSTALL_DIR%'; ^
   $s.Description = 'Configurar servidor de imagens'; ^
   $s.Save()" >nul 2>&1

:: ── Resultado ─────────────────────────────────────────────────────────
echo.
echo ============================================================
echo   INSTALACAO CONCLUIDA!
echo.
echo   Programa  : %INSTALL_DIR%\WinPE_Studio.exe
echo   Workspace : %INSTALL_DIR%\WinPE_Studio_Workspace\
echo   Imagens   : %INSTALL_DIR%\IMAGENS\IMG\  (compartilhado como \\servidor\IMG)
echo   Atalho    : Area de Trabalho - WinPE Studio
echo.
echo   PROXIMOS PASSOS:
echo   1. Abra o WinPE Studio pelo atalho na Area de Trabalho
echo   2. Va em Inicio e selecione uma ISO WinPE
echo   3. Injete os drivers corporativos em Customizar
echo   4. Inicie o servidor PXE em Rede PXE
echo ============================================================
echo.
pause
