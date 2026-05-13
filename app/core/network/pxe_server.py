"""
PXE Server Engine v3.0 — WinPE & PXE Studio
=============================================
Changelog:
  v1.0 — Servidor basico HTTP/TFTP
  v2.0 — DHCP com Offer, campos sname/file, porta 4011
  v2.1 — Bind 0.0.0.0, broadcast duplo
  v3.0 — REESCRITA COMPLETA:
         - BUG FIX: DHCP agora responde REQUEST→ACK (antes so fazia Offer)
         - BUG FIX: Pasta resources/boot era inexistente, arquivos copiados automaticamente
         - BUG FIX: Deteccao de iPXE (Option 175) para evitar loop de chainloading
         - TFTP com socket separado por cliente (RFC 1350)
         - Logs detalhados de diagnostico na inicializacao
         - Pool de IPs com controle de alocacao
"""
import socket
import threading
import logging
import struct
import subprocess
import os
import shutil
import json
import select
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Callable

VERSION = "3.0"

logger = logging.getLogger(__name__)

# Pasta onde os binarios de boot reais estao (seu disco)
BOOT_FILES_SOURCE = Path(r"E:\PXEGEMINI\boot")
REQUIRED_BOOT_FILES = ["ipxe.efi", "wimboot"]
OPTIONAL_BOOT_FILES = ["snponly.efi", "undionly.kpxe", "httpdisk.exe", "httpdisk.sys"]


# --- Helpers de Rede ---
def ipv4_to_int(ip: str) -> int:
    return struct.unpack('!I', socket.inet_aton(ip))[0]

def int_to_ipv4(value: int) -> str:
    return socket.inet_ntoa(struct.pack('!I', value & 0xFFFFFFFF))

def compute_broadcast(ip: str, mask: str) -> str:
    ip_val = ipv4_to_int(ip)
    mask_val = ipv4_to_int(mask)
    return int_to_ipv4((ip_val & mask_val) | ((~mask_val) & 0xFFFFFFFF))

def ensure_firewall_rule(name: str, protocol: str, port: int):
    try:
        subprocess.run(['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                        f'name={name}'], capture_output=True)
        subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule',
                        f'name={name}', 'dir=in', 'action=allow',
                        f'protocol={protocol.upper()}', f'localport={int(port)}',
                        'profile=any'], check=True, capture_output=True)
    except Exception as e:
        logger.warning(f"Firewall rule failed for {name}: {e}")


class PxeHttpHandler(SimpleHTTPRequestHandler):
    """HTTP handler silencioso."""
    def log_message(self, fmt, *args):
        pass


