"""Worker para extrair ISO e injetar drivers de rede automaticamente."""
import shutil
import subprocess
from pathlib import Path

from app.workers.base_worker import BaseWorker
from app.core.iso_service import IsoService, IsoError
from app.core.dism_service import DismService

# ── Pasta de drivers embutida no programa ────────────────────────────────── #
# Quando empacotado pelo PyInstaller, usa sys._MEIPASS
# Quando rodando como script, usa o caminho relativo normal
import sys as _sys
if getattr(_sys, 'frozen', False):
    _APP_BASE = Path(_sys._MEIPASS)
else:
    _APP_BASE = Path(__file__).parent.parent

# Primário: pasta dentro do próprio programa (app/resources/drivers)
_RESOURCES_DRIVERS = _APP_BASE / "app" / "resources" / "drivers"

# Fallback: Snappy Driver Installer externo (caso o usuário tenha instalado)
_SDI_DRIVERS = Path(r"E:\snappidriver\SDI\Drivers")

def _driver_pack(filename: str) -> Path:
    """Retorna o caminho do pacote .7z — primeiro no programa, depois no SDI externo."""
    internal = _RESOURCES_DRIVERS / filename
    if internal.exists():
        return internal
    external = _SDI_DRIVERS / filename
    if external.exists():
        return external
    return internal  # retorna o interno mesmo que não exista (erro será tratado depois)

# Pacotes de drivers LAN
SDI_LAN_INTEL   = _driver_pack("DP_LAN_Intel_26044.7z")
SDI_LAN_OTHERS  = _driver_pack("DP_LAN_Others_26044.7z")
SDI_LAN_REALTEK = _driver_pack("DP_LAN_Realtek-NT_26044.7z")

# Pacotes corporativos (Dell/HP/Lenovo 8ª geração+)
SDI_MASS_STORAGE = _driver_pack("DP_MassStorage_26044.7z")
SDI_CHIPSET      = _driver_pack("DP_Chipset_26044.7z")
SDI_WLAN         = _driver_pack("DP_WLAN-WiFi_26044.7z")

# Pasta temporaria de extracao dos drivers
DRIVER_EXTRACT_DIR = Path(r"C:\KIRO_Drivers_Temp")

# 7-Zip
_7ZIP_CANDIDATES = [
    r"C:\Program Files\7-Zip\7z.exe",
    r"C:\Program Files (x86)\7-Zip\7z.exe",
]


def _find_7zip() -> str | None:
    """Localiza 7z.exe — primeiro embutido no programa, depois no sistema."""
    import sys as _sys
    if getattr(_sys, 'frozen', False):
        _base = Path(_sys._MEIPASS)
    else:
        _base = Path(__file__).parent.parent

    # 1. Embutido em resources/tools/
    bundled = _base / "app" / "resources" / "tools" / "7z.exe"
    if bundled.exists():
        return str(bundled)

    # 2. Instalação padrão do sistema
    for c in _7ZIP_CANDIDATES:
        if Path(c).exists():
            return c

    import shutil as sh
    return sh.which("7z")


