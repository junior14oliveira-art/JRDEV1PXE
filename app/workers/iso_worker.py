"""Worker para extrair ISO em background."""
from pathlib import Path
from app.workers.base_worker import BaseWorker
from app.core.iso_service import IsoService, IsoError


class ExtractIsoWorker(BaseWorker):
    """Extrai uma ISO para uma pasta de trabalho."""

    def __init__(self, iso_path: str, work_dir: str, parent=None):
        super().__init__(parent)
        self.iso_path = iso_path
        self.work_dir = work_dir

    def run(self):
        try:
            self._log(f"Iniciando extração: {self.iso_path}")
            self.progress.emit(5)

            svc = IsoService()
            svc.extract_iso(
                self.iso_path,
                self.work_dir,
                log_cb=self._log,
            )
            self.progress.emit(80)

            self._log("Detectando estrutura WinPE...")
            info = svc.detect_winpe_structure(self.work_dir)
            self.progress.emit(100)

            if info.get("boot_wim"):
                self._log(f"✅ boot.wim encontrado: {info['boot_wim']}")
            else:
                self._log("⚠️  boot.wim não localizado — verifique a ISO.")

            if info.get("bcd"):
                self._log(f"✅ BCD encontrado: {info['bcd']}")
            else:
                self._log("⚠️  BCD não localizado — boot PXE pode falhar (0xc000000f).")

            if info.get("boot_sdi"):
                self._log(f"✅ boot.sdi encontrado: {info['boot_sdi']}")
            else:
                self._log("⚠️  boot.sdi não localizado.")

            self.finished.emit(True, "Extração concluída com sucesso.")
        except IsoError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            self.finished.emit(False, f"Erro inesperado: {e}")
