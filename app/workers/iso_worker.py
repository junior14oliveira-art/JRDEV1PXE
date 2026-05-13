"""Worker para extrair ISO e injetar drivers de rede automaticamente."""
import shutil
import subprocess
from pathlib import Path

from app.workers.base_worker import BaseWorker
from app.core.iso_service import IsoService, IsoError
from app.core.dism_service import DismService

# Pacote de drivers LAN Intel do Snappy Driver Installer
SDI_LAN_INTEL = Path(r"E:\snappidriver\SDI\Drivers\DP_LAN_Intel_26044.7z")
SDI_LAN_OTHERS = Path(r"E:\snappidriver\SDI\Drivers\DP_LAN_Others_26044.7z")
SDI_LAN_REALTEK = Path(r"E:\snappidriver\SDI\Drivers\DP_LAN_Realtek-NT_26044.7z")

# Pasta temporaria de extracao dos drivers
DRIVER_EXTRACT_DIR = Path(r"C:\KIRO_Drivers_Temp")

# 7-Zip
_7ZIP_CANDIDATES = [
    r"C:\Program Files\7-Zip\7z.exe",
    r"C:\Program Files (x86)\7-Zip\7z.exe",
]


def _find_7zip() -> str | None:
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
