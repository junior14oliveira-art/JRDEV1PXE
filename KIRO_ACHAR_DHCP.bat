@echo off
title KIRO - ACHAR DHCP NA REDE
color 0B

echo ============================================================
echo   KIRO - IDENTIFICAR QUEM DA DHCP NA REDE
echo ============================================================
echo.

echo [1] IPs ativos nesta maquina:
ipconfig | findstr /i "IPv4 Gateway"
echo.

echo [2] Tabela ARP - dispositivos que responderam:
arp -a
echo.

echo [3] Varrendo rede 192.168.0.x em busca de dispositivos...
echo     (aguarde ~30 segundos)
echo.
for /L %%i in (1,1,30) do (
    ping -n 1 -w 100 192.168.0.%%i >nul 2>&1
    if !errorlevel! equ 0 echo     [ATIVO] 192.168.0.%%i
)

echo.
echo [4] Varrendo rede 192.168.88.x (rede do notebook)...
setlocal EnableDelayedExpansion
for /L %%i in (1,1,10) do (
    ping -n 1 -w 100 192.168.88.%%i >nul 2>&1
    if !errorlevel! equ 0 echo     [ATIVO] 192.168.88.%%i
)

echo.
echo [5] ARP atualizado apos varredura:
arp -a
echo.

echo ============================================================
echo   SE APARECER 192.168.88.1 = tem roteador/modem na rede
echo   O dispositivo em 192.168.88.1 esta dando DHCP ao notebook
echo ============================================================
echo.
pause
