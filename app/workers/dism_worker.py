"""Worker para operações DISM em background."""
from app.workers.base_worker import BaseWorker
from app.core.dism_service import DismService, DismError


class DismMountWorker(BaseWorker):
    """Monta um arquivo WIM."""
    def __init__(self, wim_path: str, mount_dir: str, index: int = 1, parent=None):
        super().__init__(parent)
        self.wim_path = wim_path
        self.mount_dir = mount_dir
        self.index = index

    def run(self):
        try:
            self._log(f"Montando WIM: {self.wim_path} (Index {self.index})...")
            self.progress.emit(10)
            svc = DismService()
            result = svc.mount_wim(
                wim_path=self.wim_path,
                mount_dir=self.mount_dir,
                index=self.index,
                log_cb=self._log
            )
            # mount_wim retorna (success, real_mount_dir)
            success, real_mount_dir = result if isinstance(result, tuple) else (result, self.mount_dir)
            self.progress.emit(100)
            if success:
                # Passa o diretório real usado (pode ser alternativo se o original estava travado)
                self.finished.emit(True, real_mount_dir)
            else:
                self.finished.emit(False, "Falha ao montar WIM. Verifique os logs.")
        except Exception as e:
            self.finished.emit(False, f"Erro: {e}")


class DismUnmountWorker(BaseWorker):
    """Desmonta um arquivo WIM."""
    def __init__(self, mount_dir: str, commit: bool = True, parent=None):
        super().__init__(parent)
        self.mount_dir = mount_dir
        self.commit = commit

    def run(self):
        try:
            action = "Salvando" if self.commit else "Descartando"
            self._log(f"Desmontando WIM ({action} alterações)...")
            self.progress.emit(10)
            svc = DismService()
            success = svc.unmount_wim(
                mount_dir=self.mount_dir,
                commit=self.commit,
                log_cb=self._log
            )
            self.progress.emit(100)
            if success:
                self.finished.emit(True, "WIM desmontado com sucesso.")
            else:
                self.finished.emit(False, "Falha ao desmontar WIM. Use 'Limpar Montagens' se necessário.")
        except Exception as e:
            self.finished.emit(False, f"Erro: {e}")
class DismPatchWorker(BaseWorker):
    """Corrige caminhos em scripts BAT/CMD para o Disco X:."""
    def __init__(self, mount_dir: str, parent=None):
        super().__init__(parent)
        self.mount_dir = mount_dir

    def run(self):
        try:
            self._log("Iniciando análise de scripts (.bat/.cmd)...")
            self.progress.emit(20)
            svc = DismService()
            count = svc.patch_scripts_for_pe(self.mount_dir, log_cb=self._log)
            self.progress.emit(100)
            self.finished.emit(True, f"Sucesso! {count} scripts foram adaptados para o Disco X:.")
        except Exception as e:
            self.finished.emit(False, f"Erro ao corrigir scripts: {e}")
