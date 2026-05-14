"""
KIRO Conector Background v2.0
==============================
Roda silencioso no WinPE ao iniciar.
- Inicia servicos de rede (DHCP, Netman, NSI, NDIS)
- Habilita adaptadores de rede
- Renova DHCP
- Conecta Z: ao servidor de imagens
- Quando conectar, abre Explorer em Z e encerra
- Log salvo no Desktop do WinPE
"""
import subprocess
import time
import sys
import os

# ── Configuracao ──────────────────────────────────────────────────────────── #
SERVER_IP  = "192.168.0.21"
SHARE      = "IMG"
USER       = "ACESSO"
PASS       = "REDE"
DRIVE      = "Z:"
MAX_TRIES  = 60       # tentativas maximas (60 x 10s = 10 minutos)
RETRY_SECS = 10       # segundos entre tentativas

# Log no desktop do WinPE
if os.path.exists("X:\\Users\\Default\\Desktop"):
    LOG_FILE = "X:\\Users\\Default\\Desktop\\KIRO_BG.log"
else:
    LOG_FILE = "C:\\KIRO_BG.log"

# ── Log ───────────────────────────────────────────────────────────────────── #
def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── Helpers ───────────────────────────────────────────────────────────────── #
def run(cmd: str, timeout: int = 15) -> tuple[int, str]:
    """Executa comando, retorna (exit_code, output)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)

def drive_connected() -> bool:
    """Verifica se Z: ja esta mapeado e acessivel."""
    try:
        return os.path.exists(f"{DRIVE}\\")
    except Exception:
        return False

def has_real_ip() -> bool:
    """Verifica se tem IP valido (nao APIPA 169.254.x)."""
    try:
        _, out = run("ipconfig", timeout=8)
        for line in out.splitlines():
            l = line.lower()
            if "ipv4" in l or "endere" in l:
                if "192.168." in line or " 10." in line or "172." in line:
                    if "169.254." not in line:
                        return True
        return False
    except Exception:
        return False

# ── Inicializacao de rede (logica do KIRO_REDE_FIX) ──────────────────────── #
def init_network():
    """
    Replica o KIRO_REDE_FIX.bat:
    1. Inicia servicos essenciais de rede
    2. Habilita adaptadores fisicos
    3. Renova DHCP
    """
    log("--- Iniciando servicos de rede ---")
    services = ["Dhcp", "LanmanWorkstation", "Netman", "nsi", "ndis", "MRxSmb20"]
    for svc in services:
        rc, _ = run(f"sc start {svc}")
        if rc == 0:
            log(f"  [OK] Servico iniciado: {svc}")

    time.sleep(3)

    log("--- Habilitando adaptadores de rede ---")
    # Lista interfaces disponiveis
    _, ifaces_out = run("netsh interface show interface")
    log(ifaces_out[:300] if ifaces_out else "  (sem saida)")

    # Tenta habilitar interfaces comuns no WinPE
    for iface in [
        "Ethernet", "Ethernet 2", "Ethernet 3",
        "Local Area Connection", "Local Area Connection 2",
        "LAN", "Rede Local",
    ]:
        run(f'netsh interface set interface "{iface}" enable')

    time.sleep(2)

    log("--- Renovando DHCP ---")
    rc, out = run("ipconfig /renew", timeout=30)
    log(out[:200] if out else "  (sem saida)")
    time.sleep(5)

    log("--- Estado da rede apos init ---")
    _, ipout = run("ipconfig")
    for line in ipout.splitlines():
        if any(k in line for k in ["IPv4", "Endere", "Gateway", "Subnet", "Mask"]):
            log(f"  {line.strip()}")

# ── Conectar SMB ─────────────────────────────────────────────────────────── #
def try_connect() -> bool:
    """Tenta conectar ao share SMB."""
    # Remove conexao anterior
    run(f"net use {DRIVE} /delete /yes")
    time.sleep(1)

    rc, out = run(
        f'net use {DRIVE} "\\\\{SERVER_IP}\\{SHARE}" {PASS} /user:{USER} /persistent:no',
        timeout=20
    )
    if rc == 0:
        return True

    # Log do erro para diagnostico
    err_map = {
        "53":   "Host nao encontrado (rede/firewall)",
        "67":   "Share nao existe (GEMINI_HOST.bat nao rodou?)",
        "86":   "Senha incorreta",
        "1219": "Conflito de credenciais",
        "1326": "Usuario/senha invalidos",
        "1231": "Rede inacessivel (sub-redes diferentes)",
    }
    for code, desc in err_map.items():
        if f"erro {code}" in out.lower() or f"error {code}" in out.lower():
            log(f"  Erro {code}: {desc}")
            break
    return False

def open_explorer():
    """Abre Explorer em Z apos conectar."""
    for exp in [
        r"X:\Windows\System32\explorer.exe",
        r"X:\Windows\explorer.exe",
        r"C:\Windows\System32\explorer.exe",
    ]:
        if os.path.exists(exp):
            subprocess.Popen([exp, f"{DRIVE}\\"])
            log(f"Explorer aberto em {DRIVE}\\")
            return
    log("Explorer nao encontrado — abra manualmente: " + DRIVE)

# ── Main ─────────────────────────────────────────────────────────────────── #
def main() -> int:
    # Cria log
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"KIRO BG v2.0 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Servidor: {SERVER_IP} | Share: {SHARE} | Drive: {DRIVE}\n")
            f.write("=" * 50 + "\n")
    except Exception:
        pass

    log("=" * 50)
    log("KIRO Conector BG v2.0 iniciado")
    log(f"Servidor: {SERVER_IP} | Share: \\\\{SERVER_IP}\\{SHARE}")
    log(f"Drive: {DRIVE} | Max tentativas: {MAX_TRIES}")
    log("=" * 50)

    # Se ja estiver conectado, nao faz nada
    if drive_connected():
        log(f"[OK] {DRIVE} ja conectado. Encerrando.")
        return 0

    # Inicializar rede (servicos + adaptadores + DHCP)
    init_network()

    # Loop de tentativas
    for attempt in range(1, MAX_TRIES + 1):
        log(f"\n[{attempt}/{MAX_TRIES}] Tentando conectar a \\\\{SERVER_IP}\\{SHARE}...")

        # Verificar IP
        if not has_real_ip():
            log("  Sem IP valido. Reiniciando rede...")
            init_network()

        # Tentar conectar
        if try_connect():
            log(f"\n{'='*50}")
            log(f"[SUCESSO] {DRIVE} = \\\\{SERVER_IP}\\{SHARE}")
            log(f"{'='*50}")
            open_explorer()
            log("Encerrando - conexao estabelecida.")
            return 0

        if attempt < MAX_TRIES:
            log(f"  Aguardando {RETRY_SECS}s...")
            time.sleep(RETRY_SECS)

    log(f"\n[TIMEOUT] Nao conectou apos {MAX_TRIES} tentativas ({MAX_TRIES * RETRY_SECS // 60} min).")
    log("Verifique:")
    log(f"  1. GEMINI_HOST.bat rodou como Admin no servidor {SERVER_IP}")
    log(f"  2. Servidor acessivel: ping {SERVER_IP}")
    log(f"  3. Share ativo: net share IMG")
    log(f"  4. Firewall porta 445 liberada")
    return 1


if __name__ == "__main__":
    sys.exit(main())