class PxeServer:
    """Servidor PXE completo: DHCP + TFTP + HTTP."""

    def __init__(self, interface_ip: str, subnet_mask: str, work_dir: str):
        self.ip = interface_ip
        self.mask = subnet_mask
        self.work_dir = Path(work_dir) if work_dir else Path(".")
        self.boot_dir = Path(__file__).parent.parent.parent / "resources" / "boot"
        self.is_running = False
        self._http_srv = None
        self._threads: list = []
        self._leases: Dict[str, str] = {}  # MAC -> IP
        self._next_ip_offset = 100

    # ------------------------------------------------------------------ #
    #  INICIALIZACAO
    # ------------------------------------------------------------------ #
    def start(self, log_cb: Optional[Callable] = None):
        self.is_running = True
        self._log = log_cb or (lambda msg: None)

        self._log(f"====== PXE Server Engine v{VERSION} ======")
        self._log(f"[INIT] IP do Servidor: {self.ip}")
        self._log(f"[INIT] Mascara: {self.mask}")
        self._log(f"[INIT] Broadcast: {compute_broadcast(self.ip, self.mask)}")
        self._log(f"[INIT] Diretorio de trabalho: {self.work_dir}")

        # 1. Firewall
        self._log("[INIT] Abrindo portas no Firewall...")
        ensure_firewall_rule("WinPE Studio DHCP", "UDP", 67)
        ensure_firewall_rule("WinPE Studio DHCP-BINL", "UDP", 4011)
        ensure_firewall_rule("WinPE Studio TFTP", "UDP", 69)
        ensure_firewall_rule("WinPE Studio HTTP", "TCP", 8080)
        self._log("[INIT] Firewall OK")

        # 2. Preparar arquivos de boot
        if not self._prepare_boot_files():
            self._log("[ERRO] Falha critica ao preparar arquivos de boot!")
            self.is_running = False
            return

        # 3. Gerar script iPXE
        self._generate_ipxe_script()

        # 4. Diagnostico: listar arquivos de boot
        self._log("[INIT] Arquivos no diretorio de boot:")
        for f in sorted(self.boot_dir.iterdir()):
            size = f.stat().st_size if f.is_file() else 0
            label = f"{size // 1024} KB" if size > 1024 else f"{size} B"
            self._log(f"  -> {f.name} [{label}]")

        # 5. Iniciar servicos
        self._threads = [
            threading.Thread(target=self._run_http, daemon=True, name="HTTP"),
            threading.Thread(target=self._run_tftp, daemon=True, name="TFTP"),
            threading.Thread(target=self._run_dhcp, daemon=True, name="DHCP"),
        ]
        for t in self._threads:
            t.start()

        self._log("[INIT] ====== SERVIDOR PRONTO ======")

    def _prepare_boot_files(self) -> bool:
        """Copia arquivos de boot de E:\\PXEGEMINI\\boot para resources/boot."""
        self._log(f"[BOOT] Verificando diretorio: {self.boot_dir}")
        self.boot_dir.mkdir(parents=True, exist_ok=True)

        # Copiar do source se existir
        if BOOT_FILES_SOURCE.exists():
            self._log(f"[BOOT] Fonte encontrada: {BOOT_FILES_SOURCE}")
            for fname in REQUIRED_BOOT_FILES + OPTIONAL_BOOT_FILES:
                src = BOOT_FILES_SOURCE / fname
                dst = self.boot_dir / fname
                if src.exists():
                    shutil.copy2(str(src), str(dst))
                    self._log(f"[BOOT] Copiado: {fname} ({src.stat().st_size // 1024} KB)")
                else:
                    self._log(f"[BOOT] Nao encontrado: {fname}")
        else:
            self._log(f"[BOOT] AVISO: Pasta fonte nao existe: {BOOT_FILES_SOURCE}")

        # Copiar boot.wim do projeto (sources/boot.wim)
        source_wim = self.work_dir / "sources" / "boot.wim"
        if source_wim.exists():
            shutil.copy2(str(source_wim), str(self.boot_dir / "boot.wim"))
            self._log(f"[BOOT] boot.wim copiado ({source_wim.stat().st_size // 1024 // 1024} MB)")

        # Copiar BCD e boot.sdi — necessarios para o Windows Boot Manager dentro do WIM
        # Estrutura esperada na pasta do projeto: Boot/BCD e Boot/boot.sdi
        for bcd_candidate in [
            self.work_dir / "Boot" / "BCD",
            self.work_dir / "boot" / "BCD",
            self.work_dir / "EFI" / "Microsoft" / "Boot" / "BCD",
        ]:
            if bcd_candidate.exists():
                shutil.copy2(str(bcd_candidate), str(self.boot_dir / "BCD"))
                self._log(f"[BOOT] BCD copiado de: {bcd_candidate}")
                break
        else:
            self._log("[BOOT] AVISO: BCD nao encontrado no projeto (boot pode falhar com 0xc000000f)")

        for sdi_candidate in [
            self.work_dir / "Boot" / "boot.sdi",
            self.work_dir / "boot" / "boot.sdi",
        ]:
            if sdi_candidate.exists():
                shutil.copy2(str(sdi_candidate), str(self.boot_dir / "boot.sdi"))
                self._log(f"[BOOT] boot.sdi copiado de: {sdi_candidate}")
                break
        else:
            self._log("[BOOT] AVISO: boot.sdi nao encontrado no projeto")

        # Verificar arquivos obrigatorios
        ok = True
        for fname in REQUIRED_BOOT_FILES:
            if not (self.boot_dir / fname).exists():
                self._log(f"[ERRO] Arquivo OBRIGATORIO ausente: {fname}")
                ok = False
        return ok

    def _generate_ipxe_script(self):
        """Gera boot.ipxe (usado pelo iPXE via HTTP) e autoexec.ipxe (fallback TFTP).

        O wimboot requer que BCD e boot.sdi sejam passados como initrd ANTES do boot.wim
        para que o Windows Boot Manager encontre o BCD e nao retorne 0xc000000f.
        """
        url = f"http://{self.ip}:8080"

        # Monta as linhas de initrd condicionalmente (so inclui se o arquivo existir)
        initrd_lines = []
        if (self.boot_dir / "BCD").exists():
            initrd_lines.append(f"initrd {url}/BCD           BCD")
        if (self.boot_dir / "boot.sdi").exists():
            initrd_lines.append(f"initrd {url}/boot.sdi      boot.sdi")
        initrd_lines.append(f"initrd {url}/boot.wim      boot.wim")

        content = (
            f"#!ipxe\n"
            f"echo WinPE Studio PXE v{VERSION}\n"
            f"echo Servidor: {self.ip}\n"
            f"set boot-url {url}\n"
            f"kernel ${{boot-url}}/wimboot\n"
            + "\n".join(initrd_lines) + "\n"
            f"boot\n"
        )

        # boot.ipxe — servido via HTTP quando o iPXE ja esta rodando
        boot_script = self.boot_dir / "boot.ipxe"
        boot_script.write_text(content)
        self._log(f"[BOOT] Script iPXE gerado: {boot_script}")

        # autoexec.ipxe — solicitado via TFTP pelo iPXE logo apos carregar
        # (antes de receber o DHCP com a URL HTTP). Alias do boot.ipxe.
        autoexec = self.boot_dir / "autoexec.ipxe"
        autoexec.write_text(content)
        self._log(f"[BOOT] autoexec.ipxe gerado (alias TFTP): {autoexec}")

    # ------------------------------------------------------------------ #
    #  HTTP SERVER
    # ------------------------------------------------------------------ #
    def _run_http(self):
        try:
            self._http_srv = HTTPServer(('0.0.0.0', 8080), PxeHttpHandler)
            os.chdir(str(self.boot_dir))
            self._log(f"[HTTP] ONLINE em 0.0.0.0:8080 (servindo {self.boot_dir})")
            self._http_srv.serve_forever()
        except Exception as e:
            self._log(f"[HTTP] ERRO: {e}")

    # ------------------------------------------------------------------ #
    #  TFTP SERVER (RFC 1350 — socket separado por cliente)
    # ------------------------------------------------------------------ #
    def _run_tftp(self):
        try:
            main_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            main_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            main_sock.bind(('0.0.0.0', 69))
            self._log(f"[TFTP] ONLINE em 0.0.0.0:69")

            while self.is_running:
                main_sock.settimeout(1.0)
                try:
                    data, addr = main_sock.recvfrom(2048)
                except socket.timeout:
                    continue

                if len(data) > 2 and data[1] == 1:  # RRQ
                    parts = data[2:].split(b'\x00')
                    filename = parts[0].decode(errors='ignore')
                    self._log(f"[TFTP] RRQ de {addr[0]}:{addr[1]} -> {filename}")
                    
                    # Passar o pacote de dados inteiro para parsear as opcoes
                    t = threading.Thread(
                        target=self._tftp_transfer, args=(addr, filename, data),
                        daemon=True
                    )
                    t.start()
        except Exception as e:
            self._log(f"[TFTP] ERRO: {e}")

    def _tftp_transfer(self, client_addr, filename, rrq_data):
        """Transfere um arquivo via TFTP usando socket dedicado e com OACK."""
        path = self.boot_dir / filename
        if not path.exists():
            self._log(f"[TFTP] ERRO: {filename} nao encontrado")
            return

        xfer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        xfer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # BUG FIX: Bind em 0.0.0.0 (nao no IP especifico).
        # Clientes UEFI rigorosos (Dell, HP) exigem que a resposta venha do mesmo
        # endereco que recebeu o RRQ. Ao usar 0.0.0.0 o kernel roteia corretamente.
        xfer.bind(('0.0.0.0', 0))
        xfer.settimeout(5.0)

        try:
            file_size = path.stat().st_size

            # 1. Parsear Opcoes do RRQ (blksize e tsize)
            blksize = 512
            parts = rrq_data[2:].split(b'\x00')
            options = {}
            # parts[0]=filename, parts[1]=mode, depois pares chave/valor
            for i in range(2, len(parts) - 1, 2):
                if parts[i]:
                    opt_name = parts[i].decode(errors='ignore').lower()
                    val = parts[i + 1].decode(errors='ignore') if (i + 1) < len(parts) else ''
                    options[opt_name] = val

            use_oack = False
            oack_pkt = bytearray(b'\x00\x06')  # OACK Opcode
            if 'blksize' in options:
                # Limitar a 1468 para evitar fragmentacao em redes com MTU 1500
                blksize = min(int(options['blksize']), 1468)
                oack_pkt += b'blksize\x00' + str(blksize).encode() + b'\x00'
                use_oack = True
            if 'tsize' in options:
                oack_pkt += b'tsize\x00' + str(file_size).encode() + b'\x00'
                use_oack = True

            self._log(f"[TFTP] Enviando {filename} ({file_size // 1024} KB) | BlkSize={blksize}")

            # 2. Se pediu opcoes, mandar OACK primeiro e aguardar ACK(0)
            if use_oack:
                retries = 3
                oack_acked = False
                while retries > 0:
                    xfer.sendto(bytes(oack_pkt), client_addr)
                    try:
                        ack_data, _ = xfer.recvfrom(512)
                        # ACK para OACK deve ter block number = 0
                        if len(ack_data) >= 4 and ack_data[1] == 4 and ack_data[2:4] == b'\x00\x00':
                            oack_acked = True
                            break
                    except socket.timeout:
                        retries -= 1
                if not oack_acked:
                    self._log(f"[TFTP] Timeout aguardando ACK do OACK para {filename}")
                    return

            # 3. Transmissao do arquivo bloco a bloco (RFC 1350)
            with open(path, "rb") as f:
                block = 1
                while True:
                    chunk = f.read(blksize)
                    # chunk vazio ou menor que blksize = ultimo bloco (sinal de EOF)
                    is_last = len(chunk) < blksize

                    pkt = struct.pack(">HH", 3, block % 65536) + chunk
                    
                    # Enviar com retransmissao
                    retries = 5
                    acked = False
                    while retries > 0:
                        xfer.sendto(pkt, client_addr)
                        try:
                            ack_data, _ = xfer.recvfrom(512)
                            if len(ack_data) >= 4 and ack_data[1] == 4:
                                acked = True
                                break
                        except socket.timeout:
                            retries -= 1

                    if not acked:
                        self._log(f"[TFTP] Timeout enviando bloco {block} de {filename}")
                        return

                    block += 1
                    # BUG FIX: usar blksize negociado (nao hardcoded 512) para detectar EOF
                    if is_last:
                        break

            self._log(f"[TFTP] OK: {filename} enviado ({block - 1} blocos)")
        except Exception as e:
            self._log(f"[TFTP] ERRO transferindo {filename}: {e}")
        finally:
            xfer.close()

    # ------------------------------------------------------------------ #
    #  DHCP SERVER (State Machine: Discover→Offer, Request→ACK)
    # ------------------------------------------------------------------ #
    def _run_dhcp(self):
        try:
            # Socket 67 (DHCP Server) - usado para RECEBER e ENVIAR (porta origem 67 obrigatória)
            s67 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s67.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s67.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s67.bind(('0.0.0.0', 67))

            s4011 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s4011.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s4011.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s4011.bind(('0.0.0.0', 4011))

            # Socket de ENVIO DEDICADO - Forca o Windows a sair pela placa Ethernet
            self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Bind porta 67 e IP da interface
            try:
                self._send_sock.bind((self.ip, 67))
            except:
                self._send_sock.bind((self.ip, 0))

            self._log(f"[DHCP] ONLINE em 0.0.0.0:67 e 0.0.0.0:4011")
            self._log(f"[DHCP] Envio ancorado na placa {self.ip}")

            while self.is_running:
                r, _, _ = select.select([s67, s4011], [], [], 1.0)
                for sock in r:
                    try:
                        data, addr = sock.recvfrom(4096)
                        port = sock.getsockname()[1]
                        if len(data) > 240 and data[0] == 1:
                            self._handle_dhcp(sock, data, addr, port)
                    except Exception as e:
                        self._log(f"[DHCP] Erro ao processar pacote: {e}")
        except Exception as e:
            self._log(f"[DHCP] ERRO FATAL: {e}")

    def _parse_options(self, data: bytes) -> dict:
        """Extrai opcoes DHCP do pacote."""
        opts = {}
        i = 240
        while i < len(data):
            code = data[i]
            if code == 255:
                break
            if code == 0:
                i += 1
                continue
            if i + 1 >= len(data):
                break
            length = data[i + 1]
            if i + 2 + length > len(data):
                break
            opts[code] = data[i + 2:i + 2 + length]
            i += 2 + length
        return opts

    def _get_ip_for_mac(self, mac: bytes) -> str:
        """Aloca IP para o cliente PXE, assim como o iVentoy (pool .200+)."""
        mac_str = mac.hex(':')
        if mac_str not in self._leases:
            base = ".".join(self.ip.split('.')[:-1])
            # Forcar pool iniciando em 200
            self._leases[mac_str] = f"{base}.{max(200, self._next_ip_offset)}"
            self._next_ip_offset += 1
        return self._leases[mac_str]

    def _handle_dhcp(self, sock, data, addr, port):
        """Processa pacote DHCP em modo Normal (dando IP)."""
        xid = data[4:8]
        mac = data[28:34]
        mac_str = ':'.join(f'{b:02x}' for b in mac)

        opts = self._parse_options(data)
        msg_type = opts.get(53, b'\x01')[0]
        
        is_ipxe = 175 in opts
        vendor_class = opts.get(60, b'')
        is_pxe = vendor_class.startswith(b'PXEClient')

        if not is_pxe and not is_ipxe:
            return  # Ignorar tráfego nao-PXE

        if msg_type == 1:  # DHCPDISCOVER
            self._log(f"[DHCP] <<< DISCOVER PXE de {mac_str} (iPXE={is_ipxe})")
            self._send_dhcp_reply(sock, data, mac, xid, 2, is_ipxe)  # OFFER
        elif msg_type == 3:  # DHCPREQUEST
            req_ip = socket.inet_ntoa(opts[50]) if 50 in opts else "N/A"
            srv_id = socket.inet_ntoa(opts[54]) if 54 in opts else "N/A"
            self._log(f"[DHCP] <<< REQUEST PXE de {mac_str} na porta {port} (Requer IP: {req_ip}, Do Servidor: {srv_id})")
            
            # So responder com ACK se o Server ID for para nós, ou se nao tiver Server ID (renew)
            if srv_id == self.ip or srv_id == "N/A":
                self._send_dhcp_reply(sock, data, mac, xid, 5, is_ipxe)  # ACK
            else:
                self._log(f"[DHCP] Ignorando REQUEST (enderecado ao roteador {srv_id})")

    def _send_dhcp_reply(self, sock, data, mac, xid, reply_type, is_ipxe):
        """Envia pacote DHCP (OFFER ou ACK) com alocação de IP."""
        offered_ip = self._get_ip_for_mac(mac)
        boot_file = f"http://{self.ip}:8080/boot.ipxe" if is_ipxe else "ipxe.efi"
        type_name = "OFFER" if reply_type == 2 else "ACK"
        
        self._log(f"[DHCP] >>> {type_name}: IP={offered_ip} boot={boot_file}")

        pkt = bytearray(240)
        pkt[0] = 2       # BOOTREPLY
        pkt[1] = 1       # Ethernet
        pkt[2] = 6       # MAC length
        pkt[4:8] = xid
        pkt[10:12] = b'\x80\x00'  # Broadcast
        pkt[16:20] = socket.inet_aton(offered_ip)  # yiaddr (IP Oferecido)
        pkt[20:24] = socket.inet_aton(self.ip)     # siaddr (Server IP)
        pkt[28:34] = mac

        sname = self.ip.encode('ascii')[:64]
        pkt[44:44 + len(sname)] = sname

        bf = boot_file.encode('ascii')[:127] + b'\x00'
        pkt[108:108 + len(bf)] = bf

        pkt[236:240] = b'\x63\x82\x53\x63'  # Magic cookie

        options = bytearray()
        options += bytes([53, 1, reply_type])
        options += bytes([54, 4]) + socket.inet_aton(self.ip)
        options += bytes([1, 4]) + socket.inet_aton(self.mask)  # Subnet Mask
        options += bytes([3, 4]) + socket.inet_aton(self.ip)    # Router (Fake)
        options += bytes([51, 4]) + struct.pack('!I', 3600)     # Lease Time
        options += bytes([60, 9]) + b'PXEClient'
        
        # Option 43: Vendor-Specific (MÁGICA DO PXE)
        # Sub-opção 6: PXE_DISCOVERY_CONTROL = 8 (Pula a descoberta e vai direto pro TFTP)
        vendor_opts = bytes([6, 1, 8])
        options += bytes([43, len(vendor_opts)]) + vendor_opts
        
        tftp_name = self.ip.encode('ascii') + b'\x00'
        options += bytes([66, len(tftp_name)]) + tftp_name
        bf67 = boot_file.encode('ascii') + b'\x00'
        options += bytes([67, len(bf67)]) + bf67
        options += bytes([255])

        pkt += options

        try:
            # Enviar via broadcast global (obrigatorio para UEFI) usando o socket dedicado (Ethernet)
            self._send_sock.sendto(bytes(pkt), ('255.255.255.255', 68))
            self._log(f"[DHCP] >>> {type_name} enviado pela placa {self.ip}")
        except Exception as e:
            self._log(f"[DHCP] ERRO ao enviar {type_name}: {e}")

    # ------------------------------------------------------------------ #
    #  CONTROLE
    # ------------------------------------------------------------------ #
    def stop(self, log_cb=None):
        self.is_running = False
        if self._http_srv:
            self._http_srv.shutdown()
        msg = f"[STOP] Servidor PXE v{VERSION} encerrado."
        if log_cb:
            log_cb(msg)
        if self._log:
            self._log(msg)



def get_network_interfaces():
    """Detecta interfaces de rede ativas via PowerShell."""
    interfaces = []
    script = ("Get-NetIPConfiguration | Where-Object "
              "{ $_.NetAdapter.Status -eq 'Up' -and $_.IPv4Address } "
              "| ConvertTo-Json")
    try:
        res = subprocess.run(
            ['powershell', '-NoProfile', '-Command', script],
            capture_output=True, text=True, timeout=10
        )
        if not res.stdout.strip():
            return []
        data = json.loads(res.stdout)
        if isinstance(data, dict):
            data = [data]
        for item in data:
            prefix = int(item['IPv4Address']['PrefixLength'])
            mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
            mask = socket.inet_ntoa(struct.pack('!I', mask_int))
            interfaces.append({
                'name': item['InterfaceAlias'],
                'ip': item['IPv4Address']['IPAddress'],
                'mask': mask,
            })
    except Exception:
        hostname = socket.gethostname()
        interfaces.append({
            'name': 'Padrao',
            'ip': socket.gethostbyname(hostname),
            'mask': '255.255.255.0',
        })
    return interfaces
