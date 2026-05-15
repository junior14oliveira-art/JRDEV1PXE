# KIRO_REDE.exe - Conector SMB Background para WinPE
# Inicia servicos de rede, renova DHCP e conecta Z: ao servidor de imagens.
# Quando conectar, abre Explorer em Z:\ e encerra.
# Log: X:\Users\Default\Desktop\KIRO_REDE.log

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
MAX_TRIES  = 60
RETRY_SECS = 10

# ── Log ───────────────────────────────────────────────────────────────────── #
_desktop = "X:\\Users\\Default\\Desktop"
LOG_FILE  = os.path.join(_desktop, "KIRO_REDE.log") if os.path.exists(_desktop) else "C:\\KIRO_REDE.log"

def log(msg):
    ts   = time.strftime("%H:%M:%S")
    line = "[" + ts + "] " + msg
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── Helpers ───────────────────────────────────────────────────────────────── #
def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)

def drive_connected():
    try:
        return os.path.exists(DRIVE + "\\")
    except Exception:
        return False

def has_real_ip():
    try:
        _, out = run("ipconfig", timeout=8)
        for line in out.splitlines():
            if "192.168." in line or " 10." in line or "172." in line:
                if "169.254." not in line:
                    return True
        return False
    except Exception:
        return False

# ── Inicializacao de rede (igual ao KIRO_REDE_FIX.bat) ───────────────────── #
def init_network():
    log("--- Iniciando servicos de rede ---")
    for svc in ["Dhcp", "LanmanWorkstation", "Netman", "nsi", "ndis", "MRxSmb20"]:
        rc, _ = run("sc start " + svc)
        if rc == 0:
            log("  Servico iniciado: " + svc)
    time.sleep(3)

    log("--- Habilitando adaptadores ---")
    for iface in ["Ethernet", "Ethernet 2", "Ethernet 3",
                  "Local Area Connection", "Local Area Connection 2",
                  "LAN", "Rede Local"]:
        run('netsh interface set interface "' + iface + '" enable')

    log("--- Renovando DHCP ---")
    rc, out = run("ipconfig /renew", timeout=30)
    for line in out.splitlines():
        if line.strip():
            log("  " + line.strip())
    time.sleep(5)

    log("--- IP atual ---")
    _, ipout = run("ipconfig")
    for line in ipout.splitlines():
        if any(k in line for k in ["IPv4", "Endere", "Gateway", "Subnet", "Mask"]):
            log("  " + line.strip())

# ── Conectar SMB ─────────────────────────────────────────────────────────── #
def try_connect():
    run("net use " + DRIVE + " /delete /yes")
    time.sleep(1)
    rc, out = run(
        'net use ' + DRIVE + ' "\\\\' + SERVER_IP + '\\' + SHARE + '" '
        + PASS + ' /user:' + USER + ' /persistent:no',
        timeout=20
    )
    if rc != 0:
        codes = {"53": "Host nao encontrado", "67": "Share nao existe",
                 "86": "Senha incorreta", "1219": "Conflito credenciais",
                 "1326": "Usuario/senha invalidos", "1231": "Rede inacessivel"}
        for code, desc in codes.items():
            if "erro " + code in out.lower() or "error " + code in out.lower():
                log("  Erro " + code + ": " + desc)
                break
    return rc == 0

def open_explorer():
    for exp in [
        "X:\\Windows\\System32\\explorer.exe",
        "X:\\Windows\\explorer.exe",
        "C:\\Windows\\System32\\explorer.exe",
    ]:
        if os.path.exists(exp):
            subprocess.Popen([exp, DRIVE + "\\"])
            log("Explorer aberto em " + DRIVE + "\\")
            return
    log("Explorer nao encontrado. Abra manualmente: " + DRIVE)

# ── Main ─────────────────────────────────────────────────────────────────── #
def main():
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("KIRO_REDE v2.0 - " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
            f.write("Servidor: " + SERVER_IP + " | Share: " + SHARE + " | Drive: " + DRIVE + "\n")
            f.write("=" * 50 + "\n")
    except Exception:
        pass

    log("=" * 50)
    log("KIRO_REDE v2.0 iniciado")
    log("Servidor: \\\\" + SERVER_IP + "\\" + SHARE + " -> " + DRIVE)
    log("=" * 50)

    if drive_connected():
        log("[OK] " + DRIVE + " ja conectado. Encerrando.")
        return 0

    # Inicializar rede
    init_network()

    # Loop de tentativas
    for attempt in range(1, MAX_TRIES + 1):
        log("\n[" + str(attempt) + "/" + str(MAX_TRIES) + "] Tentando conectar...")

        if not has_real_ip():
            log("  Sem IP valido. Reiniciando rede...")
            init_network()

        if try_connect():
            log("=" * 50)
            log("[SUCESSO] " + DRIVE + " = \\\\" + SERVER_IP + "\\" + SHARE)
            log("=" * 50)
            open_explorer()
            log("Encerrando.")
            return 0

        if attempt < MAX_TRIES:
            log("  Aguardando " + str(RETRY_SECS) + "s...")
            time.sleep(RETRY_SECS)

    log("[TIMEOUT] Nao conectou apos " + str(MAX_TRIES) + " tentativas.")
    log("Verifique:")
    log("  1. GEMINI_HOST.bat rodou como Admin no servidor " + SERVER_IP)
    log("  2. ping " + SERVER_IP)
    log("  3. net share IMG (no servidor)")
    log("  4. Firewall porta 445 liberada")
    return 1


if __name__ == "__main__":
    sys.exit(main())
