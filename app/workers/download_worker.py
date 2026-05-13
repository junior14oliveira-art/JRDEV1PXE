"""Worker para baixar arquivos em background."""
from app.workers.base_worker import BaseWorker
from app.core.download_service import DownloadService

class DownloadWorker(BaseWorker):
    def __init__(self, url: str, dest_path: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            self._log(f"Baixando imagem base...")
            svc = DownloadService()
            success = svc.download_file(
                url=self.url,
                dest_path=self.dest_path,
                progress_cb=self.progress.emit,
                log_cb=self._log
            )
            if success:
                self.finished.emit(True, f"Download concluído: {self.dest_path}")
            else:
                self.finished.emit(False, "Falha no download. Verifique sua conexão.")
        except Exception as e:
            self.finished.emit(False, f"Erro: {e}")
