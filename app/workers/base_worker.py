"""Worker base: executa tarefas pesadas em thread separada sem travar a UI."""
from PySide6.QtCore import QThread, Signal


class BaseWorker(QThread):
    """
    Thread base para tarefas longas.
    Emite sinais de progresso, log e conclusão.
    """
    log_message = Signal(str)          # Linha de log para exibir
    progress = Signal(int)             # 0-100
    finished = Signal(bool, str)       # sucesso, mensagem final

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        """Sobrescrever nas subclasses."""
        raise NotImplementedError

    def _log(self, msg: str):
        self.log_message.emit(msg)
