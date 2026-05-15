"""
Serviço de licenciamento do WinPE Studio.

FLUXO:
  1. Você gera uma chave no painel admin informando só o PRAZO (3/6/12 meses).
  2. Cliente instala o programa e cola a chave.
  3. Na PRIMEIRA ativação:
     - Programa valida a assinatura da chave (HMAC-SHA256 com segredo)
     - Grava o MAC do PC junto com a chave em license.dat
     - A chave fica "amarrada" a este PC
  4. Em toda execução seguinte:
     - Verifica se o MAC ainda bate (evita copiar license.dat para outro PC)
     - Verifica se a data não expirou
  5. Se expirado ou MAC diferente → bloqueia o programa.

FORMATO DA CHAVE (o que o cliente recebe):
  KIRO-AAAA-BBBB-CCCC-DDDD
  (20 chars base32 do HMAC, divididos em grupos de 4, prefixo KIRO-)
  A data de expiração fica DENTRO da chave (não precisa informar ao cliente).
"""

import hashlib
import hmac
import json
import os
import subprocess
import uuid
from base64 import b32encode, b32decode
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Segredo compartilhado ────────────────────────────────────────────────── #
# TROQUE ESTE VALOR antes de distribuir — mantenha em segredo absoluto!
# Este mesmo valor deve estar no license_manager.py
_SECRET = b"KIRO_WINPE_2024_#@!_MUDE_ANTES_DE_DISTRIBUIR_#@!"

# MACs isentos de licença (máquinas do desenvolvedor)
# Adicione o MAC do seu notebook aqui — nunca precisará de licença
_DEVELOPER_MACS = {
    "00155DD3E415",   # Notebook JRDEV1 - Ethernet principal
    "00155D4E59DB",   # Notebook JRDEV1 - Ethernet alternativa (Hyper-V)
}

# Onde salvar a licença no PC do cliente
# IMPORTANTE: Usa PROGRAMDATA (C:\ProgramData) em vez de APPDATA
# porque o programa roda como Admin (UAC) e o APPDATA muda de perfil
# ProgramData é acessível por todos os usuários/níveis de elevação
_LICENSE_DIR  = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "WinPEStudio"
_LICENSE_FILE = _LICENSE_DIR / "license.dat"


# ══════════════════════════════════════════════════════════════════════════ #
#  Hardware ID                                                               #
# ══════════════════════════════════════════════════════════════════════════ #

def get_machine_id() -> str:
    """
    Retorna o MAC address da interface Ethernet principal (sem separadores).
    Fallback: uuid.getnode().
    Sempre retorna 12 chars hex maiúsculos.
    """
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "Get-NetAdapter | Where-Object {$_.Status -eq 'Up' -and $_.MediaType -eq '802.3'} "
                "| Sort-Object LinkSpeed -Descending | Select-Object -First 1 -ExpandProperty MacAddress"
            ],
            capture_output=True, text=True, timeout=10
        )
        mac = result.stdout.strip().replace("-", "").replace(":", "").upper()
        if mac and len(mac) == 12:
            return mac
    except Exception:
        pass
    # Fallback
    return f"{uuid.getnode():012X}"


def get_machine_id_display() -> str:
    """Retorna o MAC formatado: XX-XX-XX-XX-XX-XX"""
    mid = get_machine_id()
    return "-".join(mid[i:i+2] for i in range(0, 12, 2))


# ══════════════════════════════════════════════════════════════════════════ #
#  Geração de chave (usado pelo license_manager — painel admin)             #
# ══════════════════════════════════════════════════════════════════════════ #

def generate_license_key(expiry_date: date) -> str:
    """
    Gera uma chave de licença baseada APENAS na data de expiração.
    O MAC NÃO entra na chave — é amarrado só na ativação.

    Formato: KIRO-AAAA-BBBB-CCCC-DDDD
    """
    payload = f"WINPE|{expiry_date.isoformat()}"
    sig = hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest()
    # 10 bytes → 16 chars base32
    b32 = b32encode(sig[:10]).decode().rstrip("=")
    return f"KIRO-{b32[0:4]}-{b32[4:8]}-{b32[8:12]}-{b32[12:16]}"


def _verify_key_signature(key: str, expiry_date: date) -> bool:
    """Verifica se a assinatura da chave é válida para a data informada."""
    expected = generate_license_key(expiry_date)
    return hmac.compare_digest(
        key.upper().replace(" ", "").replace("-", ""),
        expected.upper().replace(" ", "").replace("-", "")
    )


