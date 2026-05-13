@echo off
setlocal EnableDelayedExpansion
title KIRO - DIAGNOSTICO DE REDE
color 0C

set "LOGFILE=C:\KIRO_REDE.txt"
if exist "X:\Users\Default\Desktop\" set "LOGFILE=X:\Users\Default\Desktop\KIRO_REDE.txt"
echo. > "%LOGFILE%"

call :L "====== KIRO REDE FIX %DATE% %TIME% ======"

:: ── Lista todos os adaptadores (com e sem driver) ─────────────────────
call :L "--- ADAPTADORES DETECTADOS (wmic) ---"
wmic nic get Name,NetConnectionID,NetEnabled,MACAddress /format:list 2>nul
wmic nic get Name,NetConnectionID,NetEnabled,MACAddress /format:list >> "%LOGFILE%" 2>nul

:: ── Dispositivos PnP de rede sem driver ───────────────────────────────
call :L "--- DISPOSITIVOS SEM DRIVER ---"
wmic path Win32_PnPEntity where "ConfigManagerErrorCode != 0" get Name,DeviceID /format:list 2>nul
wmic path Win32_PnPEntity where "ConfigManagerErrorCode != 0" get Name,DeviceID /format:list >> "%LOGFILE%" 2>nul

:: ── Tenta iniciar servicos de rede ────────────────────────────────────
call :L "--- INICIANDO SERVICOS ---"
sc start Dhcp              >nul 2>&1 && call :L "Dhcp: iniciado"
sc start LanmanWorkstation >nul 2>&1 && call :L "LanmanWorkstation: iniciado"
sc start Netman            >nul 2>&1 && call :L "Netman: iniciado"
sc start nsi               >nul 2>&1 && call :L "NSI: iniciado"
sc start ndis              >nul 2>&1 && call :L "NDIS: iniciado"
timeout /t 3 /nobreak >nul

:: ── Tenta habilitar adaptadores via netsh ─────────────────────────────
call :L "--- TENTANDO HABILITAR ADAPTADORES ---"
for /f "tokens=*" %%A in ('netsh interface show interface 2^>nul ^| findstr /v "Admin"') do (
    call :L "Interface: %%A"
)
netsh interface show interface 2>nul
netsh interface show interface >> "%LOGFILE%" 2>nul

:: Tenta habilitar todos
netsh interface set interface "Ethernet" enable >nul 2>&1
netsh interface set interface "Local Area Connection" enable >nul 2>&1
netsh interface set interface "Ethernet 2" enable >nul 2>&1

:: ── Renova DHCP ───────────────────────────────────────────────────────
call :L "--- RENOVANDO DHCP ---"
ipconfig /renew 2>nul
ipconfig /renew >> "%LOGFILE%" 2>nul
timeout /t 5 /nobreak >nul

:: ── Estado final ──────────────────────────────────────────────────────
call :L "--- IPCONFIG FINAL ---"
ipconfig /all 2>nul
ipconfig /all >> "%LOGFILE%" 2>nul

echo.
echo ============================================================
type "%LOGFILE%"
echo ============================================================
echo   Log: %LOGFILE%
echo   FIM - Janela aberta
echo ============================================================
pause > nul
goto :EOF

:L
echo [%TIME%] %~1
echo [%TIME%] %~1 >> "%LOGFILE%"
goto :eof
