@echo off
setlocal EnableDelayedExpansion
title KIRO DIAGNOSTICO
color 0A

set "LOGFILE=C:\KIRO_DIAG.txt"
if exist "X:\Users\Default\Desktop\" set "LOGFILE=X:\Users\Default\Desktop\KIRO_DIAG.txt"

echo. > "%LOGFILE%"
call :L "====== KIRO DIAGNOSTICO %DATE% %TIME% ======"
echo.

:: ── Sistema ───────────────────────────────────────────────────────────
call :L "--- SISTEMA ---"
call :L "ComputerName: %COMPUTERNAME%"
call :L "Drives existentes:"
for %%D in (C D E X Y Z) do (
    if exist %%D:\ call :L "  %%D:\ existe"
)

:: ── Estado das placas de rede ─────────────────────────────────────────
call :L "--- PLACAS DE REDE (ipconfig /all) ---"
ipconfig /all 2>nul
ipconfig /all >> "%LOGFILE%" 2>nul

:: ── Servicos de rede no WinPE ─────────────────────────────────────────
call :L "--- SERVICOS DE REDE ---"
sc query Dhcp    2>nul | findstr "STATE"
sc query Dhcp    >> "%LOGFILE%" 2>nul
sc query Netman  2>nul | findstr "STATE"
sc query Netman  >> "%LOGFILE%" 2>nul
sc query Dnscache 2>nul | findstr "STATE"
sc query Dnscache >> "%LOGFILE%" 2>nul
sc query LanmanWorkstation 2>nul | findstr "STATE"
sc query LanmanWorkstation >> "%LOGFILE%" 2>nul

:: ── Tenta iniciar DHCP se parado ──────────────────────────────────────
call :L "--- TENTANDO INICIAR DHCP ---"
sc start Dhcp >nul 2>&1
sc start LanmanWorkstation >nul 2>&1
sc start Netman >nul 2>&1
timeout /t 3 /nobreak >nul

:: ── Tenta renovar IP via DHCP ─────────────────────────────────────────
call :L "--- RENOVANDO IP (ipconfig /renew) ---"
ipconfig /renew 2>nul
ipconfig /renew >> "%LOGFILE%" 2>nul
timeout /t 5 /nobreak >nul

:: ── IP apos renovacao ─────────────────────────────────────────────────
call :L "--- IP APOS RENOVACAO ---"
ipconfig 2>nul
ipconfig >> "%LOGFILE%" 2>nul

:: ── Ping ──────────────────────────────────────────────────────────────
call :L "--- PING 192.168.0.21 ---"
ping -n 3 192.168.0.21 2>nul
ping -n 3 192.168.0.21 >> "%LOGFILE%" 2>nul

:: ── Ping gateway ──────────────────────────────────────────────────────
call :L "--- PING GATEWAY 192.168.0.1 ---"
ping -n 2 192.168.0.1 2>nul
ping -n 2 192.168.0.1 >> "%LOGFILE%" 2>nul

:: ── Porta 445 ─────────────────────────────────────────────────────────
call :L "--- TESTE PORTA 445 ---"
powershell -NoProfile -Command ^
  "try{$t=New-Object Net.Sockets.TcpClient;$t.Connect('192.168.0.21',445);Write-Host '[OK] Porta 445 ABERTA';$t.Close()}catch{Write-Host '[ERRO] Porta 445 FECHADA/inacessivel'}" 2>nul
powershell -NoProfile -Command ^
  "try{$t=New-Object Net.Sockets.TcpClient;$t.Connect('192.168.0.21',445);'[OK] Porta 445 ABERTA';$t.Close()}catch{'[ERRO] Porta 445 FECHADA'}" >> "%LOGFILE%" 2>nul

:: ── net use ───────────────────────────────────────────────────────────
call :L "--- TESTE NET USE ---"
net use Z: "\\192.168.0.21\IMG" REDE /user:ACESSO /persistent:no
set "ERR=%errorlevel%"
call :L "net use resultado: %ERR%"
if %ERR% equ 0 (
    call :L "SUCESSO! Z: mapeado."
    dir Z:\ /w 2>nul
    dir Z:\ /w >> "%LOGFILE%" 2>nul
    net use Z: /delete /y >nul 2>&1
) else (
    call :L "FALHOU codigo %ERR%"
)

:: ── Resultado ─────────────────────────────────────────────────────────
echo.
echo ============================================================
echo   LOG SALVO EM: %LOGFILE%
echo ============================================================
echo.
type "%LOGFILE%"
echo.
echo ============================================================
echo   FIM - Janela aberta
echo ============================================================
pause > nul
goto :EOF

:L
echo [%TIME%] %~1
echo [%TIME%] %~1 >> "%LOGFILE%"
goto :eof