class ExtractIsoWorker(BaseWorker):
    """Extrai uma ISO para uma pasta de trabalho e injeta drivers de rede."""

    def __init__(self, iso_path: str, work_dir: str, parent=None):
        super().__init__(parent)
        self.iso_path = iso_path
        self.work_dir = work_dir

    def run(self):
        try:
            # ── 1. Extrair ISO ────────────────────────────────────────
            self._log(f"Iniciando extração: {self.iso_path}")
            self.progress.emit(5)

            svc = IsoService()
            svc.extract_iso(
                self.iso_path,
                self.work_dir,
                log_cb=self._log,
            )
            self.progress.emit(60)

            # ── 2. Detectar estrutura ─────────────────────────────────
            self._log("Detectando estrutura WinPE...")
            info = svc.detect_winpe_structure(self.work_dir)

            if info.get("boot_wim"):
                self._log(f"✅ boot.wim: {info['boot_wim']}")
            else:
                self._log("⚠️  boot.wim não localizado — verifique a ISO.")

            if info.get("bcd"):
                self._log(f"✅ BCD: {info['bcd']}")
            else:
                self._log("⚠️  BCD não localizado — boot PXE pode falhar.")

            if info.get("boot_sdi"):
                self._log(f"✅ boot.sdi: {info['boot_sdi']}")

            self.progress.emit(65)

            # Injeção de drivers removida daqui — agora é feita sob demanda
            # via diálogo na MainWindow após a extração

            self.progress.emit(100)
            self.finished.emit(True, "Extração concluída com sucesso.")

        except IsoError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            self.finished.emit(False, f"Erro inesperado: {e}")

    # ─────────────────────────────────────────────────────────────────── #
    def _inject_network_drivers(self, boot_wim: str):
        """Extrai drivers LAN do SDI e injeta no boot.wim via DISM."""
        self._log("─" * 50)
        self._log("🔌 Verificando necessidade de injeção de drivers...")

        wim_path = Path(boot_wim)
        work_dir_name = wim_path.parent.parent.name.lower()

        # ISOs que já têm drivers de rede completos — pula injeção
        SKIP_KEYWORDS = ["strelec", "hiren", "hirens", "win10xpe", "win11pe",
                         "sergei", "falconfour", "ubcd", "medicat"]
        for kw in SKIP_KEYWORDS:
            if kw in work_dir_name:
                self._log(f"✅ ISO '{kw}' já possui drivers de rede — injeção ignorada.")
                self._log("─" * 50)
                return

        self._log("📦 Iniciando injeção de drivers de rede...")
        mount_dir = wim_path.parent.parent / f"Mount_{wim_path.parent.parent.name}"

        # ── Extrair drivers do SDI ────────────────────────────────────
        driver_dir = self._extract_sdi_drivers()
        if not driver_dir:
            self._log("⚠️  Drivers SDI não encontrados — injeção ignorada.")
            self._log("    Instale o Snappy Driver Installer em E:\\snappidriver\\SDI")
            return

        # ── Limpar mount travado se existir ──────────────────────────
        self._log("🧹 Limpando mounts DISM anteriores...")
        subprocess.run(
            ["dism", "/Cleanup-Wim"],
            capture_output=True, timeout=60
        )
        if mount_dir.exists():
            subprocess.run(
                f'rd /s /q "{mount_dir}"',
                shell=True, capture_output=True, timeout=30
            )

        # ── Montar WIM ────────────────────────────────────────────────
        dism = DismService()
        self._log(f"📂 Montando boot.wim em {mount_dir}...")
        result = dism.mount_wim(wim_path, mount_dir, index=1, log_cb=self._log)

        # mount_wim retorna (bool, str) com o dir real usado
        if isinstance(result, tuple):
            ok, real_mount = result
        else:
            ok, real_mount = result, str(mount_dir)

        if not ok:
            self._log("❌ Falha ao montar boot.wim — injeção cancelada.")
            return

        real_mount_path = Path(real_mount)

        # ── Injetar drivers ───────────────────────────────────────────
        self._log(f"💉 Injetando drivers de rede de: {driver_dir}")

        # Coleta todas as subpastas que contenham .inf x64
        # Filtra pastas x64 para evitar erro 50 (incompatibilidade de arquitetura)
        inf_dirs: list[Path] = []
        for inf in driver_dir.rglob("*.inf"):
            parent = inf.parent
            name_lower = str(parent).lower()
            # Aceita pastas x64, 10x64, amd64 — rejeita x86, xp, ia64
            if any(k in name_lower for k in ("x64", "amd64", "10x64", "ndis6")):
                if parent not in inf_dirs:
                    inf_dirs.append(parent)
            elif not any(k in name_lower for k in ("x86", "xp", "ia64", "win7x86")):
                # Pasta sem indicador de arch — inclui mesmo assim
                if parent not in inf_dirs:
                    inf_dirs.append(parent)

        if not inf_dirs:
            # Fallback: injeta tudo com recurse
            inf_dirs = [driver_dir]

        self._log(f"   → {len(inf_dirs)} pastas de driver encontradas")
        total_ok = 0
        for d in inf_dirs:
            ok = dism.add_drivers(
                real_mount_path,
                d,
                recurse=False,  # já estamos pasta por pasta
                log_cb=None,    # silencioso para não poluir o log
            )
            if ok:
                total_ok += 1

        self._log(f"✅ {total_ok}/{len(inf_dirs)} pacotes de driver injetados!")

        # ── Desmontar e salvar ────────────────────────────────────────
        self._log("💾 Salvando boot.wim com drivers...")
        saved = dism.unmount_wim(real_mount_path, commit=True, log_cb=self._log)

        if saved:
            self._log("✅ boot.wim salvo com drivers de rede!")
        else:
            self._log("❌ Erro ao salvar boot.wim.")

        # ── Limpeza ───────────────────────────────────────────────────
        try:
            if DRIVER_EXTRACT_DIR.exists():
                shutil.rmtree(str(DRIVER_EXTRACT_DIR), ignore_errors=True)
        except Exception:
            pass

        self._log("─" * 50)

    def _extract_sdi_drivers(self) -> Path | None:
        """Extrai os pacotes LAN do SDI e retorna a pasta com os .inf."""
        seven_zip = _find_7zip()
        if not seven_zip:
            self._log("⚠️  7-Zip não encontrado — não é possível extrair drivers SDI.")
            return None

        # Pacotes a extrair (Intel + Others para cobrir mais placas)
        packages = [
            (SDI_LAN_INTEL,   "Intel"),
            (SDI_LAN_OTHERS,  "Others"),
            (SDI_LAN_REALTEK, "Realtek"),
        ]

        extracted_any = False
        for pkg, label in packages:
            if not pkg.exists():
                self._log(f"⚠️  Pacote SDI não encontrado: {pkg.name}")
                continue

            dest = DRIVER_EXTRACT_DIR / label
            dest.mkdir(parents=True, exist_ok=True)

            self._log(f"📦 Extraindo {pkg.name}...")
            result = subprocess.run(
                [seven_zip, "x", str(pkg), f"-o{dest}", "-y"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                self._log(f"✅ {label} extraído.")
                extracted_any = True
            else:
                self._log(f"⚠️  Erro ao extrair {label}: {result.stderr[:100]}")

        if not extracted_any:
            return None

        return DRIVER_EXTRACT_DIR


# ══════════════════════════════════════════════════════════════════════════════
# Worker: Injeção de Pacote Corporativo
# Notebooks Dell Latitude / HP EliteBook / Lenovo ThinkPad — 8ª geração+
# Drivers: LAN Intel, LAN Others, LAN Realtek, MassStorage, Chipset, WLAN
# ══════════════════════════════════════════════════════════════════════════════

# Mapeamento de pacotes por categoria
CORPORATE_PACKS = {
    "lan": [
        ("DP_LAN_Intel_26044.7z",      "LAN Intel (I219-LM)"),
        ("DP_LAN_Others_26044.7z",     "LAN Others (Broadcom/Marvell)"),
        ("DP_LAN_Realtek-NT_26044.7z", "LAN Realtek"),
    ],
    "storage": [
        ("DP_MassStorage_26044.7z",    "Mass Storage (NVMe/SATA)"),
    ],
    "chipset": [
        ("DP_Chipset_26044.7z",        "Chipset Intel 8ª gen+"),
    ],
    "wlan": [
        ("DP_WLAN-WiFi_26044.7z",      "Wi-Fi (Intel AX/9xxx/8xxx)"),
    ],
}


class CorporateDriverWorker(BaseWorker):
    """
    Injeta pacote de drivers corporativos no boot.wim.
    Cobre Dell Latitude, HP EliteBook, Lenovo ThinkPad — 8ª geração Intel+.

    Parâmetros:
        boot_wim   : caminho completo do boot.wim já extraído
        categories : lista de categorias a injetar
                     ex: ["lan", "storage", "chipset", "wlan"]
    """

    def __init__(self, boot_wim: str, categories: list[str], parent=None):
        super().__init__(parent)
        self.boot_wim = Path(boot_wim)
        self.categories = categories

    def run(self):
        try:
            self._log("═" * 55)
            self._log("🏢 PACOTE CORPORATIVO — Dell/HP/Lenovo 8ª gen+")
            self._log("═" * 55)

            seven_zip = _find_7zip()
            if not seven_zip:
                self.finished.emit(False, "7-Zip não encontrado. Instale em C:\\Program Files\\7-Zip")
                return

            # ── Montar WIM ───────────────────────────────────────────
            mount_dir = self.boot_wim.parent.parent / f"Mount_Corp_{self.boot_wim.parent.parent.name}"
            dism = DismService()

            self._log("🧹 Limpando mounts anteriores...")
            subprocess.run(["dism", "/Cleanup-Wim"], capture_output=True, timeout=60)
            if mount_dir.exists():
                subprocess.run(f'rd /s /q "{mount_dir}"', shell=True,
                               capture_output=True, timeout=30)

            self._log(f"📂 Montando boot.wim...")
            self.progress.emit(5)
            result = dism.mount_wim(self.boot_wim, mount_dir, index=1, log_cb=self._log)
            if isinstance(result, tuple):
                ok, real_mount = result
            else:
                ok, real_mount = result, str(mount_dir)

            if not ok:
                self.finished.emit(False, "Falha ao montar boot.wim.")
                return

            real_mount_path = Path(real_mount)
            self.progress.emit(10)

            # ── Extrair e injetar por categoria ──────────────────────
            total_cats = len(self.categories)
            injected_total = 0
            failed_packs = []

            for cat_idx, cat in enumerate(self.categories):
                packs = CORPORATE_PACKS.get(cat, [])
                if not packs:
                    continue

                self._log(f"\n📦 Categoria: {cat.upper()}")
                cat_extract_dir = DRIVER_EXTRACT_DIR / "corp" / cat
                cat_extract_dir.mkdir(parents=True, exist_ok=True)

                for filename, label in packs:
                    pack_path = _driver_pack(filename)
                    if not pack_path.exists():
                        self._log(f"  ⚠️  {label} — pacote não encontrado: {pack_path.name}")
                        failed_packs.append(label)
                        continue

                    self._log(f"  📥 Extraindo {label}...")
                    dest = cat_extract_dir / filename.replace(".7z", "")
                    dest.mkdir(parents=True, exist_ok=True)

                    result = subprocess.run(
                        [seven_zip, "x", str(pack_path), f"-o{dest}", "-y"],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode != 0:
                        self._log(f"  ❌ Erro ao extrair {label}")
                        failed_packs.append(label)
                        continue

                    # Coleta pastas x64 com .inf
                    inf_dirs: list[Path] = []
                    for inf in dest.rglob("*.inf"):
                        parent = inf.parent
                        name_lower = str(parent).lower()
                        if any(k in name_lower for k in ("x64", "amd64", "10x64", "ndis6")):
                            if parent not in inf_dirs:
                                inf_dirs.append(parent)
                        elif not any(k in name_lower for k in ("x86", "xp", "ia64", "win7x86")):
                            if parent not in inf_dirs:
                                inf_dirs.append(parent)

                    if not inf_dirs:
                        inf_dirs = [dest]

                    self._log(f"  💉 Injetando {label} ({len(inf_dirs)} pastas)...")
                    ok_count = 0
                    for d in inf_dirs:
                        if dism.add_drivers(real_mount_path, d, recurse=False, log_cb=None):
                            ok_count += 1
                    injected_total += ok_count
                    self._log(f"  ✅ {ok_count}/{len(inf_dirs)} drivers injetados")

                # Progresso por categoria
                prog = 10 + int((cat_idx + 1) / total_cats * 75)
                self.progress.emit(prog)

            # ── Salvar WIM ───────────────────────────────────────────
            self._log("\n💾 Salvando boot.wim com drivers corporativos...")
            self.progress.emit(88)
            saved = dism.unmount_wim(real_mount_path, commit=True, log_cb=self._log)

            # ── Limpeza ──────────────────────────────────────────────
            try:
                corp_dir = DRIVER_EXTRACT_DIR / "corp"
                if corp_dir.exists():
                    shutil.rmtree(str(corp_dir), ignore_errors=True)
            except Exception:
                pass

            self.progress.emit(100)

            if saved:
                msg = f"✅ Pacote corporativo injetado! {injected_total} drivers."
                if failed_packs:
                    msg += f"\n⚠️ Não encontrados: {', '.join(failed_packs)}"
                self.finished.emit(True, msg)
            else:
                self.finished.emit(False, "Erro ao salvar boot.wim.")

        except Exception as e:
            self.finished.emit(False, f"Erro inesperado: {e}")
