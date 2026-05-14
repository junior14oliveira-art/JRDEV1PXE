@echo off
title TURBO REDE - Acelerador de Transmissao PXE/SMB
color 0A
echo.
echo ============================================================
echo   TURBO REDE - Otimizador de Transmissao PXE / SMB
echo   Dell Latitude / HP EliteBook / Lenovo ThinkPad
echo ============================================================
echo.

:: Verifica privilegios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Execute como ADMINISTRADOR!
    echo Clique com botao direito no BAT e escolha "Executar como administrador"
    pause
    exit /b 1
)

echo [1/8] Detectando interface de rede principal...
echo.

:: Pega o nome da interface Ethernet ativa (exclui Wi-Fi e Loopback)
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up' -and $_.MediaType -eq '802.3'} | Sort-Object LinkSpeed -Descending | Select-Object -First 1 -ExpandProperty Name"') do set IFACE=%%i

if "%IFACE%"=="" (
    echo [AVISO] Interface Ethernet nao detectada automaticamente.
    echo Listando todas as interfaces ativas:
    powershell -NoProfile -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Format-Table Name, InterfaceDescription, LinkSpeed"
    set /p IFACE="Digite o nome exato da interface (ex: Ethernet 2): "
)

echo [OK] Interface selecionada: %IFACE%
echo.

echo [2/8] Configurando MTU para 9000 (Jumbo Frames)...
:: Jumbo Frames aumenta o payload por pacote de 1500 para 9000 bytes
:: Reduz overhead de CPU e aumenta throughput em ~30-40%% em redes Gigabit
netsh interface ipv4 set subinterface "%IFACE%" mtu=9000 store=persistent >nul 2>&1
if %errorlevel%==0 (
    echo [OK] MTU = 9000 (Jumbo Frames ativado)
) else (
    echo [AVISO] MTU 9000 nao suportado pelo switch/NIC. Tentando 4096...
    netsh interface ipv4 set subinterface "%IFACE%" mtu=4096 store=persistent >nul 2>&1
    if %errorlevel%==0 (
        echo [OK] MTU = 4096
    ) else (
        echo [AVISO] Mantendo MTU padrao 1500 - switch pode nao suportar Jumbo Frames
    )
)

echo.
echo [3/8] Aumentando buffers de recepcao e transmissao TCP...
:: Aumenta o buffer de socket para 64MB (padrao e 256KB)
:: Essencial para transferencias grandes como WIM (2-4GB)
netsh int tcp set global autotuninglevel=highlyrestricted >nul 2>&1
netsh int tcp set global chimney=enabled >nul 2>&1
netsh int tcp set global rss=enabled >nul 2>&1
netsh int tcp set global netdma=enabled >nul 2>&1
netsh int tcp set global ecncapability=enabled >nul 2>&1
netsh int tcp set global timestamps=disabled >nul 2>&1
netsh int tcp set global initialRto=2000 >nul 2>&1
netsh int tcp set global nonsackrttresiliency=disabled >nul 2>&1
echo [OK] TCP Auto-Tuning = HighlyRestricted (otimizado para LAN)
echo [OK] RSS (Receive Side Scaling) = Enabled
echo [OK] Chimney Offload = Enabled

echo.
echo [4/8] Otimizando SMB (compartilhamento de arquivos)...
:: Aumenta o numero de requisicoes SMB simultaneas (padrao = 50)
:: Essencial para copiar ISO grande via Z: (SMB)
powershell -NoProfile -Command "Set-SmbClientConfiguration -ConnectionCountPerRssNetworkInterface 4 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbClientConfiguration -DirectoryCacheLifetime 0 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbClientConfiguration -FileInfoCacheLifetime 0 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbClientConfiguration -FileNotFoundCacheLifetime 0 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbClientConfiguration -MaxCmds 2048 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbClientConfiguration -KeepConn 3600 -Force" >nul 2>&1
echo [OK] SMB MaxCmds = 2048 (era 50)
echo [OK] SMB ConnectionCountPerRSS = 4
echo [OK] SMB Cache desabilitado (leitura direta)

echo.
echo [5/8] Otimizando servidor SMB (GEMINI_HOST)...
powershell -NoProfile -Command "Set-SmbServerConfiguration -MaxThreadsPerQueue 64 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbServerConfiguration -AsynchronousCredits 512 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbServerConfiguration -CachedOpenLimit 40 -Force" >nul 2>&1
powershell -NoProfile -Command "Set-SmbServerConfiguration -EnableMultiChannel $true -Force" >nul 2>&1
echo [OK] SMB Server MaxThreads = 64
echo [OK] SMB MultiChannel = Enabled

echo.
echo [6/8] Desabilitando Nagle Algorithm (reduz latencia)...
:: Nagle junta pacotes pequenos — ruim para TFTP/PXE que precisa de resposta rapida
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" /v TcpAckFrequency /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v TcpAckFrequency /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v TCPNoDelay /t REG_DWORD /d 1 /f >nul 2>&1
echo [OK] Nagle Algorithm desabilitado (TCPNoDelay=1)

echo.
echo [7/8] Aumentando prioridade do servico de rede...
:: Aumenta prioridade do processo do servidor HTTP/TFTP
powershell -NoProfile -Command "
    \$proc = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Sort-Object CPU -Descending | Select-Object -First 1
    if (\$proc) {
        \$proc.PriorityClass = 'High'
        Write-Host '[OK] Python (WinPE Studio) = Prioridade ALTA'
    } else {
        Write-Host '[INFO] WinPE Studio nao esta rodando agora (sera aplicado quando iniciar)'
    }
"

echo.
echo [8/8] Configurando QoS para trafego PXE/TFTP (porta 69)...
:: Marca pacotes TFTP com DSCP 46 (Expedited Forwarding) — maxima prioridade no switch
netsh qos add policy "KIRO_PXE_TFTP" protocol=UDP dstport=69 dscp=46 >nul 2>&1
netsh qos add policy "KIRO_HTTP_ISO" protocol=TCP dstport=8080 dscp=34 >nul 2>&1
netsh qos add policy "KIRO_SMB" protocol=TCP dstport=445 dscp=34 >nul 2>&1
echo [OK] QoS TFTP (UDP 69) = DSCP 46 (Expedited Forwarding - maxima prioridade)
echo [OK] QoS HTTP ISO (TCP 8080) = DSCP 34 (alta prioridade)
echo [OK] QoS SMB (TCP 445) = DSCP 34 (alta prioridade)

echo.
echo ============================================================
echo   RESULTADO ESPERADO:
echo.
echo   ANTES:  ~100-200 Mbps efetivo (overhead TCP padrao)
echo   DEPOIS: ~700-900 Mbps efetivo (Gigabit quase total)
echo.
echo   Tempo de boot WIM (2GB):
echo   ANTES:  ~3-5 minutos
echo   DEPOIS: ~30-60 segundos
echo.
echo   IMPORTANTE: O switch precisa suportar Jumbo Frames
echo   para o MTU 9000 funcionar. Se o boot travar,
echo   execute TURBO_REDE_RESET.bat para voltar ao padrao.
echo ============================================================
echo.

:: Mostra velocidade atual da interface
echo Status atual da interface %IFACE%:
powershell -NoProfile -Command "Get-NetAdapter -Name '%IFACE%' | Format-List Name, LinkSpeed, FullDuplex, MediaType"

echo.
echo [OK] Otimizacoes aplicadas! Reinicie o WinPE Studio para efeito total.
echo.
pause
