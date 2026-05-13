"""Orquestrador principal — instancia a janela e inicia a aplicação."""
from loguru import logger
from app.ui.main_window import MainWindow


class MainController:
    """
    Controlador principal. Instancia a MainWindow e inicializa a aplicação.
    A lógica de operações (ISO, DISM) é gerenciada pelos Workers dentro
    da própria MainWindow, mantendo o código simples.
    """

    def __init__(self):
        self.view = MainWindow()
        logger.info("WinPE Studio inicializado.")

    def start(self) -> None:
        """Exibe a janela principal."""
        self.view.show()
