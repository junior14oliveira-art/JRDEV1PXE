"""Worker para construir a ISO final em background."""
from app.workers.base_worker import BaseWorker
from app.core.iso_service import IsoService, IsoError


class BuildIsoWorker(BaseWorker):
    """Constrói uma nova ISO a partir do diretório de trabalho."""

    def __init__(self, source_dir: str, output_iso: str,
                 oscdimg_path: str = "oscdimg",
                 volume_label: str = "WINPE_CUSTOM",
                 parent=None):
        super().__init__(parent)
        self.source_dir = source_dir
        self.output_iso = output_iso
        self.oscdimg_path = oscdimg_path
        self.volume_label = volume_label

    def run(self):
        try:
            self._log(f"Iniciando construção da ISO...")
            self._log(f"Fonte : {self.source_dir}")
            self._log(f"Saída : {self.output_iso}")
            self.progress.emit(10)

            svc = IsoService()
            svc.build_iso(
                source_dir=self.source_dir,
                output_iso=self.output_iso,
                oscdimg_path=self.oscdimg_path,
                volume_label=self.volume_label,
                log_cb=self._log,
            )
            self.progress.emit(100)
            self.finished.emit(True, f"ISO gerada: {self.output_iso}")
        except IsoError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            self.finished.emit(False, f"Erro inesperado: {e}")
