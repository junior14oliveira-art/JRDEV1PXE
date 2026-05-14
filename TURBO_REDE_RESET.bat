@echo off
title TURBO REDE - RESET para padrao
color 0C
echo.
echo ============================================================
echo   TURBO REDE RESET - Voltando configuracoes ao padrao
echo ============================================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Execute como ADMINISTRADOR!
    pause
    exit /b 1
)

:: Detecta interface
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up' -and $_.MediaType -eq '802.3'} | Sort-Object LinkSpeed -Descending | Select-Object -First 1 -ExpandProperty Name"') do set IFACE=%%i

echo [1/5] Resetando MTU para 1500 (padrao)...
netsh interface ipv4 set subinterface "%IFACE%" mtu=1500 store=persistent >nul 2>&1
echo [OK] MTU = 1500

echo [2/5] Resetando TCP para configuracoes padrao...
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global chimney=default >nul 2>&1
netsh int tcp set global rss=enabled >nul 2>&1
netsh int tcp set global initialRto=3000 >nul 2>&1
echo [OK] TCP resetado

echo [3/5] Resetando Nagle Algorithm...
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v TcpAckFrequency /f >nul 2>&1
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v TCPNoDelay /f >nul 2>&1
echo [OK] Nagle Algorithm reativado

echo [4/5] Removendo politicas QoS...
netsh qos delete policy "KIRO_PXE_TFTP" >nul 2>&1
netsh qos delete policy "KIRO_HTTP_ISO" >nul 2>&1
netsh qos delete policy "KIRO_SMB" >nul 2>&1
echo [OK] QoS removido

echo [5/5] Resetando SMB...
powershell -NoProfile -Command "Set-SmbClientConfiguration -MaxCmds 50 -Force" >nul 2>&1
echo [OK] SMB resetado

echo.
echo [OK] Tudo voltou ao padrao do Windows.
echo Reinicie o computador para garantir que todas as mudancas foram aplicadas.
echo.
pause