def extract_expiry_from_key(key: str) -> date | None:
    """
    Descobre a data de expiração embutida na chave testando datas futuras.
    Testa dia a dia nos próximos 5 anos.
    Retorna a date se encontrar, None se a chave for inválida.
    """
    today = date.today()

    # Testa datas futuras (até 5 anos = 1825 dias)
    for days_ahead in range(0, 1826):
        candidate = today + timedelta(days=days_ahead)
        if _verify_key_signature(key, candidate):
            return candidate

    # Testa datas já expiradas (últimos 2 anos) para detectar chaves vencidas
    for days_back in range(1, 731):
        candidate = today - timedelta(days=days_back)
        if _verify_key_signature(key, candidate):
            return candidate

    return None


# ══════════════════════════════════════════════════════════════════════════ #
#  Status                                                                    #
# ══════════════════════════════════════════════════════════════════════════ #

class LicenseStatus:
    VALID     = "valid"
    EXPIRED   = "expired"
    INVALID   = "invalid"
    NOT_FOUND = "not_found"
    WRONG_MAC = "wrong_mac"


# ══════════════════════════════════════════════════════════════════════════ #
#  Ativação (primeira vez)                                                   #
# ══════════════════════════════════════════════════════════════════════════ #

def activate_license(key: str) -> tuple[bool, str]:
    """
    Ativa a licença no PC atual.
    - Valida a assinatura da chave
    - Descobre a data de expiração embutida na chave
    - Amarra ao MAC deste PC
    - Salva em license.dat

    Retorna (sucesso, mensagem).
    """
    key = key.strip().upper()

    # Descobre a data de expiração testando combinações
    expiry = extract_expiry_from_key(key)
    if expiry is None:
        return False, (
            "❌ Chave inválida.\n\n"
            "Verifique se digitou corretamente.\n"
            "Formato esperado: KIRO-XXXX-XXXX-XXXX-XXXX"
        )

    today = date.today()
    if today > expiry:
        return False, (
            f"❌ Esta licença expirou em {expiry.strftime('%d/%m/%Y')}.\n\n"
            "Entre em contato para renovar."
        )

    # Amarra ao MAC deste PC
    machine_id = get_machine_id()
    days_left  = (expiry - today).days

    _LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "key":        key,
        "machine_id": machine_id,
        "expiry":     expiry.isoformat(),
        "activated":  datetime.now().isoformat(),
    }
    _LICENSE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return True, (
        f"✅ Licença ativada com sucesso!\n\n"
        f"Válida até: {expiry.strftime('%d/%m/%Y')} ({days_left} dias restantes)\n"
        f"Máquina: {get_machine_id_display()}"
    )


# ══════════════════════════════════════════════════════════════════════════ #
#  Verificação (toda execução)                                               #
# ══════════════════════════════════════════════════════════════════════════ #

def check_license() -> tuple[str, dict]:
    """
    Verifica a licença salva.

    Retorna (status, info):
      status : LicenseStatus.*
      info   : dict com detalhes (expiry, days_left, machine_id, etc.)
    """
    # ── Whitelist do desenvolvedor — sem licença necessária ──────── #
    current_mac = get_machine_id()
    if current_mac.upper() in _DEVELOPER_MACS:
        from datetime import date
        return LicenseStatus.VALID, {
            "key":        "DEVELOPER",
            "machine_id": current_mac,
            "expiry":     "2099-12-31",
            "days_left":  99999,
            "activated":  "developer",
        }
    # ─────────────────────────────────────────────────────────────── #

    if not _LICENSE_FILE.exists():
        return LicenseStatus.NOT_FOUND, {}

    try:
        data       = json.loads(_LICENSE_FILE.read_text(encoding="utf-8"))
        key        = data.get("key", "")
        machine_id = data.get("machine_id", "")
        expiry_str = data.get("expiry", "")

        expiry = date.fromisoformat(expiry_str)
        today  = date.today()

        # 1. Verifica MAC
        current_mac = get_machine_id()
        if current_mac.upper() != machine_id.upper():
            return LicenseStatus.WRONG_MAC, {
                "machine_id": machine_id,
                "current":    current_mac,
            }

        # 2. Verifica assinatura
        if not _verify_key_signature(key, expiry):
            return LicenseStatus.INVALID, {}

        # 3. Verifica expiração
        days_left = (expiry - today).days
        info = {
            "key":        key,
            "machine_id": machine_id,
            "expiry":     expiry_str,
            "days_left":  days_left,
            "activated":  data.get("activated", ""),
        }

        if today > expiry:
            return LicenseStatus.EXPIRED, info

        return LicenseStatus.VALID, info

    except Exception as e:
        return LicenseStatus.INVALID, {"error": str(e)}
