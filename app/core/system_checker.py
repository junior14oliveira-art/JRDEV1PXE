"""Verificador de dependências e ambiente do sistema para o WinPE Studio."""
import subprocess
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass, field
from loguru import logger
from app.utils.disk_utils import get_free_space_gb


@dataclass
class SystemStatus:
    is_admin: bool = False
    adk_path: str = ""
    adk_found: bool = False
    dism_path: str = ""
    dism_found: bool = False
    oscdimg_path: str = ""
    oscdimg_found: bool = False
    sevenz_path: str = ""
    sevenz_found: bool = False
    free_space_gb: float = 0.0
    windows_version: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.dism_found and self.is_admin and self.free_space_gb >= 5.0


# ── Localiza pasta de ferramentas embutidas ───────────────────────────────── #
def _get_tools_dir() -> Path:
    """Retorna a pasta tools/ — funciona como script e como .exe empacotado."""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent
    return base / "app" / "resources" / "tools"


# Caminhos conhecidos do Windows ADK
_ADK_ROOTS = [
    r"C:\Program Files (x86)\Windows Kits\10",
    r"C:\Program Files\Windows Kits\10",
]
_OSCDIMG_SUBPATHS = [
    r"Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe",
    r"Assessment and Deployment Kit\Deployment Tools\x86\Oscdimg\oscdimg.exe",
]


def detect_system() -> SystemStatus:
    """Executa todas as verificações de ambiente e retorna um SystemStatus."""
    import ctypes
    status = SystemStatus()
    tools_dir = _get_tools_dir()

    # Verificar admin
    try:
        status.is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not status.is_admin:
            status.warnings.append("Sem privilégios de administrador. DISM exige admin.")
    except Exception:
        pass

    # DISM (nativo do Windows)
    dism = shutil.which("dism") or r"C:\Windows\System32\dism.exe"
    if Path(dism).exists():
        status.dism_found = True
        status.dism_path = dism
        logger.info(f"DISM encontrado: {dism}")
    else:
        status.errors.append("DISM não encontrado. Instale o Windows ADK.")

    # ── oscdimg: primeiro nas ferramentas embutidas, depois no ADK ────────── #
    bundled_oscdimg = tools_dir / "oscdimg.exe"
    if bundled_oscdimg.exists():
        status.oscdimg_found = True
        status.oscdimg_path = str(bundled_oscdimg)
        status.adk_found = True
        logger.info(f"oscdimg embutido: {bundled_oscdimg}")
    else:
        # Fallback: ADK instalado no sistema
        for adk_root in _ADK_ROOTS:
            if Path(adk_root).exists():
                status.adk_found = True
                status.adk_path = adk_root
                for sub in _OSCDIMG_SUBPATHS:
                    candidate = Path(adk_root) / sub
                    if candidate.exists():
                        status.oscdimg_found = True
                        status.oscdimg_path = str(candidate)
                        logger.info(f"oscdimg ADK: {candidate}")
                        break
                break

    if not status.oscdimg_found:
        status.warnings.append("oscdimg não encontrado — geração de ISO indisponível.")

    # ── 7-Zip: primeiro embutido, depois sistema ──────────────────────────── #
    bundled_7z = tools_dir / "7z.exe"
    if bundled_7z.exists():
        status.sevenz_found = True
        status.sevenz_path = str(bundled_7z)
        logger.info(f"7-Zip embutido: {bundled_7z}")
    else:
        for candidate in [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            shutil.which("7z") or "",
        ]:
            if candidate and Path(candidate).exists():
                status.sevenz_found = True
                status.sevenz_path = candidate
                logger.info(f"7-Zip sistema: {candidate}")
                break

    if not status.sevenz_found:
        status.warnings.append("7-Zip não encontrado — injeção de drivers indisponível.")

    # Espaço em disco
    status.free_space_gb = get_free_space_gb("E:\\") or get_free_space_gb("C:\\")
    if status.free_space_gb < 5.0:
        status.warnings.append(f"Pouco espaço em disco: {status.free_space_gb} GB livres.")

    # Versão do Windows
    try:
        result = subprocess.run(
            ["cmd", "/c", "ver"], capture_output=True, text=True, timeout=5
        )
        status.windows_version = result.stdout.strip()
    except Exception:
        status.windows_version = "Desconhecida"

    return status
