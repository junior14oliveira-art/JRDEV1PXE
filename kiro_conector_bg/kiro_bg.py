"""
KIRO Conector Background
Roda silencioso no WinPE, renova DHCP e conecta Z: ao servidor de imagens.
Quando conectar, para sozinho.
"""
import subprocess
import time
import sys
import os
import ctypes

# ── Configuracao ──────────────────────────────────────────────────────────── #
SERVER_IP   = "192.168.0.21"
SHARE       = "IMG"
USER        = "ACESSO"
PASS        = "REDE"
DRIVE       = "Z:"
MAX_TRIES   = 60        # tentativas maximas (60 x 10s = 10 minutos)
RETRY_SECS  = 10        # segundos entre tentativas
LOG_FILE    = r"X:\Users\Default\Desktop\KIRO_BG.log"

# ── Log ───────────────────────────────────────────────────────────────────── #
def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── Helpers ───────────────────────────────────────────────────────────────── #
def run(cmd: str) -> int:
    """Executa comando e retorna exit code."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=15)
        return r.returncode
    except Exception:
        return -1

def drive_connected() -> bool:
    """Verifica se Z: ja esta mapeado."""
    return os.path.exists(f"{DRIVE}\\")

def renew_dhcp():
    """Tenta renovar DHCP em todas as interfaces."""
    run("ipconfig /renew")

def try_connect() -> bool:
    """Tenta conectar ao share SMB."""
    # Remove conexao anterior se existir
    run(f'net use {DRIVE} /delete /yes')
    time.sleep(1)

    # Tenta conectar
    rc = run(f'net use {DRIVE} "\\\\{SERVER_IP}\\{SHARE}" {PASS} /user:{USER} /persistent:no')
    return rc == 0

def has_ip() -> bool:
    """Verifica se tem IP valido (nao APIPA 169.254.x)."""
    try:
        r = subprocess.run("ipconfig", shell=True, capture_output=True,
                           text=True, timeout=5)
        out = r.stdout
        # Tem IP real se tiver 192.168. ou 10. ou 172.
        for line in out.splitlines():
            if "IPv4" in line or "Endere" in line:
                if "192.168." in line or "10." in line or "172." in line:
                    if "169.254." not in line:
                        return True
        return False
    except Exception:
        return False

# ── Loop principal ────────────────────────────────────────────────────────── #
def main():
    log("=" * 50)
    log("KIRO Conector BG iniciado")
    log(f"Servidor: {SERVER_IP} | Share: {SHARE} | Drive: {DRIVE}")
    log("=" * 50)

    # Se ja estiver conectado, nao faz nada
    if drive_connected():
        log(f"[OK] {DRIVE} ja conectado. Encerrando.")
        return 0

    for attempt in range(1, MAX_TRIES + 1):
        log(f"[{attempt}/{MAX_TRIES}] Tentando conectar...")

        # 1. Verificar se tem IP
        if not has_ip():
            log("  Sem IP valido. Renovando DHCP...")
            renew_dhcp()
            time.sleep(3)

        # 2. Tentar conectar
        if try_connect():
            log(f"[SUCESSO] {DRIVE} conectado em \\\\{SERVER_IP}\\{SHARE}")

            # Abrir Explorer na pasta Z:
            for exp in [
                r"X:\Windows\System32\explorer.exe",
                r"X:\Windows\explorer.exe",
                r"C:\Windows\System32\explorer.exe",
            ]:
                if os.path.exists(exp):
                    subprocess.Popen([exp, f"{DRIVE}\\"])
                    log(f"Explorer aberto em {DRIVE}\\")
                    break

            log("Encerrando - conexao estabelecida.")
            return 0

        log(f"  Falhou. Aguardando {RETRY_SECS}s...")
        time.sleep(RETRY_SECS)

    log(f"[TIMEOUT] Nao foi possivel conectar apos {MAX_TRIES} tentativas.")
    log(f"Verifique: GEMINI_HOST.bat rodou no servidor {SERVER_IP}?")
    return 1


if __name__ == "__main__":
    sys.exit(main())
