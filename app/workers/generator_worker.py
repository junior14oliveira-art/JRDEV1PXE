"""Worker para geração de WinPE em background."""
from app.workers.base_worker import BaseWorker
from app.core.generator_service import GeneratorService

class GeneratorWorker(BaseWorker):
    def __init__(self, dest_iso: str, arch: str = "amd64", parent=None):
        super().__init__(parent)
        self.dest_iso = dest_iso
        self.arch = arch

    def run(self):
        try:
            self._log("Iniciando geração de WinPE limpo via ADK...")
            self.progress.emit(20)
            svc = GeneratorService()
            success = svc.generate_vanilla_pe(
                dest_iso=self.dest_iso,
                arch=self.arch,
                log_cb=self._log
            )
            self.progress.emit(100)
            if success:
                self.finished.emit(True, f"WinPE gerado com sucesso: {self.dest_iso}")
            else:
                self.finished.emit(False, "Falha ao gerar WinPE. Verifique se o WinPE Add-on do ADK está instalado.")
        except Exception as e:
            self.finished.emit(False, f"Erro: {e}")
